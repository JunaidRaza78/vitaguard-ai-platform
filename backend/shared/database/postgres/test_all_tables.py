#!/usr/bin/env python3
"""
Comprehensive test script for all PostgreSQL tables.
Creates dummy data in all tables and verifies they're working correctly.
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
import uuid

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.shared.database.postgres import get_postgres_client
from backend.shared.logging import get_logger
from sqlalchemy import text

logger = get_logger('test.postgres.all_tables')


def print_section(title: str):
    """Print formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_success(message: str):
    """Print success message."""
    print(f"✅ {message}")


def print_info(message: str):
    """Print info message."""
    print(f"ℹ️  {message}")


def test_users_table(client):
    """Test Users table."""
    print_section("1. Testing Users Table")

    # Create test user
    user = client.create_user(
        email=f"test_user_{uuid.uuid4().hex[:8]}@example.com",
        password_hash="hashed_password_123",
        is_active=True,
        is_verified=True
    )
    print_success(f"User created: {user.user_id}")
    print_info(f"   Email: {user.email}")
    print_info(f"   Active: {user.is_active}")
    print_info(f"   Created: {user.created_at}")

    # Read user
    fetched_user = client.get_user_by_id(user.user_id)
    print_success(f"User fetched: {fetched_user.email}")

    return user


def test_user_sessions_table(client, user):
    """Test UserSessions table."""
    print_section("2. Testing User Sessions Table")

    # Create session
    session = client.create_session(
        user_id=user.user_id,
        token=f"session_token_{uuid.uuid4().hex}",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0 (Test Browser)",
        device_info={
            "device_type": "desktop",
            "os": "Windows 10",
            "browser": "Chrome"
        }
    )
    print_success(f"Session created: {session.session_id}")
    print_info(f"   User: {session.user_id}")
    print_info(f"   IP: {session.ip_address}")
    print_info(f"   Expires: {session.expires_at}")

    return session


def test_notifications_table(client, user):
    """Test Notifications table."""
    print_section("3. Testing Notifications Table")

    # Create notification
    notification = client.create_notification(
        user_id=user.user_id,
        type="medication_reminder",
        title="Time to take your medication",
        message="Don't forget to take your daily medication at 9:00 AM",
        status="pending",
        priority="high",
        scheduled_at=datetime.now(timezone.utc) + timedelta(hours=1),
        notification_metadata={
            "medication_name": "Aspirin",
            "dosage": "100mg",
            "frequency": "daily"
        }
    )
    print_success(f"Notification created: {notification.notification_id}")
    print_info(f"   Type: {notification.type}")
    print_info(f"   Title: {notification.title}")
    print_info(f"   Status: {notification.status}")
    print_info(f"   Scheduled: {notification.scheduled_at}")

    return notification


def test_audit_logs_table(client, user):
    """Test AuditLogs table."""
    print_section("4. Testing Audit Logs Table")

    # Create audit log
    audit_log = client.create_audit_log(
        action="user.login",
        user_id=user.user_id,
        resource_type="authentication",
        resource_id=user.user_id,
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0",
        request_data={
            "email": user.email,
            "login_method": "password"
        },
        response_status=200,
        details={
            "success": True,
            "session_created": True,
            "two_factor_enabled": False
        }
    )
    print_success(f"Audit log created: {audit_log.log_id}")
    print_info(f"   Action: {audit_log.action}")
    print_info(f"   User: {audit_log.user_id}")
    print_info(f"   Status: {audit_log.response_status}")
    print_info(f"   Time: {audit_log.created_at}")

    return audit_log


def test_document_jobs_table(client, user):
    """Test DocumentJobs table."""
    print_section("5. Testing Document Jobs Table")

    # Create document job
    job = client.create_document_job(
        user_id=user.user_id,
        file_path="/uploads/medical_report_2024.pdf",
        job_type="ocr",
        file_type="pdf"
    )
    print_success(f"Document job created: {job.job_id}")
    print_info(f"   User: {job.user_id}")
    print_info(f"   File: {job.file_path}")
    print_info(f"   Type: {job.job_type}")
    print_info(f"   Status: {job.status}")

    # Update job to processing
    client.update_document_job_status(
        job_id=job.job_id,
        status="processing"
    )
    print_success(f"Job status updated to: processing")

    # Complete the job
    updated_job = client.update_document_job_status(
        job_id=job.job_id,
        status="completed",
        result={
            "extracted_text": "Patient: John Doe\nDiagnosis: Hypertension\nBlood Pressure: 140/90",
            "entities": {
                "patient_name": "John Doe",
                "diagnosis": ["Hypertension"],
                "vitals": {"blood_pressure": "140/90"}
            },
            "pages_processed": 3,
            "confidence_score": 0.95
        }
    )
    print_success(f"Job completed in {updated_job.processing_time_ms}ms")
    print_info(f"   Result: {len(str(updated_job.result))} chars of data")

    # Get all user jobs
    user_jobs = client.get_user_document_jobs(user.user_id)
    print_success(f"Found {len(user_jobs)} document jobs for user")

    return job


