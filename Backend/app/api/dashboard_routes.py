"""
Family Health Dashboard API Endpoints
REST API for dashboard overview, member details, health events, timelines, and risk scores
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional
from datetime import datetime
import logging

from app.schemas.dashboard import (
    HealthEventCreate,
    HealthEventResponse,
    FamilyDashboardResponse,
    MemberDetailResponse,
    RiskScoreResponse,
    TimelineResponse,
    FamilyConditionHeatmapResponse,
)
from app.middleware.auth import get_current_active_user
from app.services.dashboard_service import dashboard_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/dashboard",
    tags=["Dashboard"],
    responses={404: {"description": "Not found"}},
)


# ==========================================
# FAMILY DASHBOARD OVERVIEW
# ==========================================

@router.get(
    "/family/{family_id}",
    response_model=FamilyDashboardResponse,
    summary="Family health overview",
    description="Get aggregated health overview for all family members",
)
async def get_family_dashboard(
    family_id: str,
    current_user: dict = Depends(get_current_active_user),
):
    """Get aggregated health overview for all family members."""
    try:
        result = dashboard_service.get_family_dashboard(family_id)
        return result
    except Exception as e:
        logger.error(f"Error getting family dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get family dashboard",
        )


@router.get(
    "/family/{family_id}/conditions",
    response_model=FamilyConditionHeatmapResponse,
    summary="Family condition heatmap",
    description="Get condition distribution across family members",
)
async def get_family_condition_heatmap(
    family_id: str,
    current_user: dict = Depends(get_current_active_user),
):
    """Get condition distribution across family members."""
    try:
        return dashboard_service.get_family_condition_heatmap(family_id)
    except Exception as e:
        logger.error(f"Error getting condition heatmap: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get condition heatmap",
        )


# ==========================================
# MEMBER DETAIL
# ==========================================

@router.get(
    "/member/{user_id}",
    response_model=MemberDetailResponse,
    summary="Member health detail",
    description="Get detailed health information for a single family member",
)
async def get_member_detail(
    user_id: str,
    current_user: dict = Depends(get_current_active_user),
):
    """Get detailed health information for a single family member."""
    try:
        result = dashboard_service.get_member_detail(user_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found",
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting member detail: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get member detail",
        )


# ==========================================
# HEALTH EVENT TIMELINE
# ==========================================

@router.post(
    "/events",
    response_model=HealthEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create health event",
    description="Create a new health event for the current user",
)
async def create_health_event(
    event_data: HealthEventCreate,
    current_user: dict = Depends(get_current_active_user),
):
    """Create a new health event for the current user."""
    try:
        result = dashboard_service.create_health_event(
            user_id=current_user["user_id"],
            event_data=event_data,
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create health event",
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating health event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create health event",
        )


@router.get(
    "/timeline/{user_id}",
    response_model=TimelineResponse,
    summary="Health event timeline",
    description="Get chronological health event timeline for a member",
)
async def get_user_timeline(
    user_id: str,
    event_types: Optional[str] = Query(None, description="Comma-separated event types filter"),
    start_date: Optional[datetime] = Query(None, description="Filter events after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter events before this date"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(get_current_active_user),
):
    """Get chronological health event timeline for a member."""
    try:
        types_list = event_types.split(",") if event_types else None
        return dashboard_service.get_user_timeline(
            user_id=user_id,
            event_types=types_list,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        logger.error(f"Error getting timeline: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get timeline",
        )


# ==========================================
# RISK SCORING
# ==========================================

@router.get(
    "/risk/{user_id}",
    response_model=RiskScoreResponse,
    summary="Hereditary risk scores",
    description="Calculate hereditary risk scores based on family history graph",
)
async def get_risk_scores(
    user_id: str,
    current_user: dict = Depends(get_current_active_user),
):
    """Calculate hereditary risk scores based on family history graph."""
    try:
        return dashboard_service.get_hereditary_risk_scores(user_id)
    except Exception as e:
        logger.error(f"Error calculating risk scores: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate risk scores",
        )


# ==========================================
# AUDIT TRAIL
# ==========================================

@router.get(
    "/audit/trail",
    summary="Get audit trail",
    description="Get access audit trail for compliance (admin/user access)",
)
async def get_audit_trail(
    current_user: dict = Depends(get_current_active_user),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """Get audit trail entries for compliance tracking."""
    from shared.database.postgres.postgres_client import PostgresClient
    from shared.database.postgres.models import AuditLog

    try:
        db_client = PostgresClient()
        with db_client as db:
            session = db.get_session()

            # Build query
            query = session.query(AuditLog)

            # Filter by user_id if provided (or current user if not admin)
            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
            else:
                # Non-admin users can only see their own audit logs
                if not current_user.get("is_superuser"):
                    query = query.filter(AuditLog.user_id == current_user["user_id"])

            # Filter by action type
            if action:
                query = query.filter(AuditLog.action.like(f"%{action}%"))

            # Order by most recent first
            query = query.order_by(AuditLog.created_at.desc())

            # Paginate
            total = query.count()
            logs = query.offset(offset).limit(limit).all()

            # Format response
            results = []
            for log in logs:
                results.append({
                    "log_id": log.log_id,
                    "user_id": log.user_id,
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent,
                    "response_status": log.response_status,
                    "details": log.details,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                })

            return {
                "audit_logs": results,
                "total": total,
                "page": (offset // limit) + 1,
                "page_size": limit,
            }

    except Exception as e:
        logger.error(f"Error fetching audit trail: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch audit trail",
        )
