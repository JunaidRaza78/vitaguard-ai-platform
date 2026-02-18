"""
Notification API Endpoints
REST API for medication reminders and notifications
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional
import logging

from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationListResponse,
    NotificationStatus,
    NotificationType,
    NotificationPriority,
    MedicationRemindersResponse,
    SendNotificationResponse,
    MedicationReminderCreate,
)
from app.services.notification_service import notification_service
from app.middleware.auth import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/notifications",
    tags=["Notifications"],
    responses={404: {"description": "Not found"}},
)


# ==================== User Notification Endpoints ====================

@router.get(
    "/me",
    response_model=NotificationListResponse,
    summary="Get my notifications",
    description="Get notifications for the current user"
)
async def get_my_notifications(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get notifications for the authenticated user.

    - **status**: Filter by notification status (pending, sent, failed)
    - **limit**: Maximum number of results (default: 20)
    - **offset**: Pagination offset
    """
    try:
        notifications = notification_service.get_user_notifications(
            user_id=current_user["user_id"],
            status=status,
            limit=limit,
            offset=offset
        )

        return NotificationListResponse(
            notifications=notifications,
            total=len(notifications),  # TODO: Get actual total count
            page=(offset // limit) + 1,
            page_size=limit
        )

    except Exception as e:
        logger.error(f"Error fetching notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch notifications"
        )


@router.get(
    "/me/medications",
    response_model=MedicationRemindersResponse,
    summary="Get my medication reminders",
    description="Get medication reminders from Neo4j for the current user"
)
async def get_my_medication_reminders(
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get active medications with reminder times for the authenticated user.
    Data is fetched from Neo4j.
    """
    try:
        reminders = notification_service.get_user_medications(
            user_id=current_user["user_id"]
        )

        return MedicationRemindersResponse(
            reminders=reminders,
            total=len(reminders)
        )

    except Exception as e:
        logger.error(f"Error fetching medication reminders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch medication reminders"
        )


# ==================== Admin/System Endpoints ====================

@router.post(
    "/create",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a notification",
    description="Create a new notification (admin/system use)"
)
async def create_notification(
    notification_data: NotificationCreate,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Create a new notification.

    - **user_id**: Target user ID
    - **type**: Notification type (medication_reminder, etc.)
    - **title**: Notification title
    - **message**: Notification message
    - **priority**: Priority level
    - **scheduled_at**: When to send (optional, defaults to now)
    """
    try:
        notification = notification_service.create_notification(
            user_id=notification_data.user_id,
            notification_type=notification_data.type,
            title=notification_data.title,
            message=notification_data.message,
            priority=notification_data.priority,
            scheduled_at=notification_data.scheduled_at,
            metadata=notification_data.metadata
        )

        if not notification:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create notification"
            )

        return notification

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create notification"
        )


@router.post(
    "/medication-reminder",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create medication reminder",
    description="Create a medication reminder notification"
)
async def create_medication_reminder(
    reminder_data: MedicationReminderCreate,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Create a medication reminder notification.

    - **user_id**: Target user ID
    - **medication_id**: Medication ID from Neo4j
    - **medication_name**: Medication name
    - **dosage**: Dosage information
    - **reminder_time**: Time in HH:MM format
    - **scheduled_at**: When to send the reminder
    """
    try:
        notification = notification_service.create_notification(
            user_id=reminder_data.user_id,
            notification_type=NotificationType.MEDICATION_REMINDER,
            title=f"Take {reminder_data.medication_name}",
            message=f"Time to take your medication: {reminder_data.medication_name} - {reminder_data.dosage}",
            priority=NotificationPriority.HIGH,
            scheduled_at=reminder_data.scheduled_at,
            metadata={
                "medication_id": reminder_data.medication_id,
                "medication_name": reminder_data.medication_name,
                "dosage": reminder_data.dosage,
                "reminder_time": reminder_data.reminder_time
            }
        )

        if not notification:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create medication reminder"
            )

        return notification

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating medication reminder: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create medication reminder"
        )


@router.post(
    "/send/{notification_id}",
    response_model=SendNotificationResponse,
    summary="Send a notification",
    description="Immediately send a pending notification"
)
async def send_notification(
    notification_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Immediately send a pending notification.

    - **notification_id**: ID of the notification to send
    """
    try:
        # Get the notification
        notifications = notification_service.get_user_notifications(
            user_id=current_user["user_id"],
            limit=1000
        )

        notification = next(
            (n for n in notifications if n.notification_id == notification_id),
            None
        )

        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )

        if notification.status != NotificationStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Notification is not pending (status: {notification.status})"
            )

        # Send the notification
        success = notification_service.send_notification(notification)

        from datetime import datetime, timezone

        return SendNotificationResponse(
            success=success,
            notification_id=notification_id,
            message="Notification sent successfully" if success else "Failed to send notification",
            sent_at=datetime.now(timezone.utc) if success else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send notification"
        )


