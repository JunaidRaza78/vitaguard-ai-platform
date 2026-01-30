"""
Family Health Manager - Unified API
Complete FastAPI application with Authentication and Medical RAG Chatbot
"""

import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager
import time
import json
import uuid

from fastapi import FastAPI, Request, status, HTTPException, Depends, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.exceptions import RequestValidationError
import shutil
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel
from sqlalchemy import text

# Add Backend directory to path for imports
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Import authentication router
from app.api.auth import router as auth_router

# Import RAG chatbot components
try:
    from ollama_rag.rag_chatbot import get_chatbot
    from ollama_rag.ollama_client import get_ollama_client
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("RAG chatbot components not available")
    get_chatbot = None
    get_ollama_client = None

# Direct import to avoid complex dependency chains
from shared.database.postgres.postgres_client import PostgresClient

# Neo4j client for graph database
try:
    from shared.database.neo4j.neo4j_client import Neo4jClient
    neo4j_client = Neo4jClient()
    NEO4J_AVAILABLE = True
except Exception as e:
    NEO4J_AVAILABLE = False
    neo4j_client = None

# Setup logging FIRST so we can see import errors
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Dataset directory for uploaded files
DATASET_DIR = Path(__file__).parent.parent / "dataset"
DATASET_DIR.mkdir(exist_ok=True)

# Import document processing functions
DOCUMENT_PROCESSING_ERROR = None  # Store error for debugging
try:
    from shared.database.chroma.extract_text_with_specialty import ingest_medical_pdfs
    from shared.database.chroma.generate_embeddings import generate_medical_embeddings
    from shared.database.chroma.query_by_agent import query_medical_documents
    DOCUMENT_PROCESSING_AVAILABLE = True
    logger.info("✅ Document processing components loaded successfully")
except Exception as e:
    # Catch ALL exceptions, not just ImportError, to see the real error
    import traceback
    DOCUMENT_PROCESSING_ERROR = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
    logger.error(f"❌ Document processing components not available: {e}")
    logger.error(f"   Traceback: {traceback.format_exc()}")
    print(f"❌ DOCUMENT PROCESSING IMPORT FAILED: {e}", file=sys.stderr)
    ingest_medical_pdfs = None
    generate_medical_embeddings = None
    query_medical_documents = None
    DOCUMENT_PROCESSING_AVAILABLE = False

# Database client
postgres_client = PostgresClient()


# ==========================================
# LIFESPAN MANAGEMENT
# ==========================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - handles startup and shutdown events"""
    # Startup
    logger.info("=" * 60)
    logger.info("🚀 Starting Family Health Manager - Unified API")
    logger.info("=" * 60)

    # PostgreSQL client uses context manager pattern - will connect when used
    logger.info("✅ PostgreSQL client initialized (connects on first use)")

    # Test Ollama connection
    if get_ollama_client:
        try:
            ollama_client = get_ollama_client()
            logger.info("✅ Ollama client initialized")
        except Exception as e:
            logger.warning(f"⚠️  Ollama client initialization failed: {e}")

    logger.info("🎉 All services initialized successfully")
    logger.info("=" * 60)

    yield

    # Shutdown
    logger.info("=" * 60)
    logger.info("🛑 Shutting down Family Health Manager API")
    logger.info("=" * 60)
    logger.info("✅ Shutdown complete")


# ==========================================
# CREATE FASTAPI APPLICATION
# ==========================================

app = FastAPI(
    title="Family Health Manager API",
    description="Unified API for Authentication and Medical RAG Chatbot",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)


