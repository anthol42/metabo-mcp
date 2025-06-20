from dataclasses import dataclass, field, fields
from typing import Optional, Union, Dict, Tuple, List, Any

@dataclass
class Protein:
    """
    Represents a protein in the HMDB database.
    """
    protein_accession: Optional[str] = field(default=None, metadata={"desc": "Protein HMDB accession number"})
    name: Optional[str] = field(default=None, metadata={"desc": "Common name of the protein"})
    uniprot_id: Optional[str] = field(default=None, metadata={"desc": "Uniprot ID"})
    gene_name: Optional[str] = field(default=None, metadata={"desc": "Gene name"})
    protein_type: Optional[str] = field(default=None, metadata={"desc": "Protein type"})

    @classmethod
    def FromXML(cls, elem: Union[Dict[str, Any], 'ElementTree.Element']) -> 'Protein':
        """
        Load a Protein object from an XML element or dictionary.
        :param elem: The XML element or dictionary containing protein data
        :return: The Protein object
        """
        if elem is None:
            return cls()
        data = {field.name: elem.findtext(field.name) for field in fields(cls)}

        return cls(**data)

    def toDB(self, cursor, metabolite_accession):
        """
        Save the Protein object to the database.
        :param cursor: Database cursor
        :param metabolite_accession: The accession number of the associated metabolite
        """
        cursor.execute("""
            INSERT INTO protein (protein_accession, metabolite_accession, name, uniprot_id, gene_name, protein_type)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (self.protein_accession,
              metabolite_accession,
              self.name,
              self.uniprot_id,
              self.gene_name,
              self.protein_type))
