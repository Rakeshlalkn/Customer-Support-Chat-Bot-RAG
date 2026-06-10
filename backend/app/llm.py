"""LLM providers. OpenAI, Gemini, or a no-key demo fallback."""
import os
from typing import Protocol

from .config import get_settings


# keep the prompt short and direct. rules > long explanations
SYSTEM_PROMPT = """You are a customer support assistant. Answer using ONLY the context below.
If the answer isn't in the context, say you don't know and suggest contacting a human.
Be concise (2-4 sentences). Cite the source filename in parentheses, e.g. (refund-policy.md).
Don't make up details that aren't in the context."""


class LLM(Protocol):
    def generate(self, question: str, chunks: list[str], sources: list[str]) -> str: ...


class OpenAILLM:
    def __init__(self, api_key: str, model: str) -> None:
        from langchain_openai import ChatOpenAI
        self._llm = ChatOpenAI(api_key=api_key, model=model, temperature=0.2)

    def generate(self, question, chunks, sources):
        from langchain.schema import SystemMessage, HumanMessage
        ctx = "\n\n---\n\n".join(f"[{s}]\n{c}" for s, c in zip(sources, chunks))
        msg = self._llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Context:\n{ctx}\n\nQ: {question}\nA:"),
        ])
        return msg.content if hasattr(msg, "content") else str(msg)


class GeminiLLM:
    def __init__(self, api_key: str, model: str) -> None:
        from langchain_google_genai import ChatGoogleGenerativeAI
        self._llm = ChatGoogleGenerativeAI(google_api_key=api_key, model=model, temperature=0.2)

    def generate(self, question, chunks, sources):
        from langchain.schema import SystemMessage, HumanMessage
        ctx = "\n\n---\n\n".join(f"[{s}]\n{c}" for s, c in zip(sources, chunks))
        msg = self._llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Context:\n{ctx}\n\nQ: {question}\nA:"),
        ])
        return msg.content if hasattr(msg, "content") else str(msg)


class DemoLLM:
    """No-key fallback. Picks the best-matching chunk and shows it as the answer."""

    def generate(self, question, chunks, sources):
        if not chunks:
            return "I don't have anything in the knowledge base that matches that. Try uploading a relevant doc or rephrasing."

        # cheap keyword overlap scoring - good enough for the demo path
        q_tokens = {t.lower() for t in question.split() if len(t) > 2}
        scored = []
        for c, s in zip(chunks, sources):
            c_tokens = {t.lower() for t in c.split() if len(t) > 2}
            scored.append((len(q_tokens & c_tokens), c, s))
        scored.sort(key=lambda x: x[0], reverse=True)
        score, chunk, src = scored[0]

        excerpt = chunk.strip().replace("\n", " ")
        if len(excerpt) > 500:
            excerpt = excerpt[:500].rsplit(" ", 1)[0] + "..."

        if score == 0:
            return f"Closest match I could find ({src}): \"{excerpt}\" — not sure this answers your question though, mind rephrasing?"
        return f"{excerpt} ({src})"


def get_llm() -> LLM:
    s = get_settings()
    if s.llm_provider == "openai" and s.openai_api_key:
        return OpenAILLM(s.openai_api_key, s.openai_model)
    if s.llm_provider == "gemini" and s.google_api_key:
        return GeminiLLM(s.google_api_key, s.gemini_model)
    return DemoLLM()
