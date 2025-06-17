# LIPID MAPS MCP server

## About
This MCP server will give access to the search tool of the LIPID MAPS database. The available tools are described in the
**Tools** section.

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
        "lipidmaps": {
            "command": "uv",
            "args": [
                "--directory",
                "absolute/path/metabo-mcp/lipidmaps",
                "run",
                "server.py"
            ]
        }
    }
}
```

## Tools
Implemented tools from this server
### Search
Search for compounds in the LipidMaps database using a query string.
It returns a list of compounds that match the query with the following fields:

| Field         | Description                                                         |
|---------------|---------------------------------------------------------------------|
| `regno`       | LipidMaps internal registration number                              |
| `lm_id`       | Unique LipidMaps ID (e.g., LMGP01010573)                            |
| `name`        | Common lipid name with specific fatty acid chains                   |
| `sys_name`    | Systematic IUPAC name                                               |
| `synonyms`    | Alternative names, often semicolon-separated                        |
| `abbrev`      | Abbreviated lipid name (e.g., PC 34:0)                              |
| `abbrev_chains` | Abbreviation including chain composition (e.g., PC 16:0_18:0)     |
| `core`        | Core lipid category (e.g., Glycerophospholipids [GP])              |
| `main_class`  | Main lipid class (e.g., Glycerophosphocholines [GP01])             |
| `sub_class`   | Subclass (e.g., Diacylglycerophosphocholines [GP0101])             |
| `exactmass`   | Exact monoisotopic mass (as string)                                 |
| `formula`     | Chemical formula (e.g., C42H84NO8P)                                 |
| `inchi`       | IUPAC InChI representation                                          |
| `inchi_key`   | InChIKey (hashed InChI for searching)                               |
| `hmdb_id`     | HMDB identifier                                                     |
| `chebi_id`    | ChEBI identifier                                                    |
| `pubchem_cid` | PubChem Compound ID                                                 |
| `smiles`      | SMILES representation of the molecule                               |
