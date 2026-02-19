#!/usr/bin/env python3
"""Test FamilyOperations directly"""
import sys
sys.path.insert(0, '/Users/junaidraza/Documents/Projects/agentic-ai-family-health-manager/Backend')

from shared.database.neo4j.operations.family_ops import FamilyOperations

def test_get_user_families():
    user_id = "a2a3d05f-f971-400d-a885-b0190ce765bf"

    try:
        ops = FamilyOperations()
        print(f"Testing get_user_families for {user_id}...")
        results = ops.get_user_families(user_id)

        print(f"Results type: {type(results)}")
        print(f"Results length: {len(results)}")

        if results:
            print(f"\nFirst result:")
            print(f"  Keys: {results[0].keys()}")
            print(f"  Data: {results[0]}")

            family = results[0].get("family", {})
            print(f"\nFamily object type: {type(family)}")
            if hasattr(family, '__dict__'):
                print(f"Family attributes: {family.__dict__}")
            else:
                print(f"Family data: {family}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_get_user_families()