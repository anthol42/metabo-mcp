import requests
from typing import Literal, Optional, Union
from mcp.server.fastmcp import Image, FastMCP

mcp = FastMCP("KEGG")
DATABASES = Literal[
    'pathway',
    'brite',
    'module',
    'ko',
    'vg',
    'vp',
    'ag',
    'genome',
    'compound',
    'glycan',
    'reaction',
    'rclass',
    'enzyme',
    'network',
    'variant',
    'disease',
    'drug',
    'dgroup',
    'organism',
    'hsa', # human organism
    'mmu' # mouse organism
]
BASE_URL = "https://rest.kegg.jp"

@mcp.tool()
def list(database: DATABASES, option: Optional[str] = None):
    """
    Obtain an extensive list of entry identifiers and associated names from a KEGG database.

    ## Pathways
    For the pathway database, you can use the option specifier to list only the pathways of a specific organism.
    If not provided, only reference pathways are returned. For example, to list all human pathways, use:
    `'pathway', option='hsa`'.

    ## Examples
    database= 'organism':
    ```
    T01001	hsa	Homo sapiens (human)	Eukaryotes;Animals;Mammals;Primates
    T01005	ptr	Pan troglodytes (chimpanzee)	Eukaryotes;Animals;Mammals;Primates
    T02283	pps	Pan paniscus (bonobo)	Eukaryotes;Animals;Mammals;Primates
    ...
    ```
    :param database: The KEGG database to query. Must be one of the available DATABASES.
    :param option: Optional parameter to specify additional options for the query. Dependent on the database.
    :return: A text containing all the identifiers and names from the specified KEGG database.
    """
    url = f'{BASE_URL}/list/{database}'
    if option:
        url += f'/{option}'
    response = requests.get(url)
    if not response.ok:
        raise Exception(f"Error fetching data from KEGG: {response.status_code} {response.text}")
    return response.text

@mcp.tool()
def find(database: DATABASES, query: str,
         option: Optional[Literal['formula', 'exact_mass', 'mol_weight']] = None) -> str:
    """
    Find entries with matching query keyword or other query data in the specified KEGG database.

    ## option:
    If specified for a valid database, the formula search is a partial match irrespective of the order of atoms
    given. The exact mass (or molecular weight) is checked by rounding off to the same decimal place as the query
    data. A range of values may also be specified with the minus(-) sign.

    ## Examples
    Search for compounds with a specific formula:\
    database = 'compound', query = C7H10O5, option=formula
    ```
    cpd:C00493	C7H10O5
    cpd:C04236	C7H10O5
    ...
    ```
    You can also search for a formula containing X element:\
    database = 'compound', query = C7H10O5, option=formula

    You can also search for a range of molecular weights:\
    database = 'compound', query = 100-200, option=mol_weight

    You can also search with multiple keywords:\
    database = 'genes', query = 'shiga+toxin'

    Or a single keyword with a space:\
    database = 'genes', query = 'shiga toxin'

    :param database: The KEGG database to search in. Must be one of the available DATABASES.
    :param query: The search query string.
    :param option: Optional parameter to specify additional options for the query. Dependent on the database.
    :return: A text containing the search results from the specified KEGG database.
    """
    url = f'{BASE_URL}/find/{database}/{query}'
    if option:
        url += f'/{option}'

    response = requests.get(url)
    if not response.ok:
        raise Exception(f"Error fetching data from KEGG: {response.status_code} {response.text}")
    return response.text

@mcp.tool()
def get(identifier: str, option: Optional[Literal[
    'aaseq',
    'ntseq',
    'mol',
    'kcf',
    'image',
    'image2x',
    'conf',
    'kgml',
    'json'
]] = None) -> Union[str, Image]:
    """
    This operation retrieves given database entries in a flat file format or in other formats with options. Flat
    file formats are available for all KEGG databases except brite. The input is limited up to 10 entries.

    Options allow retrieval of selected fields, including sequence data from genes entries, chemical structure data
    or gif image files from compound, glycan and drug entries, png image files or kgml files from pathway entries.
    The input is limited to one compound/glycan/drug entry with the image option, and to one pathway entry with the
    image or kgml option.

    ## Examples
    - Retrieves a compound entry and a glycan entry: `identifier='C01290+G00092'`
    - Retrieves a human gene entry and an E.coli O157 gene entry: `identifier='hsa:10458+ece:Z5100'`
    - Retrieves amino acid sequences of a human gene and an E.coli O157 gene: `identifier='hsa:10458+ece:Z5100/aaseq'`
    - Retrieves the gif image file of a compound: `identifier='C00002', option='image'`
    - Retrieves the png image file of a pathway map: `identifier='hsa00600', option='image'`
    - Retrieves the doubled-sized png image file of a reference pathway map: `identifier='map006000', option='image2x'`
    - Retrieves the conf file of a pathway map: `identifier='hsa00600', option='conf'`
    - Retrieves the KGML file of a pathway map: `identifier='hsa00600', option='kgml'`
    - Retrieves the htext file of a brite hierarchy: `identifier='br:br08301'`
    - Retrieves the JSON file of a brite hierarchy: `identifier='br:br08301', option='json'`

    :param identifier: The identifier of the entry to fetch.
    :param option: Optional parameter to specify additional options for the query. Dependent on the database. Check the examples above for valid options.
    :return: A text containing the details of the specified entry from the KEGG database or the image if requested.
    """
    url = f'{BASE_URL}/get/{identifier}'
    if option:
        url += f'/{option}'
    response = requests.get(url)
    if not response.ok:
        raise Exception(f"Error fetching data from KEGG: {response.status_code} {response.text}")
    if response.headers['content-type'].startswith('image'):
        return Image(data=response.content, format='gif')
    else:
        return response.text

@mcp.tool()
def ddi(query: str) -> str:
    """
    This operation searches against the KEGG drug interaction database, where drug-drug interactions designated as
    contraindication (CI) and precaution (P) in Japanese drug labels are extracted, standardized by KEGG
    identifiers and annotated with any possible molecular mechanims. The first form reports all known interactions,
    while the second form can be used to check if any drug pair in a given set of drugs is CI or P.

    ## Examples
    - Drugs that are known to interact with a given drug: `query='D00564'`
    - Check if drug-drug interactions are present among given drugs: `query='D00564+D00100+D00109'`
    - Drug products that are known to interact with Gleevec: `query='ndc:0078-0401'`

    :param query: Single entry of the following databases: drug, ndc, or yj
    :return: A text containing the drug-drug interaction information from the KEGG database.
    """
    url = f'{BASE_URL}/get/{query}'
    response = requests.get(url)
    if not response.ok:
        raise Exception(f"Error fetching data from KEGG: {response.status_code} {response.text}")
    return response.text


if __name__ == '__main__':
    print("Starting LIPID MAPS MCP server...")
    mcp.run(transport='stdio')
