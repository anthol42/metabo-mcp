from typing import Optional

class Installer:
    def __call__(self) -> Optional[str]:
        """
        If something fails, return the error message as a string.
        :return:
        """
        raise NotImplementedError()

    @property
    def args(self):
        return []
