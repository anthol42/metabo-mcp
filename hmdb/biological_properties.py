from dataclasses import dataclass, field, fields
from typing import Optional, Union, Dict, Tuple, List
from pathway import Pathway

@dataclass
class BiologicalProperties:
    """
    Represents the biological properties of a metabolite.
    """

    cellular_locations: List[str] = field(default_factory=list, metadata={"help": "List of cellular locations"})
    biospecimen_locations: List[str] = field(default_factory=list, metadata={"help": "List of biospecimen locations"})
    tissue_locations: List[str] = field(default_factory=list, metadata={"help": "List of tissue locations"})
    pathways: List[Pathway] = field(default_factory=list, metadata={"help": "List of pathways associated with the metabolite"})

    @classmethod
    def FromXML(cls, elem: Union[Dict, 'ElementTree.Element']) -> 'BiologicalProperties':
        """
        Load a BiologicalProperties object from an XML element or dictionary.
        :param elem: The XML element or dictionary containing biological properties data
        :return: The BiologicalProperties object
        """
        cellular_locations = [loc.text for loc in elem.find('cellular_locations')]
        biospecimen_locations = [loc.text for loc in elem.find('biospecimen_locations')]
        tissue_locations = [loc.text for loc in elem.find('tissue_locations')]
        # Handle pathways
        pathways = [Pathway.FromXML(pathway_elem) for pathway_elem in elem.find('pathways')]

        return cls(
            cellular_locations=cellular_locations,
            biospecimen_locations=biospecimen_locations,
            tissue_locations=tissue_locations,
            pathways=pathways
        )