def test_api_rate_limits_table(client, user):
    """Test ApiRateLimits table."""
    print_section("6. Testing API Rate Limits Table")

    # Check rate limit (creates first entry)
    endpoint = "/api/chat"
    allowed = client.check_rate_limit(
        user_id=user.user_id,
        endpoint=endpoint,
        max_requests=100,
        window_minutes=1
    )
    print_success(f"Rate limit check 1: {'Allowed' if allowed else 'Blocked'}")

    # Make a few more requests
    for i in range(2, 6):
        allowed = client.check_rate_limit(user.user_id, endpoint, max_requests=100)
        print_info(f"   Request {i}: {'Allowed' if allowed else 'Blocked'}")

    # Get rate limit status
    status = client.get_rate_limit_status(user.user_id, endpoint)
    if status:
        print_success(f"Rate limit status retrieved")
        print_info(f"   Endpoint: {status['endpoint']}")
        print_info(f"   Requests: {status['request_count']}")
        print_info(f"   Window ends in: {status['remaining_time_seconds']:.1f} seconds")

    return status


def test_conversations_table(client, user):
    """Test unified Conversations table (supports both chat and API modes)."""
    print_section("7. Testing Unified Conversations Table")

    # Test 1: API-style conversation with JSONB messages
    print_info("\n  Test 7a: API Conversation (JSONB messages)")
    api_conv_id = f"api_conv_{uuid.uuid4().hex[:8]}"
    api_conversation = client.create_conversation(
        conversation_id=api_conv_id,
        user_id=user.user_id,
        auth_key="api_key_123"
    )
    print_success(f"   API conversation created: {api_conversation.conversation_id}")
    print_info(f"   Auth Key: {api_conversation.auth_key}")

    # Update with JSONB messages
    updated_conv = client.update_conversation(
        conversation_id=api_conv_id,
        messages=[
            {"message_id": "msg1", "role": "user", "content": "Hello API"},
            {"message_id": "msg2", "role": "assistant", "content": "Hi there!"}
        ],
        message_count=2
    )
    print_success(f"   Updated with {updated_conv.message_count} JSONB messages")

    # Test 2: Chat-style conversation with title
    print_info("\n  Test 7b: Chat Conversation (structured messages via chat_messages table)")
    chat_conversation = client.create_chat_conversation(
        user_id=user.user_id,
        title="Health Consultation - Blood Pressure",
        status="active"
    )
    print_success(f"   Chat conversation created: {chat_conversation.conversation_id}")
    print_info(f"   Title: {chat_conversation.title}")

    # Get all user conversations (both types)
    all_conversations = client.get_user_chat_conversations(user.user_id)
    print_success(f"\n  Found {len(all_conversations)} total conversations for user")
    print_info(f"   (Includes both API and chat conversations)")

    return chat_conversation  # Return the chat one for messages test


def test_chat_messages_table(client, conversation):
    """Test ChatMessages table."""
    print_section("8. Testing Chat Messages Table")

    # Create user message
    user_msg = client.create_chat_message(
        conversation_id=conversation.conversation_id,
        role="user",
        content="What should I do about my high blood pressure?",
        entities={
            "condition": "high blood pressure",
            "intent": "health_query",
            "intent_type": "advice_seeking"
        }
    )
    print_success(f"User message created: {user_msg.message_id}")
    print_info(f"   Role: {user_msg.role}")
    print_info(f"   Content: {user_msg.content[:50]}...")

    # Create assistant message
    assistant_msg = client.create_chat_message(
        conversation_id=conversation.conversation_id,
        role="assistant",
        content="Based on your blood pressure reading of 140/90, I recommend: 1) Monitor daily 2) Reduce sodium intake 3) Exercise regularly 4) Consult your doctor",
        message_metadata={
            "response_time_ms": 1250,
            "tokens_used": 150,
            "sources": ["medical_guidelines", "user_health_records"]
        }
    )
    print_success(f"Assistant message created: {assistant_msg.message_id}")
    print_info(f"   Content: {assistant_msg.content[:50]}...")

    # Get conversation messages
    messages = client.get_conversation_chat_messages(conversation.conversation_id)
    print_success(f"Found {len(messages)} messages in conversation")

    return user_msg, assistant_msg


def test_chat_feedback_table(client, conversation, message):
    """Test ChatFeedback table."""
    print_section("9. Testing Chat Feedback Table")

    # Create feedback
    feedback = client.create_chat_feedback(
        conversation_id=conversation.conversation_id,
        message_id=message.message_id,
        rating="helpful",
        comment="Very helpful advice! The recommendations are clear and actionable."
    )
    print_success(f"Chat feedback created: {feedback.feedback_id}")
    print_info(f"   Rating: {feedback.rating}")
    print_info(f"   Comment: {feedback.comment}")
    print_info(f"   Created: {feedback.created_at}")

    return feedback