@router.post(
    "/process-pending",
    summary="Process pending notifications",
    description="Process and send all pending notifications (admin)"
)
async def process_pending_notifications(
    current_user: dict = Depends(get_current_active_user)
):
    """
    Process and send all pending notifications that are due.
    Admin/system endpoint.
    """
    # Check if user is superuser
    if not current_user.get("is_superuser"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser access required"
        )

    try:
        result = notification_service.process_pending_notifications()
        return {
            "success": True,
            "message": f"Processed {result['sent']} sent, {result['failed']} failed"
        }
    except Exception as e:
        logger.error(f"Error processing notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process notifications"
        )


@router.post(
    "/create-daily-reminders",
    summary="Create daily medication reminders",
    description="Create medication reminders for today (admin)"
)
async def create_daily_reminders(
    current_user: dict = Depends(get_current_active_user)
):
    """
    Create medication reminder notifications for today.
    Admin/system endpoint - typically called by scheduler.
    """
    # Check if user is superuser
    if not current_user.get("is_superuser"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser access required"
        )

    try:
        count = notification_service.create_medication_reminders_for_today()
        return {
            "success": True,
            "message": f"Created {count} medication reminders for today"
        }
    except Exception as e:
        logger.error(f"Error creating daily reminders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create daily reminders"
        )


# ==================== Add Medication Reminder to Neo4j ====================

from pydantic import BaseModel
from typing import List
from datetime import date as date_type
import uuid as _uuid


class AddMedicationRequest(BaseModel):
    medication_name: str
    dosage: str
    frequency: str
    reminder_times: List[str]   # e.g. ["08:00", "20:00"]
    start_date: Optional[str] = None  # YYYY-MM-DD, defaults to today


@router.post(
    "/add-medication",
    status_code=status.HTTP_201_CREATED,
    summary="Add medication reminder",
    description="Create Medication node + TAKES relationship in Neo4j with reminder times"
)
async def add_medication_reminder(
    data: AddMedicationRequest,
    current_user: dict = Depends(get_current_active_user),
):
    """
    Add a medication with reminder times to Neo4j for the current user.
    Creates a Medication node and a TAKES relationship with reminder times.
    """
    try:
        from shared.database.neo4j.operations.family_ops import FamilyOperations

        ops = FamilyOperations()
        user_id = current_user["user_id"]

        first = current_user.get("first_name", "") or ""
        last = current_user.get("last_name", "") or ""
        full_name = f"{first} {last}".strip() or current_user.get("username", "")

        medication_id = str(_uuid.uuid4())
        start_date = data.start_date or date_type.today().isoformat()

        query = """
        MERGE (u:User {userId: $userId})
        SET u.name = $userName, u.email = $userEmail
        WITH u
        CREATE (m:Medication {
            medicationId: $medicationId,
            name: $medicationName
        })
        CREATE (u)-[:TAKES {
            startDate: date($startDate),
            dosage: $dosage,
            frequency: $frequency,
            status: 'active',
            reminderTimes: $reminderTimes
        }]->(m)
        RETURN m
        """

        params = {
            "userId": user_id,
            "userName": full_name,
            "userEmail": current_user.get("email", ""),
            "medicationId": medication_id,
            "medicationName": data.medication_name,
            "startDate": start_date,
            "dosage": data.dosage,
            "frequency": data.frequency,
            "reminderTimes": data.reminder_times,
        }

        records = ops.execute_query(query, params)
        if not records:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add medication reminder to Neo4j",
            )

        # Also create a PostgreSQL notification record so it appears in notifications list
        try:
            reminder_times_str = ", ".join(data.reminder_times) if data.reminder_times else "N/A"
            notification_service.create_notification(
                user_id=user_id,
                notification_type=NotificationType.MEDICATION_REMINDER,
                title=f"💊 {data.medication_name} — {data.dosage}",
                message=f"Take {data.medication_name} ({data.dosage}) {data.frequency}. Reminder times: {reminder_times_str}. Starting: {start_date}.",
                priority=NotificationPriority.MEDIUM,
                metadata={
                    "medication_id": medication_id,
                    "medication_name": data.medication_name,
                    "dosage": data.dosage,
                    "frequency": data.frequency,
                    "reminder_times": data.reminder_times,
                    "start_date": start_date,
                }
            )
        except Exception as notif_err:
            logger.warning(f"Failed to create PostgreSQL notification record: {notif_err}")

        return {
            "success": True,
            "medication_id": medication_id,
            "message": f"Medication '{data.medication_name}' added with {len(data.reminder_times)} reminder(s)",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding medication reminder: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add medication reminder",
        )


# ==================== Send Direct Email (for Neo4j-only notifications) ====================

class SendDirectEmailRequest(BaseModel):
    title: str
    message: str
    recipient_emails: List[str]


