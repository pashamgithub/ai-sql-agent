import os
import chromadb
from pathlib import Path
from collections import Counter
from app.core.logger import logger

BASE_DIR = Path(__file__).resolve().parent
DB_PATH  = os.path.join(BASE_DIR, "vector_db")
DOC_PATH = os.path.abspath(
    os.path.join(BASE_DIR, "..", "..", "data", "db_schema_info.txt")
)

client = chromadb.PersistentClient(path=DB_PATH)

# Always start fresh
try:
    client.delete_collection("schema_docs")
except:
    pass

collection = client.get_or_create_collection(name="schema_docs")

with open(DOC_PATH, encoding="utf-8") as f:
    content = f.read()

chunks = content.split("---")

chunk_id        = 0
doc_count       = 0
current_section = "general"  # tracks which section we're in

for chunk in chunks:
    clean = chunk.strip()

    if len(clean) < 50:
        continue

    # Update current section when a section header is found
    clean_upper = clean.upper()
    if "TABLE DEFINITIONS" in clean_upper:
        current_section = "table"
    elif "JOIN PATTERNS" in clean_upper:
        current_section = "join"
    elif "CRITICAL GOTCHAS" in clean_upper or "GOTCHAS" in clean_upper:
        current_section = "gotcha"
    elif "QUERY PATTERNS" in clean_upper:
        current_section = "pattern"
    elif "BUSINESS METRICS" in clean_upper:
        current_section = "metric"
    elif "COMPLETE QUERY TEMPLATES" in clean_upper:
        current_section = "pattern"

    # Content-based detection takes priority over section
    if "Table:" in clean:
        doc_type = "table"
    elif "Pattern:" in clean or "Complete Query:" in clean:
        doc_type = "pattern"
    else:
        doc_type = current_section  # inherit section type

    logger.info(f"[{doc_type}] {clean[:80].replace(chr(10), ' ')}")

    collection.add(
        documents=[clean],
        ids=[str(chunk_id)],
        metadatas=[{"doc_type": doc_type, "chunk_id": chunk_id}]
    )

    chunk_id  += 1
    doc_count += 1

logger.info(f"\nVector DB created successfully")
logger.info(f"Total chunks indexed: {doc_count}")
logger.info(f"Breakdown:")

all_meta = collection.get(include=["metadatas"])["metadatas"]
counts   = Counter(m["doc_type"] for m in all_meta)
for dtype, count in sorted(counts.items()):
    logger.info(f"  {dtype:10} : {count} chunks")