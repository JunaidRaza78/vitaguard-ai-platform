"""
Family Health Manager - Unified API
Complete FastAPI application with Authentication and Medical RAG Chatbot
"""

import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional
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
from shared.database.redis.redis_client import RedisClient

# Import notifications router
try:
    from app.api.notifications import router as notifications_router
    NOTIFICATIONS_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"Notifications router not available: {e}")
    notifications_router = None
    NOTIFICATIONS_AVAILABLE = False

# Import Google OAuth router
try:
    from app.api.google_auth_routes import router as google_auth_router
    GOOGLE_AUTH_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"Google Auth router not available: {e}")
    google_auth_router = None
    GOOGLE_AUTH_AVAILABLE = False

# Import Family router
try:
    from app.api.family_routes import router as family_router
    FAMILY_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"Family router not available: {e}")
    family_router = None
    FAMILY_AVAILABLE = False

# Import Dashboard router
try:
    from app.api.dashboard_routes import router as dashboard_router
    DASHBOARD_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"Dashboard router not available: {e}")
    dashboard_router = None
    DASHBOARD_AVAILABLE = False

# Import Vitals router
try:
    from app.api.vitals_routes import router as vitals_router
    VITALS_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"Vitals router not available: {e}")
    vitals_router = None
    VITALS_AVAILABLE = False

# Import Labs router
try:
    from app.api.lab_routes import router as labs_router
    LABS_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"Labs router not available: {e}")
    labs_router = None
    LABS_AVAILABLE = False

# Import Chat router
try:
    from app.api.chat_routes import router as chat_router
    CHAT_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"Chat router not available: {e}")
    chat_router = None
    CHAT_AVAILABLE = False

# Import FHIR router
try:
    from app.api.fhir_routes import router as fhir_router
    FHIR_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"FHIR router not available: {e}")
    fhir_router = None
    FHIR_AVAILABLE = False

# Import Data Export router
try:
    from app.api.data_export_routes import router as data_export_router
    DATA_EXPORT_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"Data export router not available: {e}")
    data_export_router = None
    DATA_EXPORT_AVAILABLE = False


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
import os
if os.path.exists("/app"):
    # Docker environment
    DATASET_DIR = Path("/app/dataset")
else:
    # Local development - dataset folder inside Backend
    DATASET_DIR = Path(__file__).parent / "dataset"
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

    # Initialize Redis client
    try:
        from shared.database import init_redis, redis_client
        import shared.database as db_module
        db_module.redis_client = RedisClient()
        db_module.redis_client.get_client()  # Test connection
        logger.info("✅ Redis client initialized")
    except Exception as e:
        logger.warning(f"⚠️  Redis client initialization failed: {e}")

    # Test Ollama connection
    if get_ollama_client:
        try:
            ollama_client = get_ollama_client()
            logger.info("✅ Ollama client initialized")
        except Exception as e:
            logger.warning(f"⚠️  Ollama client initialization failed: {e}")

    # Start Notification Scheduler
    notification_scheduler_instance = None
    try:
        from app.services.notification_scheduler import notification_scheduler
        if notification_scheduler.start():
            notification_scheduler_instance = notification_scheduler
            logger.info("✅ Notification scheduler started (medication reminders + pending processor)")
        else:
            logger.warning("⚠️  Notification scheduler failed to start, using simple processor")
            from app.services.notification_scheduler import simple_processor
            await simple_processor.start(check_interval_seconds=60)
            logger.info("✅ Simple notification processor started (60s interval)")
    except Exception as e:
        logger.warning(f"⚠️  Notification scheduler not available: {e}")

    logger.info("🎉 All services initialized successfully")
    logger.info("=" * 60)

    yield

    # Shutdown
    logger.info("=" * 60)
    logger.info("🛑 Shutting down Family Health Manager API")
    logger.info("=" * 60)

    # Stop notification scheduler
    try:
        if notification_scheduler_instance:
            notification_scheduler_instance.stop()
            logger.info("✅ Notification scheduler stopped")
        else:
            from app.services.notification_scheduler import simple_processor
            await simple_processor.stop()
            logger.info("✅ Simple notification processor stopped")
    except Exception as e:
        logger.warning(f"Error stopping notification scheduler: {e}")

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
# NOTIFICATIONS ROUTER
# ==========================================

# Include notifications endpoints under /api/v1/notifications
if NOTIFICATIONS_AVAILABLE and notifications_router:
    app.include_router(notifications_router)
    logger.info("✅ Notifications router loaded")
else:
    logger.warning("⚠️ Notifications router not available")


# ==========================================
# GOOGLE OAUTH ROUTER
# ==========================================

# Include Google OAuth endpoints under /api/v1/auth/google
if GOOGLE_AUTH_AVAILABLE and google_auth_router:
    app.include_router(google_auth_router)
    logger.info("✅ Google Auth router loaded")
else:
    logger.warning("⚠️ Google Auth router not available")


# ==========================================
# FAMILY ROUTER
# ==========================================

# Include family endpoints under /api/v1/families
if FAMILY_AVAILABLE and family_router:
    app.include_router(family_router)
    logger.info("✅ Family router loaded")
