"""
Access Control Operations for Neo4j
Handles permissions, roles, and authorization for family and health data
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid


class AccessControlOperations:
    """Access control and permission operations for Neo4j."""

    def __init__(self, client):
        """Initialize with Neo4j client."""
        self.client = client

    # ==================== Permission Checks ====================

    def user_can_add_family_member(
        self,
        user_id: str,
        family_id: str
    ) -> Dict[str, Any]:
        """
        Check if user has permission to add members to family.

        User can add members if they are:
        1. Family creator (createdBy)
        2. Admin role in family
        3. Parent role in family

        Args:
            user_id: User attempting the action
            family_id: Target family

        Returns:
            {
                "has_permission": bool,
                "reason": str,
                "user_role": str or None
            }
        """
        query = """
        MATCH (f:Family {familyId: $familyId})
        OPTIONAL MATCH (u:User {userId: $userId})-[r:MEMBER_OF]->(f)
        RETURN f.createdBy AS creator,
               r.role AS userRole,
               CASE
                   WHEN f.createdBy = $userId THEN true
                   WHEN r.role IN ['admin', 'parent'] THEN true
                   ELSE false
               END AS hasPermission
        """

        params = {
            "userId": user_id,
            "familyId": family_id
        }

        result = self.client.execute_query(query, params)

        if not result:
            return {
                "has_permission": False,
                "reason": "Family not found",
                "user_role": None
            }

        r = result[0]
        has_permission = r["hasPermission"]
        user_role = r["userRole"]

        if has_permission:
            if r["creator"] == user_id:
                reason = "User is family creator"
            else:
                reason = f"User has {user_role} role"
        else:
            if user_role:
                reason = f"User role '{user_role}' does not have permission to add members"
            else:
                reason = "User is not a member of this family"

        return {
            "has_permission": has_permission,
            "reason": reason,
            "user_role": user_role
        }

    def user_can_view_member_data(
        self,
        requesting_user_id: str,
        target_user_id: str
    ) -> Dict[str, Any]:
        """
        Check if user can view another member's health data.

        User can view data if:
        1. It's their own data
        2. They're in same family with appropriate role
        3. They're a guardian of the target user

        Args:
            requesting_user_id: User requesting access
            target_user_id: User whose data is being requested

        Returns:
            {
                "has_permission": bool,
                "reason": str,
                "relationship": str or None
            }
        """
        # Self access always allowed
        if requesting_user_id == target_user_id:
            return {
                "has_permission": True,
                "reason": "Own data",
                "relationship": "self"
            }

        query = """
        MATCH (requestor:User {userId: $requestorId})
        MATCH (target:User {userId: $targetId})

        // Check if in same family
        OPTIONAL MATCH (requestor)-[r1:MEMBER_OF]->(f:Family)<-[r2:MEMBER_OF]-(target)

        // Check if requestor is guardian
        OPTIONAL MATCH (requestor)-[g:GUARDIAN_OF]->(target)

        RETURN
            f.familyId AS familyId,
            r1.role AS requestorRole,
            r2.role AS targetRole,
            g IS NOT NULL AS isGuardian,
            CASE
                WHEN g IS NOT NULL THEN true
                WHEN r1.role IN ['admin', 'parent'] AND f IS NOT NULL THEN true
                ELSE false
            END AS hasPermission
        """

        params = {
            "requestorId": requesting_user_id,
            "targetId": target_user_id
        }

        result = self.client.execute_query(query, params)

        if not result or not result[0]["hasPermission"]:
            return {
                "has_permission": False,
                "reason": "No family relationship or insufficient permissions",
                "relationship": None
            }

        r = result[0]

        if r["isGuardian"]:
            relationship = "guardian"
            reason = "User is guardian of target member"
        elif r["familyId"]:
            relationship = "family"
            reason = f"Same family, requestor role: {r['requestorRole']}"
        else:
            relationship = None
            reason = "Unknown"

        return {
            "has_permission": r["hasPermission"],
            "reason": reason,
            "relationship": relationship
        }

    def user_can_modify_member_data(
        self,
        requesting_user_id: str,
        target_user_id: str
    ) -> Dict[str, Any]:
        """
        Check if user can modify another member's health data.

        More restrictive than viewing - only guardians and admins.

        Args:
            requesting_user_id: User requesting access
            target_user_id: User whose data would be modified

        Returns:
            {
                "has_permission": bool,
                "reason": str
            }
        """
        # Self modification always allowed
        if requesting_user_id == target_user_id:
            return {
                "has_permission": True,
                "reason": "Own data"
            }

        query = """
        MATCH (requestor:User {userId: $requestorId})
        MATCH (target:User {userId: $targetId})

        // Check guardian relationship
        OPTIONAL MATCH (requestor)-[g:GUARDIAN_OF]->(target)

        // Check family admin
        OPTIONAL MATCH (requestor)-[r:MEMBER_OF {role: 'admin'}]->(f:Family)<-[:MEMBER_OF]-(target)

        RETURN
            g IS NOT NULL AS isGuardian,
            f IS NOT NULL AS isFamilyAdmin,
            (g IS NOT NULL OR f IS NOT NULL) AS hasPermission
        """

        params = {
            "requestorId": requesting_user_id,
            "targetId": target_user_id
        }

        result = self.client.execute_query(query, params)

        if not result:
            return {
                "has_permission": False,
                "reason": "No relationship found"
            }

        r = result[0]

        if not r["hasPermission"]:
            return {
                "has_permission": False,
                "reason": "Only guardians and family admins can modify member data"
            }

        if r["isGuardian"]:
            reason = "User is guardian"
        elif r["isFamilyAdmin"]:
            reason = "User is family admin"
        else:
            reason = "Unknown"

        return {
            "has_permission": r["hasPermission"],
            "reason": reason
        }

    # ==================== Secure Operations ====================

    def add_family_member_secure(
        self,
        requesting_user_id: str,
        new_member_user_id: str,
        family_id: str,
        role: str = "member",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Add family member with permission check.

        Args:
            requesting_user_id: User attempting to add member
            new_member_user_id: User to be added
            family_id: Target family
            role: Role for new member (member, parent, child, admin)

        Returns:
            {
                "success": bool,
                "message": str,
                "relationship": dict or None
            }
        """
        # Check permission
        permission = self.user_can_add_family_member(requesting_user_id, family_id)

        if not permission["has_permission"]:
            return {
                "success": False,
                "message": f"Permission denied: {permission['reason']}",
                "relationship": None
            }

        # Check if already member
        check_query = """
        MATCH (u:User {userId: $userId})-[r:MEMBER_OF]->(f:Family {familyId: $familyId})
        RETURN count(r) AS alreadyMember
        """

        check_result = self.client.execute_query(check_query, {
            "userId": new_member_user_id,
            "familyId": family_id
        })

        if check_result and check_result[0]["alreadyMember"] > 0:
            return {
                "success": False,
                "message": "User is already a member of this family",
                "relationship": None
            }

        # Add member
        add_query = """
        MATCH (u:User {userId: $userId})
        MATCH (f:Family {familyId: $familyId})
        CREATE (u)-[r:MEMBER_OF {
            role: $role,
            joinedAt: datetime(),
            addedBy: $addedBy
        }]->(f)
        RETURN r
        """

        add_params = {
            "userId": new_member_user_id,
            "familyId": family_id,
            "role": role,
            "addedBy": requesting_user_id
        }

        result = self.client.execute_query(add_query, add_params)

        if result:
            return {
                "success": True,
                "message": f"Member added successfully as {role}",
                "relationship": dict(result[0]["r"])
            }
        else:
            return {
                "success": False,
                "message": "Failed to add member - user or family not found",
                "relationship": None
            }

    def remove_family_member_secure(
        self,
        requesting_user_id: str,
        member_user_id: str,
        family_id: str
    ) -> Dict[str, Any]:
        """
        Remove family member with permission check.
        Only family creator and admins can remove members.

        Args:
            requesting_user_id: User attempting to remove member
            member_user_id: User to be removed
            family_id: Target family

        Returns:
            {
                "success": bool,
                "message": str
            }
        """
        # Check permission
        permission = self.user_can_add_family_member(requesting_user_id, family_id)

        if not permission["has_permission"]:
            return {
                "success": False,
                "message": f"Permission denied: {permission['reason']}"
            }

        # Prevent removing family creator
        check_query = """
        MATCH (f:Family {familyId: $familyId})
        RETURN f.createdBy = $memberId AS isCreator
        """

        check_result = self.client.execute_query(check_query, {
            "familyId": family_id,
            "memberId": member_user_id
        })

        if check_result and check_result[0]["isCreator"]:
            return {
                "success": False,
                "message": "Cannot remove family creator"
            }

        # Remove member
        remove_query = """
        MATCH (u:User {userId: $userId})-[r:MEMBER_OF]->(f:Family {familyId: $familyId})
        DELETE r
        RETURN count(r) AS removed
        """

        result = self.client.execute_query(remove_query, {
            "userId": member_user_id,
            "familyId": family_id
        })

        if result and result[0]["removed"] > 0:
            return {
                "success": True,
                "message": "Member removed successfully"
            }
        else:
            return {
                "success": False,
                "message": "Member not found in family"
            }

    # ==================== Guardian Relationships ====================

    def create_guardian_relationship(
        self,
        guardian_user_id: str,
        ward_user_id: str,
        relationship_type: str = "parent",
        **kwargs
    ) -> bool:
        """
        Create guardian relationship (parent, legal_guardian, caretaker).
        This grants guardian full access to ward's health data.

        Args:
            guardian_user_id: Guardian user ID
            ward_user_id: Ward (person being cared for) user ID
            relationship_type: parent, legal_guardian, caretaker

        Returns:
            Success status
        """
        query = """
        MATCH (guardian:User {userId: $guardianId})
        MATCH (ward:User {userId: $wardId})
        CREATE (guardian)-[r:GUARDIAN_OF {
            relationshipType: $relationType,
            createdAt: datetime(),
            canViewData: true,
            canModifyData: true
        }]->(ward)
        RETURN count(r) AS created
        """

        params = {
            "guardianId": guardian_user_id,
            "wardId": ward_user_id,
            "relationType": relationship_type
        }

        result = self.client.execute_query(query, params)
        return result[0]["created"] > 0 if result else False

    def get_user_guardians(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all guardians of a user."""
        query = """
        MATCH (guardian:User)-[r:GUARDIAN_OF]->(ward:User {userId: $userId})
        RETURN guardian, r
        """

        result = self.client.execute_query(query, {"userId": user_id})
        return [{
            "guardian": dict(r["guardian"]),
            "relationship": dict(r["r"])
        } for r in result]

    def get_user_wards(self, guardian_user_id: str) -> List[Dict[str, Any]]:
        """Get all people under user's guardianship."""
        query = """
        MATCH (guardian:User {userId: $guardianId})-[r:GUARDIAN_OF]->(ward:User)
        RETURN ward, r
        """

        result = self.client.execute_query(query, {"guardianId": guardian_user_id})
        return [{
            "ward": dict(r["ward"]),
            "relationship": dict(r["r"])
        } for r in result]

    # ==================== Role Management ====================

    def update_family_member_role(
        self,
        requesting_user_id: str,
        target_user_id: str,
        family_id: str,
        new_role: str
    ) -> Dict[str, Any]:
        """
        Update family member's role (requires admin permission).

        Args:
            requesting_user_id: User making the change
            target_user_id: User whose role is changing
            family_id: Target family
            new_role: New role (admin, parent, child, member)

        Returns:
            {
                "success": bool,
                "message": str
            }
        """
        # Check permission
        permission = self.user_can_add_family_member(requesting_user_id, family_id)

        if not permission["has_permission"]:
            return {
                "success": False,
                "message": f"Permission denied: {permission['reason']}"
            }

        # Update role
        query = """
        MATCH (u:User {userId: $userId})-[r:MEMBER_OF]->(f:Family {familyId: $familyId})
        SET r.role = $newRole,
            r.roleUpdatedAt = datetime(),
            r.roleUpdatedBy = $updatedBy
        RETURN r
        """

        params = {
            "userId": target_user_id,
            "familyId": family_id,
            "newRole": new_role,
            "updatedBy": requesting_user_id
        }

        result = self.client.execute_query(query, params)

        if result:
            return {
                "success": True,
                "message": f"Role updated to {new_role}"
            }
        else:
            return {
                "success": False,
                "message": "Failed to update role - member not found"
            }

    # ==================== Audit Trail ====================

    def log_access_attempt(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        granted: bool,
        reason: str
    ) -> bool:
        """
        Log access attempt for audit trail.

        Args:
            user_id: User attempting access
            action: view, modify, delete, etc.
            resource_type: User, HealthRecord, Medication, etc.
            resource_id: ID of resource
            granted: Whether access was granted
            reason: Reason for grant/deny

        Returns:
            Success status
        """
        query = """
        CREATE (log:AccessLog {
            logId: $logId,
            userId: $userId,
            action: $action,
            resourceType: $resourceType,
            resourceId: $resourceId,
            granted: $granted,
            reason: $reason,
            timestamp: datetime()
        })
        RETURN count(log) AS created
        """

        params = {
            "logId": str(uuid.uuid4()),
            "userId": user_id,
            "action": action,
            "resourceType": resource_type,
            "resourceId": resource_id,
            "granted": granted,
            "reason": reason
        }

        result = self.client.execute_query(query, params)
        return result[0]["created"] > 0 if result else False

    def get_access_logs(
        self,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get access logs, optionally filtered by user."""
        query = """
        MATCH (log:AccessLog)
        WHERE $userId IS NULL OR log.userId = $userId
        RETURN log
        ORDER BY log.timestamp DESC
        LIMIT $limit
        """

        result = self.client.execute_query(query, {
            "userId": user_id,
            "limit": limit
        })

        return [dict(r["log"]) for r in result]
