"""Ingest docs into the vector store."""
from pathlib import Path

from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from .config import get_settings
from .vector_store import get_vectorstore


def _splitter() -> RecursiveCharacterTextSplitter:
    s = get_settings()
    return RecursiveCharacterTextSplitter(
        chunk_size=s.chunk_size,
        chunk_overlap=s.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )


def chunk_text(text: str, source: str) -> list[Document]:
    return _splitter().create_documents([text], metadatas=[{"source": source}])


def add_text(text: str, source: str) -> int:
    if not text.strip():
        return 0
    docs = chunk_text(text, source)
    if not docs:
        return 0
    get_vectorstore().add_documents(docs)
    return len(docs)


def add_documents(docs: list[Document]) -> int:
    if not docs:
        return 0
    get_vectorstore().add_documents(docs)
    return len(docs)


def load_file(path: str) -> list[Document]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)

    suffix = p.suffix.lower()
    if suffix in {".txt", ".md"}:
        text = p.read_text(encoding="utf-8", errors="ignore")
    elif suffix == ".pdf":
        from PyPDF2 import PdfReader
        text = "\n".join(page.extract_text() or "" for page in PdfReader(str(p)).pages)
    elif suffix == ".docx":
        import docx
        text = "\n".join(par.text for par in docx.Document(str(p)).paragraphs)
    else:
        # try as plain text, will probably be garbage
        text = p.read_text(encoding="utf-8", errors="ignore")

    return chunk_text(text, source=p.name)
