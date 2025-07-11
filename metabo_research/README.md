# Metabolomic Research Agent
This agent, usable by MCP takes a question about the implication of a metabolite in a condition as input and will 
search in PubMed for relevant articles. Then, it will extract the relevant information and synthesize it to answer the 
question.

## Workflow
1. Reformulate the question into different formulations to increase the chances of finding relevant articles.
2. Identify the metabolite(s) in the question and search in PubChem for articles related to the metabolite(s).
3. An agent will read the abstracts of all articles and determine if they are relevant to the question.
4. Another agent will extract the relevant information from the article and synthesize it to answer the question.
5. A concatenation of the answers will be returned with the references.

## Examples
