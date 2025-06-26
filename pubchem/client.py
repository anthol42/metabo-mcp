import requests
from typing import Literal, Union

class PubChemClient:
    def __init__(self, base_url: str = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/"):
        self.base_url = base_url


    def _format_input(self, domain: Literal['substance', 'compound'],
                      namespace: Literal['cid', 'name', 'smiles', 'inchi', 'inchikey', 'formula'],
                      identifier: str) -> str:
        """
        Format the input for the PubChem API.
        :param domain: The domain of the input (e.g. 'substance' or 'compound'). Some options have been removed because they are not relevant
        :param namespace: The type of the identifier. Some options have been removed because they are not relevant.
        :param identifier: The identifier of the input (e.g. 'xref/PubMedID')
        """
        return f"{domain}/{namespace}/{identifier}"

    def _format_operation(self, what: Literal['record', 'properties', 'synonyms', 'sids', 'cids',
    'classification', 'pubmed', 'description']):
        properties = [
            "MolecularFormula", "MolecularWeight", "CanonicalSMILES", "IsomericSMILES", "InChI", "InChIKey",
            "IUPACName",
            "XLogP", "ExactMass", "MonoisotopicMass", "TPSA", "Complexity", "Charge", "HBondDonorCount",
            "HBondAcceptorCount",
            "RotatableBondCount", "HeavyAtomCount", "IsotopeAtomCount", "AtomStereoCount", "DefinedAtomStereoCount",
            "UndefinedAtomStereoCount", "BondStereoCount", "DefinedBondStereoCount", "UndefinedBondStereoCount",
            "CovalentUnitCount", "Volume3D", "XStericQuadrupole3D", "YStericQuadrupole3D", "ZStericQuadrupole3D",
            "FeatureCount3D", "FeatureAcceptorCount3D", "FeatureDonorCount3D", "FeatureAnionCount3D",
            "FeatureCationCount3D",
            "FeatureRingCount3D", "FeatureHydrophobeCount3D", "ConformerModelRMSD3D", "EffectiveRotorCount3D",
            "ConformerCount3D"
        ]
        if what == "properties":
            properties = ",".join(properties)
            return f"property/{properties}"
        elif what == "pubmed":
            return f"xrefs/PubMedID"
        else:
            return f"{what}"

    def get(self, search_domain: Literal['substance', 'compound'],
            query_type: Literal['cid', 'name', 'smiles', 'inchi', 'inchikey', 'formula'],
            query: str,
            search_what: Literal['record', 'properties', 'synonyms', 'sids', 'cids',
                'classification', 'pubmed', 'description'] = 'description'
            ) -> dict:
        """
        Get data from the PubChem API.
        :param search_domain: In what domain to search.
        :param query_type: What is the query? A CID, name, SMILES, InChI, InChIKey, formula, etc
        :param query: The query to search for.
        :param search_what: What to retrieve from the API. If 'record', it will return the full record.
        :return: A dictionary containing the data from the PubChem API.
        """
        url = self.base_url
        url += "/" + self._format_input(search_domain, query_type, query)
        url += "/" + self._format_operation(search_what)
        url += "/JSON"
        response = requests.get(url)
        if not response.ok:
            raise RuntimeError(f"Failed to fetch data from PubChem: {response.status_code} {response.reason}")
        data = response.json()
        if "InformationList" in data:
            if "Information" in data["InformationList"]:
                return data["InformationList"]["Information"]
            else:
                return data["InformationList"]
        else:
            return data

if __name__ == "__main__":
    import json
    client = PubChemClient()
    print(client.get('compound', 'name', 'caffein', 'pubmed'))