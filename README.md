# Metabo-MCP
This package contains multiple MCP servers that allows LLMs to access databases essential for metabolomics research.

## Run the pipeline
```bash
uv run metabolomic_analysis/pipeline.py
```
## Installation
This is the installation steps for Claude Desktop. Make sure you have installed it before [Claude Desktop](https://claude.ai/download)\
You must also have installed [UV](https://docs.astral.sh/uv/getting-started/installation/). You also may need to install xgboost headers. I installed them using [homebrew](https://brew.sh).
1. Open your terminal
2. Clone the repository:
```bash
git clone https://github.com/anthol42/metabo-mcp.git
```
3. Change to the project directory:
```bash
cd metabo-mcp
```
4. Since this project uses [UV](https://docs.astral.sh/uv/getting-started/installation/), you must install it first if not already installed. Once 
installed, you can move to the project directory and run the following command to install the dependencies:
```bash
uv sync
```
5. Run the installation script and answer the questions:
```bash
uv run install.py
```

## Update 
To update the package, you can pull the latest changes from the repository, sync the dependencies, and run the 
installation script again:
```bash
git pull
uv sync
uv run install.py
```
## Developer
Please, run uv sync after each pull to be sure you have the latest dependencies.