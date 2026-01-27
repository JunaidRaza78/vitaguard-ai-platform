"""
Family Health Manager - Authentication Service
Main FastAPI application for user authentication and management
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import time

from app.api.auth import router as auth_router
from shared.database.postgres.postgres_client import PostgresClient
from shared.logging.logger import setup_logger

# Setup logging
logger = setup_logger(__name__)

# Database client
postgres_client = PostgresClient()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager - handles startup and shutdown events
    """
    # Startup
    logger.info("🚀 Starting Family Health Manager - Authentication Service")

    try:
        # Initialize database connection
        await postgres_client.connect()
        logger.info("✅ PostgreSQL connected successfully")
    except Exception as e:
        logger.error(f"❌ Failed to connect to PostgreSQL: {e}")
        raise

    yield

    # Shutdown
    logger.info("🛑 Shutting down Authentication Service")
    try:
        await postgres_client.disconnect()
        logger.info("✅ PostgreSQL disconnected successfully")
    except Exception as e:
        logger.error(f"❌ Error disconnecting PostgreSQL: {e}")


# Create FastAPI application
app = FastAPI(
    title="Family Health Manager - Auth API",
    description="Authentication and user management API for Family Health Manager",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)


# ==========================================
# MIDDLEWARE
# ==========================================

# CORS Middleware - Allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted Host Middleware - Prevent Host header attacks
# app.add_middleware(
#     TrustedHostMiddleware,
#     allowed_hosts=["localhost", "127.0.0.1", "*.yourdomain.com"]
# )


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
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Validation error",
            "details": exc.errors()
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
# ROUTERS
# ==========================================

# Include authentication router
app.include_router(auth_router)


# ==========================================
# ROOT ENDPOINTS
# ==========================================

@app.get(
    "/",
    tags=["Root"],
    summary="API Root",
    description="Get API information and status"
)
async def root():
    """Root endpoint - API information"""
    return {
        "service": "Family Health Manager - Authentication API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "register": "/api/v1/auth/register",
            "login": "/api/v1/auth/login",
            "refresh": "/api/v1/auth/refresh",
            "logout": "/api/v1/auth/logout",
            "profile": "/api/v1/auth/me",
            "verify_email": "/api/v1/auth/verify-email",
            "forgot_password": "/api/v1/auth/forgot-password",
            "reset_password": "/api/v1/auth/reset-password",
            "change_password": "/api/v1/auth/change-password"
        }
    }


@app.get(
    "/health",
    tags=["Health"],
    summary="Health Check",
    description="Check service health and database connectivity"
)
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "service": "auth-api",
        "timestamp": time.time()
    }

    # Check PostgreSQL connection
    try:
        await postgres_client.execute("SELECT 1")
        health_status["database"] = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["database"] = "disconnected"
        health_status["status"] = "unhealthy"
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
        await postgres_client.execute("SELECT 1")
        return {"ready": True, "service": "auth-api"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"ready": False, "service": "auth-api", "error": str(e)}
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
