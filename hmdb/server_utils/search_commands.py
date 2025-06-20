
possible_search_fields = ['name', 'chemical_formula', 'iupac_name', 'inchikey', 'smiles',
    'drugbank_id', 'foodb_id', 'pubchem_compound_id', 'chebi_id', 'kegg_id',
    'wikipedia_id']

def search_all(regex: bool = False) -> str:
    if regex:
        return """
        SELECT DISTINCT accession, name, chemical_formula, average_molecular_weight, monisotopic_molecular_weight, 
                iupac_name, traditional_iupac, inchikey, smiles, drugbank_id, foodb_id, pubchem_compound_id, 
                chebi_id, kegg_id, wikipedia_id
        FROM metabolite m
        WHERE 
            accession REGEXP ? OR
            chemical_formula REGEXP ? OR
            iupac_name REGEXP ? OR
            inchikey REGEXP ? OR
            drugbank_id REGEXP ? OR
            foodb_id REGEXP ? OR
            pubchem_compound_id REGEXP ? OR
            chebi_id REGEXP ? OR
            kegg_id REGEXP ? OR
            name REGEXP ? OR
            wikipedia_id REGEXP ?
        """
    else:
        return """
        SELECT DISTINCT accession, name, chemical_formula, average_molecular_weight, monisotopic_molecular_weight, 
                        iupac_name, traditional_iupac, inchikey, smiles, drugbank_id, foodb_id, pubchem_compound_id, 
                        chebi_id, kegg_id, wikipedia_id
        FROM metabolite m
        WHERE 
        accession = ? OR
        chemical_formula = ? OR
        iupac_name = ? OR
        inchikey = ? OR
        drugbank_id = ? OR
        foodb_id = ? OR
        pubchem_compound_id = ? OR
        chebi_id = ? OR
        kegg_id = ? OR
        LOWER(name) LIKE LOWER(?) OR
        LOWER(wikipedia_id) LIKE LOWER(?)
        """

def search_field(field: str, regex: bool = False) -> str:
    if field not in possible_search_fields:
        raise ValueError(f"Invalid search field: {field}. Must be one of {possible_search_fields}.")
    if regex:
        return f"""
        SELECT DISTINCT accession, name, chemical_formula, average_molecular_weight, monisotopic_molecular_weight, 
                        iupac_name, traditional_iupac, inchikey, smiles, drugbank_id, foodb_id, pubchem_compound_id, 
                        chebi_id, kegg_id, wikipedia_id
        FROM metabolite m
        WHERE {field} REGEXP ?
        """
    else:
        if field in ['name', 'wikipedia_id']:
            field_op = f"LOWER({field}) LIKE LOWER(?)"
        else:
            field_op = f"{field} = ?"
        return f"""
        SELECT DISTINCT accession, name, chemical_formula, average_molecular_weight, monisotopic_molecular_weight, 
                        iupac_name, traditional_iupac, inchikey, smiles, drugbank_id, foodb_id, pubchem_compound_id, 
                        chebi_id, kegg_id, wikipedia_id
        FROM metabolite m
        WHERE {field_op}
        """