#!/usr/bin/env python3
"""Check notifications scheduled times"""
import sys
sys.path.insert(0, '/Users/junaidraza/Documents/Projects/agentic-ai-family-health-manager/Backend')

from shared.database.postgres.postgres_client import PostgresClient
from shared.database.postgres.models import Notification
from datetime import datetime, timezone

def check_notifications():
    db_client = PostgresClient()
    with db_client as db:
        session = db.get_session()

        # Check all notifications
        notifications = session.query(Notification).filter(
            Notification.user_id == "a2a3d05f-f971-400d-a885-b0190ce765bf"
        ).order_by(Notification.scheduled_at).all()

        now = datetime.now(timezone.utc)
        print(f"Current time (UTC): {now}")
        print(f"\nTotal notifications: {len(notifications)}\n")

        pending_future = 0
        pending_past = 0

        for n in notifications[:10]:  # Show first 10
            scheduled = n.scheduled_at
            is_future = scheduled > now if scheduled else False
            is_pending = n.status == "pending"

            if is_pending and is_future:
                pending_future += 1
            elif is_pending and not is_future:
                pending_past += 1

            print(f"Type: {n.type}")
            print(f"  Title: {n.title}")
            print(f"  Status: {n.status}")
            print(f"  Scheduled: {scheduled}")
            print(f"  Is future: {is_future}")
            print()

        print(f"Pending + Future: {pending_future}")
        print(f"Pending + Past: {pending_past}")

if __name__ == "__main__":
    check_notifications()