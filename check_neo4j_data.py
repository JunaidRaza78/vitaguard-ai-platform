#!/usr/bin/env python3
"""
Quick script to check what data exists in Neo4j for test user
"""
import sys
sys.path.insert(0, '/Users/junaidraza/Documents/Projects/agentic-ai-family-health-manager/Backend')

from shared.database.neo4j.neo4j_client import Neo4jClient

def check_data():
    client = Neo4jClient()
    user_id = "a2a3d05f-f971-400d-a885-b0190ce765bf"

    with client.get_session() as session:
        # Check for User node
        result = session.run("""
            MATCH (u:User {userId: $userId})
            RETURN u.name as name, u.email as email
        """, userId=user_id)
        user = result.single()
        if user:
            print(f"✅ User found: {user['name']} ({user['email']})")
        else:
            print(f"❌ User NOT found in Neo4j!")
            return

        # Check for VitalSign nodes
        result = session.run("""
            MATCH (u:User {userId: $userId})-[:HAS_VITAL]->(v:VitalSign)
            RETURN count(v) as count
        """, userId=user_id)
        count = result.single()["count"]
        print(f"Vitals: {count}")

        # Check for Medication nodes
        result = session.run("""
            MATCH (u:User {userId: $userId})-[:TAKES]->(m:Medication)
            RETURN count(m) as count
        """, userId=user_id)
        count = result.single()["count"]
        print(f"Medications: {count}")

        # Check for LabResult nodes
        result = session.run("""
            MATCH (u:User {userId: $userId})-[:HAS_LAB_RESULT]->(lr:LabResult)
            RETURN count(lr) as count
        """, userId=user_id)
        count = result.single()["count"]
        print(f"Lab Results: {count}")

        # Check for Condition nodes
        result = session.run("""
            MATCH (u:User {userId: $userId})-[:HAS_CONDITION]->(c:Condition)
            RETURN count(c) as count
        """, userId=user_id)
        count = result.single()["count"]
        print(f"Conditions: {count}")

        # Check family relationships
        result = session.run("""
            MATCH (u:User {userId: $userId})-[r]-(other:User)
            WHERE type(r) IN ['PARENT_OF', 'SIBLING_OF', 'SPOUSE_OF']
            RETURN count(DISTINCT other) as count
        """, userId=user_id)
        count = result.single()["count"]
        print(f"Family Members: {count}")

if __name__ == "__main__":
    check_data()