else:
    logger.warning("⚠️ Family router not available")


# ==========================================
# DASHBOARD ROUTER
# ==========================================

# Include dashboard endpoints under /api/v1/dashboard
if DASHBOARD_AVAILABLE and dashboard_router:
    app.include_router(dashboard_router)
    logger.info("✅ Dashboard router loaded")
else:
    logger.warning("⚠️ Dashboard router not available")


# ==========================================
# VITALS ROUTER
# ==========================================

# Include vitals endpoints under /api/v1/vitals
if VITALS_AVAILABLE and vitals_router:
    app.include_router(vitals_router)
    logger.info("✅ Vitals router loaded")
else:
    logger.warning("⚠️ Vitals router not available")

# Include labs endpoints under /api/v1/labs
if LABS_AVAILABLE and labs_router:
    app.include_router(labs_router)
    logger.info("✅ Labs router loaded")
else:
    logger.warning("⚠️ Labs router not available")

# Include chat endpoints under /api/v1/chat
if CHAT_AVAILABLE and chat_router:
    app.include_router(chat_router)
    logger.info("✅ Chat router loaded")
else:
    logger.warning("⚠️ Chat router not available")

# Include FHIR endpoints under /api/v1/fhir
if FHIR_AVAILABLE and fhir_router:
    app.include_router(fhir_router)
    logger.info("✅ FHIR router loaded")
else:
    logger.warning("⚠️ FHIR router not available")

# Include data export endpoints under /api/v1/data
if DATA_EXPORT_AVAILABLE and data_export_router:
    app.include_router(data_export_router)
    logger.info("✅ Data export router loaded")
else:
    logger.warning("⚠️ Data export router not available")


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
# DOCUMENT Q&A ENDPOINT
# ==========================================

class DocumentAskRequest(BaseModel):
    question: str
    specialty: Optional[str] = None
    top_k: int = 5


@app.post(
    "/api/v1/documents/ask",
    tags=["Document Processing"],
    summary="Ask a question about uploaded documents",
    description="Search documents and generate an AI answer based on the retrieved context",
)
async def ask_document(request: DocumentAskRequest):
    """Ask a question using the uploaded documents as context via RAG pipeline."""
    try:
        from ollama_rag.rag_chatbot import get_chatbot

        chatbot = get_chatbot()
        conv_id = f"doc_ask_{uuid.uuid4().hex[:12]}"
        result = chatbot.chat(
            question=request.question,
            conversation_id=conv_id,
            specialty=request.specialty,
            stream=False,
        )

        sources = []
        if isinstance(result, dict):
            answer = result.get("answer", "")
            raw_sources = result.get("sources", [])
            for s in raw_sources:
                if isinstance(s, dict):
                    sources.append(s.get("source") or s.get("title") or str(s))
                else:
                    sources.append(str(s))
        else:
            answer = str(result)

        return {
            "answer": answer,
            "sources": sources,
            "context_used": result.get("context_used", False) if isinstance(result, dict) else False,
        }
    except Exception as e:
        logger.error(f"Document ask error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to answer question: {str(e)}")


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
            "google_oauth": {
                "login": "/api/v1/auth/google/login",
                "callback": "/api/v1/auth/google/callback",
                "status": "/api/v1/auth/google/status"
            },
            "notifications": {
                "my_notifications": "/api/v1/notifications/me",
                "my_medication_reminders": "/api/v1/notifications/me/medications",
                "create": "/api/v1/notifications/create",
                "create_medication_reminder": "/api/v1/notifications/medication-reminder",
                "send": "/api/v1/notifications/send/{notification_id}",
                "process_pending": "/api/v1/notifications/process-pending",
                "create_daily_reminders": "/api/v1/notifications/create-daily-reminders",
                "test_email": "/api/v1/notifications/test-email"
            },
            "medical_chatbot": {
                "chat": "/api/v1/chat",
                "embeddings": "/api/v1/embeddings/generate"
            },
            "document_processing": {
                "upload": "/api/v1/documents/upload",
                "search": "/api/v1/documents/search"
            },
            "dashboard": {
                "family_overview": "/api/v1/dashboard/family/{family_id}",
                "member_detail": "/api/v1/dashboard/member/{user_id}",
                "create_event": "/api/v1/dashboard/events",
                "timeline": "/api/v1/dashboard/timeline/{user_id}",
                "risk_scores": "/api/v1/dashboard/risk/{user_id}",
                "condition_heatmap": "/api/v1/dashboard/family/{family_id}/conditions"
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

    # Check Notifications service
    if NOTIFICATIONS_AVAILABLE:
        health_status["services"]["notifications"] = "available"
    else:
        health_status["services"]["notifications"] = "unavailable"

    # Check Google Auth service
    if GOOGLE_AUTH_AVAILABLE:
        health_status["services"]["google_oauth"] = "available"
    else:
        health_status["services"]["google_oauth"] = "unavailable"

    # Check Notification Scheduler
    try:
        from app.services.notification_scheduler import notification_scheduler
        health_status["services"]["notification_scheduler"] = "running" if notification_scheduler.is_running() else "stopped"
    except Exception:
        health_status["services"]["notification_scheduler"] = "unavailable"

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
