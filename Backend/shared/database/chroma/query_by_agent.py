import chromadb
import logging
from sentence_transformers import SentenceTransformer
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser
from pathlib import Path
from typing import Optional
import os

# -------------------------------------------------
# LOGGING
# -------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------------------------------
# 🔒 SINGLE SOURCE OF TRUTH (ABSOLUTE PATH)
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[3]  # Backend/
CHROMA_DATA_PATH = BASE_DIR / "shared" / "database" / "chroma" / "chroma_data"
BM25_INDEX_PATH = BASE_DIR / "shared" / "database" / "chroma" / "bm25_index"

logger.info(f"Using ChromaDB path: {CHROMA_DATA_PATH}")

# -------------------------------------------------
# INIT MODELS
# -------------------------------------------------
model = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path=str(CHROMA_DATA_PATH))

# 🔒 SAFE COLLECTION LOAD (NO CRASH)
try:
    collection = client.get_collection("medical_docs")
except Exception:
    logger.warning("Collection 'medical_docs' not found. Creating empty collection.")
    collection = client.get_or_create_collection("medical_docs")

logger.info(f"Chroma collection size: {collection.count()}")

# -------------------------------------------------
# BM25 SCHEMA
# -------------------------------------------------
schema = Schema(
    id=ID(stored=True),
    text=TEXT(stored=True),
    specialty=ID(stored=True)
)

# -------------------------------------------------
# BUILD BM25 INDEX
# -------------------------------------------------
def build_bm25_index():
    BM25_INDEX_PATH.mkdir(exist_ok=True)

    if not os.listdir(BM25_INDEX_PATH):
        ix = create_in(BM25_INDEX_PATH, schema)
    else:
        ix = open_dir(BM25_INDEX_PATH)

    writer = ix.writer()

    docs = collection.get(include=["documents", "metadatas"])

    for doc_id, text, meta in zip(
        docs["ids"], docs["documents"], docs["metadatas"]
    ):
        if meta.get("type") == "content":
            writer.add_document(
                id=doc_id,
                text=text,
                specialty=meta.get("specialty", "general")
            )

    writer.commit()
    return ix

# -------------------------------------------------
# SEMANTIC SEARCH
# -------------------------------------------------
def query_agent(query_text, agent_specialty=None, n_results=5):
    embedding = model.encode(query_text).tolist()

    where = {"specialty": agent_specialty} if agent_specialty else None

    return collection.query(
        query_embeddings=[embedding],
        n_results=n_results,
        where=where,
        include=["documents", "metadatas", "distances"]
    )

# -------------------------------------------------
# 🔥 HYBRID SEARCH (SEMANTIC + BM25)
# -------------------------------------------------
def query_medical_documents(
    query_text: str,
    agent_specialty: Optional[str] = None,
    n_results: int = 5,
    alpha: float = 0.7
):
    semantic = query_agent(query_text, agent_specialty, n_results * 2)

    semantic_scores = {}
    semantic_meta = {}

    for doc, meta, dist in zip(
        semantic["documents"][0],
        semantic["metadatas"][0],
        semantic["distances"][0]
    ):
        semantic_scores[doc] = 1 - dist
        semantic_meta[doc] = meta

    ix = build_bm25_index()
    bm25_scores = {}

    with ix.searcher() as searcher:
        parser = QueryParser("text", ix.schema)
        q = parser.parse(query_text)
        results = searcher.search(q, limit=n_results * 2)

        for hit in results:
            if agent_specialty and hit["specialty"] != agent_specialty:
                continue
            bm25_scores[hit["text"]] = hit.score

    combined = {}

    for doc, s in semantic_scores.items():
        combined[doc] = alpha * s

    for doc, k in bm25_scores.items():
        combined[doc] = combined.get(doc, 0) + (1 - alpha) * k

    ranked = sorted(combined.items(), key=lambda x: x[1], reverse=True)[:n_results]

    response = []
    for doc, score in ranked:
        meta = semantic_meta.get(doc, {})
        response.append({
            "score": round(score * 100, 2),
            "agent": meta.get("specialty", "general"),
            "type": meta.get("type"),
            "source_file": meta.get("source_file"),
            "text": doc[:300] + "..." if len(doc) > 300 else doc
        })

    return {
        "query": query_text,
        "agent": agent_specialty or "all",
        "count": len(response),
        "results": response
    }
