# Medical Multi-Agent RAG System

## Quick Start

### 1. Activate Virtual Environment
```bash
cd /Users/azt/Documents/Chroma/Backend/shared/database/chroma
source ../../../../venv/bin/activate
```

### 2. Start API Server
```bash
uvicorn api:app --reload --port 8000
```

### 3. Test API
```bash
# Health check
curl http://localhost:8000/health

# Upload PDF
curl -X POST "http://localhost:8000/upload" \
  -F "file=@/path/to/document.pdf"

# Search
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "diabetes treatment", "agent": "endocrinology", "top_k": 5}'
```

## Debugging Guide

### Enable Debug Logging

Change logging level in any file:
```python
logging.basicConfig(level=logging.DEBUG)  # More verbose
```

### Log Locations

Logs are printed to console with timestamps:
```
2026-01-15 20:00:00 - __main__ - INFO - Processing PDF 1/39: diabetes.pdf
2026-01-15 20:00:01 - __main__ - DEBUG - Generated content_hash: abc123...
2026-01-15 20:00:02 - __main__ - INFO - Detected specialty: endocrinology
```

### Common Debug Scenarios

#### 1. Upload Not Working
```python
# Check logs for:
logger.info(f"Uploading file: {file.filename} to {file_path}")
logger.info(f"File saved successfully: {file.filename}")
logger.info(f"Background tasks scheduled for: {file.filename}")
```

#### 2. Duplicate Detection Issues
```python
# Check logs for:
logger.debug(f"Generated content_hash: {content_hash}")
logger.info(f"Skipped (duplicate filename): {pdf_path.name}")
logger.info(f"Skipped (duplicate content): {pdf_path.name}")
```

#### 3. Search Not Returning Results
```python
# Check logs for:
logger.info(f"Search query: '{query}', agent: {agent}, top_k: {top_k}")
logger.info(f"Search completed. Found {results.get('count', 0)} results")
```

#### 4. PDF Extraction Errors
```python
# Check logs for:
logger.info(f"Extracted {len(reader.pages)} pages from {doc_name}")
logger.error(f"Error extracting PDF {pdf_path}: {str(e)}")
```

### Debugging with VSCode

1. Create `.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI Server",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "api:app",
        "--reload",
        "--port",
        "8000"
      ],
      "cwd": "${workspaceFolder}/Backend/shared/database/chroma",
      "python": "${workspaceFolder}/venv/bin/python"
    }
  ]
}
```

2. Set breakpoints in any .py file
3. Press F5 to start debugging

### Step-by-Step Debugging

#### Test Individual Components

**1. Test PDF Extraction:**
```python
from extract_text_with_specialty import extract_pdf, generate_content_hash

doc_name, text = extract_pdf("../../../dataset/diabetes.pdf")
print(f"Extracted {len(text)} characters")
print(f"Content hash: {generate_content_hash(text)}")
```

**2. Test Embedding Generation:**
```python
from generate_embeddings import generate_medical_embeddings

result = generate_medical_embeddings()
print(result)
```

**3. Test Query:**
```python
from query_by_agent import query_medical_documents

results = query_medical_documents(
    query_text="diabetes treatment",
    agent_specialty="endocrinology",
    n_results=5
)
print(results)
```

### Error Handling

All functions now have try-except blocks with logging:

```python
try:
    # Operation
    logger.info("Operation started")
except Exception as e:
    logger.error(f"Error: {str(e)}", exc_info=True)
    raise
```

The `exc_info=True` parameter logs full stack traces for debugging.

### Performance Monitoring

Add timing logs:
```python
import time

start = time.time()
# Your operation
elapsed = time.time() - start
logger.info(f"Operation took {elapsed:.2f} seconds")
```

## File Structure

```
chroma/
├── api.py                             # FastAPI server (main entry)
├── extract_text_with_specialty.py    # PDF extraction & processing
├── generate_embeddings.py            # Embedding generation
├── query_by_agent.py                 # Search engine
├── agent_types.py                     # Medical specialties
├── migrate_add_content_hash.py       # One-time migration
├── chroma_data/                       # Vector database
├── bm25_index/                        # BM25 search index
└── requirements.txt                   # Dependencies
```

## Key Features

✅ **Duplicate Detection**: Content-based hash (beginning, middle, end samples)
✅ **Error Handling**: Try-except blocks with detailed logging
✅ **Logging**: Comprehensive logs at INFO and DEBUG levels
✅ **Validation**: Input validation for all API endpoints
✅ **Background Processing**: Upload triggers async ingestion
✅ **Hybrid Search**: Semantic (ChromaDB) + Keyword (BM25)

## Troubleshooting

### Issue: "Collection not found"
**Solution:** Run PDF ingestion first:
```python
from extract_text_with_specialty import ingest_medical_pdfs
ingest_medical_pdfs()
```

### Issue: "No embeddings found"
**Solution:** Generate embeddings:
```python
from generate_embeddings import generate_medical_embeddings
generate_medical_embeddings()
```

### Issue: "File already exists"
**Check:** Is it a renamed duplicate?
```python
# Logs will show:
# "Already processed (same content, different name) - SKIPPING"
```

## Environment

- **Python**: 3.11+
- **ChromaDB**: Persistent storage at `./chroma_data/`
- **Model**: all-MiniLM-L6-v2 (384 dimensions)
- **Dataset**: `../../../dataset/*.pdf`
