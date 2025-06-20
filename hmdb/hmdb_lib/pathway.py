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
        if elem is None:
            return cls()
        data = {field.name: elem.findtext(field.name) for field in fields(cls)}

        return cls(**data)

    @classmethod
    def FromDB(cls, cursor, pathway_id: int) -> 'Pathway':
        """
        Load a Pathway object from the database.
        :param cursor: Database cursor
        :param pathway_id: ID of the pathway in the database
        :return: The Pathway object
        """
        cursor.execute("""
            SELECT name, smpdb_id, kegg_map_id FROM pathway WHERE id = ?
        """, (pathway_id,))
        row = cursor.fetchone()
        return cls(**row)


    def toDB(self, cursor):
        """
        Save the pathway to the database.
        :param cursor: Database cursor
        :param accession: Accession number of the metabolite
        """
        # Check if smpdb_id, kegg_map_id does not exist in the database
        cursor.execute("""
            SELECT id FROM pathway WHERE smpdb_id = ? AND kegg_map_id = ?
        """, (self.smpdb_id, self.kegg_map_id))
        existing_id = cursor.fetchone()
        if existing_id:
            return existing_id[0]

        # Otherwise, insert the new pathway
        cursor.execute("""
            INSERT INTO pathway (name, smpdb_id, kegg_map_id)
            VALUES (?, ?, ?)
        """, (self.name, self.smpdb_id, self.kegg_map_id))

        return cursor.lastrowid
