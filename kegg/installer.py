from project_utils import Installer



class KeggInstaller(Installer):
    def __call__(self):
        # Nothing to install for KEGG, only an api
        return None