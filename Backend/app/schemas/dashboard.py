"""
Family Health Dashboard Schemas
Pydantic models for dashboard endpoints
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ==========================================
# ENUMS
# ==========================================

class HealthEventType(str, Enum):
    VISIT = "visit"
    VITAL_READING = "vital_reading"
    MEDICATION_CHANGE = "medication_change"
    LAB_RESULT = "lab_result"
    VACCINATION = "vaccination"
    CONDITION_DIAGNOSED = "condition_diagnosed"


class EventSeverity(str, Enum):
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"


class RiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


# ==========================================
# REQUEST SCHEMAS
# ==========================================

class HealthEventCreate(BaseModel):
    event_type: HealthEventType
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    event_date: datetime
    provider_name: Optional[str] = None
    location: Optional[str] = None
    event_data: Optional[Dict[str, Any]] = None
    severity: Optional[EventSeverity] = None

    model_config = {"from_attributes": True}


class HealthEventUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    event_date: Optional[datetime] = None
    provider_name: Optional[str] = None
    location: Optional[str] = None
    event_data: Optional[Dict[str, Any]] = None
    severity: Optional[EventSeverity] = None

    model_config = {"from_attributes": True}


# ==========================================
# RESPONSE SCHEMAS
# ==========================================

class HealthEventResponse(BaseModel):
    event_id: str
    user_id: str
    event_type: str
    title: str
    description: Optional[str] = None
    event_date: datetime
    provider_name: Optional[str] = None
    location: Optional[str] = None
    event_data: Optional[Dict[str, Any]] = None
    severity: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MemberHealthOverview(BaseModel):
    userId: str
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    conditionCount: int = 0
    conditionNames: List[str] = []
    medicationCount: int = 0
    medicationNames: List[str] = []
    recentVitals: List[Dict[str, Any]] = []

    model_config = {"from_attributes": True}


class FamilyDashboardResponse(BaseModel):
    family_id: str
    family_name: Optional[str] = None
    members: List[MemberHealthOverview]
    total_members: int

    model_config = {"from_attributes": True}


class ConditionDetail(BaseModel):
    conditionId: Optional[str] = None
    name: Optional[str] = None
    category: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    diagnosedDate: Optional[str] = None

    model_config = {"from_attributes": True}


class MedicationDetail(BaseModel):
    medicationId: Optional[str] = None
    name: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    startDate: Optional[str] = None

    model_config = {"from_attributes": True}


class MemberDetailResponse(BaseModel):
    userId: str
    name: Optional[str] = None
    conditions: List[ConditionDetail] = []
    medications: List[MedicationDetail] = []
    recentEvents: List[HealthEventResponse] = []

    model_config = {"from_attributes": True}


class HereditaryRisk(BaseModel):
    conditionId: Optional[str] = None
    conditionName: str
    category: Optional[str] = None
    icdCode: Optional[str] = None
    riskScore: float
    riskLevel: str

    model_config = {"from_attributes": True}


class RiskScoreResponse(BaseModel):
    user_id: str
    user_name: Optional[str] = None
    risks: List[HereditaryRisk]
    overall_risk_level: str
    generated_at: datetime

    model_config = {"from_attributes": True}


class ConditionHeatmapEntry(BaseModel):
    conditionName: str
    category: Optional[str] = None
    affectedMembers: List[Dict[str, Any]]
    memberCount: int

    model_config = {"from_attributes": True}


class FamilyConditionHeatmapResponse(BaseModel):
    family_id: str
    conditions: List[ConditionHeatmapEntry]

    model_config = {"from_attributes": True}


class TimelineResponse(BaseModel):
    user_id: str
    events: List[HealthEventResponse]
    total: int
    has_more: bool

    model_config = {"from_attributes": True}