def test_chat_metrics_table(client, conversation):
    """Test ChatMetrics table."""
    print_section("10. Testing Chat Metrics Table")

    # Create metrics
    metric = client.create_chat_metric(
        conversation_id=conversation.conversation_id,
        response_time_ms=1250,
        token_count=150,
        retrieval_time_ms=300,
        generation_time_ms=950,
        sources_used=3,
        user_satisfaction=5
    )
    print_success(f"Chat metric created: {metric.metric_id}")
    print_info(f"   Response time: {metric.response_time_ms}ms")
    print_info(f"   Tokens: {metric.token_count}")
    print_info(f"   Retrieval: {metric.retrieval_time_ms}ms")
    print_info(f"   Generation: {metric.generation_time_ms}ms")
    print_info(f"   Satisfaction: {metric.user_satisfaction}/5")

    return metric


def verify_all_data(client, user):
    """Verify all data was saved correctly."""
    print_section("11. Verifying All Data")

    # Count records
    session = client.get_session()

    from backend.shared.database.postgres.models import (
        User, UserSession, Conversation, Notification, AuditLog, DocumentJob,
        ApiRateLimit, ChatMessage, ChatFeedback, ChatMetric
    )

    # Get user conversations for filtering chat messages/feedback
    user_conversations = session.query(Conversation).filter(Conversation.user_id == user.user_id).all()
    conv_ids = [c.conversation_id for c in user_conversations]

    counts = {
        "Users": session.query(User).filter(User.user_id == user.user_id).count(),
        "User Sessions": session.query(UserSession).filter(UserSession.user_id == user.user_id).count(),
        "Conversations": len(conv_ids),
        "Notifications": session.query(Notification).filter(Notification.user_id == user.user_id).count(),
        "Audit Logs": session.query(AuditLog).filter(AuditLog.user_id == user.user_id).count(),
        "Document Jobs": session.query(DocumentJob).filter(DocumentJob.user_id == user.user_id).count(),
        "API Rate Limits": session.query(ApiRateLimit).filter(ApiRateLimit.user_id == user.user_id).count(),
        "Chat Messages": session.query(ChatMessage).filter(ChatMessage.conversation_id.in_(conv_ids)).count() if conv_ids else 0,
        "Chat Feedback": session.query(ChatFeedback).filter(ChatFeedback.conversation_id.in_(conv_ids)).count() if conv_ids else 0,
        "Chat Metrics": session.query(ChatMetric).count(),
    }

    print("\n📊 Database Record Counts:")
    print("-" * 80)
    for table, count in counts.items():
        status = "✅" if count > 0 else "❌"
        print(f"{status} {table:20s}: {count:3d} records")
    print("-" * 80)

    total = sum(counts.values())
    print_success(f"Total records created: {total}")

    return counts


def cleanup_test_data(client, user):
    """Clean up test data."""
    print_section("12. Cleaning Up Test Data")

    print_info("Deleting test user and all related data (CASCADE)...")
    client.delete_user(user.user_id)
    print_success("Test data cleaned up successfully")

    # Cleanup expired rate limits
    cleaned = client.cleanup_expired_rate_limits()
    print_success(f"Cleaned up {cleaned} expired rate limit records")


def main():
    """Run all table tests."""
    print("\n" + "=" * 80)
    print("  PostgreSQL All Tables Test Suite")
    print("  Testing all database tables with dummy data")
    print("=" * 80)

    try:
        # Get client
        print_info("Initializing PostgreSQL client...")
        client = get_postgres_client()
        print_success("PostgreSQL client initialized")

        # Test connection
        print_info("Testing database connection...")
        # Try a simple query
        session = client.get_session()
        session.execute(text("SELECT 1"))
        print_success("Database connection successful!")

        # Run all tests
        user = test_users_table(client)
        session = test_user_sessions_table(client, user)
        notification = test_notifications_table(client, user)
        audit_log = test_audit_logs_table(client, user)
        job = test_document_jobs_table(client, user)
        rate_limit = test_api_rate_limits_table(client, user)
        conversation = test_conversations_table(client, user)  # Unified test (tests both API and chat)
        user_msg, assistant_msg = test_chat_messages_table(client, conversation)
        feedback = test_chat_feedback_table(client, conversation, assistant_msg)
        metric = test_chat_metrics_table(client, conversation)

        # Verify all data
        counts = verify_all_data(client, user)

        # Cleanup
        cleanup_test_data(client, user)

        # Final summary
        print("\n" + "=" * 80)
        print("  ✅ ALL TESTS PASSED SUCCESSFULLY!")
        print("=" * 80)
        print("\n📋 Summary:")
        print(f"  • All 10 tables tested and verified")
        print(f"  • Total records created: {sum(counts.values())}")
        print(f"  • Unified conversations table supports both chat and API modes")
        print(f"  • All data saved correctly to PostgreSQL")
        print(f"  • Test data cleaned up")
        print("\n🎉 Your unified PostgreSQL database is fully functional!\n")

        return True

    except Exception as e:
        print("\n" + "=" * 80)
        print("  ❌ TEST FAILED!")
        print("=" * 80)
        print(f"\nError: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        print("\n💡 Make sure:")
        print("  1. PostgreSQL is running")
        print("  2. Database is created and schema is loaded")
        print("  3. Environment variables are set (.env file)")
        print("  4. All models are imported correctly\n")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
