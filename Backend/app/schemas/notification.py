"""
Notification Schemas for Medication Reminders
Pydantic models for notification API requests/responses
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class NotificationType(str, Enum):
    """Types of notifications"""
    MEDICATION_REMINDER = "medication_reminder"
    APPOINTMENT_REMINDER = "appointment_reminder"
    VACCINATION_REMINDER = "vaccination_reminder"
    HEALTH_ALERT = "health_alert"
    PROACTIVE_ALERT = "proactive_alert"
    SYSTEM = "system"


class NotificationStatus(str, Enum):
    """Notification statuses"""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NotificationPriority(str, Enum):
    """Notification priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# ==================== Request Schemas ====================

class NotificationCreate(BaseModel):
    """Schema for creating a notification"""
    user_id: str = Field(..., description="User ID to notify")
    type: NotificationType = Field(default=NotificationType.MEDICATION_REMINDER)
    title: str = Field(..., max_length=255)
    message: str = Field(..., description="Notification message")
    priority: NotificationPriority = Field(default=NotificationPriority.MEDIUM)
    scheduled_at: Optional[datetime] = Field(None, description="When to send the notification")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    model_config = {"from_attributes": True}


class MedicationReminderCreate(BaseModel):
    """Schema for creating a medication reminder notification"""
    user_id: str = Field(..., description="User ID")
    medication_id: str = Field(..., description="Medication ID from Neo4j")
    medication_name: str = Field(..., description="Medication name")
    dosage: str = Field(..., description="Dosage information")
    reminder_time: str = Field(..., description="Time in HH:MM format")
    scheduled_at: datetime = Field(..., description="Scheduled send time")

    model_config = {"from_attributes": True}


class NotificationUpdate(BaseModel):
    """Schema for updating a notification"""
    status: Optional[NotificationStatus] = None
    sent_at: Optional[datetime] = None
    retry_count: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}


# ==================== Response Schemas ====================

class NotificationResponse(BaseModel):
    """Schema for notification response"""
    notification_id: str
    user_id: str
    type: str
    title: Optional[str]
    message: str
    status: str
    priority: Optional[str]
    scheduled_at: Optional[datetime]
    sent_at: Optional[datetime]
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None
    retry_count: int = 0

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    """Schema for list of notifications"""
    notifications: List[NotificationResponse]
    total: int
    page: int = 1
    page_size: int = 20

    model_config = {"from_attributes": True}


class MedicationReminderInfo(BaseModel):
    """Info about a medication reminder"""
    medication_id: str
    medication_name: str
    generic_name: Optional[str] = None
    dosage: str
    frequency: str
    reminder_times: List[str] = []
    status: str
    user_email: str
    user_name: str

    model_config = {"from_attributes": True}


class MedicationRemindersResponse(BaseModel):
    """Response for medication reminders query"""
    reminders: List[MedicationReminderInfo]
    total: int

    model_config = {"from_attributes": True}


class SendNotificationResponse(BaseModel):
    """Response after sending a notification"""
    success: bool
    notification_id: str
    message: str
    sent_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
