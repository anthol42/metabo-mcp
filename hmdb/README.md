# KEGG MCP server

## About
This MCP server will give access to multiple tools for interacting with the HMDB databases. A presentation of available 
tools is written in the **Tools** section.

## Installation
Write down the path of this directory.

1. Sync the uv environment
```commandline
uv sync
```
2. Edit the claude config file to add the server

MacOS:\
Edit the `~/Library/Application Support/Claude/claude_desktop_config.json` file and add the following entry to the 
`mcpServers` object:

```text
{
    "mcpServers": {
        ...
        "hmdb": {
            "command": "uv",
            "args": [
                "--directory",
                "absolute/path/metabo-mcp/hmdb",
                "run",
                "server.py"
            ]
        }
    }
}
```

## Tools
Currently, the MCP server does not use the API since we do not have access. To counter this,
we download the HMDB metabolite database and parse it. This means we only have access to metabolites. We currently give 
access to this information:
- Description and useful information about a metabolite
- Cross-references ids (Ids of other databases)
- Taxonomy
- Properties of the metabolite (experimental and predicted)
- Normal and abnormal concentrations
- Associated proteins.

If you want to add more features, please contact the developers.

## Search
Allows to do a search in the HMDB database by exact match or regex expressions. If there is too many results, the 
response is paginated (Max 10 results per page). The request will return a table of mulitple columns:
- accession
- name
- chemical_formula
- average_molecular_weight
- monisotopic_molecular_weight
- iupac_name
- traditional_iupac
- inchikey
- smiles
- drugbank_id
- foodb_id
- pubchem_compound_id
- chebi_id
- kegg_id
- wikipedia_id (wikipedia name)

## Get metabolite
This function allows to retrieve all information implemented about a metabolite given its accession number. The llm
can specify which information about the metabolite it wants to retrieve. The response is a json object, except for the
concentrations that are reported as a table (csv). The following fields can be requested:
- all
- description
- taxonomy 
- properties
- concentrations
- protein_associations
- 