from dataclasses import dataclass, field, fields, asdict
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

    @classmethod
    def FromDB(cls, cursor, accession: str) -> 'Taxonomy':
        """
        Load a Taxonomy object from the database.
        :param cursor: Database cursor
        :param accession: Accession number of the metabolite
        :return: The Taxonomy object
        """
        cursor.execute("SELECT description, direct_parent, kingdom, super_class, cls, sub_class, molecular_framework  "
                       "FROM taxonomy WHERE accession = ?", (accession,))
        row = cursor.fetchone()
        if not row:
            return cls()
        data = dict(row)

        # Load alternative parents
        cursor.execute("SELECT alt_parent FROM taxonomy_alternative_parent WHERE accession = ?", (accession,))
        data['alternative_parents'] = [r[0] for r in cursor.fetchall()]

        # Load substituents
        cursor.execute("SELECT substituent FROM taxonomy_substituent WHERE accession = ?", (accession,))
        data['substituents'] = [r[0] for r in cursor.fetchall()]

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

        if self.alternative_parents:
            cursor.executemany("INSERT INTO taxonomy_alternative_parent (accession, alt_parent) VALUES (?, ?)",
                               [(accession, parent) for parent in self.alternative_parents])

        if self.substituents:
            cursor.executemany("INSERT INTO taxonomy_substituent (accession, substituent) VALUES (?, ?)",
                               [(accession, subs) for subs in self.substituents])
    def todict(self) -> dict:
        """
        Convert the Taxonomy object to a dictionary.
        :return: Dictionary representation of the Taxonomy object
        """
        return asdict(self)