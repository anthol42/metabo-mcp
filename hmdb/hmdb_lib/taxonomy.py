from dataclasses import dataclass, field, fields
from typing import Optional, Union, Dict, Tuple, List

@dataclass
class Taxonomy:
    """
    Represents the taxonomy of a metabolite in the HMDB database.
    """
    description: Optional[str] = field(default=None, metadata={"desc": "Description of the taxonomy"})
    direct_parent: Optional[str] = field(default=None, metadata={"desc": "Direct parent taxonomy"})
    kingdom: Optional[str] = field(default=None, metadata={"desc": "Kingdom of the taxonomy"})
    super_class: Optional[str] = field(default=None, metadata={"desc": "Super class of the taxonomy"})
    cls: Optional[str] = field(default=None, metadata={"desc": "Class of the taxonomy"})  # 'cls' is fine if you're not using it as a method name
    sub_class: Optional[str] = field(default=None, metadata={"desc": "Sub class of the taxonomy"})
    molecular_framework: Optional[str] = field(default=None, metadata={"desc": "Molecular framework of the taxonomy"})
    alternative_parents: List[str] = field(default_factory=list, metadata={"desc": "Alternative parent taxonomy"})
    substituents: List[str] = field(default_factory=list, metadata={"desc": "Substituents of the taxonomy"})

    @classmethod
    def FromXML(cls, elem: 'ElementTree.Element') -> 'Taxonomy':
        """
        Load a Taxonomy object from an XML element or dictionary.
        :param elem: The XML element or dictionary containing taxonomy data
        :return: The Taxonomy object
        """
        if elem is None:
            return cls()
        data = {field.name: elem.findtext(field.name) for field in fields(cls)}
        if elem.find('alternative_parents'):
            data['alternative_parents'] = [ap.text for ap in elem.find('alternative_parents')]
        if elem.find('substituents'):
            data['substituents'] = [s.text for s in elem.find('substituents')]
        data["cls"] = elem.findtext("class")

        return cls(**data)

    def toDB(self, cursor, accession: str):
        """
        Store the taxonomy data in the database.
        :param cursor: Database cursor
        :param accession: Accession number of the metabolite
        """
        cursor.execute("""
            INSERT INTO taxonomy (accession, description, direct_parent, kingdom, super_class, cls, sub_class, 
                                  molecular_framework)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (accession, self.description, self.direct_parent, self.kingdom, self.super_class, self.cls,
             self.sub_class, self.molecular_framework)
        )

        tax_id = cursor.lastrowid
        if self.alternative_parents:
            cursor.executemany("INSERT INTO taxonomy_alternative_parent (taxonomy_id, alt_parent) VALUES (?, ?)",
                               [(tax_id, parent) for parent in self.alternative_parents])

        if self.substituents:
            cursor.executemany("INSERT INTO taxonomy_substituent (taxonomy_id, substituent) VALUES (?, ?)",
                               [(tax_id, subs) for subs in self.substituents])