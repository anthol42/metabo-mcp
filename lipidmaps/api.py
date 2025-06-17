import requests
from dataclasses import dataclass, field, fields
from typing import Optional

@dataclass
class Match:
    """
    Represents a match in the LipidMaps database.
    """

    regno: str = field(metadata={"desc": "LipidMaps internal registration number"})
    lm_id: str = field(metadata={"desc": "Unique LipidMaps ID (e.g., LMGP01010573)"})
    name: str = field(metadata={"desc": "Common lipid name with specific fatty acid chains"})
    sys_name: str = field(metadata={"desc": "Systematic IUPAC name"})
    synonyms: str = field(metadata={"desc": "Alternative names, often semicolon-separated"})
    abbrev: str = field(metadata={"desc": "Abbreviated lipid name (e.g., PC 34:0)"})
    abbrev_chains: str = field(metadata={"desc": "Abbreviation including chain composition (e.g., PC 16:0_18:0)"})
    core: str = field(metadata={"desc": "Core lipid category (e.g., Glycerophospholipids [GP])"})
    main_class: str = field(metadata={"desc": "Main lipid class (e.g., Glycerophosphocholines [GP01])"})
    sub_class: str = field(metadata={"desc": "Subclass (e.g., Diacylglycerophosphocholines [GP0101])"})
    exactmass: str = field(metadata={"desc": "Exact monoisotopic mass (as string)"})
    formula: str = field(metadata={"desc": "Chemical formula (e.g., C42H84NO8P)"})
    inchi: str = field(metadata={"desc": "IUPAC InChI representation"})
    inchi_key: str = field(metadata={"desc": "InChIKey (hashed InChI for searching)"})
    hmdb_id: Optional[str] = field(metadata={"desc": "HMDB identifier"})
    chebi_id: str = field(metadata={"desc": "ChEBI identifier"})
    pubchem_cid: str = field(metadata={"desc": "PubChem Compound ID"})
    smiles: str = field(metadata={"desc": "SMILES representation of the molecule"})

    @classmethod
    def FromDict(cls, data: dict) -> 'Match':
        """
        Load a Match object from a match in the LipidMaps database using the API
        :param data: The data dictionary containing lipid information
        :return: The Match object
        """
        # Make a shallow copy so we don't mutate the original input
        cleaned_data = data.copy()
        cleaned_data.pop('input', None)  # Remove 'input' if it exists
        valid_data = {key.name: data.get(key.name, None) for key in fields(cls)}
        # Sanity check, check if some keys are present, but not in the class
        unknown_keys = set(cleaned_data.keys()) - set(valid_data.keys())
        if unknown_keys:
            print(f"Found these unknown keys in the data: {unknown_keys}. ")
        return cls(**valid_data)

    def to_dict(self) -> dict:
        """
        Convert the Match object to a dictionary.
        :return: A dictionary representation of the Match object
        """
        return {field.name: getattr(self, field.name) for field in fields(self)}

class LipidMapsClient:
    """
    Client for interacting with the LipidMaps API.
    """

    def __init__(self, base_url="https://www.lipidmaps.org/rest"):
        self.base_url = base_url

    def search_compund(self, query: str) -> list[Match]:
        """
        Search for compounds in the LipidMaps database using a query string.
        :param query: The search query string. Example: DG(17:0_22:4) or Cer(d18:0/24:0)
        :return: A list of Match objects representing the search results
        """
        matches = []
        data = self._fetch_url(f"{self.base_url}/compound/abbrev_chains/{query}/all/json")
        if isinstance(data, dict):
            if any("Row" in key for key in data.keys()):
                matches.extend([Match.FromDict(match) for _, match in data.items()])
            else:
                matches.append(Match.FromDict(data))

        data = self._fetch_url(f"{self.base_url}/compound/abbrev/{query}/all/json")
        if isinstance(data, dict):
            if any("Row" in key for key in data.keys()):
                matches.extend([Match.FromDict(match) for _, match in data.items()])
            else:
                matches.append(Match.FromDict(data))

        return matches

    def _fetch_url(self, url) -> Match:
        """
        Fetch a specific compound by its LipidMaps ID.
        :param lm_id: The LipidMaps ID of the compound
        :return: A Match object representing the compound
        """
        response = requests.get(url)
        if not response.ok:
            raise Exception(f"Error fetching data from LipidMaps: {response.status_code} {response.text}")
        data = response.json()
        return data

if __name__ == "__main__":
    # Example usage
    client = LipidMapsClient()
    results = client.search_compund("DG(14:0_22:6)")
    for match in results:
        print(match)