#!/usr/bin/env python3
"""
Re-seed notifications with correct future times for TODAY
"""
import sys
sys.path.insert(0, '/Users/junaidraza/Documents/Projects/agentic-ai-family-health-manager/Backend')

from shared.database.postgres.postgres_client import PostgresClient
from shared.database.postgres.models import Notification
from datetime import datetime, timezone
import uuid

def reseed_notifications():
    user_id = "a2a3d05f-f971-400d-a885-b0190ce765bf"

    db_client = PostgresClient()
    with db_client as db:
        session = db.get_session()

        # Delete old pending notifications to avoid duplicates
        session.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.type == "medication_reminder"
        ).delete()
        session.commit()

        # Get current time
        now = datetime.now(timezone.utc)
        today = now.date()

        # Create future medication reminders for TODAY
        future_reminders = [
            ("medication_reminder", "Time for Metformin (Morning)",
             "Take your Metformin 500mg morning dose. Take with food.", "high",
             datetime(today.year, today.month, today.day, 8, 0, 0, tzinfo=timezone.utc)),

            ("medication_reminder", "Time for Panadol",
             "Take your Panadol 500mg tablet as prescribed.", "high",
             datetime(today.year, today.month, today.day, 15, 0, 0, tzinfo=timezone.utc)),  # 3 PM

            ("medication_reminder", "Time for Metformin (Evening)",
             "Take your Metformin 500mg evening dose. Take with dinner.", "high",
             datetime(today.year, today.month, today.day, 20, 0, 0, tzinfo=timezone.utc)),  # 8 PM

            ("medication_reminder", "Time for Atorvastatin",
             "Take your Atorvastatin 20mg bedtime dose.", "high",
             datetime(today.year, today.month, today.day, 21, 0, 0, tzinfo=timezone.utc)),  # 9 PM
        ]

        count = 0
        for notif_type, title, message, priority, scheduled in future_reminders:
            # Only create if it's in the future
            if scheduled > now:
                notification = Notification(
                    notification_id=str(uuid.uuid4()),
                    user_id=user_id,
                    type=notif_type,
                    title=title,
                    message=message,
                    status="pending",
                    priority=priority,
                    scheduled_at=scheduled,
                )
                session.add(notification)
                count += 1
                print(f"✅ Created: {title} at {scheduled.strftime('%I:%M %p')} (status: pending)")
            else:
                print(f"⏭️  Skipped (past): {title} at {scheduled.strftime('%I:%M %p')}")

        session.commit()
        print(f"\n✅ Created {count} pending medication reminders for today")

        # Also create some appointment reminders
        from datetime import timedelta
        tomorrow = now + timedelta(days=1)
        next_week = now + timedelta(days=7)

        appointments = [
            ("appointment_reminder", "Cardiology Follow-up Tomorrow",
             "Your cardiology appointment with Dr. Johnson is tomorrow at 10:00 AM", "high",
             datetime(tomorrow.year, tomorrow.month, tomorrow.day, 9, 0, 0, tzinfo=timezone.utc)),

            ("appointment_reminder", "Lab Work Next Week",
             "Reminder: Fasting blood panel next week. Remember to fast 12 hours before.", "medium",
             datetime(next_week.year, next_week.month, next_week.day, 7, 0, 0, tzinfo=timezone.utc)),
        ]

        for notif_type, title, message, priority, scheduled in appointments:
            notification = Notification(
                notification_id=str(uuid.uuid4()),
                user_id=user_id,
                type=notif_type,
                title=title,
                message=message,
                status="pending",
                priority=priority,
                scheduled_at=scheduled,
            )
            session.add(notification)
            count += 1
            print(f"✅ Created: {title} at {scheduled.strftime('%Y-%m-%d %I:%M %p')}")

        session.commit()
        print(f"\n🎉 Total pending notifications created: {count}")

if __name__ == "__main__":
    reseed_notifications()