#!/usr/bin/env python3
"""Test family endpoint with detailed error info"""
import sys
sys.path.insert(0, '/Users/junaidraza/Documents/Projects/agentic-ai-family-health-manager/Backend')

from app.schemas.family import FamilyResponse, FamilyListResponse
from shared.database.neo4j.operations.family_ops import FamilyOperations

def test_endpoint_logic():
    user_id = "a2a3d05f-f971-400d-a885-b0190ce765bf"

    try:
        ops = FamilyOperations()
        results = ops.get_user_families(user_id)
        print(f"✅ Got {len(results)} family results from Neo4j")

        families = []
        for i, item in enumerate(results):
            print(f"\n--- Processing family {i+1} ---")
            f = item.get("family", {})
            print(f"Family data: {f}")

            try:
                family_response = FamilyResponse(
                    familyId=f.get("familyId", ""),
                    name=f.get("name", ""),
                    createdBy=str(f.get("createdBy") or ""),
                    createdAt=str(f.get("createdAt") or ""),
                )
                families.append(family_response)
                print(f"✅ Created FamilyResponse for: {f.get('name')}")
            except Exception as e:
                print(f"❌ Error creating FamilyResponse: {e}")
                raise

        print(f"\n✅ Created {len(families)} FamilyResponse objects")

        # Try to create the list response
        list_response = FamilyListResponse(families=families, total=len(families))
        print(f"✅ Created FamilyListResponse: total={list_response.total}")

        # Try to serialize to JSON
        json_data = list_response.model_dump()
        print(f"✅ Serialized to JSON: {len(json_data['families'])} families")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_endpoint_logic()