"""
Lab Report API Endpoints
REST API for lab result interpretation, storage, and AI analysis
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
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


# ==========================================
# LAB HISTORY & SAVE
# ==========================================

class SaveLabResultsRequest(BaseModel):
    """Save multiple lab results at once."""
    results: Dict[str, float] = Field(..., description="Map of test_key -> value")
    report_date: str = Field(..., description="Report date (YYYY-MM-DD)")
    report_id: Optional[str] = Field(None, description="Optional report ID")
    ai_summary: Optional[str] = Field(None, description="AI interpretation summary")


@router.post(
    "/save-results",
    status_code=status.HTTP_201_CREATED,
    summary="Save lab results",
    description="Save multiple lab results to Neo4j with optional AI summary",
)
async def save_lab_results(
    data: SaveLabResultsRequest,
    current_user: dict = Depends(get_current_active_user),
):
    """Save multiple lab results at once with optional AI summary."""
    try:
        report_id = data.report_id or f"report-{current_user['user_id']}-{data.report_date}"
        saved_count = 0

        from shared.database.neo4j.neo4j_client import Neo4jClient
        from shared.database.neo4j.operations.vitals_ops import VitalsOperations

        client = Neo4jClient()
        vitals_ops = VitalsOperations(client)

        for test_key, value in data.results.items():
            # Get reference range and classify
            from app.services.lab_report_service import LAB_REFERENCE_RANGES, lab_report_service
            ref = LAB_REFERENCE_RANGES.get(test_key.lower(), {})
            classification = lab_report_service.classify_result(test_key, value)

            result = vitals_ops.create_lab_result(
                user_id=current_user["user_id"],
                test_name=ref.get("name", test_key),
                date=data.report_date,
                result_value=str(value),
                unit=ref.get("unit", ""),
                reference_range=f"{ref.get('low', 0)}-{ref.get('high', 0)}" if ref else "",
                status=classification.get("status", "unknown"),
                lab_report_id=report_id,
            )
            if result:
                saved_count += 1

        # Store AI summary if provided
        summary_metadata = {}
        if data.ai_summary:
            summary_metadata = {
                "ai_summary": data.ai_summary,
                "report_date": data.report_date,
            }

        return {
            "success": True,
            "report_id": report_id,
            "saved_count": saved_count,
            "message": f"Saved {saved_count} lab results",
            "metadata": summary_metadata,
        }
    except Exception as e:
        logger.error(f"Error saving lab results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save lab results",
        )


@router.get(
    "/history",
    summary="Get lab history",
    description="Get all lab reports for the current user, grouped by date",
)
async def get_lab_history(
    current_user: dict = Depends(get_current_active_user),
    limit: int = Query(default=50, ge=1, le=200),
):
    """Get lab report history for the current user."""
    try:
        from shared.database.neo4j.neo4j_client import Neo4jClient
        from shared.database.neo4j.operations.vitals_ops import VitalsOperations

        client = Neo4jClient()
        vitals_ops = VitalsOperations(client)

        # Get all lab results for user
        results = vitals_ops.get_user_lab_results(current_user["user_id"], limit=limit)

        # Group by date
        grouped = {}
        for result in results:
            date_obj = result.get("date", "Unknown")
            # Convert Neo4j date to string if it's a date object
            if hasattr(date_obj, 'year'):
                date_str = f"{date_obj.year:04d}-{date_obj.month:02d}-{date_obj.day:02d}"
            else:
                date_str = str(date_obj) if date_obj else "Unknown"

            if date_str not in grouped:
                grouped[date_str] = {
                    "date": date_str,
                    "report_id": result.get("lab_report_id"),
                    "results": [],
                }
            grouped[date_str]["results"].append({
                "test_name": result.get("testName") or result.get("test_name"),
                "value": result.get("resultValue") or result.get("result_value"),
                "unit": result.get("unit"),
                "reference_range": result.get("referenceRange") or result.get("reference_range"),
                "status": result.get("status"),
            })

        # Convert to sorted list
        history = sorted(grouped.values(), key=lambda x: x["date"], reverse=True)

        return {
            "history": history,
            "total": len(history),
        }
    except Exception as e:
        logger.error(f"Error getting lab history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get lab history",
        )


@router.get(
    "/trend/{test_key}",
    summary="Get trend data",
    description="Get historical values for a specific lab test for trend charting",
)
async def get_lab_trend(
    test_key: str,
    current_user: dict = Depends(get_current_active_user),
    limit: int = Query(default=20, ge=1, le=100),
):
    """Get trend data for a specific lab test."""
    try:
        from shared.database.neo4j.neo4j_client import Neo4jClient
        from app.services.lab_report_service import LAB_REFERENCE_RANGES

        client = Neo4jClient()

        # Get reference range info
        ref = LAB_REFERENCE_RANGES.get(test_key, {})
        test_name = ref.get("name", test_key)

        # Query Neo4j for this specific test over time
        query = """
        MATCH (u:User {userId: $userId})-[:HAS_LAB_RESULT]->(lr:LabResult)
        WHERE lr.testName = $testName
        RETURN lr.date as date, lr.resultValue as value, lr.unit as unit,
               lr.status as status, lr.referenceRange as referenceRange
        ORDER BY lr.date DESC
        LIMIT $limit
        """

        results = client.execute_query(query, {
            "userId": current_user["user_id"],
            "testName": test_name,
            "limit": limit,
        })

        # Format for charting
        trend_data = []
        for r in results:
            try:
                date_obj = r.get("date")
                # Convert Neo4j date to string
                if hasattr(date_obj, 'year'):
                    date_str = f"{date_obj.year:04d}-{date_obj.month:02d}-{date_obj.day:02d}"
                else:
                    date_str = str(date_obj) if date_obj else None

                trend_data.append({
                    "date": date_str,
                    "value": float(r.get("value", 0)),
                    "unit": r.get("unit"),
                    "status": r.get("status"),
                    "reference_range": r.get("referenceRange"),
                })
            except (ValueError, TypeError):
                continue

        # Reverse to show oldest first (for charting)
        trend_data.reverse()

        return {
            "test_key": test_key,
            "test_name": test_name,
            "unit": ref.get("unit", ""),
            "reference_low": ref.get("low"),
            "reference_high": ref.get("high"),
            "trend_data": trend_data,
            "total_points": len(trend_data),
        }
    except Exception as e:
        logger.error(f"Error getting lab trend: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get lab trend",
        )
