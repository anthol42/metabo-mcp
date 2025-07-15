import os
from typing import TypedDict, List, Literal
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from langchain.chat_models import init_chat_model
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from pydantic import BaseModel, Field
root = Path(__file__).parent.parent

class ExtractorState(TypedDict):
    """State that will be passed between nodes"""
    query: str
    papers: List[tuple[str, str, str]]
    extracted: List[str]
    is_relevant: List[bool]

def get_system_prompt() -> str:
    with open(root / "prompts" / "extractor_sys.md", "r") as f:
        return f.read()

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")
llm = init_chat_model("anthropic:claude-3-7-sonnet-latest", temperature=0.)

def extract_single_paper(query: str, paper: str) -> str:
    """Extract information from a single paper using system prompts"""
    system_prompt = get_system_prompt()

    formatted_prompt = (f"Extract the relevant information from the following paper for the query: "
                        f"'{query}'\n\n{paper}\n\n")
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": formatted_prompt}
    ]

    response = llm.invoke(messages)
    return response.content.strip()

def format_paper(paper: tuple[str, str, str]) -> str:
    """Format the paper for extraction"""
    title, abstract, fulltext = paper
    if fulltext == "Full text not available":
        return f"# {title}\n\n### Abstract\n\n{abstract}"
    else:
        return f"# {title}\n\n### Abstract\n\n{abstract}\n\n{fulltext}"

def parallel_extraction_node(state: ExtractorState) -> dict[str, list[str]]:
    query = state["query"]
    papers = [paper for paper, is_relevant in zip(state["papers"], state["is_relevant"]) if is_relevant]

    # Use ThreadPoolExecutor for parallel execution
    if len(papers) > 0:
        with ThreadPoolExecutor(max_workers=min(len(papers), 4)) as executor:
            # Submit all reformulation tasks
            futures = [
                executor.submit(extract_single_paper, query, format_paper(paper))
                for paper in papers
            ]

            # Collect results
            extracted = []
            for future in futures:
                try:
                    result = future.result(timeout=30)  # 30 second timeout
                    extracted.append(result)
                except Exception as e:
                    print(f"Error in reformulation: {e}")
    else:
        extracted = []

    return {"extracted": extracted}

def build_extractor_graph():
    """
    Build the state graph for the extractor node.
    """
    extractor_builder = StateGraph(ExtractorState)

    extractor_builder.add_node("ParallelExtraction", parallel_extraction_node)
    extractor_builder.set_entry_point("ParallelExtraction")
    extractor_builder.add_edge("ParallelExtraction", END)

    return extractor_builder.compile()

extractor = build_extractor_graph()
