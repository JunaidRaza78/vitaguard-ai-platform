#!/usr/bin/env python3
"""Comprehensive API test"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_all_endpoints():
    print("=" * 70)
    print("COMPREHENSIVE API TEST")
    print("=" * 70)

    # 1. Login
    print("\n[1/7] Testing Login...")
    r = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "Test1234!"
    })
    if r.status_code != 200:
        print(f"   ❌ Login failed: {r.status_code} - {r.text}")
        return

    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"   ✅ Login successful")

    # 2. Lab History
    print("\n[2/7] Testing Lab History...")
    r = requests.get(f"{BASE_URL}/api/v1/labs/history", headers=headers)
    if r.status_code == 200:
        data = r.json()
        print(f"   ✅ Lab history: {data.get('total', 0)} reports")
        if data.get('history'):
            first = data['history'][0]
            print(f"      First report date: {first.get('date')}")
            print(f"      Tests: {len(first.get('results', []))}")
    else:
        print(f"   ❌ Failed: {r.status_code} - {r.text[:200]}")

    # 3. Families (/me)
    print("\n[3/7] Testing Families (/me)...")
    r = requests.get(f"{BASE_URL}/api/v1/families/me", headers=headers)
    if r.status_code == 200:
        data = r.json()
        families = data.get('families', [])
        print(f"   ✅ User families: {len(families)}")
        if families:
            print(f"      First family: {families[0].get('name')} (ID: {families[0].get('familyId')})")
    else:
        print(f"   ❌ Failed: {r.status_code} - {r.text[:200]}")

    # 4. Family Members
    print("\n[4/7] Testing Family Members...")
    # Get the Khan Family (last in the list, or use family-001)
    family_id = "family-001"  # The Khan Family from seed
    r = requests.get(f"{BASE_URL}/api/v1/families/{family_id}/members", headers=headers)
    if r.status_code == 200:
        data = r.json()
        members = data.get('members', [])
        print(f"   ✅ Family members: {len(members)}")
        for m in members[:3]:
            print(f"      - {m.get('name')} ({m.get('role', 'unknown')})")
    else:
        print(f"   ❌ Failed: {r.status_code} - {r.text[:200]}")

    # 5. Upcoming Notifications
    print("\n[5/7] Testing Upcoming Notifications...")
    r = requests.get(f"{BASE_URL}/api/v1/notifications/me/upcoming", headers=headers)
    if r.status_code == 200:
        data = r.json()
        print(f"   ✅ Upcoming notifications: {data.get('total', 0)}")
        for n in data.get('notifications', [])[:3]:
            print(f"      - {n.get('title')} ({n.get('type')})")
    else:
        print(f"   ❌ Failed: {r.status_code} - {r.text[:200]}")

    # 6. Dashboard
    print("\n[6/7] Testing Dashboard...")
    user_id = "a2a3d05f-f971-400d-a885-b0190ce765bf"
    r = requests.get(f"{BASE_URL}/api/v1/dashboard/member/{user_id}", headers=headers)
    if r.status_code == 200:
        print(f"   ✅ Dashboard loaded")
    else:
        print(f"   ❌ Failed: {r.status_code} - {r.text[:200]}")

    # 7. Vitals
    print("\n[7/7] Testing Vitals...")
    r = requests.get(f"{BASE_URL}/api/v1/vitals", headers=headers)
    if r.status_code == 200:
        data = r.json()
        print(f"   ✅ Vitals: {len(data.get('vitals', []))} records")
    else:
        print(f"   ❌ Failed: {r.status_code} - {r.text[:200]}")

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    test_all_endpoints()