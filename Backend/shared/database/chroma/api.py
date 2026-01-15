from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from pydantic import BaseModel
from pathlib import Path
import shutil
import logging

# ✅ tumhare existing functions
from extract_text_with_specialty import ingest_medical_pdfs
from generate_embeddings import generate_medical_embeddings
from query_by_agent import query_medical_documents

# Setup logging for debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Medical RAG Hybrid Search API")

# Use the same dataset folder as extract_text_with_specialty.py
DATASET_DIR = Path("../../../dataset")
DATASET_DIR.mkdir(exist_ok=True)

# =====================================================
# REQUEST MODELS
# =====================================================
class SearchRequest(BaseModel):
    query: str
    agent: str | None = None
    top_k: int = 5

# =====================================================
# HEALTH CHECK
# =====================================================
@app.get("/health")
def health():
    return {"status": "ok"}

# =====================================================
# UPLOAD PDF → INGEST → EMBEDDINGS
# =====================================================
@app.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    1. Upload PDF
    2. Ingest (Step-1)
    3. Generate embeddings (Step-2)
    """
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            logger.warning(f"Invalid file type attempted: {file.filename}")
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        file_path = DATASET_DIR / file.filename
        logger.info(f"Uploading file: {file.filename} to {file_path}")

        # Save uploaded file
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        logger.info(f"File saved successfully: {file.filename}")

        # Process in background
        background_tasks.add_task(ingest_medical_pdfs)
        background_tasks.add_task(generate_medical_embeddings)

        logger.info(f"Background tasks scheduled for: {file.filename}")

        return {
            "status": "accepted",
            "filename": file.filename,
            "message": "PDF uploaded. Ingestion & embedding running in background."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file {file.filename}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# =====================================================
# HYBRID SEARCH (SEMANTIC + BM25)
# =====================================================
@app.post("/search")
def search(request: SearchRequest):
    """
    Hybrid Search:
    - Semantic (Chroma)
    - Keyword (BM25)
    """
    try:
        # Validate query
        if not request.query or len(request.query.strip()) == 0:
            logger.warning("Empty query received")
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        if request.top_k < 1 or request.top_k > 50:
            logger.warning(f"Invalid top_k value: {request.top_k}")
            raise HTTPException(status_code=400, detail="top_k must be between 1 and 50")

        logger.info(f"Search query: '{request.query}', agent: {request.agent}, top_k: {request.top_k}")

        results = query_medical_documents(
            query_text=request.query,
            agent_specialty=request.agent,
            n_results=request.top_k
        )

        logger.info(f"Search completed. Found {results.get('count', 0)} results")

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error for query '{request.query}': {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
