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

class QueryState(TypedDict):
    """State that will be passed between nodes"""
    query: str
    papers: List[tuple[str, str]]
    is_relevant: List[bool]

class ResponseFormat(BaseModel):
    relevant: Literal['yes', 'no'] = Field(description="Wether the paper is relevant to the query or not. Answer with 'yes' or 'no'.")

def get_system_prompt() -> str:
    with open(root / "prompts" / "evaluator_sys.md", "r") as f:
        return f.read()

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")
llm = (init_chat_model("anthropic:claude-3-7-sonnet-latest", temperature=0.)
       .with_structured_output(schema=ResponseFormat.model_json_schema()))

def evaluate_single_paper(query: str, paper: str) -> bool:
    """Evaluate a single paper for relevance using system prompts"""
    system_prompt = get_system_prompt()

    formatted_prompt = f"Is the following paper relevant to the query: '{query}'\n\n{paper}\n\nPlease answer with 'yes' or 'no'."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": formatted_prompt}
    ]

    response = llm.invoke(messages)
    response = ResponseFormat.model_validate(response)
    return response.relevant == 'yes'

def format_paper(paper: tuple[str, str]) -> str:
    """Format the paper for evaluation"""
    title, abstract = paper
    return f"# {title}\n\n{abstract}"

def parallel_evaluation_node(state: QueryState) -> dict[str, str]:
    """
    Node that takes a single query and a list of papers, evaluates each paper for relevance in parallel,
    """
    query = state["query"]
    papers = state["papers"]

    # Use ThreadPoolExecutor for parallel execution
    if len(papers) > 0:
        with ThreadPoolExecutor(max_workers=min(len(papers), 4)) as executor:
            # Submit all reformulation tasks
            futures = [
                executor.submit(evaluate_single_paper, query, format_paper(paper))
                for paper in papers
            ]

            # Collect results
            evaluations = []
            for future in futures:
                try:
                    result = future.result(timeout=30)  # 30 second timeout
                    evaluations.append(result)
                except Exception as e:
                    print(f"Error in reformulation: {e}")
    else:
        evaluations = []

    return {"is_relevant": evaluations}

def create_evaluator_graph():
    """Create and return the LangGraph workflow"""

    # Initialize the graph
    workflow = StateGraph(QueryState)

    # Add nodes
    workflow.add_node("evaluate", parallel_evaluation_node)

    # Define the flow
    workflow.set_entry_point("evaluate")
    workflow.add_edge("evaluate", END)

    # Compile the graph
    return workflow.compile()

evaluator = create_evaluator_graph()

def stream_graph_updates(initial_state: QueryState):
    for event in evaluator.stream(initial_state):
        for value in event.values():
            print(value["is_relevant"])

if __name__ == "__main__":
    # Example usage
    initial_query = "Is there a link between nicotine and hyperactivity"

    # Create initial state
    initial_state: QueryState = {
        "query": initial_query,
        "papers": [
            ("Inhibitory effects of ginseng total saponin on nicotine-induced hyperactivity, reverse tolerance and dopamine receptor supersensitivity.",
             "A single administration of a low dose of nicotine produced hyperactivity in mice. A repeated administration of nicotine developed reverse tolerance to the ambulation-accelerating activity of nicotine and also developed postsynaptic dopamine (DA) receptor supersensitivity. The development of reverse tolerance was evidenced by an increased ambulatory response to nicotine, and the development of postsynaptic DA receptor supersensitivity was evidenced by the enhanced response in ambulatory activity to apomorphine, a DA receptor agonist. Administration of ginseng total saponin (GTS) prior to and during the nicotine treatment in mice inhibited not only nicotine-induced hyperactivity and reverse tolerance, but also postsynaptic DA receptor supersensitivity in nicotine-induced reverse tolerant mice. These results suggest that inhibition by GTS of nicotine-induced hyperactivity and reverse tolerance may be closely related with the inhibition of the dopaminergic activation induced by nicotine and that the development of nicotine-induced reverse tolerance may be associated with enhanced DA receptor sensitivity."),
            ("Regional and cellular induction of nicotine-metabolizing CYP2B1 in rat brain by chronic nicotine treatment.",
             "In the rat, nicotine is metabolized to cotinine primarily by hepatic cytochrome P450 (CYP) 2B1. This enzyme is also found in other organs such as the lung and the brain. Hepatic nicotine metabolism is unaltered after nicotine exposure; however, nicotine may regulate CYP2B1 in other tissues. We hypothesized that nicotine induces its own metabolism in brain by increasing CYP2B1. Male rats were treated with nicotine (0.0, 0.1, 0.3, or 1.0 mg base/kg in saline) s.c. daily for 7 days. CYP2B1 mRNA and protein were assayed in the brain and liver by reverse transcriptase-polymerase chain reaction (RT-PCR), immunoblotting, and immunocytochemistry. In control rats, CYP2B1 mRNA and protein expression were brain region- and cell-specific. CYP2B1 was not induced in the liver, but CYP2B1 mRNA and protein showed dose-dependent, region- and cell-specific patterns of induction across brain regions. At 1.0 mg nicotine/kg, the largest increase in protein was in the brain stem (5.8-fold, P < 0.05) with a corresponding increase in CYP2B1 mRNA (7.6-fold, P < 0.05). Induction of CYP2B1 was also observed in the frontal cortex, striatum, and olfactory tubercle. Immunocytochemistry showed that induction was restricted principally to neurons. These data indicate that nicotine may alter its own metabolism in the brain through transcriptional regulation, perhaps contributing to central tolerance to the effects of nicotine. CYP2B1 and its human homologue CYP2B6 also activate tobacco smoke procarcinogens such as NNK [4-(methylnitrosamino)-1-(3-pyridyl)-1-butanone]. Highly localized increases in CYP2B could result in increased mutagenesis. These data suggest roles for nicotine-induced CYP2B in central metabolic tolerance, nicotine-induced neurotoxicity, neuroplasticity, and carcinogenesis.")
        ],
        "is_relevant": [],
    }

    stream_graph_updates(initial_state)