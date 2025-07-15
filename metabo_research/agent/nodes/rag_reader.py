"""
Node that will convert a list of papers into chunks and search using the query. It will return the relevant chunks
and their reference using LangChain Document objects
"""
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils import HugginFaceEmbedding
from typing import TypedDict, List

class QueryState(TypedDict):
    """State that will be passed between nodes"""
    query: str
    papers: List[tuple[str, str, str]]
    retrieved: List[tuple[str, str]] # List of tuples (title, retrieved text)

papers = [
    ("Inhibitory effects of ginseng total saponin on nicotine-induced hyperactivity, reverse tolerance and dopamine receptor supersensitivity.",
     "A single administration of a low dose of nicotine produced hyperactivity in mice. A repeated administration of nicotine developed reverse tolerance to the ambulation-accelerating activity of nicotine and also developed postsynaptic dopamine (DA) receptor supersensitivity. The development of reverse tolerance was evidenced by an increased ambulatory response to nicotine, and the development of postsynaptic DA receptor supersensitivity was evidenced by the enhanced response in ambulatory activity to apomorphine, a DA receptor agonist. Administration of ginseng total saponin (GTS) prior to and during the nicotine treatment in mice inhibited not only nicotine-induced hyperactivity and reverse tolerance, but also postsynaptic DA receptor supersensitivity in nicotine-induced reverse tolerant mice. These results suggest that inhibition by GTS of nicotine-induced hyperactivity and reverse tolerance may be closely related with the inhibition of the dopaminergic activation induced by nicotine and that the development of nicotine-induced reverse tolerance may be associated with enhanced DA receptor sensitivity."),
    ("Regional and cellular induction of nicotine-metabolizing CYP2B1 in rat brain by chronic nicotine treatment.",
     "In the rat, nicotine is metabolized to cotinine primarily by hepatic cytochrome P450 (CYP) 2B1. This enzyme is also found in other organs such as the lung and the brain. Hepatic nicotine metabolism is unaltered after nicotine exposure; however, nicotine may regulate CYP2B1 in other tissues. We hypothesized that nicotine induces its own metabolism in brain by increasing CYP2B1. Male rats were treated with nicotine (0.0, 0.1, 0.3, or 1.0 mg base/kg in saline) s.c. daily for 7 days. CYP2B1 mRNA and protein were assayed in the brain and liver by reverse transcriptase-polymerase chain reaction (RT-PCR), immunoblotting, and immunocytochemistry. In control rats, CYP2B1 mRNA and protein expression were brain region- and cell-specific. CYP2B1 was not induced in the liver, but CYP2B1 mRNA and protein showed dose-dependent, region- and cell-specific patterns of induction across brain regions. At 1.0 mg nicotine/kg, the largest increase in protein was in the brain stem (5.8-fold, P < 0.05) with a corresponding increase in CYP2B1 mRNA (7.6-fold, P < 0.05). Induction of CYP2B1 was also observed in the frontal cortex, striatum, and olfactory tubercle. Immunocytochemistry showed that induction was restricted principally to neurons. These data indicate that nicotine may alter its own metabolism in the brain through transcriptional regulation, perhaps contributing to central tolerance to the effects of nicotine. CYP2B1 and its human homologue CYP2B6 also activate tobacco smoke procarcinogens such as NNK [4-(methylnitrosamino)-1-(3-pyridyl)-1-butanone]. Highly localized increases in CYP2B could result in increased mutagenesis. These data suggest roles for nicotine-induced CYP2B in central metabolic tolerance, nicotine-induced neurotoxicity, neuroplasticity, and carcinogenesis.")
]

def create_document_from_paper(paper: tuple[str, str, str], paper_id: int) -> Document:
    """
    Create a LangChain Document from a paper tuple.
    :param paper: A tuple containing the title and abstract of the paper
    :param paper_id: Unique identifier for the paper
    :return: Document object with formatted content and metadata
    """
    title, abstract, text = paper
    if text != "Full text not available":
        content = f"# {title}\n\n### Abstract\n\n{abstract}\n\n{text}"
    else:
        content = f"# {title}\n\n{abstract}"

    return Document(
        page_content=content,
        metadata={
            "title": title,
            "paper_id": paper_id,
            "type": "research_paper",
            "abstract": abstract[:200] + "..." if len(abstract) > 200 else abstract  # Truncated for metadata
        }
    )

def retrieval_node(state: QueryState) -> dict[str, list[tuple[str, str]]]:
    """
    Node that takes a single query and a list of papers, evaluates each paper for relevance in parallel,
    """
    query = state["query"]
    papers = state["papers"]


    # Create Document objects from papers
    documents = [create_document_from_paper(paper, i) for i, paper in enumerate(papers)]

    # Split documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        separators=[".", "!", "?", "\n", "\n\n"],
        chunk_size=500,
        chunk_overlap=0,
        keep_separator=False
    )

    # Split documents - this preserves metadata in each chunk
    docs_list = []
    for doc in documents:
        chunks = text_splitter.split_documents([doc])
        docs_list.extend(chunks)

    # Create vector store from Document objects
    vectorstore = InMemoryVectorStore.from_documents(documents=docs_list, embedding=HugginFaceEmbedding())
    retriever = vectorstore.as_retriever()

    # Get relevant documents based on the query
    raw_results = retriever.invoke(query)
    output = [(doc.metadata["title"], doc.page_content) for doc in raw_results]

    return {"retrieved": output}