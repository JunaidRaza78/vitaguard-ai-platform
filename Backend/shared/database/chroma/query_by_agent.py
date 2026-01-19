import chromadb
import logging
from sentence_transformers import SentenceTransformer
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===============================
# INIT
# ===============================
logger.info("Initializing SentenceTransformer model and ChromaDB")
model = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path="./chroma_data")
collection = client.get_collection("medical_docs")
logger.info(f"Connected to ChromaDB. Collection size: {collection.count()}")

# ===============================
# BM25 INDEX SETUP
# ===============================
INDEX_DIR = "bm25_index"

schema = Schema(
    id=ID(stored=True),
    text=TEXT(stored=True),
    specialty=ID(stored=True)
)

def build_bm25_index():
    if not os.path.exists(INDEX_DIR):
        os.mkdir(INDEX_DIR)
        ix = create_in(INDEX_DIR, schema)
    else:
        ix = open_dir(INDEX_DIR)

    writer = ix.writer()

    # ❌ REMOVE "ids" from include
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



# ===============================
# SEMANTIC SEARCH (EXISTING)
# ===============================
def query_agent(query_text, agent_specialty=None, n_results=5):
    query_embedding = model.encode(query_text).tolist()

    where_filter = {"specialty": agent_specialty} if agent_specialty else None

    return collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where_filter,
        include=["documents", "metadatas", "distances"]
    )


# ===============================
# 🔥 HYBRID SEARCH (SEMANTIC + BM25)
# ===============================
def query_medical_documents(
    query_text: str,
    agent_specialty: str | None = None,
    n_results: int = 5,
    alpha: float = 0.7
):
    """
    Hybrid Search:
    - alpha * semantic score
    - (1-alpha) * keyword (BM25) score
    """

    # ---------- Semantic ----------
    semantic = query_agent(query_text, agent_specialty, n_results * 2)

    semantic_scores = {}
    semantic_meta = {}

    for doc, meta, dist in zip(
        semantic["documents"][0],
        semantic["metadatas"][0],
        semantic["distances"][0]
    ):
        semantic_scores[doc] = (1 - dist)
        semantic_meta[doc] = meta

    # ---------- BM25 ----------
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

    # ---------- Combine ----------
    combined = {}

    for doc, s_score in semantic_scores.items():
        combined[doc] = alpha * s_score

    for doc, k_score in bm25_scores.items():
        combined[doc] = combined.get(doc, 0) + (1 - alpha) * k_score

    ranked = sorted(combined.items(), key=lambda x: x[1], reverse=True)[:n_results]

    # ---------- Response ----------
    response = []
    for doc, score in ranked:
        meta = semantic_meta.get(doc, {})
        response.append({
            "score": round(score * 100, 2),
            "agent": meta.get("specialty"),
            "type": meta.get("type"),
            "source_file": meta.get("source_file"),
            "text": doc[:300] + "..." if len(doc) > 300 else doc
        })

    return {
        "query": query_text,
        "agent": agent_specialty or "all",
        "search_type": "HYBRID (SEMANTIC + BM25)",
        "count": len(response),
        "results": response
    }
