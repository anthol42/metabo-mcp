# PubChem MCP server

## About
This MCP server will give access to the search tool of the PubChem database. The available tools are described in the
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
        "pubchem": {
            "command": "uv",
            "args": [
                "--directory",
                "absolute/path/metabo-mcp/pubchem",
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
You can search for compounds or substance in the PubChem database.\
You can search by:
- cid
- name
- smiles
- inchi
- inchikey
- formula

You can retrieve the following information:
- full record
- properties
- synonyms
- sids
- cids
- classification
- pubmed (All pubmed papers related to the compound)
- description