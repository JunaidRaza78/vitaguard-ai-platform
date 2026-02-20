"""
Vitals & Health Dashboard Schemas
Pydantic models for vitals tracking, anomaly detection, and risk scoring
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ==========================================
# ENUMS
# ==========================================

class VitalType(str, Enum):
    BLOOD_PRESSURE_SYSTOLIC = "blood_pressure_systolic"
    BLOOD_PRESSURE_DIASTOLIC = "blood_pressure_diastolic"
    HEART_RATE = "heart_rate"
    TEMPERATURE = "temperature"
    WEIGHT = "weight"
    HEIGHT = "height"
    GLUCOSE = "glucose"
    OXYGEN_SATURATION = "oxygen_saturation"
    RESPIRATORY_RATE = "respiratory_rate"
    BMI = "bmi"


class AnomalyLevel(str, Enum):
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"


class RiskCategory(str, Enum):
    CARDIOVASCULAR = "cardiovascular"
    HYPERTENSION = "hypertension"
    FEVER = "fever"
    HEART_RATE = "heart rate"


# ==========================================
# REQUEST SCHEMAS
# ==========================================

class VitalRecordCreate(BaseModel):
    """Schema for recording a vital sign measurement."""
    vital_type: VitalType
    value: float = Field(..., description="Numeric value of the measurement")
    unit: str = Field(..., max_length=50, description="Unit of measurement")
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    time: Optional[str] = Field(None, description="Time in HH:MM:SS format")
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


class BloodPressureRecordCreate(BaseModel):
    """Schema for recording blood pressure (systolic + diastolic together)."""
    systolic: float = Field(..., ge=40, le=300, description="Systolic pressure in mmHg")
    diastolic: float = Field(..., ge=20, le=200, description="Diastolic pressure in mmHg")
    heart_rate: Optional[float] = Field(None, ge=20, le=300, description="Heart rate in bpm")
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    time: Optional[str] = Field(None, description="Time in HH:MM:SS format")
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


# ==========================================
# RESPONSE SCHEMAS
# ==========================================

class VitalRecordResponse(BaseModel):
    """Response for a single vital record."""
    vital_id: str
    vital_type: str
    value: float
    unit: str
    date: str
    time: Optional[str] = None
    notes: Optional[str] = None
    status: AnomalyLevel = AnomalyLevel.NORMAL

    model_config = {"from_attributes": True}


class VitalTrendPoint(BaseModel):
    """A single data point in a vitals trend."""
    date: str
    time: Optional[str] = None
    value: float
    status: AnomalyLevel = AnomalyLevel.NORMAL

    model_config = {"from_attributes": True}


class VitalTrendResponse(BaseModel):
    """Trend data for a specific vital type, chart-ready."""
    user_id: str
    vital_type: str
    unit: str
    data_points: List[VitalTrendPoint] = []
    statistics: Dict[str, Any] = {}
    normal_range: Dict[str, float] = {}
    total_readings: int = 0

    model_config = {"from_attributes": True}


class AnomalyAlert(BaseModel):
    """A single anomaly alert for an out-of-range vital."""
    vital_id: str
    vital_type: str
    value: float
    unit: str
    date: str
    level: AnomalyLevel
    message: str
    normal_range: str

    model_config = {"from_attributes": True}


class AnomalyResponse(BaseModel):
    """Response containing all anomaly alerts for a user."""
    user_id: str
    alerts: List[AnomalyAlert] = []
    total_alerts: int = 0
    critical_count: int = 0
    warning_count: int = 0

    model_config = {"from_attributes": True}


class RiskScoreItem(BaseModel):
    """A single risk score for a health category."""
    category: RiskCategory
    score: float = Field(..., ge=0, le=100, description="Risk score 0-100")
    level: AnomalyLevel
    contributing_factors: List[str] = []
    recommendation: str = ""

    model_config = {"from_attributes": True}


class RiskScoreResponse(BaseModel):
    """Comprehensive risk score response."""
    user_id: str
    risk_scores: List[RiskScoreItem] = []
    overall_risk_level: AnomalyLevel = AnomalyLevel.NORMAL
    generated_at: datetime

    model_config = {"from_attributes": True}


class LatestVitalsResponse(BaseModel):
    """Latest reading for each vital type."""
    user_id: str
    vitals: Dict[str, VitalRecordResponse] = {}
    last_updated: Optional[datetime] = None

    model_config = {"from_attributes": True}


class FamilyTimelineEntry(BaseModel):
    """A single entry in the family health timeline."""
    user_id: str
    user_name: Optional[str] = None
    event_type: str
    title: str
    description: Optional[str] = None
    date: str
    severity: Optional[str] = None

    model_config = {"from_attributes": True}


class FamilyTimelineResponse(BaseModel):
    """Unified family health timeline."""
    family_id: str
    entries: List[FamilyTimelineEntry] = []
    total: int = 0

    model_config = {"from_attributes": True}


class DashboardSummaryResponse(BaseModel):
    """Aggregated dashboard summary for a user."""
    user_id: str
    latest_vitals: Dict[str, Any] = {}
    active_medications: List[Dict[str, Any]] = []
    upcoming_appointments: List[Dict[str, Any]] = []
    recent_anomalies: List[AnomalyAlert] = []
    risk_scores: List[RiskScoreItem] = []
    overall_health_status: AnomalyLevel = AnomalyLevel.NORMAL

    model_config = {"from_attributes": True}
