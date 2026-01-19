"""
Step 2: Generate Embeddings
- Get data from Chroma
- Generate embeddings using MiniLM
- Update Chroma with embeddings
"""

import chromadb
import logging
from sentence_transformers import SentenceTransformer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_medical_embeddings():
    """
    Step 2:
    - Load documents from Chroma
    - Generate missing embeddings
    - Update Chroma collection
    """

    print("\n" + "="*60)
    print("STEP 2: Generate & Save Embeddings")
    print("="*60)

    try:
        # Load embedding model
        print("\n📦 Loading embedding model...")
        logger.info("Loading SentenceTransformer model: all-MiniLM-L6-v2")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print(f"   ✅ Model: all-MiniLM-L6-v2")
        print(f"   ✅ Dimensions: {model.get_sentence_embedding_dimension()}")
        logger.info(f"Model loaded. Dimensions: {model.get_sentence_embedding_dimension()}")

        # Connect to Chroma
        print("\n🔌 Connecting to Chroma...")
        client = chromadb.PersistentClient(path="./chroma_data")

        try:
            collection = client.get_collection("medical_docs")
            print(f"   ✅ Collection found: medical_docs")
            print(f"   ✅ Total documents: {collection.count()}")
            logger.info(f"Connected to collection. Total docs: {collection.count()}")
        except Exception as e:
            print("   ❌ Collection not found!")
            print("   Run Step-1 ingestion first")
            logger.error(f"Collection not found: {str(e)}")
            return {"status": "failed", "reason": "collection_not_found"}

    except Exception as e:
        logger.error(f"Initialization error: {str(e)}", exc_info=True)
        return {"status": "failed", "reason": str(e)}

    # Load data
    print("\n📂 Loading documents from Chroma...")
    results = collection.get(include=["documents", "metadatas", "embeddings"])

    ids = results["ids"]
    documents = results["documents"]
    metadatas = results["metadatas"]
    existing_embeddings = results["embeddings"]

    print(f"   ✅ Loaded {len(documents)} documents")

    docs_without_embeddings = []
    docs_with_embeddings = 0

    for doc_id, doc, meta, emb in zip(ids, documents, metadatas, existing_embeddings):
        if emb is None or len(emb) == 0:
            docs_without_embeddings.append((doc_id, doc, meta))
        else:
            docs_with_embeddings += 1

    print(f"   ✅ Already have embeddings: {docs_with_embeddings}")
    print(f"   ⚠️  Need embeddings: {len(docs_without_embeddings)}")

    if not docs_without_embeddings:
        print("\n✅ ALL DOCUMENTS ALREADY HAVE EMBEDDINGS!")
        return {
            "status": "skipped",
            "total_docs": len(ids),
            "embedded": docs_with_embeddings
        }

    # Generate embeddings
    print(f"\n🔄 Generating embeddings for {len(docs_without_embeddings)} documents...")
    new_embeddings = []

    for idx, (doc_id, doc, meta) in enumerate(docs_without_embeddings, 1):
        embedding = model.encode(doc).tolist()
        new_embeddings.append((doc_id, embedding))

        if meta["type"] == "document_name":
            print(f"   ✅ {idx}. Document name embedded")
        else:
            print(f"   ✅ {idx}. Chunk {meta.get('chunk_index')} embedded")

    # Update Chroma
    print(f"\n💾 Updating {len(new_embeddings)} documents with embeddings...")
    for doc_id, embedding in new_embeddings:
        collection.update(ids=[doc_id], embeddings=[embedding])

    print("\n" + "="*60)
    print("✅ STEP 2 COMPLETE")
    print("="*60)

    return {
        "status": "success",
        "new_embeddings": len(new_embeddings),
        "total_documents": collection.count(),
        "embedding_dim": model.get_sentence_embedding_dimension()
    }
