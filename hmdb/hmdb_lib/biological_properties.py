from dataclasses import dataclass, field, fields
from typing import Optional, Union, Dict, Tuple, List
from .pathway import Pathway
from xml.etree import ElementTree

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
    def FromXML(cls, elem: ElementTree.Element) -> 'BiologicalProperties':
        """
        Load a BiologicalProperties object from an XML element or dictionary.
        :param elem: The XML element or dictionary containing biological properties data
        :return: The BiologicalProperties object
        """
        if elem is None:
            return cls()
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

    def toDB(self, cursor, accession: str):
        """
        Save the biological properties to the database.
        :param cursor: Database cursor
        :param accession: Accession number of the metabolite
        """
        if self.cellular_locations:
            cursor.executemany("""
                INSERT INTO cellular_location (metabolite_accession, location)
                VALUES (?, ?)
            """, [(accession, loc) for loc in self.cellular_locations])

        if self.biospecimen_locations:
            cursor.executemany("""
                INSERT INTO biospecimen_location (metabolite_accession, location)
                VALUES (?, ?)
            """, [(accession, loc) for loc in self.biospecimen_locations])

        if self.tissue_locations:
            cursor.executemany("""
                INSERT INTO tissue_location (metabolite_accession, location)
                VALUES (?, ?)
            """, [(accession, loc) for loc in self.tissue_locations])

        if self.pathways:
            pathway_ids = [pathway.toDB(cursor) for pathway in self.pathways]
             # remove duplicates from pathway_ids
            pathway_ids = list(set(pathway_ids))
            cursor.executemany("""
                INSERT INTO metabolite_pathway (metabolite_accession, pathway_id)
                VALUES (?, ?)
            """, [(accession, pathway_id) for pathway_id in pathway_ids])