# ==========================================
# MIDDLEWARE
# ==========================================

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests with timing"""
    start_time = time.time()

    # Log request
    logger.info(
        f"📥 {request.method} {request.url.path} - "
        f"Client: {request.client.host if request.client else 'unknown'}"
    )

    # Process request
    response = await call_next(request)

    # Calculate processing time
    process_time = time.time() - start_time

    # Log response
    logger.info(
        f"📤 {request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )

    # Add processing time to response headers
    response.headers["X-Process-Time"] = str(process_time)

    return response


# ==========================================
# EXCEPTION HANDLERS
# ==========================================

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    logger.error(f"HTTP error: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    # Convert errors to JSON-serializable format
    errors = []
    for error in exc.errors():
        err = {
            "loc": error.get("loc", []),
            "msg": str(error.get("msg", "")),
            "type": str(error.get("type", ""))
        }
        errors.append(err)
    logger.error(f"Validation error: {errors}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Validation error",
            "details": errors
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later."
        }
    )


# ==========================================
# AUTHENTICATION ROUTER
# ==========================================

# Include authentication endpoints under /api/v1/auth
app.include_router(auth_router)


# ==========================================
# RAG CHATBOT ENDPOINTS
# ==========================================

class ChatRequest(BaseModel):
    """Chat request model for RAG chatbot"""
    message: str | None = None
    question: str | None = None
    conversation_id: str | None = None
    user_id: str | None = None
    specialty: str | None = None
    top_k: int = 5
    temperature: float = 0.3
    stream: bool = False


class EmbeddingRequest(BaseModel):
    """Embedding generation request"""
    text: str


@app.post(
    "/api/v1/chat",
    tags=["Medical Chatbot"],
    summary="Chat with Medical AI",
    description="Send a medical question and get AI-powered response with RAG"
)
async def chat(req: ChatRequest):
    """
    Chat with the medical AI chatbot.

    - **message/question**: Your medical question or symptom description
    - **conversation_id**: Optional conversation ID for context (auto-generated if not provided)
    - **user_id**: Optional user ID for personalization
    - **specialty**: Optional medical specialty filter
    - **top_k**: Number of relevant documents to retrieve (default: 5)
    - **temperature**: Response creativity (0.0-1.0, default: 0.3)
    - **stream**: Enable streaming response (default: false)
    """
    if not get_chatbot:
        raise HTTPException(
            status_code=503,
            detail="Medical chatbot service is not available"
        )

    text = (req.message or req.question or "").strip()

    # Log incoming request
    logger.info(f"Chat request: {text[:50]}...")

    if not text:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    conv_id = req.conversation_id or str(uuid.uuid4())

    try:
        chatbot = get_chatbot()

        if req.stream:
            async def stream():
                for chunk in chatbot.chat(
                    question=text,
                    conversation_id=conv_id,
                    user_id=req.user_id,
                    specialty=req.specialty,
                    top_k=req.top_k,
                    temperature=req.temperature,
                    stream=True
                ):
                    yield f"data: {json.dumps(chunk)}\n\n"

            return StreamingResponse(stream(), media_type="text/event-stream")

        # Non-streaming
        result = chatbot.chat(
            question=text,
            conversation_id=conv_id,
            user_id=req.user_id,
            specialty=req.specialty,
            top_k=req.top_k,
            temperature=req.temperature,
            stream=False
        )

        # Check for empty answer
        answer = result.get("answer", "").strip()

        if not answer:
            logger.error(f"EMPTY ANSWER! Result: {result}")
            answer = "I apologize, but I'm unable to generate a response. Please try rephrasing your question."

        logger.info(f"✅ Answer length: {len(answer)} chars")

        return {
            "status": "success",
            "conversation_id": conv_id,
            "answer": answer,
            "sources": result.get("sources", []),
            "context_used": result.get("context_used", False),
            "storage": result.get("storage", "unknown")
        }

    except Exception as e:
        logger.error(f"❌ Chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Chat failed: {str(e)}"
        )


@app.post(
    "/api/v1/embeddings/generate",
    tags=["Medical Chatbot"],
    summary="Generate Text Embeddings",
    description="Generate vector embeddings for medical text"
)
def generate_embedding(req: EmbeddingRequest):
    """
    Generate vector embeddings for text.

    Used internally by the RAG system for semantic search.
    """
    try:
        from shared.database.chroma.query_by_agent import model
        return {
            "dimensions": len(model.encode(req.text)),
            "embedding": model.encode(req.text).tolist()
        }
    except Exception as e:
        logger.error(f"Embedding generation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Embedding generation failed: {str(e)}"
        )


# ==========================================
# DOCUMENT UPLOAD & SEARCH ENDPOINTS
# ==========================================

class SearchRequest(BaseModel):
    """Search request model for hybrid search"""
    query: str
    agent: str | None = None
    top_k: int = 5


@app.post(
    "/api/v1/documents/upload",
    tags=["Document Processing"],
    summary="Upload Medical PDF",
    description="Upload a PDF document for ingestion and embedding generation"
)
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    Upload a medical PDF document for processing.

    - **file**: PDF file to upload

    The document will be:
    1. Saved to the dataset directory
    2. Ingested and text extracted (background task)
    3. Embeddings generated for semantic search (background task)
    """
    if not DOCUMENT_PROCESSING_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Document processing service is not available"
        )

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


