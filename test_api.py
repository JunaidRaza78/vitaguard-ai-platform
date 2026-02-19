#!/usr/bin/env python3
"""Test the lab history API endpoint"""
import requests

BASE_URL = "http://127.0.0.1:8000"

# Step 1: Login
print("🔑 Logging in...")
response = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
    "email": "test@example.com",
    "password": "Test1234!"
})

if response.status_code != 200:
    print(f"❌ Login failed: {response.status_code}")
    print(response.text)
    exit(1)

data = response.json()
access_token = data.get("access_token")
print(f"✅ Login successful! Token: {access_token[:20]}...")

# Step 2: Get lab history
print("\n📊 Fetching lab history...")
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(f"{BASE_URL}/api/v1/labs/history", headers=headers)

if response.status_code != 200:
    print(f"❌ Failed: {response.status_code}")
    print(response.text)
else:
    data = response.json()
    print(f"✅ Success!")
    print(f"Total reports: {data.get('total', 0)}")
    if data.get('history'):
        print(f"First report date: {data['history'][0].get('date')}")
        print(f"Tests in first report: {len(data['history'][0].get('results', []))}")

# Step 3: Get notifications
print("\n🔔 Fetching notifications...")
response = requests.get(f"{BASE_URL}/api/v1/notifications/me", headers=headers)
if response.status_code == 200:
    data = response.json()
    print(f"✅ Notifications: {data.get('total', 0)}")
else:
    print(f"❌ Failed: {response.status_code}")

# Step 4: Get upcoming notifications
print("\n⏰ Fetching upcoming notifications...")
response = requests.get(f"{BASE_URL}/api/v1/notifications/me/upcoming", headers=headers)
if response.status_code == 200:
    data = response.json()
    print(f"✅ Upcoming notifications: {data.get('total', 0)}")
else:
    print(f"❌ Failed: {response.status_code}")
    print(response.text)

# Step 5: Get dashboard
print("\n📈 Fetching dashboard...")
response = requests.get(f"{BASE_URL}/api/v1/dashboard/member/a2a3d05f-f971-400d-a885-b0190ce765bf", headers=headers)
if response.status_code == 200:
    print(f"✅ Dashboard loaded")
else:
    print(f"❌ Failed: {response.status_code}")
    print(response.text)