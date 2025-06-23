import pandas as pd
import os
from pathlib import PurePath
import requests
from typing import Optional, Literal

class GeneticMarkers:
    def __init__(self, load_cache: bool = True):
        self.db = self._load_db(load_cache)

    def search(self, variation: Optional[str] = None, position: Optional[str] = None,
               gene_symbol: Optional[str] = None, entrez_gene_id: Optional[str] = None,
               condition: Optional[str] = None) -> pd.DataFrame:

        if all(param is None for param in [variation, position, gene_symbol, entrez_gene_id, condition]):
            raise ValueError("At least one search parameter must be provided.")
        df = self.db
        if variation is not None:
            df = df.loc[df['variation'] == variation]
        if position is not None:
            df = df.loc[df['position'] == position]
        if gene_symbol is not None:
            df = df.loc[df['gene_symbol'].str.lower() == gene_symbol.lower()]
        if entrez_gene_id is not None:
            df = df.loc[df['entrez_gene_id'] == entrez_gene_id]
        if condition is not None:
            # Cast NaN values to False
            df = df.loc[df['conditions'].str.lower().str.contains(condition.lower()) == True]

        return df.reset_index(drop=True)

    def _load_db(self, load_cache: bool) -> pd.DataFrame:
        root = PurePath(__file__).parent.parent
        if not os.path.exists(root / "dbs"):
            os.makedirs(root / "dbs")
        if not os.path.exists(root / "dbs/all_sequence_variants.tsv") or not load_cache:
            resp = requests.get("https://markerdb.ca/pages/download_all_sequence_variants?format=tsv")
            if not resp.ok:
                raise RuntimeError(f"Failed to download protein markers: {resp.status_code} {resp.reason}")
            with open(root / "dbs/all_sequence_variants.tsv", "w") as f:
                f.write(resp.text)
        df = pd.read_csv(root / "dbs/all_sequence_variants.tsv", sep="\t", dtype=str)
        return df

if __name__ == "__main__":
    protein_markers = GeneticMarkers()
    res = protein_markers.search(entrez_gene_id="3077", condition="hemochromatosis")
    print(res)
    # Example usage: print the first few rows of the protein markers database
    # This will load the database and print the first few entries