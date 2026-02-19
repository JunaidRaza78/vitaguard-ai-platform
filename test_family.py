#!/usr/bin/env python3
"""Test family endpoints and data"""
import sys
sys.path.insert(0, '/Users/junaidraza/Documents/Projects/agentic-ai-family-health-manager/Backend')

from shared.database.neo4j.neo4j_client import Neo4jClient
import requests

def check_neo4j_family():
    """Check family data in Neo4j"""
    print("=" * 60)
    print("Checking Neo4j Family Data")
    print("=" * 60)

    client = Neo4jClient()
    user_id = "a2a3d05f-f971-400d-a885-b0190ce765bf"

    with client.get_session() as session:
        # Check for family membership
        result = session.run("""
            MATCH (u:User {userId: $userId})-[:MEMBER_OF]->(f:Family)
            RETURN f.familyId as familyId, f.name as familyName
        """, userId=user_id)

        family = result.single()
        if family:
            family_id = family['familyId']
            print(f"✅ User is member of family: {family['familyName']}")
            print(f"   Family ID: {family_id}")

            # Check family members
            result = session.run("""
                MATCH (f:Family {familyId: $familyId})<-[:MEMBER_OF]-(member:User)
                RETURN member.userId as userId, member.name as name, member.email as email
            """, familyId=family_id)

            members = list(result)
            print(f"\n✅ Family has {len(members)} members:")
            for m in members:
                print(f"   - {m['name']} ({m['email']})")

            return family_id
        else:
            print("❌ User is NOT member of any family!")
            return None

def test_family_api(family_id):
    """Test family API endpoints"""
    print("\n" + "=" * 60)
    print("Testing Family API Endpoints")
    print("=" * 60)

    BASE_URL = "http://127.0.0.1:8000"

    # Login
    print("\n🔑 Logging in...")
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "Test1234!"
    })

    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        return

    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful!")

    # Test family members endpoint
    print(f"\n👨‍👩‍👧‍👦 Testing GET /api/v1/family/members...")
    response = requests.get(f"{BASE_URL}/api/v1/family/members", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Members: {len(data.get('members', []))}")
        for m in data.get('members', [])[:3]:
            print(f"   - {m.get('name')}")
    else:
        print(f"❌ Error: {response.text}")

    # Test family health dashboard
    if family_id:
        print(f"\n🏥 Testing GET /api/v1/dashboard/family/{family_id}...")
        response = requests.get(f"{BASE_URL}/api/v1/dashboard/family/{family_id}", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Family dashboard loaded")
        else:
            print(f"❌ Error: {response.text}")

if __name__ == "__main__":
    family_id = check_neo4j_family()
    test_family_api(family_id)