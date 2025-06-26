from project_utils import Installer
import dotenv
import os
from pathlib import PurePath



class PubChemInstaller(Installer):
    def __call__(self):
        # Nothing to install for PubChem
        pass