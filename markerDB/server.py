import os
from typing import Optional, Literal
from mcp.server.fastmcp import FastMCP

from markers import ProteinMarkers, GeneticMarkers, ChemicalMarkers

mcp = FastMCP("MarkerDB")

@mcp.tool()
def search_proteins_markerDB(compound_name: Optional[str] = None, gene_name: Optional[str] = None, uniprot_id: Optional[str] = None,
               condition: Optional[str] = None, sex: Optional[Literal['Both', 'Female', 'Male']] = None,
               biofluid: Optional[str] = None, page_size: int = 10, page_number: int = 0) -> str:
    """
    Search for protein known markers in the MarkerDB database. You can specify one or more parameters to filter the
    results. The search criteria are combined with an AND operator, meaning that all specified parameters must match
    for a result to be returned. You must specify at least one parameter to perform the search.

    The results are returned as a csv table. For briefness, the first 10 results are returned by default, but you can
    specify the `page_size` and `page_number` parameters to control the pagination of the results.

    :param compound_name: The name of the protein. Case-insensitive.
    :param gene_name: The name of the gene that encodes the protein.
    :param uniprot_id: The UniProt ID of the protein.
    :param condition: Search by condition. This will return all markers associated with the specified condition. Case-insensitive.
    :param sex: The sex of the individual from which the marker was derived. If None, all markers are returned, even for unknown sex.
    :param biofluid: The biofluid from which the marker was derived.
    :param page_size: The number of results to return per page.
    :param page_number: The page number to return. The first page is 0.
    :return: A csv table containing the search results.
    """
    proteins_markers = ProteinMarkers()
    df = proteins_markers.search(compound_name=compound_name, gene_name=gene_name, uniprot_id=uniprot_id,
                                 condition=condition, sex=sex, biofluid=biofluid)
    if df.empty:
        return "No results found. Try loosening your search criteria."

    # Paginate the results
    start = page_number * page_size
    end = start + page_size
    df = df.iloc[start:end]
    if df.empty:
        return "No results found for the specified page. Try changing the page size or page number."

    # Convert the DataFrame to a CSV string
    csv_string = df.to_csv(index=False)

    # Add metadata to the CSV string
    num_pages = len(df) // 10 + (1 if len(df) % 10 > 0 else 0)
    csv_string += f"\n\nPage {page_number + 1} of {num_pages}\n"

    return csv_string

@mcp.tool()
def search_genetics_markerDB(variation: Optional[str] = None, position: Optional[str] = None,
               gene_symbol: Optional[str] = None, entrez_gene_id: Optional[str] = None,
               condition: Optional[str] = None, page_size: int = 10, page_number: int = 0) -> str:
    """
    Search for protein known SNPs associated to conditions (genes biomarkers) in the MarkerDB database. You can specify
    one or more parameters to filter the results. The search criteria are combined with an AND operator, meaning that
    all specified parameters must match for a result to be returned. You must specify at least one parameter to perform
    the search.

    The results are returned as a csv table. For briefness, the first 10 results are returned by default, but you can
    specify the `page_size` and `page_number` parameters to control the pagination of the results.

    :param variation: The SNP id. Example: rs1385526
    :param position: The position of the SNP in the genome. Example: chr12:57138966
    :param gene_symbol: The gene official symbol. Example: LRP1
    :param entrez_gene_id: The Entrez Gene ID of the gene. Example: 4035
    :param condition: The condition associated with the SNP. This will return all markers associated with the specified condition. Case-insensitive.
    :param page_size: The number of results to return per page.
    :param page_number: The page number to return. The first page is 0.
    :return: A csv table containing the search results.
    """
    gene_markers = GeneticMarkers()
    df = gene_markers.search(variation=variation, position=position, gene_symbol=gene_symbol, condition=condition,
                             entrez_gene_id=entrez_gene_id)
    if df.empty:
        return "No results found. Try loosening your search criteria."

    # Paginate the results
    start = page_number * page_size
    end = start + page_size
    df = df.iloc[start:end]
    if df.empty:
        return "No results found for the specified page. Try changing the page size or page number."

    # Convert the DataFrame to a CSV string
    csv_string = df.to_csv(index=False)

    # Add metadata to the CSV string
    num_pages = len(df) // 10 + (1 if len(df) % 10 > 0 else 0)
    csv_string += f"\n\nPage {page_number + 1} of {num_pages}\n"

    return csv_string

@mcp.tool()
def search_chemicals_markerDB(compound_name: Optional[str] = None, hmdb_id: Optional[str] = None,
               condition: Optional[str] = None, sex: Optional[Literal['Both', 'Female', 'Male']] = None,
               biofluid: Optional[str] = None, page_size: int = 10, page_number: int = 0) -> str:
    """
    Search for chemical compounds markers in the MarkerDB database. You can specify one or more parameters to filter the
    results. The search criteria are combined with an AND operator, meaning that all specified parameters must match
    for a result to be returned. You must specify at least one parameter to perform the search.

    The results are returned as a csv table. For briefness, the first 10 results are returned by default, but you can
    specify the `page_size` and `page_number` parameters to control the pagination of the results.

    :param compound_name: The chemical compound name. Case-insensitive.
    :param hmdb_id: The HMDB ID of the chemical compound. Example: HMDB01847
    :param condition: The condition associated with the chemical compound. This will return all chemical markers associated with the specified condition. Case-insensitive.
    :param sex: The sex of the individual from which the marker was derived. If None, all markers are returned, even for unknown sex.
    :param biofluid: The biofluid from which the marker was derived.
    :param page_size: The number of results to return per page.
    :param page_number: The page number to return. The first page is 0.
    :return: A csv table containing the search results.
    """
    chemical_markers = ChemicalMarkers()
    df = chemical_markers.search(compound_name=compound_name, hmdb_id=hmdb_id,
                                 condition=condition, sex=sex, biofluid=biofluid)
    if df.empty:
        return "No results found. Try loosening your search criteria."

    # Paginate the results
    start = page_number * page_size
    end = start + page_size
    df = df.iloc[start:end]
    if df.empty:
        return "No results found for the specified page. Try changing the page size or page number."

    # Convert the DataFrame to a CSV string
    csv_string = df.to_csv(index=False)

    # Add metadata to the CSV string
    num_pages = len(df) // 10 + (1 if len(df) % 10 > 0 else 0)
    csv_string += f"\n\nPage {page_number + 1} of {num_pages}\n"

    return csv_string

if __name__ == "__main__":
    mcp.run(transport='stdio')