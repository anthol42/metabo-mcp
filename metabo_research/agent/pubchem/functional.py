import requests

base_url: str = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/"

def get_pubmed_ids(cid: str) -> list[str]:
    """
    Get PubMed IDs associated with a given CID from the PubChem database.
    :param cid: The CID of the compound.
    :return: A list of PubMed IDs.
    """
    url = f"{base_url}compound/cid/{cid}/xrefs/PubMedID/JSON"
    response = requests.get(url)

    if response.status_code != 200:
        raise RuntimeError(f"Failed to fetch data for CID {cid}: {response.text}")

    data = response.json()
    return [xref['PubMedID'] for xref in data.get('InformationList', {}).get('Information', [])][0]


if __name__ == "__main__":
    # Example usage
    cid = "89594"  # Example CID for aspirin
    try:
        pubmed_ids = get_pubmed_ids(cid)
        print(f"PubMed IDs for CID {cid}: {len(pubmed_ids)}")
    except RuntimeError as e:
        print(e)