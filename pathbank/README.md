# MarkerDB MCP server

## About
This MCP server will give access to the search tool of the PathBank database. The available tools are described in the
**Tools** section.

## Installation
If you do not want to use the installer.

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
        "pathbank": {
            "command": "uv",
            "args": [
                "--directory",
                "absolute/path/metabo-mcp/pathbank",
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
Search for pathways in the PathBank database.

### Get
Retrieve information about a pathway based on its ID. It gets:
- The name
- The description
- The specie
- The metabolites

### Not implemented:
There is currently no tool to retrieve the SBML file or the image of the pathway. This is due to technical limitations 
because most sbml files are too large to be handled by the MCP server and I did not find any good way to make a pathway 
image from SBML.
