import math
from typing import Literal
from mcp.server.fastmcp import FastMCP
from client import PubChemClient
import json

mcp = FastMCP("PubChem")
client = PubChemClient()

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
            ids = [str(e) for e in ids[start:end]]

            num_pages = math.ceil(len(ids) / 25)
            out += f"{'\n'.join(ids)}\nPage {page + 1} of {num_pages}\n"
        return out
    else:
        return json.dumps(resp)

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')

