import sys
from typing import Annotated, List, Tuple
from typing_extensions import TypedDict
import os
from pathlib import Path
from pyutils import progress

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pubmed import PubMedClient
from pubchem import get_pubmed_ids
from nodes import parallel_evaluation_node

load_dotenv(Path(__file__).parent.parent / ".env")

class State(TypedDict):
    pubchem_id: str # (CID)
    query: str
    pmids: List[str]
    papers: List[Tuple[str, str]]
    is_relevant: List[bool]

def GetPubMedIdsNode(state: State) -> State:
    """
    Node that retrieves PubMed IDs for a given PubChem ID.
    """
    pubchem_id = state["pubchem_id"]

    # Fetch PubMed IDs from PubChem
    pmids = get_pubmed_ids(pubchem_id)

    if not pmids:
        raise ValueError(f"No PubMed IDs found for PubChem ID {pubchem_id}")

    # Update state with the query and PubMed IDs
    state["pmids"] = pmids
    return state

def GetPapersNode(state: State) -> State:
    """
    Node that retrieves paper titles and abstracts for the given PubMed IDs.
    """
    pmids = state["pmids"]

    # Fetch papers from PubMed
    client = PubMedClient()
    papers = [client.get_title_and_abstract(pmid) for pmid in progress(pmids)]

    # Update state with the query and papers
    state["papers"] = papers
    return state

workflow_builder = StateGraph(State)

workflow_builder.add_node("GetPubMedIds", GetPubMedIdsNode)
workflow_builder.set_entry_point("GetPubMedIds")
workflow_builder.add_node("GetPapers", GetPapersNode)
workflow_builder.add_node("EvaluatePapers", parallel_evaluation_node)

workflow_builder.add_edge("GetPubMedIds", "GetPapers")
workflow_builder.add_edge("GetPapers", "EvaluatePapers")
workflow_builder.add_edge("EvaluatePapers", END)

workflow = workflow_builder.compile()

def stream_graph_updates(initial_state: State):
    for event in workflow.stream(initial_state):
        for value in event.values():
            print(value["is_relevant"])

if __name__ == "__main__":
    cid="5570"
    query = "Find papers that support the hypothesis that Trigonelline causes cancer"

    initial_state: State = {
        "pubchem_id": cid,
        "query": query,
        "pmids": [],
        "papers": [],
        "is_relevant": []
    }
    stream_graph_updates(initial_state)
