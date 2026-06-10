"""FastAPI app. Routes for chat, ingest, kb admin."""
import glob
import os
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .ingest import add_documents, add_text, load_file
from .models import (ChatRequest, ChatResponse, IngestRequest, IngestResponse,
                     StatsResponse)
from .rag import answer_question
from .vector_store import collection_count, get_vectorstore, reset_vectorstore

settings = get_settings()

app = FastAPI(title=settings.app_name, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name, "provider": settings.llm_provider}


@app.get("/stats", response_model=StatsResponse)
def stats():
    return StatsResponse(
        total_chunks=collection_count(),
        collection=settings.collection_name,
        provider=settings.llm_provider,
        embedding_model=settings.embedding_model,
    )


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.question.strip():
        raise HTTPException(400, "empty question")
    if collection_count() == 0:
        raise HTTPException(409, "knowledge base is empty. POST /admin/seed or /ingest first")
    r = answer_question(req.question, top_k=req.top_k)
    return ChatResponse(answer=r.answer, sources=r.sources,
                         provider=r.provider, session_id=req.session_id)


@app.post("/ingest/text", response_model=IngestResponse)
def ingest_text(req: IngestRequest):
    if not req.text:
        raise HTTPException(400, "text is required")
    n = add_text(req.text, req.source_name)
    return IngestResponse(added_chunks=n, source=req.source_name,
                          total_documents=collection_count())


@app.post("/ingest/file", response_model=IngestResponse)
async def ingest_file(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".txt", ".md", ".pdf", ".docx"}:
        raise HTTPException(400, f"unsupported file type: {suffix}")

    tmp = Path("/tmp") / file.filename
    with open(tmp, "wb") as f:
        f.write(await file.read())
    try:
        n = add_documents(load_file(str(tmp)))
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass
    return IngestResponse(added_chunks=n, source=file.filename or "upload",
                          total_documents=collection_count())


@app.post("/admin/seed")
def admin_seed():
    """Loads every .md/.txt under DATA_DIR into the store."""
    data_dir = Path(os.getenv("DATA_DIR", "./data"))
    if not data_dir.exists():
        raise HTTPException(404, f"no data dir at {data_dir}")

    total = 0
    last = "seed"
    for path in glob.glob(str(data_dir / "**/*"), recursive=True):
        p = Path(path)
        if p.is_dir() or p.suffix.lower() not in {".txt", ".md"}:
            continue
        try:
            total += add_documents(load_file(str(p)))
            last = p.name
        except Exception as e:
            print(f"[seed] skipping {p}: {e}")
    return IngestResponse(added_chunks=total, source=f"seed:{last}",
                          total_documents=collection_count())


@app.post("/admin/reset")
def admin_reset():
    reset_vectorstore()
    return {"status": "reset", "total_chunks": collection_count()}


# TODO: add proper structured logging. print() is fine for now but it bugs me.
@app.exception_handler(Exception)
def unhandled(_, exc):
    return JSONResponse(status_code=500, content={"detail": f"internal error: {exc}"})
