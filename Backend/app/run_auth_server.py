#!/usr/bin/env python3
"""
Startup script for Family Health Manager Authentication Service
Runs the FastAPI authentication API server
"""

import sys
import os
from pathlib import Path

# Add Backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import uvicorn
from dotenv import load_dotenv

# Load environment variables
env_path = backend_dir.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print(f"✅ Loaded environment from: {env_path}")
else:
    print(f"⚠️  No .env file found at: {env_path}")

def main():
    """Main entry point for authentication server"""

    # Get configuration from environment
    host = os.getenv("AUTH_HOST", "0.0.0.0")
    port = int(os.getenv("AUTH_PORT", "8001"))
    reload = os.getenv("ENVIRONMENT", "development") == "development"
    log_level = os.getenv("LOG_LEVEL", "info").lower()

    print("=" * 60)
    print("🔐 Family Health Manager - Authentication Service")
    print("=" * 60)
    print(f"📡 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"🔄 Auto-reload: {reload}")
    print(f"📝 Log level: {log_level}")
    print("=" * 60)
    print()
    print("📚 API Documentation:")
    print(f"   - Swagger UI: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/docs")
    print(f"   - ReDoc: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/redoc")
    print()
    print("🔗 Endpoints:")
    print(f"   - Register: POST /api/v1/auth/register")
    print(f"   - Login: POST /api/v1/auth/login")
    print(f"   - Refresh Token: POST /api/v1/auth/refresh")
    print(f"   - Get Profile: GET /api/v1/auth/me")
    print(f"   - Health Check: GET /health")
    print("=" * 60)
    print()

    # Run server
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
        access_log=True
    )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Authentication service stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error starting authentication service: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
