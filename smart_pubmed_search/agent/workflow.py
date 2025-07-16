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
from nodes import parallel_evaluation_node, parallel_extraction_node, retrieval_node

load_dotenv(Path(__file__).parent.parent / ".env")

class State(TypedDict):
    pubchem_id: str # (CID)
    query: str
    # Parameters
    retrieval: bool

    pmids: List[str]
    papers: List[Tuple[str, str, str, str]] # PMID, title, abstract, full_text

    # For the evaluation node
    is_relevant: List[bool]

    # For the extractor node
    extracted: List[tuple[str, str, str]]

    retrieved: List[tuple[str, str, str]]


def GetPubMedIdsNode(state: State) -> dict:
    """
    Node that retrieves PubMed IDs for a given PubChem ID.
    """
    pubchem_id = state["pubchem_id"]

    # Fetch PubMed IDs from PubChem
    pmids = get_pubmed_ids(pubchem_id)

    if not pmids:
        raise ValueError(f"No PubMed IDs found for PubChem ID {pubchem_id}")

    return {"pmids": pmids}

def GetPapersNode(state: State) -> dict:
    """
    Node that retrieves paper titles and abstracts for the given PubMed IDs.
    """
    pmids = state["pmids"]

    # Fetch papers from PubMed
    client = PubMedClient()
    papers = [(str(pmid),) + tuple(elem for elem in client.get_title_and_abstract(pmid)) for pmid in progress(pmids, desc="Retrieving paper titles and abstracts")]
    full_texts = [client.get_full_text(paper[0]) for paper in progress(papers, desc="Fetching full texts")]

    # Update state with the query and papers
    return {"papers": [
        (pmid, title, abstract, full_text)
        for (pmid, title, abstract), full_text in zip(papers, full_texts)
    ]}

def conditional_branch(state: State) -> str:
    """
    Based on the retrieval parameter, decide whether to continue with the evaluation and extraction nodes or the
    retrieval node
    """
    if state["retrieval"]:
        return "Retrieval"
    else:
        return "EvaluatePapers"

workflow_builder = StateGraph(State)

workflow_builder.add_node("GetPubMedIds", GetPubMedIdsNode)
workflow_builder.set_entry_point("GetPubMedIds")
workflow_builder.add_node("GetPapers", GetPapersNode)
workflow_builder.add_node("EvaluatePapers", parallel_evaluation_node)
workflow_builder.add_node("Extract", parallel_extraction_node)
workflow_builder.add_node("Retrieval", retrieval_node)

workflow_builder.add_edge("GetPubMedIds", "GetPapers")
workflow_builder.add_conditional_edges("GetPapers", conditional_branch, {"Retrieval": "Retrieval", "EvaluatePapers": "EvaluatePapers"})
workflow_builder.add_edge("EvaluatePapers", "Extract")
workflow_builder.add_edge("Extract", END)
workflow_builder.add_edge("Retrieval", END)
workflow = workflow_builder.compile()

def stream_graph_updates(initial_state: State):
    for event in workflow.stream(initial_state):
        print("Event: ", event)
        print("Values", event.values())
        if "extracted" in event.values():
            for extracted in event["extracted"]:
                print(extracted)
                print("=" * 100)

if __name__ == "__main__":
    cid="5570"
    query = "Find papers that support the hypothesis that Trigonelline prevents cancer"

    initial_state: State = {
        "pubchem_id": cid,
        "query": query,
        "pmids": [],
        "papers": [],
        "is_relevant": [],
        "relevant_papers_text": [],
        "extracted": []
    }
    stream_graph_updates(initial_state)
