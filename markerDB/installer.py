from project_utils import Installer
import requests
import os
from pathlib import PurePath

from .markers import ChemicalMarkers, ProteinMarkers, GeneticMarkers

class MarkerDBInstaller(Installer):
    def __call__(self):
        root = PurePath(__file__).parent
        if not os.path.exists(root / "dbs"):
            os.makedirs(root / "dbs")

        # Download the marker databases if they do not exist or if the user wants to update
        load_cache = True
        if (os.path.exists(root / "dbs" / "all_chemicals.tsv") or os.path.exists(root / "dbs" / "all_proteins.tsv") or
                os.path.exists(root / "dbs" / "all_sequence_variants.tsv")):
            load_cache = not input("Marker database already exists. Do you want to update it? (y/n): ").strip().lower() == 'y'

        # Automatically download if missing or force re-download
        ChemicalMarkers(load_cache=load_cache)
        ProteinMarkers(load_cache=load_cache)
        GeneticMarkers(load_cache=load_cache)
