# LIPID MAPS MCP server

## About
This MCP server will give access to the search tool of the LIPID MAPS database.

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