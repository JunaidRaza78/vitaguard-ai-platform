#!/usr/bin/env python3
"""
Family Health Manager - Unified API Server
Startup script for the combined Authentication + Medical RAG Chatbot API
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Get Backend directory
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# CRITICAL: Set PYTHONPATH so uvicorn's reload subprocess inherits the path
# Without this, the subprocess can't find modules when reload=True
existing_pythonpath = os.environ.get('PYTHONPATH', '')
if str(backend_dir) not in existing_pythonpath:
    os.environ['PYTHONPATH'] = str(backend_dir) + (os.pathsep + existing_pythonpath if existing_pythonpath else '')

# Load environment variables
env_path = backend_dir.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print(f"✅ Loaded environment from: {env_path}")
else:
    print(f"⚠️  No .env file found at: {env_path}")
    print(f"   Using default configuration")

import uvicorn


def print_banner():
    """Print startup banner with configuration"""
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("ENVIRONMENT", "development") == "development"
    log_level = os.getenv("LOG_LEVEL", "info").lower()

    base_url = f"http://{host if host != '0.0.0.0' else 'localhost'}:{port}"

    print()
    print("=" * 70)
    print("🏥 FAMILY HEALTH MANAGER - UNIFIED API")
    print("=" * 70)
    print()
    print("📊 Configuration:")
    print(f"   📡 Host: {host}")
    print(f"   🔌 Port: {port}")
    print(f"   🔄 Auto-reload: {reload}")
    print(f"   📝 Log level: {log_level}")
    print(f"   🌍 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print()
    print("=" * 70)
    print("📚 API DOCUMENTATION")
    print("=" * 70)
    print(f"   🔗 Swagger UI: {base_url}/docs")
    print(f"   🔗 ReDoc: {base_url}/redoc")
    print(f"   🔗 Health Check: {base_url}/health")
    print()
    print("=" * 70)
    print("🔐 AUTHENTICATION ENDPOINTS")
    print("=" * 70)
    print(f"   POST {base_url}/api/v1/auth/register")
    print(f"   POST {base_url}/api/v1/auth/login")
    print(f"   POST {base_url}/api/v1/auth/refresh")
    print(f"   POST {base_url}/api/v1/auth/logout")
    print(f"   GET  {base_url}/api/v1/auth/me")
    print(f"   PATCH {base_url}/api/v1/auth/me")
    print(f"   POST {base_url}/api/v1/auth/verify-email")
    print(f"   POST {base_url}/api/v1/auth/change-password")
    print(f"   POST {base_url}/api/v1/auth/forgot-password")
    print(f"   POST {base_url}/api/v1/auth/reset-password")
    print()
    print("=" * 70)
    print("🤖 MEDICAL CHATBOT ENDPOINTS")
    print("=" * 70)
    print(f"   POST {base_url}/api/v1/chat")
    print(f"   POST {base_url}/api/v1/embeddings/generate")
    print()
    print("=" * 70)
    print("💡 QUICK START")
    print("=" * 70)
    print(f"   1. Register a user:")
    print(f"      curl -X POST {base_url}/api/v1/auth/register \\")
    print(f"        -H 'Content-Type: application/json' \\")
    print(f"        -d '{{'")
    print(f"          \"email\": \"user@example.com\",")
    print(f"          \"username\": \"johndoe\",")
    print(f"          \"password\": \"SecurePass123!\",")
    print(f"          \"first_name\": \"John\",")
    print(f"          \"last_name\": \"Doe\"")
    print(f"        }}'")
    print()
    print(f"   2. Login:")
    print(f"      curl -X POST {base_url}/api/v1/auth/login \\")
    print(f"        -H 'Content-Type: application/json' \\")
    print(f"        -d '{{'")
    print(f"          \"email\": \"user@example.com\",")
    print(f"          \"password\": \"SecurePass123!\"")
    print(f"        }}'")
    print()
    print(f"   3. Chat with medical AI:")
    print(f"      curl -X POST {base_url}/api/v1/chat \\")
    print(f"        -H 'Content-Type: application/json' \\")
    print(f"        -d '{{'")
    print(f"          \"message\": \"I have a headache and fever\",")
    print(f"          \"user_id\": \"user123\"")
    print(f"        }}'")
    print()
    print("=" * 70)
    print("🔧 REQUIRED SERVICES")
    print("=" * 70)
    print("   ✓ PostgreSQL (port 5432) - User data & chat history")
    print("   ✓ Ollama (port 11434) - DeepSeek R1:8b model")
    print("   ○ Redis (port 6379) - Optional caching")
    print("   ○ Neo4j (port 7687) - Optional graph database")
    print()
    print("   Start services: docker compose up -d postgres")
    print("=" * 70)
    print()
    print("🚀 Starting server...")
    print()


def main():
    """Main entry point for unified API server"""

    # Print banner
    print_banner()

    # Get configuration from environment
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("ENVIRONMENT", "development") == "development"
    log_level = os.getenv("LOG_LEVEL", "info").lower()

    # Run server
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
        access_log=True,
        server_header=False,
        date_header=False
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n" + "=" * 70)
        print("👋 Server stopped by user")
        print("=" * 70)
        sys.exit(0)
    except Exception as e:
        print("\n\n" + "=" * 70)
        print(f"❌ Error starting server: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        sys.exit(1)
