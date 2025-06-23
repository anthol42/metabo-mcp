from typing import Any
from mcp.server.fastmcp import FastMCP
from api import LipidMapsClient, Match
import json

mcp = FastMCP("LIPID MAPS")
client = LipidMapsClient()

def _condense(match: dict) -> dict:
    """
    Condense the match dictionary to a more compact format.
    :param match: The match dictionary to condense.
    :return: A condensed version of the match dictionary.
    """
    return {
        'lm_id': match['lm_id'],
        'name': match['name'],
        'sys_name': match['sys_name'],
        'synonyms': match['synonyms'],
        'abbrev': match['abbrev'],
        'abbrev_chains': match['abbrev_chains']
    }

@mcp.tool()
def search_lipidmaps(name: str) -> str:
    """
    Search for compounds in the LipidMaps database using a query string.
    If there are too much results, they will be returned in a compact format. This means it will return only:
    - lm_id
    - name
    - sys_name
    - synonyms
    - abbrev
    - abbrev_chains
    If the results are return in the compact format, you can search manually for the dull information by using the name
    of the compound of interest again in this function.
    :param name: The search query string. Example: DG(17:0_22:4) or Cer(d18:0/24:0)
    :return: A json string containing the search results. If no results are found, returns an empty JSON list. Maybe
    try with a different but equivalent name.
    """

    matches = client.search_compund(name)
    if not matches:
        return '[]'

    results = [match.to_dict() for match in matches]
    if len(results) > 5:
        results = [_condense(match) for match in results]
    return json.dumps(results)

if __name__ == "__main__":
    # Initialize and run the server
    print("Starting LIPID MAPS MCP server...")
    mcp.run(transport='stdio')

