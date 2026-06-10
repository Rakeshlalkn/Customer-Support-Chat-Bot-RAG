"""Seeds the store from ./data on boot if it's empty. Run as a module."""
import os
from pathlib import Path

from .ingest import add_documents, load_file
from .vector_store import collection_count


def main() -> None:
    if collection_count() > 0:
        print(f"[seed] store already has {collection_count()} chunks, skipping")
        return

    data_dir = Path(os.getenv("DATA_DIR", "./data"))
    if not data_dir.exists():
        print(f"[seed] no data dir at {data_dir}, nothing to do")
        return

    total = 0
    for p in sorted(data_dir.glob("**/*")):
        if p.is_dir() or p.suffix.lower() not in {".txt", ".md"}:
            continue
        try:
            n = add_documents(load_file(str(p)))
            print(f"[seed] {p.name}: +{n} chunks")
            total += n
        except Exception as e:
            print(f"[seed] skipping {p}: {e}")

    print(f"[seed] done. added {total} chunks, total now {collection_count()}")


if __name__ == "__main__":
    main()
