#!/usr/bin/env python3
"""Quick test to verify the unified API can be imported"""

import sys
from pathlib import Path

# Add Backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

print("Testing unified API import...")
print("=" * 50)

try:
    # Test main app import
    print("1. Importing main FastAPI app...")
    from main import app
    print("   ✅ Main app imported successfully")

    # Check app title
    print(f"   📝 App title: {app.title}")
    print(f"   📝 Version: {app.version}")

    # Count routes
    routes = [route for route in app.routes]
    print(f"   📝 Total routes: {len(routes)}")

    # List some key endpoints
    print("\n2. Checking key endpoints...")
    endpoint_paths = [route.path for route in app.routes if hasattr(route, 'path')]

    auth_endpoints = [p for p in endpoint_paths if '/auth/' in p]
    chat_endpoints = [p for p in endpoint_paths if '/chat' in p]

    print(f"   ✅ Authentication endpoints: {len(auth_endpoints)}")
    for ep in auth_endpoints[:5]:
        print(f"      - {ep}")
    if len(auth_endpoints) > 5:
        print(f"      ... and {len(auth_endpoints) - 5} more")

    print(f"   ✅ Chat endpoints: {len(chat_endpoints)}")
    for ep in chat_endpoints:
        print(f"      - {ep}")

    print("\n3. Checking health endpoints...")
    health_endpoints = [p for p in endpoint_paths if 'health' in p or 'ready' in p]
    for ep in health_endpoints:
        print(f"   ✅ {ep}")

    print("\n" + "=" * 50)
    print("✅ All imports successful!")
    print("=" * 50)
    print("\n🚀 Ready to start server with:")
    print("   python3 run_server.py")
    print()

except ImportError as e:
    print(f"\n❌ Import Error: {e}")
    print("\nMissing dependencies? Install with:")
    print("   pip install -r requirements.txt")
    sys.exit(1)

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
