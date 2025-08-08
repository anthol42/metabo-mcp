from project_utils import Installer
import subprocess

class MetaboAnalysisInstaller(Installer):
    def __call__(self):
        # Run 'brew install libomp'
        subprocess.run(["brew", "install", "libomp"], check=True)
