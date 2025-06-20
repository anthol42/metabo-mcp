from project_utils import Installer
import dotenv
import os
from pathlib import PurePath



class PubMedInstaller(Installer):
    def __call__(self):
        root = PurePath(__file__).parent
        if not os.path.exists(root / ".env"):
            with open(root / ".env", "w") as f:
                f.write("")
        dotenv.load_dotenv(root / ".env")
        if not os.getenv("NCBI_EMAIL"):
            email = input("Please enter your NCBI email address: ")
            with open(root / ".env", "a") as f:
                f.write(f"NCBI_EMAIL={email}\n")
        return None