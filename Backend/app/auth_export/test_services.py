"""
Test script for auth_export services
Run: python test_services.py
"""

import logging
logging.basicConfig(level=logging.INFO)

# Test 1: Config Loading
print("\n=== Test 1: Config Loading ===")
try:
    from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, SMTP_USERNAME, SMTP_PASSWORD
    print(f"✓ GOOGLE_CLIENT_ID: {'*' * 10}...{GOOGLE_CLIENT_ID[-4:] if GOOGLE_CLIENT_ID else 'MISSING'}")
    print(f"✓ GOOGLE_CLIENT_SECRET: {'SET' if GOOGLE_CLIENT_SECRET else 'MISSING'}")
    print(f"✓ SMTP_USERNAME: {SMTP_USERNAME if SMTP_USERNAME else 'MISSING'}")
    print(f"✓ SMTP_PASSWORD: {'SET' if SMTP_PASSWORD else 'MISSING'}")
except Exception as e:
    print(f"✗ Config Error: {e}")

# Test 2: Google Auth Initialization
print("\n=== Test 2: Google Auth Init ===")
try:
    from google_auth import GoogleAuth
    google_auth = GoogleAuth()
    oauth = google_auth.get_oauth()
    print("✓ GoogleAuth initialized successfully")
    print(f"✓ OAuth client: {oauth}")
except Exception as e:
    print(f"✗ GoogleAuth Error: {e}")

# Test 3: Email Service Initialization
print("\n=== Test 3: Email Service Init ===")
try:
    from email_service import EmailService
    emailer = EmailService()
    print("✓ EmailService initialized successfully")
    print(f"✓ SMTP Server: {emailer.smtp_server}:{emailer.smtp_port}")
except Exception as e:
    print(f"✗ EmailService Error: {e}")

# Test 4: Send Test Email (uncomment to test)
print("\n=== Test 4: Send Test Email ===")
print("To test email sending, uncomment the code below and set your email:")
print("""
# emailer = EmailService()
# success = emailer.send_email(
#     to_email="your_email@example.com",
#     subject="Test Email from Health App",
#     body="<h1>Hello!</h1><p>This is a test email.</p>"
# )
# print(f"Email sent: {success}")
""")

print("\n=== All Basic Tests Complete ===")
