-- Metabolite class
CREATE TABLE metabolite (
    accession TEXT PRIMARY KEY,  -- Accession of the metabolite

    version TEXT,                -- Version of the HMDB database
    creation_date TEXT,          -- Creation date of the metabolite entry
    update_date TEXT,            -- Last update date of the metabolite entry
    status TEXT,                 -- Status of the metabolite

    name TEXT,                   -- Common name of the metabolite
    description TEXT,            -- Description of the metabolite
    chemical_formula TEXT,       -- Chemical formula of the metabolite
    average_molecular_weight REAL,      -- Average molecular weight
    monisotopic_molecular_weight REAL,  -- Monoisotopic molecular weight
    iupac_name TEXT,             -- IUPAC name
    traditional_iupac TEXT,      -- Traditional IUPAC name
    smiles TEXT,                 -- SMILES
    inchi TEXT,                  -- InChI
    inchikey TEXT,               -- InChIKey

    -- Cross-reference identifiers
    chemspider_id TEXT,
    drugbank_id TEXT,
    foodb_id TEXT,
    pubchem_compound_id TEXT,
    pdb_id TEXT,
    chebi_id TEXT,
    phenol_explorer_compound_id TEXT,
    knapsack_id TEXT,
    kegg_id TEXT,
    biocyc_id TEXT,
    bigg_id TEXT,
    wikipedia_id TEXT,
    metlin_id TEXT,
    vmh_id TEXT,
    fbonto_id TEXT
);

CREATE TABLE secondary_accession (
    metabolite_accession TEXT NOT NULL,
    secondary_accession TEXT NOT NULL,
    FOREIGN KEY (metabolite_accession)
        REFERENCES metabolite(accession)
);

CREATE TABLE synonym (
    metabolite_accession TEXT NOT NULL,
    synonym TEXT NOT NULL,
    FOREIGN KEY (metabolite_accession)
        REFERENCES metabolite(accession)
);
CREATE TABLE experimental_property (
    metabolite_accession TEXT NOT NULL,
    property_key         TEXT NOT NULL,
    property_value       TEXT,

    FOREIGN KEY (metabolite_accession) REFERENCES metabolite(accession),
    UNIQUE (metabolite_accession, property_key)
);
CREATE TABLE predicted_property (
    metabolite_accession TEXT NOT NULL,
    property_key         TEXT NOT NULL,
    property_value       TEXT,

    FOREIGN KEY (metabolite_accession) REFERENCES metabolite(accession),
    UNIQUE (metabolite_accession, property_key)
);

-- Taxonomy class
CREATE TABLE taxonomy (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    accession           TEXT REFERENCES metabolite(accession),  -- Accession of the taxonomy

    description         TEXT,   -- Description of the taxonomy
    direct_parent       TEXT,   -- Direct parent taxonomy
    kingdom             TEXT,   -- Kingdom of the taxonomy
    super_class         TEXT,   -- Super class of the taxonomy
    cls                 TEXT,   -- Class of the taxonomy
    sub_class           TEXT,   -- Sub class of the taxonomy
    molecular_framework TEXT    -- Molecular framework
);
CREATE TABLE taxonomy_alternative_parent (
    taxonomy_id     INTEGER NOT NULL,
    alt_parent      TEXT NOT NULL,

    FOREIGN KEY (taxonomy_id) REFERENCES taxonomy(id)
);
CREATE TABLE taxonomy_substituent (
    taxonomy_id     INTEGER NOT NULL,
    substituent     TEXT NOT NULL,

    FOREIGN KEY (taxonomy_id) REFERENCES taxonomy(id)
);

-- BiologicalProperties
CREATE TABLE cellular_location (
    metabolite_accession TEXT NOT NULL,
    location TEXT NOT NULL,
    FOREIGN KEY (metabolite_accession) REFERENCES metabolite(accession)
);

CREATE TABLE biospecimen_location (
    metabolite_accession TEXT NOT NULL,
    location TEXT NOT NULL,
    FOREIGN KEY (metabolite_accession) REFERENCES metabolite(accession)
);

CREATE TABLE tissue_location (
    metabolite_accession TEXT NOT NULL,
    location TEXT NOT NULL,
    FOREIGN KEY (metabolite_accession) REFERENCES metabolite(accession)
);

-- Pathway class
CREATE TABLE pathway (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT,                -- Name of the pathway
    smpdb_id        TEXT,                -- SMPDB identifier
    kegg_map_id     TEXT,                -- KEGG map identifier

    UNIQUE (smpdb_id, kegg_map_id)
);
CREATE TABLE metabolite_pathway (
    metabolite_accession   INTEGER NOT NULL,    -- FK to metabolite.id
    pathway_id      INTEGER NOT NULL,    -- FK to pathway.id

    PRIMARY KEY (metabolite_accession, pathway_id),
    FOREIGN KEY (metabolite_accession) REFERENCES metabolite(accession)
    FOREIGN KEY (pathway_id) REFERENCES pathway(id)
);

-- Concentrations
CREATE TABLE concentration (
    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    metabolite_accession   TEXT NOT NULL,

    type                   TEXT CHECK(type IN ('normal', 'abnormal')) NOT NULL,

    biospecimen            TEXT,
    concentration_value    TEXT,
    concentration_units    TEXT,
    subject_age            TEXT,
    subject_sex            TEXT,
    subject_condition      TEXT,

    FOREIGN KEY (metabolite_accession) REFERENCES metabolite(accession)
);

-- Protein class
CREATE TABLE protein (
    protein_accession TEXT,  -- HMDB protein accession
    metabolite_accession TEXT NOT NULL,  -- FK to metabolite.accession

    name              TEXT,              -- Common name
    uniprot_id        TEXT,              -- UniProt ID
    gene_name         TEXT,              -- Gene name
    protein_type      TEXT,              -- Protein type
    FOREIGN KEY (metabolite_accession) REFERENCES metabolite(accession),
    PRIMARY KEY (protein_accession, metabolite_accession)  -- Composite primary key
);
