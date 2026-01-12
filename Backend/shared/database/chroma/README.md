# Chroma DB - Vector Database for Medical Knowledge

Chroma vector database integration for storing and retrieving medical knowledge embeddings in the RAG-based Medical Chatbot Service.

## Overview

This module provides:
- Vector storage for medical knowledge base
- Semantic search capabilities
- Open-source embeddings using Sentence Transformers (default)
- Optional OpenAI embeddings integration
- Medical document management
- Hybrid search (vector + keyword)

## Architecture

```
chroma/
├── config.py              # Configuration settings
├── client.py              # Chroma client connection
├── embeddings.py          # OpenAI embedding service
├── init_chroma.py         # Initialization script
├── operations/
│   └── vector_ops.py      # CRUD operations
└── models/
    └── medical_document.py # Data models
```

## Installation

### 1. Install Dependencies

```bash
cd Backend/shared/database/chroma
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the Backend directory:

```env
# Chroma DB Configuration
CHROMA_CLIENT_TYPE=persistent  # or "http" for remote server
CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_PERSIST_DIRECTORY=./chroma_data
CHROMA_COLLECTION_NAME=medical_knowledge

# Embedding Settings (Open-source default)
EMBEDDING_PROVIDER=sentence-transformers  # "sentence-transformers", "huggingface", or "openai"
EMBEDDING_MODEL=all-MiniLM-L6-v2  # Fast and efficient open-source model
EMBEDDING_DIMENSION=384
DEVICE=cpu  # or "cuda" for GPU acceleration

# Alternative Open-source Models:
# - all-MiniLM-L6-v2: 384 dimensions (default, fast)
# - all-mpnet-base-v2: 768 dimensions (higher quality)
# - multi-qa-MiniLM-L6-cos-v1: 384 dimensions (optimized for Q&A)

# Optional: OpenAI Configuration (only if using EMBEDDING_PROVIDER=openai)
# OPENAI_API_KEY=your_openai_api_key_here
# EMBEDDING_MODEL=text-embedding-ada-002
# EMBEDDING_DIMENSION=1536

# Retrieval Settings
DEFAULT_TOP_K=5
MIN_RELEVANCE_SCORE=0.7
BATCH_SIZE=32
```

### 3. Initialize Database

```bash
# Initialize with sample data
python init_chroma.py

# Reset database (delete all data)
python init_chroma.py --reset
```

## Usage

### Basic Operations

#### 1. Connect to Chroma DB

```python
from shared.database.chroma import get_client

# Get client
client = get_client()

# Test connection
version = client.get_version()
print(f"Chroma version: {version}")

# Get collection
collection = client.get_or_create_collection()
print(f"Collection: {collection.name}, Count: {collection.count()}")
```

#### 2. Add Documents

```python
from shared.database.chroma import get_vector_operations
from shared.database.chroma.models import MedicalDocument, ContentType, MedicalSpecialty

# Create operations instance
vector_ops = get_vector_operations()

# Create a medical document
doc = MedicalDocument(
    title="Understanding Type 2 Diabetes",
    content="Diabetes is a chronic condition affecting blood sugar levels...",
    content_type=ContentType.DISEASE_INFO,
    specialty=MedicalSpecialty.ENDOCRINOLOGY,
    source="CDC",
    source_url="https://www.cdc.gov/diabetes",
    icd_codes=["E11"],
    keywords=["diabetes", "blood sugar", "insulin"],
    reliability_score=0.95,
    peer_reviewed=True
)

# Add document
doc_id = vector_ops.add_document(
    text=doc.content,
    metadata=doc.to_chroma_metadata()
)
print(f"Added document: {doc_id}")
```

#### 3. Search Documents

```python
# Simple search
results = vector_ops.search(
    query="What are symptoms of diabetes?",
    top_k=5,
    min_score=0.7
)

for result in results:
    print(f"Title: {result['metadata']['title']}")
    print(f"Score: {result['score']:.4f}")
    print(f"Content: {result['document'][:200]}...")
    print("-" * 60)
