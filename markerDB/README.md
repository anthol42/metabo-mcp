# MarkerDB MCP server

## About
This MCP server will give access to the search tool of the MarkerDB database. The available tools are described in the
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
        "markerDB": {
            "command": "uv",
            "args": [
                "--directory",
                "absolute/path/metabo-mcp/markerDB",
                "run",
                "server.py"
            ]
        }
    }
}
```

## Tools
Implemented tools from this server

### Search proteins
Search for proteins that are known to be markers for a specific disease or condition.

### Search chemicals
Search for chemicals (metabolites) that are known to be markers for a specific disease or condition.

### Search diseases
Search for diseases or conditions that are known to be associated with specific proteins or chemicals.
