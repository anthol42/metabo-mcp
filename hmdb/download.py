import requests
import os
from pathlib import Path
from pyutils import progress
import zipfile
from lxml import etree as ET
from typing import Union
from hmdb_lib import Metabolite
from db.db_format import create_db
from dataclasses import fields

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

def dataclass_diff(obj1, obj2):
    if type(obj1) != type(obj2):
        raise ValueError("Objects must be of the same type")

    diffs = {}
    for field in fields(obj1):
        name = field.name
        val1 = getattr(obj1, name)
        val2 = getattr(obj2, name)
        if val1 != val2:
            diffs[name] = (val1, val2)

    return diffs

def make_sql_db(filename: Union[str, Path], load_cache: bool = True):
    """
    Create if not exists the database schema for HMDB metabolite data and fill the database with the data from the xml
    file.
    :param filename:     HMDB metabolite xml filename
    :param load_cache: If false and the database already exists, it will be deleted and recreated.
    :return: None
    """
    # We will work with absolute paths so it works in any directory
    root = Path(__file__).parent
    print("Counting metabolites")
    total_metabolites = count_metabolites_simple_text(filename)
    if os.path.exists(f"{root}/db/hmdb.db") and load_cache:
        return
    if os.path.exists(f"{root}/db/hmdb.db") and not load_cache:
        os.remove(f"{root}/db/hmdb.db")

    create_db(f"{root}/db/hmdb.db")  # Create the database schema
    prg = progress(total=total_metabolites, desc="Parsing metabolites")
    count = 0
    for event, elem in ET.iterparse(filename, events=('start', 'end')):
        if event == 'end' and elem.tag.split('}')[-1] == 'metabolite':
            strip_namespace(elem)
            metabolite = Metabolite.FromXML(elem)
            metabolite.toDB(f"{root}/db/hmdb.db")  # Save to database
            elem.clear()

            count += 1
            prg.update(count)

def install_hmdb_db(load_cache: bool = True):
    """
    Install the HMDB database by downloading the data, creating the database schema and filling it with the data.
    :param load_cache: If the data or database exists, nothing will be done. Otherwise, it will ignore and overwrite.
    :return: None
    """
    filename = download_hmdb_data(load_cache=load_cache)
    make_sql_db(filename, load_cache=load_cache)

if __name__ == "__main__":
    from xml.etree import ElementTree as ET
    from pprint import pprint
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
            # if metabolite.accession == "HMDB0004827":
            #     # Save to tmp.xml for debugging
            #     ET.ElementTree(elem).write("tmp.xml", encoding='utf-8', xml_declaration=True)
            #     break
            elem.clear()  # Free
            # metabolite_db = Metabolite.FromDB("db/hmdb.db", metabolite.accession)
            # if metabolite_db.biological_properties != metabolite.biological_properties:
            #     print(metabolite.accession) # To add space
            #     break
            #
            # # To speed up the checking process, we can delete the database once in a while
            # if len(metabolites) % 5_000 == 0:
            #     os.remove("db/hmdb.db")
            #     # Create the database schema again
            #     create_db("db/hmdb.db") memory

            prg.update(len(metabolites))

    print(len(metabolites))