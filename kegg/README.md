# KEGG MCP server

## About
This MCP server will give access to multiple tools for interacting with the KEGG databases. A presentation of available 
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
        "kegg": {
            "command": "uv",
            "args": [
                "--directory",
                "absolute/path/metabo-mcp/kegg",
                "run",
                "server.py"
            ]
        }
    }
}
```

## Tools
Available tools from this server

### List
Obtain an extensive list of entry identifiers and associated names from a KEGG database.

### Find
Perform a search operation and allow to find entries with matching query keyword or other query data in the specified 
KEGG database.

### Get
This operation retrieves given database entries in a flat file format or in other formats with options (such as images). 

### DDI
This operation searches against the KEGG drug interaction database, where drug-drug interactions designated as
contraindication (CI) and precaution (P) in Japanese drug labels are extracted, standardized by KEGG
identifiers and annotated with any possible molecular mechanims. The first form reports all known interactions,
while the second form can be used to check if any drug pair in a given set of drugs is CI or P.