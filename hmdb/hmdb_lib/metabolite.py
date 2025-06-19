from dataclasses import dataclass, field, fields
from typing import Optional, Union, Dict, Tuple, List, Any
from xml.etree import ElementTree as ET

from .biological_properties import BiologicalProperties
from .concentration import Concentration, make_concentration_dataframe
from .taxonomy import Taxonomy
from .protein import Protein


@dataclass
class Metabolite:
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
        data  = {field.name: xml_element.findtext(field.name)
                 for field in fields(cls)
                 if (field.type == str or field.type == float) and xml_element.findtext(field.name) is not None}

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