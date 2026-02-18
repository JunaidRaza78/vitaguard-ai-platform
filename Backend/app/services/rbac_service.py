"""
Role-Based Access Control Service
Family-scoped roles with permission checks.
"""

import logging
from typing import Optional, Dict, Any, List
from enum import Enum

logger = logging.getLogger(__name__)


class FamilyRole(str, Enum):
    """Roles within a family."""
    ADMIN = "admin"          # Full access — can manage members, settings
    CAREGIVER = "caregiver"  # Can view/edit health data for dependents
    MEMBER = "member"        # Can view/edit own data, view family summary
    VIEWER = "viewer"        # Read-only access to family data


ROLE_PERMISSIONS = {
    FamilyRole.ADMIN: {
        "family.manage", "family.invite", "family.remove",
        "member.view", "member.edit", "member.delete",
        "vitals.view", "vitals.record", "vitals.delete",
        "medications.manage", "notifications.manage",
        "reports.view", "reports.export",
        "settings.manage",
    },
    FamilyRole.CAREGIVER: {
        "member.view", "member.edit",
        "vitals.view", "vitals.record",
        "medications.manage", "notifications.manage",
        "reports.view", "reports.export",
    },
    FamilyRole.MEMBER: {
        "member.view",
        "vitals.view", "vitals.record",
        "reports.view",
    },
    FamilyRole.VIEWER: {
        "member.view",
        "vitals.view",
        "reports.view",
    },
}


class RBACService:
    """Service for role-based access control."""

    def has_permission(self, role: str, permission: str) -> bool:
        """Check if a role has a specific permission."""
        try:
            fr = FamilyRole(role)
            return permission in ROLE_PERMISSIONS.get(fr, set())
        except ValueError:
            return False

    def get_permissions(self, role: str) -> List[str]:
        """Get all permissions for a role."""
        try:
            fr = FamilyRole(role)
            return sorted(ROLE_PERMISSIONS.get(fr, set()))
        except ValueError:
            return []

    def get_user_role_in_family(self, user_id: str, family_id: str) -> Optional[str]:
        """Get user's role in a family from Neo4j."""
        try:
            from shared.database.neo4j.operations.family_ops import FamilyOperations
            family_ops = FamilyOperations()
            members = family_ops.get_family_members(family_id)

            for member in members:
                if member.get("userId") == user_id:
                    return member.get("role", FamilyRole.MEMBER.value)

            return None
        except Exception as e:
            logger.error(f"Error getting user role: {e}")
            return None

    def check_family_access(
        self, user_id: str, family_id: str, permission: str
    ) -> bool:
        """Check if a user has permission in a family."""
        role = self.get_user_role_in_family(user_id, family_id)
        if not role:
            return False
        return self.has_permission(role, permission)

    def get_all_roles(self) -> List[Dict[str, Any]]:
        """Get all available roles with their permissions."""
        return [
            {
                "role": role.value,
                "permissions": sorted(perms),
                "description": {
                    FamilyRole.ADMIN: "Full family management access",
                    FamilyRole.CAREGIVER: "Can manage health data for dependents",
                    FamilyRole.MEMBER: "Can manage own health data",
                    FamilyRole.VIEWER: "Read-only access to family data",
                }.get(role, ""),
            }
            for role, perms in ROLE_PERMISSIONS.items()
        ]


# Singleton
rbac_service = RBACService()