@app.post(
    "/api/v1/documents/search",
    tags=["Document Processing"],
    summary="Hybrid Search Documents",
    description="Search medical documents using hybrid semantic + BM25 search"
)
def search_documents(request: SearchRequest):
    """
    Search medical documents using hybrid search.

    - **query**: Search query text
    - **agent**: Optional medical specialty filter (e.g., cardiology, neurology)
    - **top_k**: Number of results to return (1-50, default: 5)

    Returns results combining semantic search (ChromaDB) and keyword search (BM25).
    """
    if not DOCUMENT_PROCESSING_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Document search service is not available"
        )

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


# ==========================================
# ROOT ENDPOINTS
# ==========================================

@app.get(
    "/",
    tags=["Root"],
    summary="API Root",
    description="Get API information and available endpoints"
)
async def root():
    """Root endpoint - API information"""
    return {
        "service": "Family Health Manager - Unified API",
        "version": "2.0.0",
        "status": "operational",
        "docs": "/docs",
        "redoc": "/redoc",
        "services": {
            "authentication": {
                "register": "/api/v1/auth/register",
                "login": "/api/v1/auth/login",
                "refresh": "/api/v1/auth/refresh",
                "logout": "/api/v1/auth/logout",
                "profile": "/api/v1/auth/me",
                "verify_email": "/api/v1/auth/verify-email",
                "forgot_password": "/api/v1/auth/forgot-password",
                "reset_password": "/api/v1/auth/reset-password",
                "change_password": "/api/v1/auth/change-password"
            },
            "medical_chatbot": {
                "chat": "/api/v1/chat",
                "embeddings": "/api/v1/embeddings/generate"
            },
            "document_processing": {
                "upload": "/api/v1/documents/upload",
                "search": "/api/v1/documents/search"
            }
        }
    }


@app.get(
    "/health",
    tags=["Health"],
    summary="Health Check",
    description="Check service health and database connectivity"
)
async def health_check():
    """Health check endpoint for monitoring"""
    health_status = {
        "status": "healthy",
        "service": "unified-api",
        "timestamp": time.time(),
        "services": {}
    }

    # Check PostgreSQL connection
    try:
        # Use context manager for database check
        with postgres_client as db:
            db.session.execute(text("SELECT 1"))
            health_status["services"]["postgresql"] = "connected"
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")
        health_status["services"]["postgresql"] = "disconnected"
        health_status["status"] = "degraded"

    # Check document processing
    if DOCUMENT_PROCESSING_AVAILABLE:
        health_status["services"]["document_processing"] = "available"
    else:
        health_status["services"]["document_processing"] = {
            "status": "unavailable",
            "error": DOCUMENT_PROCESSING_ERROR
        }

    # Check Ollama connection
    if get_ollama_client:
        try:
            ollama = get_ollama_client()
            # Simple check to see if client is available
            health_status["services"]["ollama"] = "available"
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            health_status["services"]["ollama"] = "unavailable"
            health_status["status"] = "degraded"
    else:
        health_status["services"]["ollama"] = "not_configured"

    # Check Neo4j connection
    if NEO4J_AVAILABLE and neo4j_client:
        try:
            if neo4j_client.health_check():
                health_status["services"]["neo4j"] = "connected"
            else:
                health_status["services"]["neo4j"] = "disconnected"
        except Exception as e:
            logger.error(f"Neo4j health check failed: {e}")
            health_status["services"]["neo4j"] = "unavailable"
    else:
        health_status["services"]["neo4j"] = "not_configured"

    # Return appropriate status code
    if health_status["status"] == "degraded":
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=health_status
        )

    return health_status


@app.get(
    "/ready",
    tags=["Health"],
    summary="Readiness Check",
    description="Check if service is ready to accept requests"
)
async def readiness_check():
    """Readiness check for Kubernetes/load balancers"""
    try:
        # Check database connectivity
        with postgres_client as db:
            db.session.execute(text("SELECT 1"))
            return {
                "ready": True,
                "service": "unified-api",
                "version": "2.0.0"
            }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "ready": False,
                "service": "unified-api",
                "error": str(e)
            }
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
