import math
import os
from typing import Optional, Literal, Union
from mcp.server.fastmcp import Image, FastMCP
from pathlib import PurePath
import pandas as pd

mcp = FastMCP("PathBank")

@mcp.tool()
def search_pathway_pathbank(name: str, subject: Optional[Literal["Disease", 'Drug Action', 'Drug Metabolism', 'Metabolomic',
            'Physiological', 'Protein', 'Signaling']] = None, page_idx: int = 0) -> str:
    """
    Search for pathways in the PathBank database by name and/or subject. The name is case-insensitive and will return
    every pathway that contains the name query in its official name. The subject is optional and can be used to filter
    the results by subject.

    If there are more than 25 results, they will be paginated. The page_idx parameter is used to specify the page number
    to return, starting from 0. If there are no results, a message will be returned indicating that no pathways
    were found.
    :param name: The query name to search for in the PathBank database. It is case-insensitive.
    :param subject: The subject to filter the results by.
    :return: A csv table containing the search results.
    """
    # Load the PathBank pathways database
    root = PurePath(__file__).parent
    pathways_db = pd.read_csv(root / "dbs" / "pathbank_pathways.csv")
    metabolites_db = pd.read_csv(root / "dbs" / "pathbank_metabolites.csv")

    # Filter the pathways by name
    pathways_db = pathways_db.loc[pathways_db["Name"].str.contains(name, case=False, na=False)]
    if subject:
        pathways_db = pathways_db.loc[pathways_db["Subject"] == subject]

    if pathways_db.empty:
        return "No pathways found. Try loosening your search criteria."

    pathways_results = pathways_db[["SMPDB ID", "Name", "Subject"]]
    pathways_results = pathways_results.rename(columns={"SMPDB ID": "PathBank ID"})

    # Add species
    species = []
    for idx, row in pathways_results.iterrows():
        pathbank_id = row["PathBank ID"]
        pathway_species = metabolites_db.loc[metabolites_db["PathBank ID"] == pathbank_id, "Species"].unique()
        if len(pathway_species) > 0:
            species.append("; ".join(pathway_species))
        else:
            species.append("Unknown")
    pathways_results["Species"] = species

    # Paginate the results
    page_size = 25
    start = page_idx * page_size
    end = start + page_size
    num_pages = math.ceil(len(pathways_results) / page_size)
    pathways_results = pathways_results.iloc[start:end]

    out = pathways_results.to_csv(index=False)

    out += f"\n\nPage {page_idx + 1} of {num_pages}\n"

    return out

@mcp.tool()
def get_pathway_pathbank(pathbank_id: str) -> str:
    """
    Retrieve the name and the description of the pathway.
    In also, it lists the metabolites involved in the pathway with some identifiers.
    In addition, it lists in what species the pathway is present.

    :param pathbank_id: The identifier of the pathway.
    :return: A document containing all the information. Some is represented as a csv table while other as a text.
    """
    # Load the PathBank pathways database
    root = PurePath(__file__).parent
    pathways_db = pd.read_csv(root / "dbs" / "pathbank_pathways.csv")
    metabolites_db = pd.read_csv(root / "dbs" / "pathbank_metabolites.csv")

    # Find the pathway by its PathBank ID
    pathway = pathways_db.loc[pathways_db["SMPDB ID"] == pathbank_id].iloc[0]

    # Find metabolites involved in the pathway
    metabolites = metabolites_db.loc[metabolites_db["PathBank ID"] == pathbank_id]

    if pathway.empty:
        return f"No pathway found with PathBank ID: {pathbank_id}"

    # Format the pathway information
    document = f"# {pathway['Name']}\n"
    document += f"{pathway['Description']}\n\n"
    document += f"- Subject: {pathway['Subject']}\n"
    species = metabolites["Species"].unique()
    document += f"- Species: {', '.join(species)}\n\n"

    document += "## Metabolites Involved in the Pathway\n"
    metabolites = metabolites[["Metabolite ID", "Metabolite Name", "HMDB ID", "KEGG ID", "ChEBI ID", "DrugBank ID"]]
    document += metabolites.to_csv(index=False)

    return document

# @mcp.tool()
# def get_pathway_image_pathbank(pathbank_id: str) -> Union[str, Image]:
#     """
#     Get the visual representation of the pathway by its PathBank ID.
#     :param pathbank_id: The identifier of the pathway.
#     :return: An image
#     """
#     # Load the PathBank pathways database
#     root = PurePath(__file__).parent
#     pathways_db = pd.read_csv(root / "dbs" / "pathbank_pathways.csv")
#     pathway = pathways_db.loc[pathways_db["SMPDB ID"] == pathbank_id].iloc[0]
#
#     if pathway.empty:
#         return f"No pathway found with PathBank ID: {pathbank_id}"
#
#     sbml_id = pathway["PW ID"]
#     sbml_file = root / "dbs" / "sbml_files" / "pathbank_all_sbml" / f"{sbml_id}.sbml"
#     if not os.path.exists(sbml_file):
#         return f"No representation found for PathBank ID: {pathbank_id}"
#
#     network = sbmlnetwork.load(str(sbml_file))
#     network.set_size((1000, 1000))
#     network.draw(str(root/"tmp.png"))
#
#     image = Image(
#         path=str(root / "tmp.png"),
#     )
#
#     return image

if __name__ == "__main__":
    mcp.run(transport='stdio')




