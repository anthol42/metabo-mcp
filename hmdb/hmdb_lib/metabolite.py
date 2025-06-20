from dataclasses import dataclass, field, fields
from typing import Optional, Union, Dict, Tuple, List, Any
from xml.etree import ElementTree as ET

from .biological_properties import BiologicalProperties
from .concentration import Concentration, make_concentration_dataframe
from .taxonomy import Taxonomy
from .protein import Protein

from db.dbclass import DBClass


@dataclass
class Metabolite(DBClass):
    """
    Represents a metabolite in the HMDB database.
    """
    # General information
    accession: str = field(metadata={"desc": "Accession of the metabolite"})

    version: Optional[str] = field(default=None, metadata={"desc": "Version of the HMDB database"})
    creation_date: Optional[str] = field(default=None, metadata={"desc": "Creation date of the metabolite entry"})
    update_date: Optional[str] = field(default=None, metadata={"desc": "Last update date of the metabolite entry"})
    status: Optional[str] = field(default=None, metadata={"desc": "Status of the metabolite"})
    secondary_accessions: List[str] = field(default_factory=list, metadata={"desc": "Secondary accessions of the metabolite"})
    name: Optional[str] = field(default=None, metadata={"desc": "Common name of the metabolite"})
    description: Optional[str] = field(default=None, metadata={"desc": "Description of the metabolite"})
    synonyms: List[str] = field(default_factory=list, metadata={"desc": "Synonyms of the metabolite"})
    chemical_formula: Optional[str] = field(default=None, metadata={"desc": "Chemical formula of the metabolite"})
    average_molecular_weight: Optional[float] = field(default=None, metadata={"desc": "Average molecular weight of the metabolite"})
    monisotopic_molecular_weight: Optional[float] = field(default=None, metadata={"desc": "Monoisotopic molecular weight of the metabolite"})
    iupac_name: Optional[str] = field(default=None, metadata={"desc": "IUPAC name of the metabolite"})
    traditional_iupac: Optional[str] = field(default=None, metadata={"desc": "Traditional IUPAC name of the metabolite"})
    smiles: Optional[str] = field(default=None, metadata={"desc": "SMILES of the metabolite"})
    inchi: Optional[str] = field(default=None, metadata={"desc": "InChI of the metabolite"})
    inchikey: Optional[str] = field(default=None, metadata={"desc": "InChIKey of the metabolite"})

    # Cross-references identifiers
    chemspider_id: Optional[str] = field(default=None, metadata={"desc": "ChemSpiderId of the metabolite"})
    drugbank_id: Optional[str] = field(default=None, metadata={"desc": "DrugbankId of the metabolite"})
    foodb_id: Optional[str] = field(default=None, metadata={"desc": "FoodbId of the metabolite"})
    pubchem_compound_id: Optional[str] = field(default=None, metadata={"desc": "PubChemCompoundId of the metabolite"})
    pdb_id: Optional[str] = field(default=None, metadata={"desc": "PDBId of the metabolite"})
    chebi_id: Optional[str] = field(default=None, metadata={"desc": "ChebiId of the metabolite"})
    phenol_explorer_compound_id: Optional[str] = field(default=None, metadata={"desc": "PhenolExplorerCompound of the metabolite"})
    knapsack_id: Optional[str] = field(default=None, metadata={"desc": "KnapsackId of the metabolite"})
    kegg_id: Optional[str] = field(default=None, metadata={"desc": "KEGGId of the metabolite"})
    biocyc_id: Optional[str] = field(default=None, metadata={"desc": "BioCycId of the metabolite"})
    bigg_id: Optional[str] = field(default=None, metadata={"desc": "BigGId of the metabolite"})
    wikipedia_id: Optional[str] = field(default=None, metadata={"desc": "WikipediaId of the metabolite"})
    metlin_id: Optional[str] = field(default=None, metadata={"desc": "MetlinId of the metabolite"})
    vmh_id: Optional[str] = field(default=None, metadata={"desc": "VMHId of the metabolite"})
    fbonto_id: Optional[str] = field(default=None, metadata={"desc": "Fbonto Id of the metabolite"})

    # Nested data
    taxonomy: Optional[Taxonomy] = field(default=None, metadata={"desc": "Taxonomy of the metabolite"})
    experimental_properties: Optional[Dict[str, str]] = field(default=None, metadata={"desc": "Experimental properties of the metabolite"})
    predicted_properties: Optional[Dict[str, str]] = field(default=None, metadata={"desc": "Predicted properties of the metabolite"})
    biological_properties: Optional[BiologicalProperties] = field(default=None, metadata={"desc": "Biological properties of the metabolite"})
    normal_concentrations: List[Concentration] = field(default_factory=list, metadata={"desc": "Normal concentrations of the metabolite"})
    abnormal_concentrations: List[Concentration] = field(default_factory=list, metadata={"desc": "Abnormal concentrations of the metabolite"})
    protein_associations: List[Protein] = field(default_factory=list, metadata={"desc": "Protein associated to the metabolite"})

    @classmethod
    def FromXML(cls, xml_element: ET.Element) -> "Metabolite":
        # Step 1: Extract all scalar fields
        data  = {field.name: xml_element.find(field.name).text
                 for field in fields(cls)
                 if (field.type == str or field.type == float or field.type == Optional[str] or field.type == Optional[float])
                 and xml_element.find(field.name) is not None}
        # Step 2: Extract List fields
        if xml_element.find("secondary_accessions"):
            data["secondary_accessions"] = [elem.text for elem in xml_element.find("secondary_accessions")]
        if xml_element.find("synonyms"):
            data["synonyms"] = [elem.text for elem in xml_element.find("synonyms")]
        if xml_element.find("normal_concentrations"):
            data["normal_concentrations"] = [Concentration.FromXML(elem) for elem in xml_element.find("normal_concentrations")]
        if xml_element.find("abnormal_concentrations"):
            data["abnormal_concentrations"] = [Concentration.FromXML(elem) for elem in xml_element.find("abnormal_concentrations")]
        if xml_element.find("protein_associations"):
            data["protein_associations"] = [Protein.FromXML(elem) for elem in xml_element.find("protein_associations")]

        # Step 3: Extract nested dict
        if xml_element.find("experimental_properties"):
            data["experimental_properties"] = {elem.find("kind").text:elem.find("value").text for elem in xml_element.find("experimental_properties")}
        if xml_element.find("predicted_properties"):
            data["predicted_properties"] = {elem.find("kind").text:elem.find("value").text for elem in xml_element.find("predicted_properties")}

        # Step 4: Extract nested objects
        data["taxonomy"] = Taxonomy.FromXML(xml_element.find("taxonomy"))
        data["biological_properties"] = BiologicalProperties.FromXML(xml_element.find("biological_properties"))

        if "accession" not in data:
            print("Accession not found in XML element. Available tags:")
            for elem in xml_element:
                print(elem.tag, elem.text)
        return cls(**data)

    @classmethod
    def FromDB(cls, db_path: str, accession: str) -> "Metabolite":
        data = {}
        with cls.cursor_as_dict(db_path) as cursor:
            # Fetch the metabolite data
            cursor.execute("""
                SELECT * FROM metabolite WHERE accession = ?
            """, (accession,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Metabolite with accession {accession} not found in database.")

            # Create the Metabolite object from the row
            metabolite = cls(**row)

            # Fetch secondary accessions
            cursor.execute("""
                SELECT secondary_accession FROM secondary_accession WHERE metabolite_accession = ?
            """, (accession,))
            metabolite.secondary_accessions = [r['secondary_accession'] for r in cursor.fetchall()]

            # Fetch synonyms
            cursor.execute("""
                SELECT synonym FROM synonym WHERE metabolite_accession = ?
            """, (accession,))
            metabolite.synonyms = [r['synonym'] for r in cursor.fetchall()]

            # Fetch experimental properties
            cursor.execute("""
                SELECT property_key, property_value FROM experimental_property WHERE metabolite_accession = ?
            """, (accession,))
            metabolite.experimental_properties = {r['property_key']: r['property_value'] for r in cursor.fetchall()}

            # Fetch predicted properties
            cursor.execute("""
                SELECT property_key, property_value FROM predicted_property WHERE metabolite_accession = ?
            """, (accession,))
            metabolite.predicted_properties = {r['property_key']: r['property_value'] for r in cursor.fetchall()}

            # Fetch concentrations
            cursor.execute("""
                SELECT biospecimen, 
                       concentration_value, 
                       concentration_units, 
                       subject_age,
                       subject_sex,
                       subject_condition
                FROM concentration WHERE metabolite_accession = ? AND type = 'normal'
            """, (accession,))
            metabolite.normal_concentrations = [Concentration(**r) for r in cursor.fetchall()]

            cursor.execute("""
                           SELECT biospecimen,
                                  concentration_value,
                                  concentration_units,
                                  subject_age,
                                  subject_sex,
                                  subject_condition
                           FROM concentration
                           WHERE metabolite_accession = ?
                             AND type = 'abnormal'
                           """, (accession,))
            metabolite.abnormal_concentrations = [Concentration(**r) for r in cursor.fetchall()]

            # Fetch protein associations
            cursor.execute("""
                SELECT protein_accession, name, uniprot_id, gene_name, protein_type FROM protein WHERE metabolite_accession = ?
            """, (accession,))
            metabolite.protein_associations = [Protein(**r) for r in cursor.fetchall()]

            # Fetch taxonomy
            metabolite.taxonomy = Taxonomy.FromDB(cursor, accession)

            # Fetch biological properties
            metabolite.biological_properties = BiologicalProperties.FromDB(cursor, accession)
        return metabolite
    def toDB(self, db_path: str) -> bool:
        """
        Save the metabolite to the database.
        :param db_path: Path to the database file
        :return: True if successful, False otherwise
        """
        with self.cursor(db_path) as cursor:
            # Insert or update the metabolite in the database
            cursor.execute("""
                INSERT OR REPLACE INTO metabolite (accession, version, creation_date, update_date, status,
                                                    name, description, chemical_formula, average_molecular_weight,
                                                    monisotopic_molecular_weight, iupac_name, traditional_iupac,
                                                    smiles, inchi, inchikey, chemspider_id, drugbank_id,
                                                    foodb_id, pubchem_compound_id, pdb_id, chebi_id,
                                                    phenol_explorer_compound_id, knapsack_id, kegg_id,
                                                    biocyc_id, bigg_id, wikipedia_id, metlin_id,
                                                    vmh_id, fbonto_id)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                self.accession,
                self.version,
                self.creation_date,
                self.update_date,
                self.status,
                self.name,
                self.description,
                self.chemical_formula,
                self.average_molecular_weight,
                self.monisotopic_molecular_weight,
                self.iupac_name,
                self.traditional_iupac,
                self.smiles,
                self.inchi,
                self.inchikey,
                self.chemspider_id,
                self.drugbank_id,
                self.foodb_id,
                self.pubchem_compound_id,
                self.pdb_id,
                self.chebi_id,
                self.phenol_explorer_compound_id,
                self.knapsack_id,
                self.kegg_id,
                self.biocyc_id,
                self.bigg_id,
                self.wikipedia_id,
                self.metlin_id,
                self.vmh_id,
                self.fbonto_id
            ))
            # Add vector data
            self._add_secondary_accessions_db(cursor)
            self._add_synonyms_db(cursor)

            # Add dict data
            self._add_experimental_properties_db(cursor)
            self._add_predicted_properties_db(cursor)

            # Add nested objects
            if self.taxonomy:
                self.taxonomy.toDB(cursor, self.accession)
            if self.biological_properties:
                self.biological_properties.toDB(cursor, self.accession)

            # List nested objects
            self._add_concentrations_db(cursor)
            self._add_protein_associations_db(cursor)

    def _add_secondary_accessions_db(self, cursor):
        """
        Add secondary accessions to the database.
        :param cursor: Database cursor
        """
        # With execute many, we can insert multiple rows at once
        if self.secondary_accessions:
            cursor.executemany("""
                INSERT INTO secondary_accession (metabolite_accession, secondary_accession)
                VALUES (?, ?)
            """, [(self.accession, sec_acc) for sec_acc in self.secondary_accessions])

    def _add_synonyms_db(self, cursor):
        """
        Add synonyms to the database.
        :param cursor: Database cursor
        """
        # With execute many, we can insert multiple rows at once
        if self.synonyms:
            cursor.executemany("""
                INSERT INTO synonym (metabolite_accession, synonym)
                VALUES (?, ?)
            """, [(self.accession, syn) for syn in self.synonyms])

    def _add_experimental_properties_db(self, cursor):
        """
        Add experimental properties to the database.
        :param cursor: Database cursor
        """
        if self.experimental_properties:
            cursor.executemany("""
                INSERT INTO experimental_property (metabolite_accession, property_key, property_value)
                VALUES (?, ?, ?)
            """, [(self.accession, key, value) for key, value in self.experimental_properties.items()])

    def _add_predicted_properties_db(self, cursor):
        """
        Add predicted properties to the database.
        :param cursor: Database cursor
        """
        if self.predicted_properties:
            cursor.executemany("""
                INSERT INTO predicted_property (metabolite_accession, property_key, property_value)
                VALUES (?, ?, ?)
            """, [(self.accession, key, value) for key, value in self.predicted_properties.items()])

    def _add_concentrations_db(self, cursor):
        """
        Add normal concentrations to the database.
        :param cursor: Database cursor
        """
        if self.normal_concentrations:
            conc_ids = [conc.toDB(cursor, self.accession, 'normal') for conc in self.normal_concentrations]
        if self.abnormal_concentrations:
            conc_ids = [conc.toDB(cursor, self.accession, 'abnormal') for conc in self.abnormal_concentrations]

    def _add_protein_associations_db(self, cursor):
        """
        Add protein associations to the database.
        :param cursor: Database cursor
        """
        if self.protein_associations:
            [protein.toDB(cursor, self.accession) for protein in self.protein_associations]

def strip_namespace(elem):
    for el in elem.iter():
        if '}' in el.tag:
            el.tag = el.tag.split('}', 1)[1]  # Remove namespace
if __name__ == "__main__":
    from pprint import pprint
    xml = ET.parse("output2.xml")
    root = xml.getroot()
    strip_namespace(root)
    metabolite = Metabolite.FromXML(root)
    pprint(metabolite.secondary_accessions)