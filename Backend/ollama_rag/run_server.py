#!/usr/bin/env python3
"""
Run script for Medical RAG Chatbot API
Production-safe launcher
"""

import sys
from pathlib import Path
import argparse
import uvicorn

# ------------------------------------------------------------------
# PATH SETUP
# ------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent
CHROMA_DIR = PROJECT_ROOT / "shared" / "database" / "chroma"

# Add paths safely - SCRIPT_DIR MUST be first to avoid chroma/api.py conflict
sys.path.insert(0, str(CHROMA_DIR))        # query_by_agent (add last, search first from end)
sys.path.insert(0, str(PROJECT_ROOT))      # backend.*
sys.path.insert(0, str(SCRIPT_DIR))        # api.py (FIRST priority)

# ------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------
def main():
    print("=" * 60)
    print("Medical RAG Chatbot API")
    print("=" * 60)
    print(f"Script dir     : {SCRIPT_DIR}")
    print(f"Project root   : {PROJECT_ROOT}")
    print(f"ChromaDB dir   : {CHROMA_DIR}")
    print("=" * 60)

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    uvicorn.run(
        "api:app",          # 🔥 Let uvicorn import normally
        host="0.0.0.0",
        port=args.port,
        reload=args.reload,
        log_level="info"
    )


if __name__ == "__main__":
    main()
