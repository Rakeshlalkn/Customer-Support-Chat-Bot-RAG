"""Chroma wrapper. Embedded client (no separate server) + local embeddings."""
import os
from functools import lru_cache

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

from .config import get_settings


@lru_cache
def _embeddings() -> HuggingFaceEmbeddings:
    # small model, runs fine on cpu. swap to a bigger one if you need better recall
    s = get_settings()
    return HuggingFaceEmbeddings(
        model_name=s.embedding_model,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


@lru_cache
def get_vectorstore() -> Chroma:
    s = get_settings()
    os.makedirs(s.chroma_persist_dir, exist_ok=True)

    client = chromadb.PersistentClient(
        path=s.chroma_persist_dir,
        settings=ChromaSettings(anonymized_telemetry=False, allow_reset=True),
    )
    return Chroma(
        client=client,
        collection_name=s.collection_name,
        embedding_function=_embeddings(),
        persist_directory=s.chroma_persist_dir,
    )


def reset_vectorstore() -> None:
    s = get_settings()
    client = chromadb.PersistentClient(
        path=s.chroma_persist_dir,
        settings=ChromaSettings(anonymized_telemetry=False, allow_reset=True),
    )
    try:
        client.delete_collection(s.collection_name)
    except Exception:
        # collection didn't exist, whatever
        pass
    get_vectorstore.cache_clear()
    _embeddings.cache_clear()


def collection_count() -> int:
    try:
        return get_vectorstore()._collection.count()
    except Exception:
        return 0
