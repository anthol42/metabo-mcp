import requests
import os
from pathlib import Path
from pyutils import progress
import zipfile
from lxml import etree as ET
from typing import Union
from metabolite import Metabolite
def read_xml(path: Union[str, Path]):
    tree = ET.parse(path)
    return tree.getroot()

def download_hmdb_data(load_cache: bool = True) -> None:
    root = Path(__file__).parent
    hmdb_path = root / ".cache"

    if os.path.exists(hmdb_path / "hmdb_metabolites.xml") and load_cache:
        print("Loading HMDB cache from disk.")
        return read_xml(hmdb_path / "hmdb_metabolites.xml")

    hmdb_url = "https://www.hmdb.ca/system/downloads/current/hmdb_metabolites.zip"

    if not hmdb_path.exists():
        hmdb_path.mkdir(parents=True)


    with requests.get(hmdb_url, stream=True) as r:
        total_size = float(r.headers.get("content-length", 0)) / 1e6 # Convert to MB
        prg = progress(total=total_size, desc="Downloading HMDB data", type="pip", unit="MB")
        if r.status_code != 200:
            raise Exception(f"Failed to download HMDB data: {r.status_code} {r.text}")

        downloaded_size = 0
        with open(hmdb_path / "hmdb_metabolites.zip", "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded_size += len(chunk) / 1e6  # Convert to MB
                prg.update(downloaded_size)

    # Unzip the downloaded file
    print("Unzipping HMDB data...")
    with zipfile.ZipFile(hmdb_path / "hmdb_metabolites.zip", 'r') as zip_ref:
        zip_ref.extractall(hmdb_path)

    print("Reading HMDB data...")
    return read_xml(hmdb_path / "hmdb_metabolites.xml")


if __name__ == "__main__":
    from xml.etree import ElementTree as ET
    file = download_hmdb_data()
    metabolites = []
    for elem in progress(file):
        elem: ET.Element
        metabolites.append(Metabolite.FromXML(elem))

    print(len(metabolites))