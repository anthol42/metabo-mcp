import math
from pathlib import PurePath
from typing import Literal, List
from mcp.server.fastmcp import FastMCP
from client import PubChemClient
from Bio import Entrez
from dotenv import load_dotenv
import os
import json

path = PurePath(__file__).parent.parent / "pubmed/.env"
load_dotenv(dotenv_path=path)
EMAIL = os.getenv("NCBI_EMAIL")

mcp = FastMCP("PubChem")
client = PubChemClient()

def fetch_paper_titles(pmids: List[str]) -> List[str]:
    """
    Fetch the titles of papers given a list of PubMed IDs (PMIDs).
    :param pmids: List of PubMed IDs.
    :return: List of paper titles.
    """
    Entrez.email = EMAIL
    with Entrez.efetch(db="pubmed", id=",".join(pmids), rettype="xml", retmode="xml") as handle:
        articles = Entrez.read(handle)
        titles = []
        for article in articles.get("PubmedArticle", []):
            try:
                article_info = article["MedlineCitation"]["Article"]
                title = article_info.get("ArticleTitle", "No title available")
            except KeyError:
                title = "No title available"
            titles.append(title)
        return titles

@mcp.tool()
async def search(search_domain: Literal['substance', 'compound'],
            query_type: Literal['cid', 'name', 'smiles', 'inchi', 'inchikey', 'formula'],
            query: str,
            search_what: Literal['record', 'properties', 'synonyms', 'sids', 'cids',
                'classification', 'pubmed', 'description'] = 'description', page: int = 0) -> str:
    """
    Search for a compound or a substance in the PubChem database. You can search by different query types, but you must
    specify what type is your query. Then you can specify what you want to retrieve from the database. To get the
    common name, you can retrieve the 'description' field or the 'synonyms' field.

    If you want all the pubmed papers related to the compound, you can use 'pubmed'. Note that this may return a lot
    of results. If there are more than 25 results, they will be paginated.

    If you really want to retrieve the full record, you can use 'record', but this will return a lot of data.
    IMPORTANT: Do not use this unless you really need it.
    :param search_domain: In what domain of the database to search. Can be 'substance' or 'compound'.
    :param query_type: What is the query? A CID, name, SMILES, InChI, InChIKey, formula, etc.
    :param query: The query to search for.
    :param search_what: What to retrieve from the API. If 'record', it will return the full record.
    :param page: The page number of the results to return if the results are paginated. Default is 0.
    :return the data as a JSON string.
    """
    resp = client.get(search_domain, query_type, query, search_what)

    if search_what == "pubmed":
        out = ""
        for res in resp:
            out += f"\nCID: {res['CID']}\n"
            ids = res["PubMedID"]
            # Paginate the results
            start = page * 25
            end = start + 25
            titles = fetch_paper_titles([str(e) for e in ids[start:end]])
            ids = [f"{id_}: {title}" for id_, title in zip(ids[start:end], titles)]

            num_pages = math.ceil(len(ids) / 25)
            out += f"{'\n'.join(ids)}\nPage {page + 1} of {num_pages}\n"
        return out
    else:
        return json.dumps(resp)

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
    # print(search('compound', 'cid', '2244', 'pubmed'))
