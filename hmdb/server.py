from hmdb_lib import Metabolite, make_concentration_dataframe
from typing import Literal
from server_utils import GetCursor, search_all, search_field, escape_like_specials
import pandas as pd
import json
from mcp.server.fastmcp import FastMCP
from pathlib import Path
import os

SEARCH_TYPES = Literal[
    'all', 'name', 'chemical_formula', 'iupac_name', 'inchikey', 'smiles',
    'drugbank_id', 'foodb_id', 'pubchem_compound_id', 'chebi_id', 'kegg_id',
    'wikipedia_name',
]
mcp = FastMCP("HMDB")

@mcp.tool()
async def search(query: str, search_in: SEARCH_TYPES = 'name', regex: bool = False, page: int = 0) -> str:
    """
    Search for metabolites in the HMDB databases based on a query string. You can refine the search by specifying the
    field to search in. It will return a string representing a csv of the results with the name of the match and some
    ids based on the search criteria. Note that it searches by exact match for ids and it search for a substring
    containing the query for names columns, not text similarity. SQL special tokens sucha as _ or % will be escaped.
    If you want additional information on a specific metabolite you found in the search results, you will need to use
    the 'get' method to retrieve the metabolite data with the exact HMDB accession number (ID).
    :param query: The query string to search for in the HMDB database.
    :param search_in: You can specify the field to search in.
    :param regex: If True, the query is treated as a regular expression. Note that this will make the search slower.
    :param page: The page number of the results to return. When there are more than 10 results, the table is paginated.
    :return: A csv corresponding to the search results.
    """
    with GetCursor() as cursor:
        if search_in == "all":
            command = search_all(regex=regex)
            if regex:
                cursor.execute(command, (query, query, query, query, query, query, query, query, query, query, query))
            else:
                cursor.execute(command, (query, query, query, query, query, query, query, query, query,
                                         f"%{escape_like_specials(query)}%", f"%{escape_like_specials(query)}%"))
        else:
            command = search_field(field=search_in, regex=regex)
            if regex:
                cursor.execute(command, (query,))
            else:
                if search_in in ['name', 'wikipedia_id']:
                    cursor.execute(command, (f"%{escape_like_specials(query)}%",))
                else:
                    cursor.execute(command, (query,))
        results = cursor.fetchall()
        if not results:
            return "No results found. Consider using a different query or search field."
        # Convert results to CSV format
        df = pd.DataFrame(results, columns=[
            'accession', 'name', 'chemical_formula', 'average_molecular_weight',
            'monisotopic_molecular_weight', 'iupac_name', 'traditional_iupac',
            'inchikey', 'smiles', 'drugbank_id', 'foodb_id',
            'pubchem_compound_id', 'chebi_id', 'kegg_id', 'wikipedia_name'
        ])
        if len(df) > 10:
            df = df.iloc[page * 10:(page + 1) * 10]
        num_pages = len(results) // 10 + (1 if len(results) % 10 > 0 else 0)
        csv_result = df.to_csv(index=False)
        csv_result += f"\nPage {page + 1} of {num_pages}"
        return csv_result.strip()


@mcp.tool()
async def get(accession: str,
        field: Literal['all', 'description', 'taxonomy',
        'properties', 'concentrations', 'protein_associations'] = 'description') -> str:
    """
    Get a detailed view of a metabolite based on its accession number (HMDB id). You can specify the field to retrieve
    to get less data. Usually, it returns a JSON string representing the metabolite data in a hierarchical format.
    However, the concentrations data is returned as a csv table.
    IMPORTANT: PRIORITIZE A SPECIFIC FIELD TO AVOID OVERLOADING THE RESPONSE (AVOID 'ALL').
    :param accession: The HMDB accession number (HMDB ID) of the metabolite to retrieve.
    :param field: The field to retrieve. If 'all', it will return all the available data. Note that this might be a
    LOT of data, so it is preferable to specify the field you are interested in.
    :return: The requested data. If the metabolite is not found, it will return 'Not found'.
    """
    metabolite = Metabolite.FromDB("db/hmdb.db", accession=accession)
    if field == 'all':
        data = metabolite.todict()
        data["normal_concentrations"] = make_concentration_dataframe(metabolite.normal_concentrations)
        data["abnormal_conc"] = make_concentration_dataframe(metabolite.abnormal_concentrations)

        return json.dumps(data)
    elif field == 'description':
        return json.dumps(
            dict(
                accession = metabolite.accession,

                version= metabolite.version,
                creation_date = metabolite.creation_date,
                update_date = metabolite.update_date,
                status = metabolite.status,
                secondary_accessions = metabolite.secondary_accessions,
                name = metabolite.name,
                description = metabolite.description,
                synonyms = metabolite.synonyms,
                chemical_formula = metabolite.chemical_formula,
                average_molecular_weight = metabolite.average_molecular_weight,
                monisotopic_molecular_weight = metabolite.monisotopic_molecular_weight,
                iupac_name = metabolite.iupac_name,
                traditional_iupac = metabolite.traditional_iupac,
                smiles = metabolite.smiles,
                inchi = metabolite.inchi,
                inchikey = metabolite.inchikey,

                # Cross-references identifiers
                chemspider_id = metabolite.chemspider_id,
                drugbank_id = metabolite.drugbank_id,
                foodb_id = metabolite.foodb_id,
                pubchem_compound_id = metabolite.pubchem_compound_id,
                pdb_id = metabolite.pdb_id,
                chebi_id = metabolite.chebi_id,
                phenol_explorer_compound_id = metabolite.phenol_explorer_compound_id,
                knapsack_id = metabolite.knapsack_id,
                kegg_id = metabolite.kegg_id,
                biocyc_id = metabolite.biocyc_id,
                bigg_id = metabolite.bigg_id,
                wikipedia_id = metabolite.wikipedia_id,
                metlin_id = metabolite.metlin_id,
                vmh_id = metabolite.vmh_id,
                fbonto_id = metabolite.fbonto_id,
        ))
    elif field == "taxonomy":
        return json.dumps(metabolite.taxonomy.todict())
    elif field == "properties":
        properties = metabolite.predicted_properties
        properties.update(metabolite.experimental_properties)
        return json.dumps(properties)
    elif field == "concentrations":
        if not metabolite.normal_concentrations and not metabolite.abnormal_concentrations:
            return "No concentrations data available for this metabolite."
        normal_df = make_concentration_dataframe(metabolite.normal_concentrations)
        abnormal_df = make_concentration_dataframe(metabolite.abnormal_concentrations)
        return f"Normal Concentrations:\n{normal_df}\n\nAbnormal Concentrations:\n{abnormal_df}"
    elif field == "protein_associations":
        data = metabolite.todict()
        return json.dumps(data["protein_associations"])
    else:
        raise ValueError(f"Invalid field: {field}. Must be one of 'all', 'description', 'taxonomy', 'properties', "
                         f"'concentrations', 'protein_associations'.")
if __name__ == '__main__':
    root = Path(__file__).parent
    os.chdir(root)
    mcp.run(transport='stdio')
