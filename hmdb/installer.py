from project_utils import Installer
import os
from pathlib import PurePath
import sys
sys.path.append(str(PurePath(__file__).parent))
from hmdb.download import install_hmdb_db


class HMDBInstaller(Installer):
    def __call__(self):
        # If already installed, do nothing
        load_cache = True
        if os.path.exists(PurePath(__file__).parent / "db" / "hmdb.db"):
            answer = input(f"Found an existing databse. Do you want to reinstall it? (y/n): ")
            if answer.lower().strip() in ["y", "yes"]:
                load_cache = False
        install_hmdb_db(load_cache=load_cache)
