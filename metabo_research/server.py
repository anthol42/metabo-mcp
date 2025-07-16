from mcp.server.fastmcp import FastMCP
from agent.workflow import workflow, State
from agent.utils.functional import is_claude_key_valid

async def smart_search(cid: str, query: str, retrieval: bool = True) -> str:
    """
    Search in all the papers related to the compound with the given CID. It returns all the relevant
    information found in each paper related to the query.

    Please, always use retrieval=True, unless really necessary. Using retrieval to True means that the content of all
    papers are converted to embeddings and the results are retrieved using a vector database. Like a RAG. If retrieval
    is False, it will use a research agent that will read each paper, then extract the relevant information. This is
    much more costly, so use it only if you really need to. The retrieval method is much faster and cheaper, and still
    really good!

    The query must be a question of a metabolite related to a health condition. For example: "Does nicotine increase
    the risk of lung cancer?".

    :param cid: The pubchem ID of the compound to search for.
    :param query: The query to search for in the papers related to the compound and a health condition.
    :param retrieval: Whether or not to use RAG search. IMPORTANT: Always use retrieval=True, unless you really need to use the research agent.
    :return: The important information found in the papers related to the query.
    """
    if not is_claude_key_valid():
        # If not access to Claude, force the retrieval method
        retrieval = True

    inital_state: State = dict(
        pubchem_id=cid,
        query=query,
        retrieval=retrieval,
        pmids=[],
        papers=[],
        is_relevant=[],
        extracted=[],
        retrieved=[]
    )

    final_state = workflow.invoke(inital_state)

    if retrieval:
        retrieved = final_state["retrieved"]


if __name__ == "__main__":
    print(is_claude_key_valid())