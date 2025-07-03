# Metabolomic Analysis MCP server
This server provides access to some prebuilt pipelines or functions that allow the analysis of the data and the 
production of figures.

**Note: This project is strongly inspired by the [MEDIC](https://pypi.org/project/medic-ml/) application that provides an intuitive GUI to automatically 
perform reproducible and interpretable classification experiments for metabolomic data.**


## Tools
### Main (TODO: Change name)
Pipeline that does (Inspired by MEDIC):
1. Load the data
2. Prepare the data (Setting up feature columns, target columns, id columns and pair samples columns)
3. Split the data
4. Hyperparameter search using Cross Validation and bayesian optimization.
5. Extract meaningful representation from results and make figures and tables
6. Make a report

