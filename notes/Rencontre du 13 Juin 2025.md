# Objectif final du projet
"Le but est de ne pas avoir besoin de PhD pour faire de la métabolomique"

# Use cases
- À partir d'un CSV de concentrations de différentes molécules, trouver celles qui ne sont pas dans le range normal et donner de l'information la dessus et les maladies associés en cross-ref les BD et la litérature.
- Cross-ref la litérature et les BD afin de trouver de l'info sur un métabolite et les maladies/pathways associé.
- Comparer un spectre à une BD de spectres associé à des conditions. (Nous allons faire cette BD en accumulant des données)
- À partir d'une liste de métabolites ou ratios déterminé comme significatif par l'utilisateur, chercher dans tous les bases de données le plus d'info possible et le résumer à l'utilisateur avec les références.
- Envoyer un documents CSV comparatif de samples (condition VS contrôle) et trouver les métabolites significatifs. Une fois que c'est fait, faire l'analyse et la recherche de littérature de ces métabolites.

# Priorité
Il faut lauch la première version le plus tôt possible
Implémenter/intégrer en priorité trois serveur MCP:
- HMDB
- [Lipidmaps]([https://www.lipidmaps.org](https://www.lipidmaps.org)) 
- PubMed (Il existe déjà des serveurs MCP [BioMedMCP](https://github.com/gosset-ai/mcps), [SimplePubMedMCP](https://github.com/andybrandt/mcp-simple-pubmed), [PubMedMCP](https://github.com/grll/pubmedmcp))



# Autre
On peut écrire à Francis pour des questions. Dès que ces trois serveurs sont implémenté, on lui montre et lui envoie pour qu'il puisse les utiliser.