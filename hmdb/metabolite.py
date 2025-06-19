from dataclasses import dataclass, field, fields
from typing import Optional, Union, Dict, Tuple, List, Any
from xml.etree import ElementTree as ET

from biological_properties import BiologicalProperties
from concentration import Concentration, make_concentration_dataframe
from taxonomy import Taxonomy
from protein import Protein


@dataclass
class Metabolite:
    """
    Represents a metabolite in the HMDB database.
    """
    # General information
    version: str = field(metadata={"desc": "Version of the HMDB database"})
    creation_date: str = field(metadata={"desc": "Creation date of the metabolite entry"})
    update_date: str = field(metadata={"desc": "Last update date of the metabolite entry"})
    accession: str = field(metadata={"desc": "Accession of the metabolite"})
    status: str = field(metadata={"desc": "Status of the metabolite"})
    secondary_accessions: List[str] = field(metadata={"desc": "Secondary accessions of the metabolite"})
    name: str = field(metadata={"desc": "Common name of the metabolite"})
    description: str = field(metadata={"desc": "Description of the metabolite"})
    synonyms: List[str] = field(metadata={"desc": "Synonyms of the metabolite"})
    chemical_formula: str = field(metadata={"desc": "Chemical formula of the metabolite"})
    average_molecular_weight: float = field(metadata={"desc": "Average molecular weight of the metabolite"})
    monisotopic_molecular_weight: float = field(metadata={"desc": "Monoisotopic molecular weight of the metabolite"})
    iupac_name: str = field(metadata={"desc": "IUPAC name of the metabolite"})
    traditional_iupac: str = field(metadata={"desc": "Traditional IUPAC name of the metabolite"})
    smiles: str = field(metadata={"desc": "SMILES of the metabolite"})
    inchi: str = field(metadata={"desc": "InChI of the metabolite"})
    inchikey: str = field(metadata={"desc": "InChIKey of the metabolite"})

    # Cross-references identifiers
    chemspider_id: str = field(metadata={"desc": "ChemSpiderId of the metabolite"})
    drugbank_id: str = field(metadata={"desc": "DrugbankId of the metabolite"})
    foodb_id: str = field(metadata={"desc": "FoodbId of the metabolite"})
    pubchem_compound_id: str = field(metadata={"desc": "PubChemCompoundId of the metabolite"})
    pdb_id: str = field(metadata={"desc": "PDBId of the metabolite"})
    chebi_id: str = field(metadata={"desc": "ChebiId of the metabolite"})
    phenol_explorer_compound_id: str = field(metadata={"desc": "PhenolExplorerCompound of the metabolite"})
    knapsack_id: str = field(metadata={"desc": "KnapsackId of the metabolite"})
    kegg_id: str = field(metadata={"desc": "KEGGId of the metabolite"})
    biocyc_id: str = field(metadata={"desc": "BioCycId of the metabolite"})
    bigg_id: str = field(metadata={"desc": "BigGId of the metabolite"})
    wikipedia_id: str = field(metadata={"desc": "WikipediaId of the metabolite"})
    metlin_id: str = field(metadata={"desc": "MetlinId of the metabolite"})
    vmh_id: str = field(metadata={"desc": "VMHId of the metabolite"})
    fbonto_id: str = field(metadata={"desc": "Fbonto Id of the metabolite"})

    # Nested data
    taxonomy: Taxonomy = field(metadata={"desc": "Taxonomy of the metabolite"})
    experimental_properties: Dict[str, str] = field(metadata={"desc": "Experimental properties of the metabolite"})
    predicted_properties: Dict[str, str] = field(metadata={"desc": "Predicted properties of the metabolite"})
    biological_properties: BiologicalProperties = field(metadata={"desc": "Biological properties of the metabolite"})
    normal_concentrations: List[Concentration] = field(metadata={"desc": "Normal concentrations of the metabolite"})
    abnormal_concentrations: List[Concentration] = field(metadata={"desc": "Abnormal concentrations of the metabolite"})
    protein_associations: List[Protein] = field(metadata={"desc": "Protein associated to the metabolite"})

    @classmethod
    def FromXML(cls, xml_element: ET.Element) -> "Metabolite":
        # Step 1: Extract all scalar fields
        data  = {field.name: xml_element.findtext(field.name)
                 for field in fields(cls)
                 if (field.type == str or field.type == float) and xml_element.findtext(field.name) is not None}

        # Step 2: Extract List fields
        data["secondary_accessions"] = [elem.text for elem in xml_element.find("secondary_accessions")]
        data["synonyms"] = [elem.text for elem in xml_element.find("synonyms")]
        data["normal_concentrations"] = [Concentration.FromXML(elem) for elem in xml_element.findall("normal_concentrations/concentration")]
        data["abnormal_concentrations"] = [Concentration.FromXML(elem) for elem in xml_element.findall("abnormal_concentrations/concentration")]
        data["protein_associations"] = [Protein.FromXML(elem) for elem in xml_element.findall("protein_associations/protein")]

        # Step 3: Extract nested dict
        data["experimental_properties"] = {elem.find("kind").text:elem.find("value").text for elem in xml_element.find("experimental_properties")}
        data["predicted_properties"] = {elem.find("kind").text:elem.find("value").text for elem in xml_element.find("predicted_properties")}

        # Step 4: Extract nested objects
        data["taxonomy"] = Taxonomy.FromXML(xml_element.find("taxonomy"))
        data["biological_properties"] = BiologicalProperties.FromXML(xml_element.find("biological_properties"))

        return cls(**data)

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