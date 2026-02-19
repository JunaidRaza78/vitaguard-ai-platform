#!/usr/bin/env python3
"""Check what's in Neo4j for lab results"""
import sys
sys.path.insert(0, '/Users/junaidraza/Documents/Projects/agentic-ai-family-health-manager/Backend')

from shared.database.neo4j.neo4j_client import Neo4jClient

client = Neo4jClient()
user_id = "a2a3d05f-f971-400d-a885-b0190ce765bf"

with client.get_session() as session:
    # Get recent lab results
    result = session.run("""
        MATCH (u:User {userId: $userId})-[:HAS_LAB_RESULT]->(lr:LabResult)
        RETURN lr.testName as testName, lr.resultValue as value,
               lr.date as date, lr.unit as unit
        ORDER BY lr.date DESC
        LIMIT 20
    """, userId=user_id)

    records = list(result)
    print(f"Found {len(records)} lab results:\n")

    for i, r in enumerate(records[:10], 1):
        print(f"{i}. Test: '{r['testName']}' | Value: {r['value']} | Date: {r['date']}")