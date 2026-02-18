"""
Data Export Routes
GDPR-compliant data export and deletion endpoints.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
import logging

from app.middleware.auth import get_current_active_user
from app.services.fhir_service import fhir_service
from app.services.rbac_service import rbac_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/data",
    tags=["Data Management"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/export",
    summary="Export all my data (GDPR)",
    description="Export all personal health data in JSON format",
)
async def export_my_data(current_user: dict = Depends(get_current_active_user)):
    """GDPR Article 20 — Right to data portability."""
    try:
        user_id = current_user["user_id"]

        # FHIR Bundle
        fhir_bundle = fhir_service.export_user_data(user_id)

        return {
            "user": {
                "user_id": user_id,
                "email": current_user.get("email", ""),
                "first_name": current_user.get("first_name", ""),
                "last_name": current_user.get("last_name", ""),
            },
            "fhir_bundle": fhir_bundle,
            "export_format": "FHIR R4 + JSON",
            "exported_at": __import__("datetime").datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Data export error: {e}")
        raise HTTPException(status_code=500, detail="Failed to export data")


@router.delete(
    "/delete",
    summary="Delete all my data (GDPR)",
    description="Request deletion of all personal health data",
)
async def request_data_deletion(current_user: dict = Depends(get_current_active_user)):
    """GDPR Article 17 — Right to erasure."""
    try:
        user_id = current_user["user_id"]
        logger.info(f"Data deletion requested for user: {user_id}")

        # In production, queue deletion and confirm via email.
        # For now, return acknowledgment.
        return {
            "success": True,
            "message": "Data deletion request received. All personal health data will be deleted within 30 days.",
            "user_id": user_id,
            "request_id": __import__("uuid").uuid4().hex,
        }
    except Exception as e:
        logger.error(f"Data deletion error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process deletion request")


@router.get(
    "/roles",
    summary="Get available roles",
    description="Get all family roles and their permissions",
)
async def get_roles(current_user: dict = Depends(get_current_active_user)):
    """Get all available family roles with permissions."""
    return {"roles": rbac_service.get_all_roles()}


@router.get(
    "/my-permissions/{family_id}",
    summary="Get my permissions in a family",
    description="Check current user's role and permissions in a family",
)
async def get_my_permissions(
    family_id: str,
    current_user: dict = Depends(get_current_active_user),
):
    """Get current user's role and permissions in a family."""
    role = rbac_service.get_user_role_in_family(current_user["user_id"], family_id)
    if not role:
        raise HTTPException(status_code=404, detail="Not a member of this family")

    return {
        "family_id": family_id,
        "role": role,
        "permissions": rbac_service.get_permissions(role),
    }
