from dataclasses import dataclass, field, fields
from typing import Optional, Union, Dict, Tuple, List

@dataclass
class Pathway:
    """
    Represents a metabolic pathway in the HMDB database.
    """
    name: Optional[str] = field(default=None, metadata={"desc": "Name of the pathway"})
    smpdb_id: Optional[str] = field(default=None, metadata={"desc": "SMPDB identifier of the pathway"})
    kegg_map_id: Optional[str] = field(default=None, metadata={"desc": "KEGG identifier of the pathway"})

    @classmethod
    def FromXML(cls, elem: Union[Dict, 'ElementTree.Element']) -> 'Pathway':
        """
        Load a Pathway object from an XML element or dictionary.
        :param elem: The XML element or dictionary containing pathway data
        :return: The Pathway object
        """
        data = {field.name: elem.findtext(field.name) for field in fields(cls)}

        return cls(**data)