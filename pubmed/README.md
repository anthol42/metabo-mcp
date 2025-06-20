# LIPID MAPS MCP server

## About
This MCP server will give access to Pubmed and Pubmed central The available tools are described in the
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
        "pubmed": {
            "command": "uv",
            "args": [
                "--directory",
                "absolute/path/metabo-mcp/pubmed",
                "run",
                "server.py"
            ]
        }
    }
}
```

## Tools
Implemented tools from this server
## Search
Search papers given the query using the Pubmed API.

## Get abstract
You can read the abstract of a paper given its Pubmed ID.

## Get full text
You can read the full text of a paper given its Pubmed ID. This will return the HTML content of the paper.

## Get similar papers
You can get similar papers given a Pubmed ID. This will return a list of Pubmed IDs of similar papers.