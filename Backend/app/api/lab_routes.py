"""
Lab Report API Endpoints
REST API for lab result interpretation, storage, and AI analysis
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import Optional, Dict
from pydantic import BaseModel, Field
import logging

from app.middleware.auth import get_current_active_user
from app.services.lab_report_service import lab_report_service
from app.services.emergency_service import emergency_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/labs",
    tags=["Lab Reports"],
    responses={404: {"description": "Not found"}},
)


# ==========================================
# REQUEST SCHEMAS
# ==========================================

class LabResultsRequest(BaseModel):
    """Submit structured lab results for interpretation."""
    results: Dict[str, float] = Field(..., description="Map of test_key -> value")
    user_context: Optional[str] = Field(None, description="Optional patient context")

    model_config = {"json_schema_extra": {"examples": [{"results": {"glucose": 125, "hemoglobin": 10.5, "tsh": 6.0}}]}}


class TextReportRequest(BaseModel):
    """Submit free-text lab report for parsing."""
    text: str = Field(..., description="Raw text from lab report")
    user_context: Optional[str] = None


class StoreLabResultRequest(BaseModel):
    """Store a single lab result."""
    test_key: str
    value: float
    report_date: str
    report_id: Optional[str] = None


class EmergencyCheckRequest(BaseModel):
    """Check a message for emergency indicators."""
    message: str


# ==========================================
# ENDPOINTS
# ==========================================

@router.post(
    "/interpret",
    summary="Interpret lab results",
    description="Submit structured lab results for AI-powered interpretation",
)
async def interpret_lab_results(
    data: LabResultsRequest,
    current_user: dict = Depends(get_current_active_user),
):
    """Interpret lab results with classification and AI summary."""
    try:
        result = lab_report_service.interpret_lab_results(
            results=data.results,
            user_context=data.user_context,
        )
        return result
    except Exception as e:
        logger.error(f"Error interpreting lab results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to interpret lab results",
        )


@router.post(
    "/parse-text",
    summary="Parse text lab report",
    description="Parse free-text lab report and interpret results",
)
async def parse_text_report(
    data: TextReportRequest,
    current_user: dict = Depends(get_current_active_user),
):
    """Parse free-text lab report, extract values, and interpret."""
    try:
        parsed = lab_report_service.parse_text_report(data.text)
        if not parsed:
            return {"parsed_results": {}, "message": "No lab values could be extracted from the text."}

        interpretation = lab_report_service.interpret_lab_results(
            results=parsed,
            user_context=data.user_context,
        )
        return {
            "parsed_results": parsed,
            "interpretation": interpretation,
        }
    except Exception as e:
        logger.error(f"Error parsing text report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to parse lab report",
        )


@router.post(
    "/store",
    status_code=status.HTTP_201_CREATED,
    summary="Store lab result",
    description="Store a lab result in Neo4j",
)
async def store_lab_result(
    data: StoreLabResultRequest,
    current_user: dict = Depends(get_current_active_user),
):
    """Store a single lab result in Neo4j for the current user."""
    try:
        result = lab_report_service.store_lab_result(
            user_id=current_user["user_id"],
            test_key=data.test_key,
            value=data.value,
            report_date=data.report_date,
            report_id=data.report_id,
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store lab result",
            )
        return {"success": True, "result": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error storing lab result: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store lab result",
        )


@router.get(
    "/reference-ranges",
    summary="Get reference ranges",
    description="Get all available lab test reference ranges",
)
async def get_reference_ranges(
    current_user: dict = Depends(get_current_active_user),
):
    """Get all available lab test reference ranges."""
    from app.services.lab_report_service import LAB_REFERENCE_RANGES
    return {
        "tests": {
            k: {
                "name": v["name"],
                "unit": v["unit"],
                "low": v["low"],
                "high": v["high"],
                "category": v["category"],
            }
            for k, v in LAB_REFERENCE_RANGES.items()
        }
    }


@router.post(
    "/emergency-check",
    summary="Check for emergency",
    description="Analyze text for emergency medical indicators",
)
async def check_emergency(
    data: EmergencyCheckRequest,
    current_user: dict = Depends(get_current_active_user),
):
    """Check a message for emergency indicators."""
    try:
        result = emergency_service.analyze_message(data.message)
        if result.get("is_emergency"):
            emergency_service.create_emergency_notification(
                user_id=current_user["user_id"],
                severity=result["severity"],
                message=result.get("response", ""),
            )
        return result
    except Exception as e:
        logger.error(f"Error checking emergency: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check emergency",
        )
