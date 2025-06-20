import os
from typing import Optional
from xml.etree import ElementTree as ET

from mcp.server.fastmcp import FastMCP
from Bio import Entrez
from dotenv import load_dotenv

load_dotenv()
EMAIL = os.getenv("NCBI_EMAIL")

mcp = FastMCP("PubMed")

@mcp.tool()
async def search_pubmed(query: str, max_results: int = 10) -> str:
    """
    Search PubMed for articles matching the query. It returns a list of:
    - Title
    - Authors
    - Published dated
    - PMID (PubMed ID)
    :param query: Search query string
    :param max_results: Maximum number of results to return
    """
    if not EMAIL:
        raise ValueError("NCBI_EMAIL environment variable is not set. Please set it to your email address.")
    Entrez.email = EMAIL
    with Entrez.esearch(db="pubmed", term=query, retmax=max_results) as handle:
        result = Entrez.read(handle)
        id_list = result["IdList"]

    if not id_list:
        return "No articles found."

    # Alternatively, parse XML for richer info
    with Entrez.efetch(db="pubmed", id=",".join(id_list), rettype="xml", retmode="xml") as handle:
        articles = Entrez.read(handle)

    lines = []
    for article in articles["PubmedArticle"]:
        citation = article["MedlineCitation"]
        pmid = citation["PMID"]
        article_info = citation["Article"]

        title = article_info.get("ArticleTitle", "No title available")
        authors_list = article_info.get("AuthorList", [])
        authors = ", ".join(
            f"{a.get('LastName', '')} {a.get('Initials', '')}".strip()
            for a in authors_list if "LastName" in a and "Initials" in a
        ) or "No authors listed"

        date = article_info.get("Journal", {}).get("JournalIssue", {}).get("PubDate", {})
        pub_date = date.get("Year") or date.get("MedlineDate") or "No date"

        lines.append(f"Title: {title}\nAuthors: {authors}\nDate: {pub_date}\nPMID: {pmid}\n")

    return "\n".join(lines)


@mcp.tool()
async def get_pubmed_abstract(pmid: str) -> str:
    """
    Get the abstract for a specific PubMed article by its PMID and tells if a record exists in PubMed Central (PMC).
    :param pmid: PubMed article ID
    """
    if not EMAIL:
        raise ValueError("NCBI_EMAIL environment variable is not set. Please set it to your email address.")
    Entrez.email = EMAIL
    with Entrez.efetch(db="pubmed", id=pmid, rettype="xml", retmode="xml") as handle:
        records = Entrez.read(handle)

    try:
        article = records["PubmedArticle"][0]
        citation = article["MedlineCitation"]
        article_data = citation.get("Article", {})
        abstract_parts = article_data.get("Abstract", {}).get("AbstractText", [])

        # Join abstract parts (some articles have sections)
        if isinstance(abstract_parts, list):
            abstract = " ".join(str(part) for part in abstract_parts)
        else:
            abstract = str(abstract_parts)

        abstract = abstract.strip() or "No abstract available."

    except Exception as e:
        return f"Could not retrieve abstract: {e}"

    # Check for full text in PubMed Central (PMC)
    with Entrez.elink(dbfrom="pubmed", db="pmc", id=pmid, linkname="pubmed_pmc") as handle:
        linkset = Entrez.read(handle)

    has_full_text = False
    try:
        links = linkset[0]["LinkSetDb"][0]["Link"]
        has_full_text = len(links) > 0
    except (IndexError, KeyError):
        pass

    status = "Full record available in PMC." if has_full_text else "Full no record available in PMC."

    return f"{abstract}\n\n{status}"


@mcp.tool()
async def get_related_articles(pmid: str, max_results: int = 5) -> str:
    """
    Find articles related to a specific PubMed article.
    :param pmid: PubMed ID of the seed article
    :param max_results: Maximum number of related articles to return (default: 5)
    """
    if not EMAIL:
        raise ValueError("NCBI_EMAIL environment variable is not set. Please set it to your email address.")
    Entrez.email = EMAIL

    # Step 1: Get related article PMIDs using elink
    with Entrez.elink(dbfrom="pubmed", db="pubmed", id=pmid, linkname="pubmed_pubmed", cmd="neighbor_score") as handle:
        linkset = Entrez.read(handle)

    try:
        related_ids = [
            link["Id"]
            for link in linkset[0]["LinkSetDb"][0]["Link"]
        ]
    except (IndexError, KeyError):
        return "No related articles found."

    if not related_ids:
        return "No related articles found."

    related_ids = related_ids[:max_results]

    # Step 2: Fetch article metadata
    with Entrez.efetch(db="pubmed", id=",".join(related_ids), rettype="xml", retmode="xml") as handle:
        records = Entrez.read(handle)

    # Step 3: Extract and format metadata
    lines = []
    for article in records["PubmedArticle"]:
        citation = article["MedlineCitation"]
        pmid = citation["PMID"]
        article_data = citation.get("Article", {})

        title = article_data.get("ArticleTitle", "No title available")
        authors_list = article_data.get("AuthorList", [])
        authors = ", ".join(
            f"{a.get('LastName', '')} {a.get('Initials', '')}".strip()
            for a in authors_list if "LastName" in a and "Initials" in a
        ) or "No authors listed"

        date = article_data.get("Journal", {}).get("JournalIssue", {}).get("PubDate", {})
        pub_date = date.get("Year") or date.get("MedlineDate") or "No date"

        lines.append(f"Title: {title}\nAuthors: {authors}\nDate: {pub_date}\nPMID: {pmid}\n")

    return "\n".join(lines)


@mcp.tool()
async def get_full_text(pmid: Optional[str] = None, pmcid: Optional[str] = None) -> str:
    """
    Get the full text of a PubMed article.
    If the full text is not available, it returns: 'Full text not available'.

    You can provide either a PMID (PubMed ID) or a PMCID (PubMed Central ID). However, you must provide at least one
    of them. If both are provided, the function will prioritize PMCID.

    :param pmid: PubMed article ID
    :param pmcid: PubMed central ID of the article
    """
    if not EMAIL:
        raise ValueError("NCBI_EMAIL environment variable is not set. Please set it to your email address.")
    Entrez.email = EMAIL

    try:
        # Step 1: Get PMCID
        with Entrez.elink(dbfrom="pubmed", db="pmc", id=pmid, linkname="pubmed_pmc") as handle:
            linkset = Entrez.read(handle)

        try:
            pmc_id = linkset[0]["LinkSetDb"][0]["Link"][0]["Id"]
        except (IndexError, KeyError):
            return "Full text not available"

        # Step 2: Fetch full text JATS XML
        with Entrez.efetch(db="pmc", id=pmc_id, rettype="full", retmode="xml") as handle:
            tree = ET.parse(handle)
            root = tree.getroot()

        # Step 3: Extract <body> content
        body = root.find(".//body")
        if body is None:
            return "Full text not available"

        sections = []

        for sec in body.findall(".//sec"):
            heading = sec.findtext("title") or ""
            paragraphs = [p.text or "" for p in sec.findall("p")]
            text = "\n".join(paragraphs).strip()

            if heading:
                sections.append(f"### {heading}\n{text}")
            else:
                sections.append(text)

        full_text = "\n\n".join(sections).strip()
        return full_text or "Full text not available"

    except Exception as e:
        return f"Full text not available ({e})"
if __name__ == "__main__":
    mcp.run(transport='stdio')