import requests
import os
from pathlib import Path
from pyutils import progress
import zipfile
from lxml import etree as ET
from typing import Union
from hmdb_lib import Metabolite
from db.db_format import create_db

def read_xml(path: Union[str, Path]):
    tree = ET.parse(path)
    return tree.getroot()

def download_hmdb_data(load_cache: bool = True) -> Path:
    root = Path(__file__).parent
    hmdb_path = root / ".cache"

    if os.path.exists(hmdb_path / "hmdb_metabolites.xml") and load_cache:
        print("Loading HMDB cache from disk.")
        return hmdb_path / "hmdb_metabolites.xml"

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
    return hmdb_path / "hmdb_metabolites.xml"

def strip_namespace(elem):
    for el in elem.iter():
        if '}' in el.tag:
            el.tag = el.tag.split('}', 1)[1]  # Remove namespace


def count_metabolites_simple_text(filename):
    """Fastest method - simple text search"""
    count = 0
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            count += line.count('<metabolite')
    return count

if __name__ == "__main__":
    from xml.etree import ElementTree as ET
    filename = download_hmdb_data()
    metabolites = []
    total_metabolites = count_metabolites_simple_text(filename)
    if os.path.exists("db/hmdb.db"):
        os.remove("db/hmdb.db")
    create_db("db/hmdb.db")  # Create the database schema

    # Process elements one at a time without loading everything
    prg = progress(total=total_metabolites, desc="Downloading metabolites")
    for event, elem in ET.iterparse(filename, events=('start', 'end')):
        if event == 'end' and elem.tag.split('}')[-1] == 'metabolite':
            strip_namespace(elem)
            metabolite = Metabolite.FromXML(elem)
            metabolites.append(metabolite)
            metabolite.toDB("db/hmdb.db")  # Save to database
            elem.clear()  # Free memory
            metabolite_db = Metabolite.FromDB("db/hmdb.db")
            if metabolite_db != metabolite:
                print("Metabolite database mismatch.")
            prg.update(len(metabolites))

    print(len(metabolites))