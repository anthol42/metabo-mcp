"""
File to parse concentration data from HMDB and convert it to a pandas DataFrame.
"""
from dataclasses import dataclass, field, fields
from typing import Optional, Union, Dict, Tuple, List, Literal
import pandas as pd
from xml.etree import ElementTree


@dataclass
class Concentration:
    biospecimen: Optional[str] = None
    concentration_value: Optional[float] = None
    concentration_units: Optional[str] = None
    subject_age: Optional[str] = None
    subject_sex: Optional[str] = None
    subject_condition: Optional[str] = None
    # references: Optional[List[str]] = field(default=None) # Not handled for now in the DB

    @classmethod
    def FromXML(cls, elem: ElementTree.Element) -> 'Concentration':
        """
        Load a Concentration object from an XML element or dictionary.
        :param elem: The XML element or dictionary containing concentration data
        :return: The Concentration object
        """
        data = {field.name: elem.findtext(field.name) for field in fields(cls)}
        # Check if subject_... is replaced by patient_...
        for field in ["subject_age", "subject_sex", "subject_condition"]:
            if data[field] is None:
                patient_field = field.replace("subject_", "patient_")
                data[field] = elem.findtext(patient_field)

        if elem.find("patient_information") is not None:
            data["subject_condition"] = elem.findtext("patient_information")
        # # Handle reference
        # reference_elem = elem.find('references')
        # if reference_elem is not None:
        #     data['references'] = [ref.find("reference_text").text for ref in reference_elem.findall('reference_text')]
        # else:
        #     data['references'] = []
        return cls(**data)

    def to_pandas(self):
        """
        Return every scala fields. i.e. every field except for the references.
        :return:
        """
        return {field.name: getattr(self, field.name) for field in fields(self) if field.name != 'references'}

    def toDB(self, cursor, metabolite_accession, type: Literal['normal', 'abnormal']) -> int:
        """
        Insert the concentration data into the database.
        :param cursor: Database cursor
        :return: The ID of the inserted concentration
        """
        cursor.execute("""
                       INSERT INTO concentration (metabolite_accession, type, biospecimen, concentration_value, 
                                                   concentration_units, subject_age, subject_sex, subject_condition)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                               """, (
            metabolite_accession,
            type,
            self.biospecimen,
            self.concentration_value,
            self.concentration_units,
            self.subject_age,
            self.subject_sex,
            self.subject_condition
        ))
        # Retrieve the last inserted ID
        return cursor.lastrowid

def make_concentration_dataframe(concentrations: List[Concentration]) -> str:
    """
    Convert a list of Concentration objects to a pandas DataFrame.
    :param concentrations: List of Concentration objects
    :return: A pandas DataFrame containing the concentration data
    """
    data = [concentration.to_pandas() for concentration in concentrations]
    return pd.DataFrame(data).to_csv(index=False)
