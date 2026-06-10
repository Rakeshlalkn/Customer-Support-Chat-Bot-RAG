"""RAG pipeline: retrieve, then generate."""
from dataclasses import dataclass

from .config import get_settings
from .llm import get_llm
from .vector_store import get_vectorstore
from .models import SourceChunk


@dataclass
class RAGAnswer:
    answer: str
    sources: list[SourceChunk]
    provider: str


def answer_question(question: str, top_k: int | None = None) -> RAGAnswer:
    s = get_settings()
    k = top_k or s.retrieval_k

    vs = get_vectorstore()
    try:
        results = vs.similarity_search_with_relevance_scores(question, k=k)
    except TypeError:
        # older chroma returns distances not relevance scores
        results = [(d, None) for d in vs.similarity_search(question, k=k)]

    chunks = [d.page_content for d, _ in results]
    sources = [d.metadata.get("source", "unknown") for d, _ in results]
    scores = [sc for _, sc in results]

    text = get_llm().generate(question, chunks, sources)

    return RAGAnswer(
        answer=text,
        sources=[SourceChunk(content=c, source=src, score=sc)
                 for c, src, sc in zip(chunks, sources, scores)],
        provider=s.llm_provider,
    )
