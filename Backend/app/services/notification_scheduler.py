"""
Notification Scheduler
Background job for processing medication reminders
Uses APScheduler for scheduling tasks
"""

import logging
from datetime import datetime, timezone
from typing import Optional
import asyncio
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class NotificationScheduler:
    """
    Scheduler for notification tasks.
    Runs background jobs to:
    1. Create daily medication reminders
    2. Send pending notifications
    """

    def __init__(self):
        self.scheduler = None
        self._is_running = False

    def init_scheduler(self):
        """Initialize APScheduler"""
        try:
            from apscheduler.schedulers.asyncio import AsyncIOScheduler
            from apscheduler.triggers.cron import CronTrigger
            from apscheduler.triggers.interval import IntervalTrigger

            self.scheduler = AsyncIOScheduler(timezone="UTC")

            # Job 1: Create medication reminders at midnight
            self.scheduler.add_job(
                self._create_daily_reminders,
                CronTrigger(hour=0, minute=5),  # Run at 00:05 UTC
                id="create_daily_reminders",
                name="Create Daily Medication Reminders",
                replace_existing=True
            )

            # Job 2: Process pending notifications every minute
            self.scheduler.add_job(
                self._process_notifications,
                IntervalTrigger(minutes=1),
                id="process_notifications",
                name="Process Pending Notifications",
                replace_existing=True
            )

            logger.info("Notification scheduler initialized with jobs")
            return True

        except ImportError:
            logger.error("APScheduler not installed. Run: pip install apscheduler")
            return False
        except Exception as e:
            logger.error(f"Error initializing scheduler: {e}")
            return False

    def start(self):
        """Start the scheduler"""
        if not self.scheduler:
            if not self.init_scheduler():
                return False

        if not self._is_running:
            self.scheduler.start()
            self._is_running = True
            logger.info("Notification scheduler started")
        return True

    def stop(self):
        """Stop the scheduler"""
        if self.scheduler and self._is_running:
            self.scheduler.shutdown(wait=False)
            self._is_running = False
            logger.info("Notification scheduler stopped")

    def is_running(self) -> bool:
        """Check if scheduler is running"""
        return self._is_running

    async def _create_daily_reminders(self):
        """Background task: Create medication reminders for the day"""
        logger.info("Running daily medication reminder creation...")
        try:
            from app.services.notification_service import notification_service
            count = notification_service.create_medication_reminders_for_today()
            logger.info(f"Created {count} medication reminders for today")
        except Exception as e:
            logger.error(f"Error creating daily reminders: {e}")

    async def _process_notifications(self):
        """Background task: Process and send pending notifications"""
        try:
            from app.services.notification_service import notification_service
            result = notification_service.process_pending_notifications()
            if result["sent"] > 0 or result["failed"] > 0:
                logger.info(f"Processed notifications: {result}")
        except Exception as e:
            logger.error(f"Error processing notifications: {e}")

    # ==================== Manual Triggers ====================

    def trigger_daily_reminders(self):
        """Manually trigger daily reminder creation"""
        if self.scheduler:
            self.scheduler.get_job("create_daily_reminders").modify(next_run_time=datetime.now(timezone.utc))
            logger.info("Triggered daily reminder creation")

    def trigger_notification_processing(self):
        """Manually trigger notification processing"""
        if self.scheduler:
            self.scheduler.get_job("process_notifications").modify(next_run_time=datetime.now(timezone.utc))
            logger.info("Triggered notification processing")


# Singleton instance
notification_scheduler = NotificationScheduler()


# ==================== Alternative: Simple Background Task ====================

class SimpleNotificationProcessor:
    """
    Simple background processor without APScheduler dependency.
    Uses asyncio for simple periodic tasks.
    """

    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self, check_interval_seconds: int = 60):
        """
        Start the notification processor.

        Args:
            check_interval_seconds: How often to check for pending notifications
        """
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop(check_interval_seconds))
        logger.info(f"Simple notification processor started (interval: {check_interval_seconds}s)")

    async def stop(self):
        """Stop the processor"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Simple notification processor stopped")

    async def _run_loop(self, interval: int):
        """Main processing loop"""
        from app.services.notification_service import notification_service

        while self._running:
            try:
                # Process pending notifications
                result = notification_service.process_pending_notifications()
                if result["sent"] > 0 or result["failed"] > 0:
                    logger.info(f"Processed: {result['sent']} sent, {result['failed']} failed")

            except Exception as e:
                logger.error(f"Error in notification loop: {e}")

            await asyncio.sleep(interval)


# Simple processor instance
simple_processor = SimpleNotificationProcessor()


@asynccontextmanager
async def notification_processor_lifespan():
    """
    Context manager for notification processor lifecycle.
    Use in FastAPI lifespan:

    @asynccontextmanager
    async def lifespan(app):
        async with notification_processor_lifespan():
            yield
    """
    await simple_processor.start(check_interval_seconds=60)
    try:
        yield
    finally:
        await simple_processor.stop()
