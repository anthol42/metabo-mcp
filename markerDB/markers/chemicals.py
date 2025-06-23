import pandas as pd
import os
from pathlib import PurePath
import requests
from typing import Optional, Literal


class ChemicalMarkers:
    def __init__(self, load_cache: bool = True):
        self.db = self._load_db(load_cache)

    def search(self, compound_name: Optional[str] = None, hmdb_id: Optional[str] = None,
               condition: Optional[str] = None, sex: Optional[Literal['Both', 'Female', 'Male']] = None,
               biofluid: Optional[str] = None) -> pd.DataFrame:

        if all(param is None for param in [compound_name, hmdb_id, condition, sex, biofluid]):
            raise ValueError("At least one search parameter must be provided.")
        df = self.db
        if compound_name is not None:
            df = df.loc[df['name'].str.lower().str.contains(compound_name.lower()) == True]
        if hmdb_id is not None:
            df = df.loc[df['hmdb_id'] == hmdb_id]
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
        if not os.path.exists(root / "dbs/all_chemicals.tsv") or not load_cache:
            resp = requests.get("https://markerdb.ca/pages/download_all_chemicals?format=tsv")
            if not resp.ok:
                raise RuntimeError(f"Failed to download protein markers: {resp.status_code} {resp.reason}")
            with open(root / "dbs/all_chemicals.tsv", "w") as f:
                f.write(resp.text)
        df = pd.read_csv(root / "dbs/all_chemicals.tsv", sep="\t", dtype=str)
        return df

if __name__ == "__main__":
    protein_markers = ChemicalMarkers()
    res = protein_markers.search(compound_name="glucose", condition="diabetes")
    print(res)
    # res.to_csv("tmp.csv", index=False)
    # Example usage: print the first few rows of the protein markers database
    # This will load the database and print the first few entries