@router.post(
    "/send-direct",
    summary="Send email directly without notification_id",
    description="Send a notification email directly to specified recipients"
)
async def send_direct_email(
    data: SendDirectEmailRequest,
    current_user: dict = Depends(get_current_active_user),
):
    """Send email directly to recipients — used for Neo4j-only medication reminders."""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from pathlib import Path
        from dotenv import dotenv_values

        env_path = Path(__file__).parent.parent / "auth_export" / "keys" / ".env"
        smtp_cfg = dotenv_values(env_path)
        smtp_user = smtp_cfg.get("SMTP_USERNAME", "")
        smtp_pass = smtp_cfg.get("SMTP_PASSWORD", "")

        if not smtp_user or not smtp_pass:
            raise HTTPException(status_code=500, detail="SMTP credentials not configured")

        sender_name = f"{current_user.get('first_name','')} {current_user.get('last_name','')}".strip()
        email_body = f"""
        <html><body style="font-family:Arial,sans-serif;">
        <div style="max-width:600px;margin:0 auto;padding:20px;">
            <h2>💊 {data.title}</h2>
            <p>{data.message}</p>
            <hr>
            <p style="color:#666;font-size:12px;">
                Sent from Family Health Manager — {sender_name}.
            </p>
        </div></body></html>
        """

        sent_to = []
        for email in data.recipient_emails:
            try:
                msg = MIMEText(email_body, 'html')
                msg['Subject'] = data.title
                msg['From'] = smtp_user
                msg['To'] = email
                with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10) as smtp:
                    smtp.login(smtp_user, smtp_pass)
                    smtp.sendmail(smtp_user, email, msg.as_string())
                sent_to.append(email)
            except Exception as e:
                logger.warning(f"Failed to send to {email}: {e}")

        return {
            "success": len(sent_to) > 0,
            "sent_to": sent_to,
            "message": f"Sent to {len(sent_to)} recipient(s)"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Direct email send error: {e}")
        raise HTTPException(status_code=500, detail="Failed to send email")


# ==================== Send to Family Members ====================

class SendToMembersRequest(BaseModel):
    notification_id: str
    recipient_emails: List[str]   # emails of family members to send to


@router.post(
    "/send-to-members",
    summary="Send notification to selected family members",
    description="Send a notification email to a list of family member emails"
)
async def send_to_family_members(
    data: SendToMembersRequest,
    current_user: dict = Depends(get_current_active_user),
):
    """
    Send a notification to selected family members by email.
    Also sends to the current user (notification owner).
    """
    try:
        import smtplib
        from email.mime.text import MIMEText
        from pathlib import Path
        from dotenv import dotenv_values

        # Get the notification details
        notifications = notification_service.get_user_notifications(
            user_id=current_user["user_id"], limit=1000
        )
        notif = next((n for n in notifications if str(n.notification_id) == data.notification_id), None)
        if not notif:
            raise HTTPException(status_code=404, detail="Notification not found")

        # Load SMTP credentials
        env_path = Path(__file__).parent.parent / "auth_export" / "keys" / ".env"
        smtp_cfg = dotenv_values(env_path)
        smtp_user = smtp_cfg.get("SMTP_USERNAME", "")
        smtp_pass = smtp_cfg.get("SMTP_PASSWORD", "")

        if not smtp_user or not smtp_pass:
            raise HTTPException(status_code=500, detail="SMTP credentials not configured")

        sent_to = []
        failed = []
        email_body = f"""
        <html><body style="font-family:Arial,sans-serif;">
        <div style="max-width:600px;margin:0 auto;padding:20px;">
            <h2>{notif.title}</h2>
            <p>{notif.message}</p>
            <hr>
            <p style="color:#666;font-size:12px;">
                Sent from Family Health Manager — {current_user.get('first_name','')} {current_user.get('last_name','')}.
            </p>
        </div></body></html>
        """

        for email in data.recipient_emails:
            try:
                msg = MIMEText(email_body, 'html')
                msg['Subject'] = notif.title or "Health Notification"
                msg['From'] = smtp_user
                msg['To'] = email
                with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10) as smtp:
                    smtp.login(smtp_user, smtp_pass)
                    smtp.sendmail(smtp_user, email, msg.as_string())
                sent_to.append(email)
            except Exception as e:
                logger.warning(f"Failed to send to {email}: {e}")
                failed.append(email)

        # Also send to the notification owner (mark as sent)
        if current_user.get("email") not in data.recipient_emails:
            notification_service.send_notification(notif)

        return {
            "success": len(sent_to) > 0,
            "sent_to": sent_to,
            "failed": failed,
            "message": f"Sent to {len(sent_to)} recipient(s)"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending to members: {e}")
        raise HTTPException(status_code=500, detail="Failed to send notification")


# ==================== Test Endpoint ====================

@router.post(
    "/test-email",
    summary="Test email sending",
    description="Send a test notification email to yourself"
)
async def test_email_notification(
    current_user: dict = Depends(get_current_active_user)
):
    """
    Send a test notification email to the current user's email.
    """
    try:
        notification = notification_service.create_notification(
            user_id=current_user["user_id"],
            notification_type=NotificationType.SYSTEM,
            title="Test Notification",
            message="This is a test notification to verify email sending is working correctly.",
            priority=NotificationPriority.LOW,
            scheduled_at=None,  # Immediate
            metadata={"test": True}
        )

        if not notification:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create test notification"
            )

        # Send immediately
        success = notification_service.send_notification(notification)

        return {
            "success": success,
            "notification_id": notification.notification_id,
            "message": "Test email sent successfully" if success else "Failed to send test email",
            "recipient": current_user.get("email")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending test email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test email"
        )
