"""
Vitals & Health Dashboard API Endpoints
REST API for vital signs tracking, anomaly detection, risk scoring,
and family health timeline
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional
import logging

from app.schemas.vitals import (
    VitalRecordCreate,
    BloodPressureRecordCreate,
    VitalRecordResponse,
    VitalTrendResponse,
    AnomalyResponse,
    RiskScoreResponse,
    LatestVitalsResponse,
    FamilyTimelineResponse,
    DashboardSummaryResponse,
)
from app.middleware.auth import get_current_active_user
from app.services.vitals_service import vitals_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/vitals",
    tags=["Vitals & Health Dashboard"],
    responses={404: {"description": "Not found"}},
)


# ==========================================
# RECORD VITALS
# ==========================================

@router.post(
    "/record",
    response_model=VitalRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a vital sign",
    description="Record a new vital sign measurement with automatic anomaly detection",
)
async def record_vital(
    vital_data: VitalRecordCreate,
    current_user: dict = Depends(get_current_active_user),
):
    """Record a new vital sign measurement."""
    try:
        result = vitals_service.record_vital(
            user_id=current_user["user_id"],
            vital_type=vital_data.vital_type.value,
            value=vital_data.value,
            unit=vital_data.unit,
            date=vital_data.date,
            time=vital_data.time,
            notes=vital_data.notes,
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to record vital sign",
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording vital: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record vital sign",
        )


@router.post(
    "/blood-pressure",
    response_model=list[VitalRecordResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Record blood pressure",
    description="Record systolic, diastolic, and optional heart rate together",
)
async def record_blood_pressure(
    bp_data: BloodPressureRecordCreate,
    current_user: dict = Depends(get_current_active_user),
):
    """Record blood pressure (systolic + diastolic + optional heart rate)."""
    try:
        results = vitals_service.record_blood_pressure(
            user_id=current_user["user_id"],
            systolic=bp_data.systolic,
            diastolic=bp_data.diastolic,
            date=bp_data.date,
            heart_rate=bp_data.heart_rate,
            time=bp_data.time,
            notes=bp_data.notes,
        )
        if not results:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to record blood pressure",
            )
        return results
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording blood pressure: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record blood pressure",
        )


# ==========================================
# VITALS TRENDS
# ==========================================

@router.get(
    "/trends/{user_id}",
    response_model=VitalTrendResponse,
    summary="Get vitals trend",
    description="Get chart-ready trend data for a specific vital type",
)
async def get_vitals_trend(
    user_id: str,
    vital_type: str = Query(..., description="Type of vital sign"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: dict = Depends(get_current_active_user),
):
    """Get chart-ready trend data for a specific vital type."""
    try:
        return vitals_service.get_vitals_trend(
            user_id=user_id,
            vital_type=vital_type,
            start_date=start_date,
            end_date=end_date,
        )
    except Exception as e:
        logger.error(f"Error getting vitals trend: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get vitals trend",
        )


# ==========================================
# LATEST VITALS
# ==========================================

@router.get(
    "/latest/{user_id}",
    response_model=LatestVitalsResponse,
    summary="Get latest vitals",
    description="Get the most recent reading for each vital type",
)
async def get_latest_vitals(
    user_id: str,
    current_user: dict = Depends(get_current_active_user),
):
    """Get the most recent reading for each vital type."""
    try:
        return vitals_service.get_latest_vitals(user_id)
    except Exception as e:
        logger.error(f"Error getting latest vitals: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get latest vitals",
        )


# ==========================================
# ANOMALY DETECTION
# ==========================================

@router.get(
    "/anomalies/{user_id}",
    response_model=AnomalyResponse,
    summary="Detect anomalies",
    description="Detect out-of-range vital readings for a user",
)
async def detect_anomalies(
    user_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    current_user: dict = Depends(get_current_active_user),
):
    """Detect out-of-range vital readings for a user."""
    try:
        return vitals_service.detect_anomalies(user_id, limit)
    except Exception as e:
        logger.error(f"Error detecting anomalies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to detect anomalies",
        )


# ==========================================
# RISK SCORING
# ==========================================

@router.get(
    "/risk-scores/{user_id}",
    response_model=RiskScoreResponse,
    summary="Calculate risk scores",
    description="Calculate cardiovascular, diabetes, obesity, and hypertension risk",
)
async def get_risk_scores(
    user_id: str,
    current_user: dict = Depends(get_current_active_user),
):
    """Calculate health risk scores based on latest vitals."""
    try:
        return vitals_service.calculate_risk_scores(user_id)
    except Exception as e:
        logger.error(f"Error calculating risk scores: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate risk scores",
        )


# ==========================================
# FAMILY TIMELINE
# ==========================================

@router.get(
    "/family-timeline/{family_id}",
    response_model=FamilyTimelineResponse,
    summary="Family health timeline",
    description="Get unified health timeline for all family members",
)
async def get_family_timeline(
    family_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    current_user: dict = Depends(get_current_active_user),
):
    """Get unified health timeline for all family members."""
    try:
        return vitals_service.get_family_timeline(family_id, limit)
    except Exception as e:
        logger.error(f"Error getting family timeline: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get family timeline",
        )


# ==========================================
# DASHBOARD SUMMARY
# ==========================================

@router.get(
    "/dashboard/{user_id}",
    response_model=DashboardSummaryResponse,
    summary="Dashboard summary",
    description="Get aggregated dashboard with vitals, anomalies, medications, and risk scores",
)
async def get_dashboard_summary(
    user_id: str,
    current_user: dict = Depends(get_current_active_user),
):
    """Get aggregated dashboard summary for a user."""
    try:
        return vitals_service.get_dashboard_summary(user_id)
    except Exception as e:
        logger.error(f"Error getting dashboard summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get dashboard summary",
        )


# ==========================================
# CONVENIENCE ENDPOINTS (user from JWT)
# ==========================================

@router.get(
    "/my/anomalies",
    response_model=AnomalyResponse,
    summary="My anomalies",
)
async def get_my_anomalies(
    limit: int = Query(default=50, ge=1, le=200),
    current_user: dict = Depends(get_current_active_user),
):
    """Detect anomalies for the currently authenticated user."""
    try:
        return vitals_service.detect_anomalies(current_user["user_id"], limit)
    except Exception as e:
        logger.error(f"Error detecting anomalies: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to detect anomalies")


@router.get(
    "/my/risk-scores",
    response_model=RiskScoreResponse,
    summary="My risk scores",
)
async def get_my_risk_scores(
    current_user: dict = Depends(get_current_active_user),
):
    """Calculate risk scores for the currently authenticated user."""
    try:
        return vitals_service.calculate_risk_scores(current_user["user_id"])
    except Exception as e:
        logger.error(f"Error calculating risk scores: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to calculate risk scores")


@router.get(
    "/my/latest",
    response_model=LatestVitalsResponse,
    summary="My latest vitals",
)
async def get_my_latest_vitals(
    current_user: dict = Depends(get_current_active_user),
):
    """Get latest vitals for the currently authenticated user."""
    try:
        return vitals_service.get_latest_vitals(current_user["user_id"])
    except Exception as e:
        logger.error(f"Error getting latest vitals: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get latest vitals")
