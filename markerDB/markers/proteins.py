import pandas as pd
import os
from pathlib import PurePath
import requests
from typing import Optional, Literal

class ProteinMarkers:
    def __init__(self, load_cache: bool = True):
        self.db = self._load_db(load_cache)

    def search(self, compound_name: Optional[str] = None, gene_name: Optional[str] = None, uniprot_id: Optional[str] = None,
               condition: Optional[str] = None, sex: Optional[Literal['Both', 'Female', 'Male']] = None,
               biofluid: Optional[str] = None) -> pd.DataFrame:

        if all(param is None for param in [compound_name, gene_name, uniprot_id, condition, sex, biofluid]):
            raise ValueError("At least one search parameter must be provided.")
        df = self.db
        if compound_name is not None:
            df = df.loc[df['name'].str.lower().str.contains(compound_name.lower()) == True]
        if gene_name is not None:
            df = df.loc[df['gene_name'] == gene_name]
        if uniprot_id is not None:
            df = df.loc[df['uniprot_id'] == uniprot_id]
        if condition is not None:
            # Cast NaN values to False
            df = df.loc[df['conditions'].str.lower().str.contains(condition.lower()) == True]
        if sex is not None:
            df = df.loc[df["sex"] == sex]
        if biofluid is not None:
            df = df.loc[df["biofluid"] == biofluid]

        return df.reset_index(drop=True)

    def _load_db(self, load_cache: bool) -> pd.DataFrame:
        root = PurePath(__file__).parent.parent
        if not os.path.exists(root / "dbs"):
            os.makedirs(root / "dbs")
        if not os.path.exists(root / "dbs/all_proteins.tsv") or not load_cache:
            resp = requests.get("https://markerdb.ca/pages/download_all_proteins?format=tsv")
            if not resp.ok:
                raise RuntimeError(f"Failed to download protein markers: {resp.status_code} {resp.reason}")
            with open(root / "dbs/all_proteins.tsv", "w") as f:
                f.write(resp.text)
        df = pd.read_csv(root / "dbs/all_proteins.tsv", sep="\t", dtype=str)
        # There is a bug in the db that causes the last column to be empty
        df = df[df.columns[:-1]]
        df = df.rename(columns={"protein_sequence": "citation"})
        return df

if __name__ == "__main__":
    protein_markers = ProteinMarkers()
    res = protein_markers.search(condition="Hemochromatosis")
    res.to_csv("tmp.csv", index=False)
    # Example usage: print the first few rows of the protein markers database
    # This will load the database and print the first few entries