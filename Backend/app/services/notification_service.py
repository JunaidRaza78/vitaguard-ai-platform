"""
Notification Service for Medication Reminders
Handles:
- Fetching medication data from Neo4j
- Creating/updating notifications in PostgreSQL
- Sending email notifications
"""

import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any

from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationStatus,
    NotificationType,
    NotificationPriority,
    MedicationReminderInfo,
)

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing medication notifications"""

    def __init__(self):
        """Initialize notification service"""
        self.email_service = None
        self._init_email_service()

    def _init_email_service(self):
        """Initialize email service"""
        try:
            from app.auth_export.email_service import EmailService
            self.email_service = EmailService()
            logger.info("Email service initialized for notifications")
        except Exception as e:
            logger.error(f"Failed to initialize email service: {e}")

    # ==================== Neo4j Operations ====================

    def get_users_with_medication_reminders(self) -> List[MedicationReminderInfo]:
        """
        Get all users with active medications that have reminder times set.
        Fetches from Neo4j.

        Returns:
            List of MedicationReminderInfo objects
        """
        from shared.database.neo4j import Neo4jClient

        try:
            client = Neo4jClient()

            query = """
            MATCH (u:User)-[r:TAKES]->(m:Medication)
            WHERE r.status = 'active' AND r.reminderTimes IS NOT NULL AND size(r.reminderTimes) > 0
            RETURN u.userId as userId, u.email as email, u.name as userName,
                   m.medicationId as medicationId, m.name as medicationName,
                   m.genericName as genericName,
                   r.dosage as dosage, r.frequency as frequency,
                   r.reminderTimes as reminderTimes, r.status as status
            """

            results = client.execute_query(query)

            reminders = []
            for record in results:
                reminder = MedicationReminderInfo(
                    medication_id=record["medicationId"],
                    medication_name=record["medicationName"],
                    generic_name=record.get("genericName"),
                    dosage=record["dosage"],
                    frequency=record["frequency"],
                    reminder_times=record["reminderTimes"] or [],
                    status=record["status"],
                    user_email=record["email"],
                    user_name=record["userName"]
                )
                reminders.append(reminder)

            logger.info(f"Found {len(reminders)} medication reminders from Neo4j")
            return reminders

        except Exception as e:
            logger.error(f"Error fetching medication reminders from Neo4j: {e}")
            return []

    def get_user_medications(self, user_id: str) -> List[MedicationReminderInfo]:
        """
        Get medications for a specific user from Neo4j.

        Args:
            user_id: User ID

        Returns:
            List of MedicationReminderInfo for the user
        """
        from shared.database.neo4j import Neo4jClient

        try:
            client = Neo4jClient()

            query = """
            MATCH (u:User {userId: $userId})-[r:TAKES]->(m:Medication)
            WHERE r.status = 'active'
            RETURN u.email as email, u.name as userName,
                   m.medicationId as medicationId, m.name as medicationName,
                   m.genericName as genericName,
                   r.dosage as dosage, r.frequency as frequency,
                   r.reminderTimes as reminderTimes, r.status as status
            """

            results = client.execute_query(query, {"userId": user_id})

            reminders = []
            for record in results:
                reminder = MedicationReminderInfo(
                    medication_id=record["medicationId"],
                    medication_name=record["medicationName"],
                    generic_name=record.get("genericName"),
                    dosage=record["dosage"],
                    frequency=record["frequency"],
                    reminder_times=record.get("reminderTimes") or [],
                    status=record["status"],
                    user_email=record["email"],
                    user_name=record["userName"]
                )
                reminders.append(reminder)

            return reminders

        except Exception as e:
            logger.error(f"Error fetching user medications from Neo4j: {e}")
            return []

    # ==================== PostgreSQL Operations ====================

    def create_notification(
        self,
        user_id: str,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        scheduled_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[NotificationResponse]:
        """
        Create a notification record in PostgreSQL.

        Args:
            user_id: User ID
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            priority: Priority level
            scheduled_at: When to send (None for immediate)
            metadata: Additional metadata

        Returns:
            Created notification or None
        """
        from shared.database.postgres.postgres_client import PostgresClient
        from shared.database.postgres.models import Notification

        try:
            notification_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)

            db_client = PostgresClient()
            with db_client as db:
                session = db.get_session()

                notification = Notification(
                    notification_id=notification_id,
                    user_id=user_id,
                    type=notification_type.value,
                    title=title,
                    message=message,
                    status=NotificationStatus.PENDING.value if scheduled_at else NotificationStatus.PENDING.value,
                    priority=priority.value,
                    scheduled_at=scheduled_at or now,
                    created_at=now,
                    notification_metadata=metadata or {},
                    retry_count=0
                )

                session.add(notification)
                session.commit()
                session.refresh(notification)

                logger.info(f"Created notification {notification_id} for user {user_id}")

                return NotificationResponse(
                    notification_id=str(notification.notification_id),
                    user_id=str(notification.user_id),
                    type=notification.type,
                    title=notification.title,
                    message=notification.message,
                    status=notification.status,
                    priority=notification.priority,
                    scheduled_at=notification.scheduled_at,
                    sent_at=notification.sent_at,
                    created_at=notification.created_at,
                    metadata=notification.notification_metadata,
                    retry_count=notification.retry_count
                )

        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            return None

    def get_pending_notifications(self) -> List[NotificationResponse]:
        """
        Get all pending notifications that are due to be sent.

        Returns:
            List of pending notifications
        """
        from shared.database.postgres.postgres_client import PostgresClient
        from shared.database.postgres.models import Notification

        try:
            db_client = PostgresClient()
            with db_client as db:
                session = db.get_session()
                now = datetime.now(timezone.utc)

                notifications = session.query(Notification).filter(
                    Notification.status == NotificationStatus.PENDING.value,
                    Notification.scheduled_at <= now
                ).all()

                result = []
                for n in notifications:
                    result.append(NotificationResponse(
                        notification_id=str(n.notification_id),
                        user_id=str(n.user_id),
                        type=n.type,
                        title=n.title,
                        message=n.message,
                        status=n.status,
                        priority=n.priority,
                        scheduled_at=n.scheduled_at,
                        sent_at=n.sent_at,
                        created_at=n.created_at,
                        metadata=n.notification_metadata,
                        retry_count=n.retry_count
                    ))

                return result

        except Exception as e:
            logger.error(f"Error fetching pending notifications: {e}")
            return []

    def get_user_notifications(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[NotificationResponse]:
        """
        Get notifications for a specific user.

        Args:
            user_id: User ID
            status: Filter by status (optional)
            limit: Max results
            offset: Pagination offset

        Returns:
            List of notifications
        """
        from shared.database.postgres.postgres_client import PostgresClient
        from shared.database.postgres.models import Notification

        try:
            db_client = PostgresClient()
            with db_client as db:
                session = db.get_session()

                query = session.query(Notification).filter(
                    Notification.user_id == user_id
                )

                if status:
                    query = query.filter(Notification.status == status)

                notifications = query.order_by(
                    Notification.created_at.desc()
                ).offset(offset).limit(limit).all()

                result = []
                for n in notifications:
                    result.append(NotificationResponse(
                        notification_id=str(n.notification_id),
                        user_id=str(n.user_id),
                        type=n.type,
                        title=n.title,
                        message=n.message,
                        status=n.status,
                        priority=n.priority,
                        scheduled_at=n.scheduled_at,
                        sent_at=n.sent_at,
                        created_at=n.created_at,
                        metadata=n.notification_metadata,
                        retry_count=n.retry_count
                    ))

                return result

        except Exception as e:
            logger.error(f"Error fetching user notifications: {e}")
            return []

    def update_notification_status(
        self,
        notification_id: str,
        status: NotificationStatus,
        sent_at: Optional[datetime] = None
    ) -> bool:
        """
        Update notification status.

        Args:
            notification_id: Notification ID
            status: New status
            sent_at: Timestamp when sent (for SENT status)

        Returns:
            Success status
        """
        from shared.database.postgres.postgres_client import PostgresClient
        from shared.database.postgres.models import Notification

        try:
            db_client = PostgresClient()
            with db_client as db:
                session = db.get_session()

                notification = session.query(Notification).filter(
                    Notification.notification_id == notification_id
                ).first()

                if not notification:
                    logger.warning(f"Notification {notification_id} not found")
                    return False

                notification.status = status.value
                if sent_at:
                    notification.sent_at = sent_at

                session.commit()
                logger.info(f"Updated notification {notification_id} status to {status.value}")
                return True

        except Exception as e:
            logger.error(f"Error updating notification status: {e}")
            return False

    def increment_retry_count(self, notification_id: str) -> bool:
        """Increment retry count for a failed notification"""
        from shared.database.postgres.postgres_client import PostgresClient
        from shared.database.postgres.models import Notification

        try:
            db_client = PostgresClient()
            with db_client as db:
                session = db.get_session()

                notification = session.query(Notification).filter(
                    Notification.notification_id == notification_id
                ).first()

                if notification:
                    notification.retry_count += 1
                    session.commit()
                    return True
                return False

        except Exception as e:
            logger.error(f"Error incrementing retry count: {e}")
            return False

    # ==================== Email Sending ====================

    def send_medication_reminder_email(
        self,
        to_email: str,
        user_name: str,
        medication_name: str,
        dosage: str,
        reminder_time: str
    ) -> bool:
        """
        Send medication reminder email.

        Args:
            to_email: Recipient email
            user_name: User's name
            medication_name: Medication name
            dosage: Dosage info
            reminder_time: Time of reminder

        Returns:
            Success status
        """
        if not self.email_service:
            logger.error("Email service not available")
            return False

        subject = f"Medication Reminder: {medication_name}"

        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #4CAF50; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background: #f9f9f9; padding: 20px; border: 1px solid #ddd; }}
                .medication-box {{ background: white; padding: 15px; border-left: 4px solid #4CAF50; margin: 15px 0; }}
                .footer {{ text-align: center; padding: 10px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Medication Reminder</h2>
                </div>
                <div class="content">
                    <p>Hello <strong>{user_name}</strong>,</p>
                    <p>This is a reminder to take your medication:</p>

                    <div class="medication-box">
                        <h3>{medication_name}</h3>
                        <p><strong>Dosage:</strong> {dosage}</p>
                        <p><strong>Scheduled Time:</strong> {reminder_time}</p>
                    </div>

                    <p>Please take your medication as prescribed. If you have any concerns, contact your healthcare provider.</p>

                    <p>Stay healthy!</p>
                </div>
                <div class="footer">
                    <p>This is an automated reminder from your Family Health Manager.</p>
                    <p>Do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        try:
            success = self.email_service.send_email(to_email, subject, body)
            if success:
                logger.info(f"Sent medication reminder to {to_email} for {medication_name}")
            else:
                logger.error(f"Failed to send medication reminder to {to_email}")
            return success
        except Exception as e:
            logger.error(f"Error sending medication reminder email: {e}")
            return False

    def send_notification(self, notification: NotificationResponse) -> bool:
        """
        Send a notification via email.

        Args:
            notification: Notification to send

        Returns:
            Success status
        """
        # Get user email from PostgreSQL
        from shared.database.postgres.postgres_client import PostgresClient
        from shared.database.postgres.models import User

        try:
            db_client = PostgresClient()
            with db_client as db:
                session = db.get_session()
                user = session.query(User).filter(
                    User.user_id == notification.user_id
                ).first()

                if not user:
                    logger.error(f"User {notification.user_id} not found")
                    return False

                user_email = user.email
                user_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username or "User"

            # Send email
            if not self.email_service:
                logger.error("Email service not available")
                return False

            subject = notification.title or "Health App Notification"
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2>{notification.title or 'Notification'}</h2>
                    <p>Hello {user_name},</p>
                    <p>{notification.message}</p>
                    <hr>
                    <p style="color: #666; font-size: 12px;">
                        This is an automated notification from your Family Health Manager.
                    </p>
                </div>
            </body>
            </html>
            """

            success = self.email_service.send_email(user_email, subject, body)

            if success:
                self.update_notification_status(
                    notification.notification_id,
                    NotificationStatus.SENT,
                    sent_at=datetime.now(timezone.utc)
                )
                logger.info(f"Notification {notification.notification_id} sent successfully")
            else:
                self.increment_retry_count(notification.notification_id)
                if notification.retry_count >= 3:
                    self.update_notification_status(
                        notification.notification_id,
                        NotificationStatus.FAILED
                    )
                logger.error(f"Failed to send notification {notification.notification_id}")

            return success

        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False

    # ==================== Scheduled Tasks ====================

    def create_medication_reminders_for_today(self) -> int:
        """
        Create medication reminder notifications for today.
        Called by scheduler.

        Returns:
            Number of notifications created
        """
        reminders = self.get_users_with_medication_reminders()
        count = 0
        today = datetime.now(timezone.utc).date()

        for reminder in reminders:
            for time_str in reminder.reminder_times:
                try:
                    # Parse HH:MM format
                    hour, minute = map(int, time_str.split(':'))
                    scheduled_time = datetime(
                        today.year, today.month, today.day,
                        hour, minute, 0, tzinfo=timezone.utc
                    )

                    # Skip if time has passed
                    if scheduled_time < datetime.now(timezone.utc):
                        continue

                    # Create notification
                    notification = self.create_notification(
                        user_id=reminder.medication_id.split('-')[0],  # Extract user_id if embedded
                        notification_type=NotificationType.MEDICATION_REMINDER,
                        title=f"Take {reminder.medication_name}",
                        message=f"Time to take your medication: {reminder.medication_name} - {reminder.dosage}",
                        priority=NotificationPriority.HIGH,
                        scheduled_at=scheduled_time,
                        metadata={
                            "medication_id": reminder.medication_id,
                            "medication_name": reminder.medication_name,
                            "dosage": reminder.dosage,
                            "reminder_time": time_str,
                            "user_email": reminder.user_email,
                            "user_name": reminder.user_name
                        }
                    )

                    if notification:
                        count += 1

                except ValueError as e:
                    logger.error(f"Invalid time format {time_str}: {e}")

        logger.info(f"Created {count} medication reminders for today")
        return count

    def process_pending_notifications(self) -> Dict[str, int]:
        """
        Process and send all pending notifications.
        Called by scheduler.

        Returns:
            Dict with sent and failed counts
        """
        pending = self.get_pending_notifications()
        sent = 0
        failed = 0

        for notification in pending:
            if self.send_notification(notification):
                sent += 1
            else:
                failed += 1

        logger.info(f"Processed notifications: {sent} sent, {failed} failed")
        return {"sent": sent, "failed": failed}


# Singleton instance
notification_service = NotificationService()
