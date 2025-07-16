import os
import sqlite3
import time
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, Literal, Tuple
from dotenv import load_dotenv
from pathlib import PurePath
from Bio import Entrez
import xml.etree.ElementTree as ET

path = PurePath(__file__).parent.parent.parent / ".env"
load_dotenv()
EMAIL = os.getenv("NCBI_EMAIL")


class PubMedClient:
    def __init__(self, cache_dir: str = ".cache", rate_limit_delay: float = 0.34):
        """
        Initialize PubMedClient with caching and rate limiting.

        Args:
            cache_dir: Directory to store cache database
            rate_limit_delay: Delay between requests in seconds (default: 0.34s = ~3 requests/second)
        """
        if not EMAIL:
            raise ValueError("NCBI_EMAIL environment variable is not set. Please set it to your email address.")

        Entrez.email = EMAIL
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0

        # Setup cache directory and database
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_db_path = self.cache_dir / "pubmed_cache.db"
        self._init_cache_db()

    def _init_cache_db(self):
        """Initialize SQLite cache database."""
        with sqlite3.connect(self.cache_db_path) as conn:
            conn.execute("""
                         CREATE TABLE IF NOT EXISTS cache
                         (
                             cache_key TEXT PRIMARY KEY,
                             method TEXT NOT NULL,
                             pmid TEXT NOT NULL,
                             response_data TEXT NOT NULL,
                             timestamp REAL NOT NULL
                         )
                         """)
            conn.commit()

    def _get_cache_key(self, method: str, pmid: str) -> str:
        """Generate cache key for request."""
        return hashlib.md5(f"{method}:{pmid}".encode()).hexdigest()

    def _get_cached_response(self, cache_key: str) -> Optional[str]:
        """Retrieve cached response if it exists."""
        with sqlite3.connect(self.cache_db_path) as conn:
            cursor = conn.execute(
                "SELECT response_data FROM cache WHERE cache_key = ?",
                (cache_key,)
            )
            result = cursor.fetchone()
            return result[0] if result else None

    def _cache_response(self, cache_key: str, method: str, pmid: str, response_data: str):
        """Cache the response data."""
        with sqlite3.connect(self.cache_db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cache (cache_key, method, pmid, response_data, timestamp) VALUES (?, ?, ?, ?, ?)",
                (cache_key, method, pmid, response_data, time.time())
            )
            conn.commit()

    def _rate_limit(self):
        """Implement rate limiting by adding delay if necessary."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_request
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def _make_entrez_request(self, method: Literal['get_title_and_abstract', 'get_full_text'], pmid: str) -> str:
        """Make rate-limited request to Entrez API."""
        cache_key = self._get_cache_key(method, pmid)

        # Check cache first
        cached_response = self._get_cached_response(cache_key)
        if cached_response:
            return cached_response

        # Apply rate limiting
        self._rate_limit()

        # Make the actual request
        if method == "get_title_and_abstract":
            handle = Entrez.efetch(db="pubmed", id=pmid, retmode="xml", rettype="abstract")
            response_data = handle.read()
            handle.close()
        elif method == "get_full_text":
            # For full text, we need to get PMC ID first, then fetch from PMC
            response_data = self._fetch_full_text_from_pmc(pmid)
        else:
            raise ValueError(f"Unknown method: {method}")

        # Cache the response
        self._cache_response(cache_key, method, pmid, response_data)

        return response_data


    def _fetch_full_text_from_pmc(self, pmid: str) -> str:
        """Fetch full text from PMC using PMID."""
        try:
            # Step 1: Get PMCID from PMID
            self._rate_limit()  # Rate limit for the elink request
            handle = Entrez.elink(dbfrom="pubmed", db="pmc", id=pmid, linkname="pubmed_pmc")
            linkset = Entrez.read(handle)
            handle.close()

            try:
                pmc_id = linkset[0]["LinkSetDb"][0]["Link"][0]["Id"]
            except (IndexError, KeyError):
                return "Full text not available"

            # Step 2: Fetch full text JATS XML from PMC
            self._rate_limit()  # Rate limit for the efetch request
            handle = Entrez.efetch(db="pmc", id=pmc_id, rettype="full", retmode="xml")
            xml_data = handle.read()
            handle.close()

            return xml_data

        except Exception as e:
            return f"Error fetching full text: {str(e)}"

    def _parse_title_and_abstract(self, xml_data: str) -> Tuple[str, str]:
        """Parse XML response to extract title and abstract.
        Return a tuple of (title, abstract)."""
        try:
            root = ET.fromstring(xml_data)

            # Find the article
            article = root.find('.//Article')
            if article is None:
                return "Article not found in response"

            # Extract title
            title_elem = article.find('.//ArticleTitle')
            title = title_elem.text if title_elem is not None else "Title not available"

            # Extract abstract
            abstract_parts = []
            abstract_elem = article.find('.//Abstract')
            if abstract_elem is not None:
                for abstract_text in abstract_elem.findall('.//AbstractText'):
                    label = abstract_text.get('Label', '')
                    text = abstract_text.text or ""
                    if label:
                        abstract_parts.append(f"{label}: {text}")
                    else:
                        abstract_parts.append(text)

            abstract = " ".join(abstract_parts) if abstract_parts else "Abstract not available"

            return title, abstract

        except ET.ParseError as e:
            return f"Error parsing XML response: {str(e)}"

    def _parse_full_text(self, xml_data: str) -> str:
        """Parse XML response to extract full text content from PMC."""
        if xml_data == "Full text not available":
            return xml_data

        if xml_data.startswith("Error fetching full text:"):
            return xml_data

        try:
            root = ET.fromstring(xml_data)

            # Step 3: Extract <body> content
            body = root.find(".//body")
            if body is None:
                return "Full text not available"

            sections = []

            for sec in body.findall(".//sec"):
                heading = sec.findtext("title") or ""
                paragraphs = []

                # Extract text from paragraphs, handling nested elements
                for p in sec.findall("p"):
                    paragraph_text = self._extract_text_from_element(p)
                    if paragraph_text:
                        paragraphs.append(paragraph_text)

                text = "\n".join(paragraphs).strip()

                if heading:
                    sections.append(f"### {heading}\n{text}")
                else:
                    sections.append(text)

            full_text = "\n\n".join(sections).strip()
            return full_text or "Full text not available"

        except ET.ParseError as e:
            return f"Error parsing XML response: {str(e)}"

    def _extract_text_from_element(self, element) -> str:
        """Extract text from an XML element, including nested elements."""
        text_parts = []

        # Get text before any child elements
        if element.text:
            text_parts.append(element.text)

        # Process child elements recursively
        for child in element:
            child_text = self._extract_text_from_element(child)
            if child_text:
                text_parts.append(child_text)

            # Get text after child element (tail)
            if child.tail:
                text_parts.append(child.tail)

        return "".join(text_parts).strip()

    def get_title_and_abstract(self, pmid: str) -> Tuple[str, str]:
        """
        Retrieve title and abstract for a given PMID.

        Args:
            pmid: PubMed ID as string

        Returns:
            String containing title and abstract
        """
        xml_data = self._make_entrez_request("get_title_and_abstract", pmid)
        return self._parse_title_and_abstract(xml_data)

    def get_full_text(self, pmid: str) -> str:
        """
        Retrieve full text content for a given PMID from PMC.

        Args:
            pmid: PubMed ID as string

        Returns:
            String containing full text content or "Full text not available" if not accessible
        """
        xml_data = self._make_entrez_request("get_full_text", pmid)
        if isinstance(xml_data, bytes):
            xml_data = xml_data.decode("utf-8")
        return self._parse_full_text(xml_data)

    def clear_cache(self):
        """Clear all cached data."""
        with sqlite3.connect(self.cache_db_path) as conn:
            conn.execute("DELETE FROM cache")
            conn.commit()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with sqlite3.connect(self.cache_db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM cache")
            total_entries = cursor.fetchone()[0]

            cursor = conn.execute("SELECT method, COUNT(*) FROM cache GROUP BY method")
            method_counts = dict(cursor.fetchall())

            return {
                "total_entries": total_entries,
                "method_counts": method_counts,
                "cache_db_path": str(self.cache_db_path)
            }

if __name__ == "__main__":
    # Example usage
    client = PubMedClient()

    pmids = [
          21561886,
          30208301,
          34774977,
          29959986,
          26593444,
          20567778,
          33148531,
          29211853,
          21985060,
          31935362,
          9011,
          1710653,
          24015256
    ]
    for pmid in pmids:
        title, abstract = client.get_title_and_abstract(pmid)
        print(f"# {title}\n\n{abstract}")
        print("="*100)