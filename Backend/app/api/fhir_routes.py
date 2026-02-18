"""
FHIR R4 API Routes
REST endpoints for FHIR interoperability — export/import health data
in FHIR R4 format.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import logging

from app.middleware.auth import get_current_active_user
from app.services.fhir_service import fhir_service
from app.services.genetic_risk_service import genetic_risk_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/fhir",
    tags=["FHIR Interoperability"],
    responses={404: {"description": "Not found"}},
)


# ==========================================
# SCHEMAS
# ==========================================

class FHIRExportRequest(BaseModel):
    """Request to export user data in FHIR format."""
    include_vitals: bool = True
    include_medications: bool = True


class FHIRImportRequest(BaseModel):
    """Import a FHIR Bundle."""
    bundle: Dict = Field(..., description="FHIR R4 Bundle resource")


class FamilyHistoryEntry(BaseModel):
    """Single family member health history entry."""
    name: Optional[str] = None
    relationship: str
    conditions: List[str]


class GeneticRiskRequest(BaseModel):
    """Request for genetic risk analysis."""
    family_history: List[FamilyHistoryEntry]


# ==========================================
# FHIR ENDPOINTS
# ==========================================

@router.get(
    "/export",
    summary="Export health data as FHIR",
    description="Export all health data as a FHIR R4 Bundle",
)
async def export_fhir(current_user: dict = Depends(get_current_active_user)):
    """Export user's health data as FHIR R4 Bundle."""
    try:
        bundle = fhir_service.export_user_data(current_user["user_id"])
        return bundle
    except Exception as e:
        logger.error(f"FHIR export error: {e}")
        raise HTTPException(status_code=500, detail="Failed to export FHIR data")


@router.get(
    "/patient",
    summary="Get FHIR Patient resource",
    description="Get current user as FHIR Patient resource",
)
async def get_fhir_patient(current_user: dict = Depends(get_current_active_user)):
    """Return current user as FHIR Patient resource."""
    return fhir_service.create_patient_resource(current_user)


@router.post(
    "/import",
    summary="Import FHIR Bundle",
    description="Import health data from a FHIR R4 Bundle",
)
async def import_fhir(
    data: FHIRImportRequest,
    current_user: dict = Depends(get_current_active_user),
):
    """Import FHIR Bundle and convert to internal format."""
    try:
        bundle = data.bundle
        entries = bundle.get("entry", [])
        imported = {"patients": 0, "observations": 0, "medications": 0}

        for entry in entries:
            resource = entry.get("resource", {})
            rtype = resource.get("resourceType", "")
            if rtype == "Patient":
                fhir_service.parse_patient(resource)
                imported["patients"] += 1
            elif rtype == "Observation":
                fhir_service.parse_observation(resource)
                imported["observations"] += 1

        return {"success": True, "imported": imported}
    except Exception as e:
        logger.error(f"FHIR import error: {e}")
        raise HTTPException(status_code=500, detail="Failed to import FHIR data")


# ==========================================
# GENETIC RISK ENDPOINTS
# ==========================================

@router.post(
    "/genetic-risk",
    summary="Analyze genetic risk",
    description="Calculate hereditary risk based on family history",
)
async def analyze_genetic_risk(
    data: GeneticRiskRequest,
    current_user: dict = Depends(get_current_active_user),
):
    """Analyze family history for hereditary risk factors."""
    try:
        family_history = [entry.model_dump() for entry in data.family_history]
        result = genetic_risk_service.analyze_family_risk(family_history)
        return result
    except Exception as e:
        logger.error(f"Genetic risk analysis error: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze genetic risk")


@router.get(
    "/genetic-risk/conditions",
    summary="Get trackable conditions",
    description="List all hereditary conditions that can be tracked",
)
async def get_trackable_conditions(current_user: dict = Depends(get_current_active_user)):
    """GET available hereditary conditions."""
    return {"conditions": genetic_risk_service.get_available_conditions()}
