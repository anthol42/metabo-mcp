from project_utils import Installer
import requests
import os
from pathlib import PurePath
from zipfile import ZipFile
from io import BytesIO
import pandas as pd
from glob import glob

class PathBankInstaller(Installer):
    def __call__(self):
        root = PurePath(__file__).parent
        if not os.path.exists(root / "dbs"):
            os.makedirs(root / "dbs")

        # Download the marker databases if they do not exist or if the user wants to update
        if (os.path.exists(root / "dbs" / "pathbank_pathways.csv") and os.path.exists(root / "dbs" / "pathbank_metabolites.csv") and
                os.path.exists(root / "dbs" / "sbml_files")):
            load = input("PathBank database already downloaded. Do you want to update it? (y/n): ").strip().lower() == 'y'
        else:
            load = True

        if not load:
            return  # Do nothing

        # Download the PathBank databases
        response = requests.get("https://pathbank.org/downloads/pathbank_all_pathways.csv.zip")
        if not response.ok:
            raise RuntimeError("Failed to download PathBank pathways database.")

        # Unzip the content and write to the file
        with ZipFile(BytesIO(response.content)) as zip_file:
            with zip_file.open("pathbank_pathways.csv") as csv_file:
                all_pathways = pd.read_csv(BytesIO(csv_file.read()))

        response = requests.get("https://pathbank.org/downloads/pathbank_all_metabolites.csv.zip")
        if not response.ok:
            raise RuntimeError("Failed to download PathBank metabolites database.")

        # Unzip the content and write to the file
        with ZipFile(BytesIO(response.content)) as zip_file:
            with zip_file.open("pathbank_all_metabolites.csv") as csv_file:
                all_metabolites = pd.read_csv(BytesIO(csv_file.read()))

        # Download the SBML files
        sbml_dir = root / "dbs" / "sbml_files"
        with open(root / "dbs" / "sbml_files.zip", "wb") as f:
            response = requests.get("https://pathbank.org/downloads/pathbank_all_sbml.zip")
            if not response.ok:
                raise RuntimeError("Failed to download PathBank SBML files.")

            f.write(response.content)
        with ZipFile(root / "dbs" / "sbml_files.zip", 'r') as zip_file:
            zip_file.extractall(sbml_dir)

        os.remove(root / "dbs" / "sbml_files.zip")

        # Now, take only the pathways of human and mouse
        metabolites = all_metabolites.loc[all_metabolites["Species"].str.lower().isin(["homo sapiens", "mus musculus"])]

        pathways2keep = metabolites["PathBank ID"].unique().tolist()
        pathways = all_pathways.loc[all_pathways["SMPDB ID"].isin(pathways2keep)]

        # Prune sbml files that are not in pathways to keep
        pw_ids = set(pathways["PW ID"].tolist())
        for file in glob(str(root / "dbs" / "sbml_files" / "pathbank_all_sbml" / "*.sbml")):
            filepath = PurePath(file)
            id_ = filepath.stem
            if id_ not in pw_ids:
                os.remove(file)

        # Save files
        metabolites.to_csv(root / "dbs" / "pathbank_metabolites.csv", index=False)
        pathways.to_csv(root / "dbs" / "pathbank_pathways.csv", index=False)



if __name__ == "__main__":
    installer = PathBankInstaller()
    installer()  # Run the installer to download the PathBank databases