```

#### 4. Filter by Metadata

```python
# Search with filters
results = vector_ops.search(
    query="diabetes treatment",
    top_k=5,
    filters={
        "specialty": "endocrinology",
        "content_type": "disease_info"
    }
)
```

#### 5. Batch Operations

```python
# Add multiple documents
texts = [
    "Document 1 content...",
    "Document 2 content...",
    "Document 3 content..."
]

metadatas = [
    {"title": "Doc 1", "source": "CDC"},
    {"title": "Doc 2", "source": "FDA"},
    {"title": "Doc 3", "source": "Mayo Clinic"}
]

doc_ids = vector_ops.add_documents_batch(texts, metadatas)
print(f"Added {len(doc_ids)} documents")
```

### Advanced Usage

#### Custom Embeddings

```python
from shared.database.chroma import get_embedding_service

# Get embedding service
embedding_service = get_embedding_service()

# Generate single embedding
text = "What is diabetes?"
embedding = embedding_service.generate_embedding(text)
print(f"Embedding dimension: {len(embedding)}")

# Generate batch embeddings
texts = ["Text 1", "Text 2", "Text 3"]
embeddings = embedding_service.generate_embeddings_batch(texts)
print(f"Generated {len(embeddings)} embeddings")
```

#### Hybrid Search

```python
# Combine vector search with keyword filtering
results = vector_ops.hybrid_search(
    query="diabetes symptoms",
    top_k=10,
    keyword_filter="insulin",
    metadata_filters={"source": "CDC"}
)
```

#### Update Documents

```python
# Update document text and metadata
vector_ops.update_document(
    document_id="doc-123",
    text="Updated content...",
    metadata={"updated_at": "2024-01-08", "version": "2.0"}
)
```

#### Delete Documents

```python
# Delete single document
vector_ops.delete_document("doc-123")

# Delete batch
doc_ids = ["doc-1", "doc-2", "doc-3"]
vector_ops.delete_documents_batch(doc_ids)
```

## Data Models

### MedicalDocument

```python
from shared.database.chroma.models import (
    MedicalDocument,
    ContentType,
    MedicalSpecialty,
    TargetAudience
)

doc = MedicalDocument(
    title="Document Title",
    content="Document content...",
    content_type=ContentType.ARTICLE,  # article, guideline, drug_info, etc.
    specialty=MedicalSpecialty.CARDIOLOGY,  # cardiology, pediatrics, etc.
    target_audience=TargetAudience.PATIENT,  # patient, healthcare_professional, etc.
    source="Mayo Clinic",
    source_url="https://example.com",
    icd_codes=["I10"],
    drug_names=["metformin"],
    keywords=["diabetes", "treatment"],
    reliability_score=0.95,
    peer_reviewed=True,
    language="en"
)
```

### SearchQuery

```python
from shared.database.chroma.models import SearchQuery, ContentType

query = SearchQuery(
    query="diabetes symptoms",
    top_k=5,
    min_score=0.7,
    content_type=ContentType.DISEASE_INFO,
    specialty=MedicalSpecialty.ENDOCRINOLOGY,
    min_reliability=0.8
)

