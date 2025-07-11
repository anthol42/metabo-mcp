import os
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from langchain.chat_models import init_chat_model
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
root = Path(__file__).parent.parent

class QueryState(TypedDict):
    """State that will be passed between nodes"""
    original_query: str
    reformulations: List[str]
    num_reformulations: int

def get_system_prompt() -> str:
    with open(root / "prompts" / "reformulator_sys.md", "r") as f:
        return f.read()

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")
llm = init_chat_model("anthropic:claude-3-5-sonnet-latest", temperature=1.)


def reformulate_single_query(query: str) -> str:
    """Reformulate a single query with a specific style using system prompts"""
    system_prompt = get_system_prompt()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query}
    ]

    response = llm.invoke(messages)
    return response.content.strip()


def parallel_reformulation_node(state: QueryState) -> QueryState:
    """
    Node that reformulates the query N times in parallel and returns the reformulations as a list with the original query
    """
    original_query = state["original_query"]
    n = state["num_reformulations"]

    # Use ThreadPoolExecutor for parallel execution
    if n > 0:
        with ThreadPoolExecutor(max_workers=min(n, 4)) as executor:
            # Submit all reformulation tasks
            futures = [
                executor.submit(reformulate_single_query, original_query)
                for _ in range(n)
            ]

            # Collect results
            reformulations = []
            for future in futures:
                try:
                    result = future.result(timeout=30)  # 30 second timeout
                    reformulations.append(result)
                except Exception as e:
                    print(f"Error in reformulation: {e}")
    else:
        reformulations = []

    # Update state with reformulations
    state["reformulations"] = [original_query] + reformulations
    return state


def create_reformulation_graph():
    """Create and return the LangGraph workflow"""

    # Initialize the graph
    workflow = StateGraph(QueryState)

    # Add nodes
    workflow.add_node("reformulate", parallel_reformulation_node)

    # Define the flow
    workflow.set_entry_point("reformulate")
    workflow.add_edge("reformulate", END)

    # Compile the graph
    return workflow.compile()

reformulator = create_reformulation_graph()



def stream_graph_updates(initial_state: QueryState):
    for event in reformulator.stream(initial_state):
        for value in event.values():
            for reform in value["reformulations"]:
                print(reform)
                print("="*100)

if __name__ == "__main__":
    # Example usage
    initial_query = "What is the link between high cortisol levels and alzaeimer's disease?"
    num_reformulations = 5

    # Create initial state
    initial_state: QueryState = {
        "original_query": initial_query,
        "reformulations": [],
        "num_reformulations": num_reformulations
    }

    stream_graph_updates(initial_state)