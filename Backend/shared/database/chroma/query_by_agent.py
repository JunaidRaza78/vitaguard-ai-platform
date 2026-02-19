import chromadb
import logging
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser
from pathlib import Path
import os

# -------------------------------------------------
# LOGGING
# -------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------------------------------
# SINGLE SOURCE OF TRUTH (ABSOLUTE PATH)
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[3]  # Backend/
CHROMA_DATA_PATH = BASE_DIR / "shared" / "database" / "chroma" / "chroma_data"
BM25_INDEX_PATH = BASE_DIR / "shared" / "database" / "chroma" / "bm25_index"

logger.info(f"Using ChromaDB path: {CHROMA_DATA_PATH}")

# -------------------------------------------------
# LAZY INIT (avoid module-level model download)
# -------------------------------------------------
_model = None
_client = None
_collection = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading SentenceTransformer model...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=str(CHROMA_DATA_PATH))
        try:
            _collection = _client.get_collection("medical_docs")
        except Exception:
            logger.warning("Collection 'medical_docs' not found. Creating empty collection.")
            _collection = _client.get_or_create_collection("medical_docs")
    return _collection


# -------------------------------------------------
# BM25 SCHEMA
# -------------------------------------------------
schema = Schema(
    id=ID(stored=True),
    text=TEXT(stored=True),
    specialty=ID(stored=True),
    user_id=ID(stored=True)  # NEW: Add user_id to BM25 index
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

    collection = _get_collection()
    docs = collection.get(include=["documents", "metadatas"])

    for doc_id, text, meta in zip(
        docs["ids"], docs["documents"], docs["metadatas"]
    ):
        if meta.get("type") == "content":
            writer.add_document(
                id=doc_id,
                text=text,
                specialty=meta.get("specialty", "general"),
                user_id=meta.get("user_id", "unknown")  # NEW: Include user_id in index
            )

    writer.commit()
    return ix

# -------------------------------------------------
# SEMANTIC SEARCH
# -------------------------------------------------
def query_agent(query_text, user_id=None, agent_specialty=None, n_results=5):
    """
    Semantic search with user isolation.

    Args:
        query_text: Search query
        user_id: REQUIRED for user isolation - only return this user's documents
        agent_specialty: Optional specialty filter
        n_results: Number of results

    Returns:
        ChromaDB query results
    """
    model = _get_model()
    collection = _get_collection()
    embedding = model.encode(query_text).tolist()

    # Build where clause with user_id filter (CRITICAL for privacy)
    where = {}
    if user_id:
        where["user_id"] = user_id  # NEW: User isolation filter
    if agent_specialty:
        where["specialty"] = agent_specialty

    return collection.query(
        query_embeddings=[embedding],
        n_results=n_results,
        where=where if where else None,  # Apply filters
        include=["documents", "metadatas", "distances"]
    )

# -------------------------------------------------
# 🔥 HYBRID SEARCH (SEMANTIC + BM25)
# -------------------------------------------------
def query_medical_documents(
    query_text: str,
    user_id: str,  # NEW: REQUIRED parameter for user isolation
    agent_specialty: str | None = None,
    n_results: int = 5,
    alpha: float = 0.7
):
    """
    Hybrid search (semantic + BM25) with user isolation.

    Args:
        query_text: Search query
        user_id: REQUIRED - Only search this user's documents
        agent_specialty: Optional specialty filter
        n_results: Number of results
        alpha: Weight for semantic vs BM25 (0.7 = 70% semantic, 30% BM25)

    Returns:
        Dict with query results and metadata
    """
    semantic = query_agent(query_text, user_id, agent_specialty, n_results * 2)

    semantic_scores = {}
    semantic_meta = {}

    for doc, meta, dist in zip(
        semantic["documents"][0],
        semantic["metadatas"][0],
        semantic["distances"][0]
    ):
        semantic_scores[doc] = 1 - dist
        semantic_meta[doc] = meta

    # Try to use existing BM25 index (read-only to avoid lock conflicts)
    bm25_scores = {}
    try:
        if os.path.exists(BM25_INDEX_PATH) and os.listdir(BM25_INDEX_PATH):
            ix = open_dir(BM25_INDEX_PATH)

            with ix.searcher() as searcher:
                parser = QueryParser("text", ix.schema)
                q = parser.parse(query_text)
                results = searcher.search(q, limit=n_results * 2)

                for hit in results:
                    # Filter by user_id AND specialty (CRITICAL for privacy)
                    if hit.get("user_id") != user_id:  # NEW: User filter
                        continue
                    if agent_specialty and hit["specialty"] != agent_specialty:
                        continue
                    bm25_scores[hit["text"]] = hit.score
        else:
            logger.warning("BM25 index not found - using semantic search only")
    except Exception as e:
        logger.warning(f"BM25 search failed: {e} - using semantic search only")

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