filters = query.to_metadata_filter()
```

## Configuration

### Client Types

#### Persistent Client (Local Storage)
```python
# .env
CHROMA_CLIENT_TYPE=persistent
CHROMA_PERSIST_DIRECTORY=./chroma_data
```

#### HTTP Client (Remote Server)
```python
# .env
CHROMA_CLIENT_TYPE=http
CHROMA_HOST=chroma-server.example.com
CHROMA_PORT=8000
```

### Embedding Models

#### Open-source Models (Default - No API Key Required)
- `all-MiniLM-L6-v2` - 384 dimensions (recommended, fast and efficient)
- `all-mpnet-base-v2` - 768 dimensions (higher quality)
- `multi-qa-MiniLM-L6-cos-v1` - 384 dimensions (optimized for Q&A)
- `all-distilroberta-v1` - 768 dimensions (balanced)

#### OpenAI Models (Optional - Requires API Key)
- `text-embedding-ada-002` - 1536 dimensions
- `text-embedding-3-small` - 1536 dimensions
- `text-embedding-3-large` - 3072 dimensions

### Performance Tuning

```python
# .env
EMBEDDING_PROVIDER=sentence-transformers  # Use open-source models
DEVICE=cuda                # Use GPU for faster embedding generation (if available)
BATCH_SIZE=32              # Batch size for embeddings (32 for local models)
DEFAULT_TOP_K=5            # Default number of results
MIN_RELEVANCE_SCORE=0.7    # Minimum relevance threshold
CHUNK_SIZE=1000            # Text chunk size (tokens)
CHUNK_OVERLAP=100          # Overlap between chunks
```

## Monitoring

### Collection Statistics

```python
stats = vector_ops.get_collection_stats()
print(f"Documents: {stats['count']}")
print(f"Metadata: {stats['metadata']}")
```

### Health Check

```python
# Check if Chroma is alive
heartbeat = client.heartbeat()
print(f"Heartbeat: {heartbeat}")
```

## Best Practices

### 1. Document Chunking

For long documents, split into chunks:
```python
def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    return chunks
```

### 2. Metadata Strategy

Include relevant metadata for filtering:
```python
metadata = {
    "title": "Document title",
    "source": "CDC",
    "content_type": "article",
    "specialty": "cardiology",
    "icd_codes": "I10,I11",
    "reliability_score": 0.95,
    "indexed_at": "2024-01-08T10:00:00Z"
}
```

### 3. Search Optimization

- Use specific queries for better results
- Apply metadata filters to narrow results
- Set appropriate min_score threshold
- Use hybrid search for complex queries

### 4. Batch Operations

Always use batch operations for multiple documents:
```python
# Good
vector_ops.add_documents_batch(texts, metadatas)

# Avoid
for text, metadata in zip(texts, metadatas):
    vector_ops.add_document(text, metadata)
```

## Troubleshooting

### Connection Issues

```python
# Test connection
try:
    client = get_client()
    heartbeat = client.heartbeat()
    print(f"✓ Connected: {heartbeat}")
except Exception as e:
    print(f"✗ Connection failed: {e}")
```

### OpenAI API Errors

Check your API key:
```bash
echo $OPENAI_API_KEY
```

### Empty Search Results

1. Verify documents exist: `collection.count()`
2. Lower min_score threshold
3. Check query relevance
4. Review metadata filters

### Performance Issues

1. Use batch operations
2. Implement caching
3. Optimize chunk size
4. Use metadata filters

## Integration with Chatbot Service

```python
# In Medical Chatbot Service (Port 8009)
from shared.database.chroma import get_vector_operations

class ChatbotRAG:
    def __init__(self):
        self.vector_ops = get_vector_operations()

    def retrieve_context(self, query: str, top_k: int = 5):
        """Retrieve relevant medical knowledge"""
        results = self.vector_ops.search(
            query=query,
            top_k=top_k,
            min_score=0.7
        )
        return [r['document'] for r in results]

    def generate_response(self, query: str):
        """Generate RAG-based response"""
        # 1. Retrieve relevant context
        context = self.retrieve_context(query)

        # 2. Combine with user health data from Neo4j
        user_context = self.get_user_health_data()

        # 3. Generate response with LLM
        prompt = self.build_prompt(query, context, user_context)
        response = self.call_llm(prompt)

        return response
```

## API Reference

See the docstrings in each module for detailed API documentation:
- [client.py](./client.py) - Client connection and management
- [embeddings.py](./embeddings.py) - Embedding generation
- [operations/vector_ops.py](./operations/vector_ops.py) - CRUD operations
- [models/medical_document.py](./models/medical_document.py) - Data models

## License

Part of the Agentic AI Family Health Manager project.
