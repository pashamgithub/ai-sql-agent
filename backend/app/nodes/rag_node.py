import os
import chromadb
from app.llm.llm_client import generate_sql
from app.core.logger import logger

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

VECTOR_DB_PATH = os.path.abspath(
    os.path.join(BASE_DIR, "..", "rag", "vector_db")
)
logger.info("VECTOR_DB_PATH",VECTOR_DB_PATH)

client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
collection = client.get_collection(name="schema_docs")


def rag_node(state):
    logger.info("\nRAG node started")
    question     = state["question"]
    intent       = state.get("intent", "")
    search_query = f"{question} {intent}".strip()

    # Retrieve by priority — patterns and joins first
    all_docs = []

    priority_config = [
        ("pattern", 2),
        ("join",    2),
        ("table",   3),
        ("gotcha",  1),
        ("metric",  1),
    ]

    for doc_type, n in priority_config:
        try:
            result = collection.query(
                query_texts=[search_query],
                n_results=n,
                where={"doc_type": doc_type}
            )
            docs = result["documents"][0]
            all_docs.extend(docs)
        except Exception:
            pass  # doc_type has fewer chunks than n_results — skip

    # Deduplicate while preserving order
    seen    = set()
    unique  = []
    for doc in all_docs:
        if doc not in seen:
            seen.add(doc)
            unique.append(doc)

    context = "\n\n".join(unique)
    logger.info(f"RAG retrieved {len(unique)} chunks")

    logger.info(f"=== RAG CHUNKS ===")
    for i, doc in enumerate(unique):
        preview = doc[:100].replace('\n', ' ')
        logger.info(f"  [{i}] {preview}")
    logger.info(f"=== END ===")

    completed = list(state.get("completed_steps") or [])
    completed.append("rag")

    return {
    "retrieved_context": context,
    "source_docs":       unique,
    "completed_steps":   completed,
    "error":             None,
    "result": {
        "status":    "rag",
        "rows":      [],
        "row_count": 0,
        "answer":    context[:500] if context else "Schema information retrieved.",
        "message":   None,
    }
}






