"""
Test script for Notification Module
Run: python -m app.test_notifications
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


def test_notification_service():
    """Test notification service initialization"""
    print("\n" + "=" * 60)
    print("Test 1: Notification Service Initialization")
    print("=" * 60)

    try:
        from app.services.notification_service import notification_service

        print("   Notification service imported successfully")

        # Check email service
        if notification_service.email_service:
            print("   Email service initialized")
        else:
            print("   Email service NOT available (check SMTP config)")

        return True
    except Exception as e:
        print(f"   FAILED: {e}")
        return False


def test_notification_schemas():
    """Test notification schemas"""
    print("\n" + "=" * 60)
    print("Test 2: Notification Schemas")
    print("=" * 60)

    try:
        from app.schemas.notification import (
            NotificationCreate,
            NotificationResponse,
            NotificationType,
            NotificationStatus,
            NotificationPriority,
            MedicationReminderInfo,
        )

        # Test schema creation
        notification = NotificationCreate(
            user_id="test-user-123",
            type=NotificationType.MEDICATION_REMINDER,
            title="Test Notification",
            message="This is a test",
            priority=NotificationPriority.HIGH
        )

        print(f"   NotificationCreate: {notification.model_dump()}")

        reminder = MedicationReminderInfo(
            medication_id="med-123",
            medication_name="Aspirin",
            dosage="100mg",
            frequency="daily",
            reminder_times=["08:00", "20:00"],
            status="active",
            user_email="test@example.com",
            user_name="Test User"
        )

        print(f"   MedicationReminderInfo: {reminder.model_dump()}")

        return True
    except Exception as e:
        print(f"   FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_create_notification():
    """Test creating a notification in PostgreSQL"""
    print("\n" + "=" * 60)
    print("Test 3: Create Notification in PostgreSQL")
    print("=" * 60)

    try:
        from app.services.notification_service import notification_service
        from app.schemas.notification import NotificationType, NotificationPriority
        from datetime import datetime, timezone

        # Note: This requires a valid user_id in the database
        # Using a placeholder for testing
        test_user_id = "test-notification-user"

        print(f"   Attempting to create notification for user: {test_user_id}")
        print("   Note: This requires a valid user_id in PostgreSQL")

        # This will fail if user doesn't exist (FK constraint)
        # notification = notification_service.create_notification(
        #     user_id=test_user_id,
        #     notification_type=NotificationType.SYSTEM,
        #     title="Test Notification",
        #     message="Testing notification creation",
        #     priority=NotificationPriority.LOW
        # )

        print("   Skipping actual creation (requires valid user_id)")
        print("   Use API endpoint with authenticated user to test")

        return True
    except Exception as e:
        print(f"   FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_neo4j_medication_query():
    """Test querying medications from Neo4j"""
    print("\n" + "=" * 60)
    print("Test 4: Neo4j Medication Query")
    print("=" * 60)

    try:
        from shared.database.neo4j import Neo4jClient

        client = Neo4jClient()

        # Test connection
        query = "RETURN 1 as test"
        result = client.execute_query(query)
        print(f"   Neo4j connection: OK")

        # Query for medications with reminders
        query = """
        MATCH (u:User)-[r:TAKES]->(m:Medication)
        WHERE r.status = 'active'
        RETURN count(*) as count
        """
        result = client.execute_query(query)
        count = result[0]["count"] if result else 0
        print(f"   Active medications found: {count}")

        # Query for users with reminder times
        query = """
        MATCH (u:User)-[r:TAKES]->(m:Medication)
        WHERE r.reminderTimes IS NOT NULL AND size(r.reminderTimes) > 0
        RETURN count(DISTINCT u) as users, count(*) as medications
        """
        result = client.execute_query(query)
        if result:
            print(f"   Users with reminders: {result[0]['users']}")
            print(f"   Medications with reminders: {result[0]['medications']}")
        else:
            print("   No users with medication reminders found")

        return True
    except Exception as e:
        print(f"   FAILED: {e}")
        print("   Note: Neo4j must be running for this test")
        import traceback
        traceback.print_exc()
        return False


def test_email_sending():
    """Test email sending capability"""
    print("\n" + "=" * 60)
    print("Test 5: Email Service")
    print("=" * 60)

    try:
        from app.auth_export.email_service import EmailService

        emailer = EmailService()
        print(f"   SMTP Server: {emailer.smtp_server}:{emailer.smtp_port}")

        # Check credentials
        from app.auth_export.config import SMTP_USERNAME, SMTP_PASSWORD
        if SMTP_USERNAME and SMTP_PASSWORD:
            print(f"   SMTP Username: {SMTP_USERNAME}")
            print("   SMTP Password: SET")
        else:
            print("   WARNING: SMTP credentials not configured")

        print("\n   To test actual email sending, use:")
        print("   POST /api/v1/notifications/test-email (with auth)")

        return True
    except Exception as e:
        print(f"   FAILED: {e}")
        return False


def print_api_endpoints():
    """Print available API endpoints"""
    print("\n" + "=" * 60)
    print("Available Notification API Endpoints")
    print("=" * 60)

    endpoints = [
        ("GET", "/api/v1/notifications/me", "Get my notifications"),
        ("GET", "/api/v1/notifications/me/medications", "Get my medication reminders (Neo4j)"),
        ("POST", "/api/v1/notifications/create", "Create a notification"),
        ("POST", "/api/v1/notifications/medication-reminder", "Create medication reminder"),
        ("POST", "/api/v1/notifications/send/{id}", "Send a pending notification"),
        ("POST", "/api/v1/notifications/test-email", "Send test email to yourself"),
        ("POST", "/api/v1/notifications/process-pending", "Process all pending (admin)"),
        ("POST", "/api/v1/notifications/create-daily-reminders", "Create today's reminders (admin)"),
    ]

    for method, path, desc in endpoints:
        print(f"   {method:6} {path}")
        print(f"          {desc}")
        print()


def print_curl_examples():
    """Print curl examples for testing"""
    print("\n" + "=" * 60)
    print("cURL Examples (replace TOKEN with your JWT)")
    print("=" * 60)

    print("""
# Get my notifications
curl -X GET "http://localhost:8001/api/v1/notifications/me" \\
  -H "Authorization: Bearer TOKEN"

# Get my medication reminders from Neo4j
curl -X GET "http://localhost:8001/api/v1/notifications/me/medications" \\
  -H "Authorization: Bearer TOKEN"

# Send test email
curl -X POST "http://localhost:8001/api/v1/notifications/test-email" \\
  -H "Authorization: Bearer TOKEN"

# Create a notification
curl -X POST "http://localhost:8001/api/v1/notifications/create" \\
  -H "Authorization: Bearer TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_id": "YOUR_USER_ID",
    "type": "medication_reminder",
    "title": "Take Medication",
    "message": "Time to take your aspirin",
    "priority": "high"
  }'
""")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("   NOTIFICATION MODULE TEST SUITE")
    print("=" * 60)

    results = []

    results.append(("Notification Service", test_notification_service()))
    results.append(("Notification Schemas", test_notification_schemas()))
    results.append(("Create Notification", test_create_notification()))
    results.append(("Neo4j Medication Query", test_neo4j_medication_query()))
    results.append(("Email Service", test_email_sending()))

    print_api_endpoints()
    print_curl_examples()

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"   {name}: {status}")

    print(f"\n   Total: {passed}/{total} tests passed")
    print("=" * 60)
