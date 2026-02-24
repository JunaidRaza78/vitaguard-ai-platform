"""
Family Management API Endpoints
REST API for family CRUD, membership, relationships, and family tree
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import Optional
import uuid
import logging

from app.schemas.family import (
    FamilyCreate,
    FamilyResponse,
    FamilyListResponse,
    FamilyMemberAdd,
    FamilyMemberResponse,
    FamilyMembersListResponse,
    FamilyRelationshipCreate,
    FamilyTreeResponse,
    FamilyTreeNode,
    FamilyTreeRelationship,
)
from app.middleware.auth import get_current_active_user
from shared.database.neo4j.operations.family_ops import FamilyOperations

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/families",
    tags=["Families"],
    responses={404: {"description": "Not found"}},
)


def _get_family_ops() -> FamilyOperations:
    """Get FamilyOperations instance (inherits BaseNeo4jClient with execute_query)."""
    return FamilyOperations()


# ==========================================
# FAMILY CRUD
# ==========================================

@router.post(
    "/",
    response_model=FamilyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_family(
    family_data: FamilyCreate,
    current_user: dict = Depends(get_current_active_user),
):
    """Create a new family and add creator as admin member."""
    try:
        ops = _get_family_ops()
        family_id = str(uuid.uuid4())

        family = ops.create_family(
            familyId=family_id,
            name=family_data.name,
            createdBy=current_user["user_id"],
        )

        if not family:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create family",
            )

        # Auto-add creator as admin member (pass name/email so User node is populated)
        first = current_user.get("first_name", "") or ""
        last = current_user.get("last_name", "") or ""
        full_name = f"{first} {last}".strip() or current_user.get("username", "")
        ops.add_user_to_family(
            userId=current_user["user_id"],
            familyId=family_id,
            role="admin",
            name=full_name,
            email=current_user.get("email"),
        )

        return FamilyResponse(
            familyId=family.get("familyId", ""),
            name=family.get("name", ""),
            createdBy=str(family.get("createdBy") or ""),
            createdAt=str(family.get("createdAt") or ""),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating family: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create family",
        )


@router.get("/me", response_model=FamilyListResponse)
async def get_my_families(
    current_user: dict = Depends(get_current_active_user),
):
    """Get all families the current user belongs to, with member counts."""
    try:
        ops = _get_family_ops()
        results = ops.get_user_families(current_user["user_id"])

        families = []
        for item in results:
            f = item.get("family", {})
            fid = f.get("familyId", "")
            # Get member count for each family
            try:
                members = ops.get_family_members(fid)
                count = len(members)
            except Exception:
                count = 0
            families.append(FamilyResponse(
                familyId=fid,
                name=f.get("name", ""),
                createdBy=str(f.get("createdBy") or ""),
                createdAt=str(f.get("createdAt") or ""),
                member_count=count,
            ))

        return FamilyListResponse(families=families, total=len(families))
    except Exception as e:
        logger.error(f"Error getting user families: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get families",
        )


@router.get("/{family_id}", response_model=FamilyResponse)
async def get_family(
    family_id: str,
    current_user: dict = Depends(get_current_active_user),
):
    """Get family details by ID."""
    try:
        ops = _get_family_ops()
        family = ops.get_family_by_id(family_id)

        if not family:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Family not found",
            )

        return FamilyResponse(
            familyId=family.get("familyId", ""),
            name=family.get("name", ""),
            createdBy=str(family.get("createdBy") or ""),
            createdAt=str(family.get("createdAt") or ""),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting family: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get family",
        )


@router.delete("/{family_id}", status_code=status.HTTP_200_OK)
async def delete_family(
    family_id: str,
    current_user: dict = Depends(get_current_active_user),
):
    """Delete a family (only creator/admin can delete)."""
    try:
        ops = _get_family_ops()
        success = ops.delete_family(family_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family not found")
        return {"message": "Family deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting family: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete family")


# ==========================================
# FAMILY MEMBER RELATIONSHIPS (tree data)
# ==========================================

@router.get("/{family_id}/relationships")
async def get_family_member_relationships(
    family_id: str,
    current_user: dict = Depends(get_current_active_user),
):
    """Get all family-type relationships between members of a family."""
    try:
        ops = _get_family_ops()
        results = ops.get_family_member_relationships(family_id)
        return {"family_id": family_id, "relationships": results}
    except Exception as e:
        logger.error(f"Error getting family relationships: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get family relationships",
        )


# ==========================================
# FAMILY MEMBERS
# ==========================================

@router.get("/{family_id}/members", response_model=FamilyMembersListResponse)
async def get_family_members(
    family_id: str,
    current_user: dict = Depends(get_current_active_user),
):
    """Get all members of a family."""
    try:
        ops = _get_family_ops()
        results = ops.get_family_members(family_id)

        members = []
        for item in results:
            user = item.get("user", {})
            rel = item.get("relationship", {})
            members.append(FamilyMemberResponse(
                userId=user.get("userId", ""),
                name=user.get("name"),
                email=user.get("email"),
                role=rel.get("role"),
                joinedAt=str(rel.get("joinedAt") or ""),
            ))

        return FamilyMembersListResponse(
            family_id=family_id,
            members=members,
            total=len(members),
        )
    except Exception as e:
        logger.error(f"Error getting family members: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get family members",
        )


@router.post("/{family_id}/members", status_code=status.HTTP_201_CREATED)
async def add_family_member(
    family_id: str,
    member_data: FamilyMemberAdd,
    current_user: dict = Depends(get_current_active_user),
):
    """Add a user to a family."""
    try:
        ops = _get_family_ops()

        # Check family exists
        family = ops.get_family_by_id(family_id)
        if not family:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Family not found",
            )

        # Resolve user — try PostgreSQL first, fall back to guest member
        member_name = member_data.name
        member_email = member_data.email
        resolved_user_id = member_data.user_id

        if not resolved_user_id:
            # Try to find registered user by email
            if member_data.email:
                try:
                    from shared.database.postgres.postgres_client import PostgresClient
                    with PostgresClient() as db:
                        pg_user = db.get_user_by_email(member_data.email)
                        if pg_user:
                            resolved_user_id = str(pg_user.user_id)
                            first = getattr(pg_user, "first_name", "") or ""
                            last = getattr(pg_user, "last_name", "") or ""
                            member_name = f"{first} {last}".strip() or getattr(pg_user, "username", "") or pg_user.email
                            member_email = str(pg_user.email)
                except Exception as lookup_err:
                    logger.warning(f"PostgreSQL lookup failed: {lookup_err}")

            # If not found in PostgreSQL → create as guest member in Neo4j
            if not resolved_user_id:
                if not member_name and not member_email:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Provide a name or email to add a family member",
                    )
                resolved_user_id = str(uuid.uuid4())
                if not member_name:
                    member_name = member_email

        success = ops.add_user_to_family(
            userId=resolved_user_id,
            familyId=family_id,
            role=member_data.role.value,
            name=member_name,
            email=member_email,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to add member. User may already be in this family.",
            )

        return {"message": "Member added successfully", "family_id": family_id, "user_id": resolved_user_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding family member: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add family member",
        )


@router.delete("/{family_id}/members/{user_id}")
async def remove_family_member(
    family_id: str,
    user_id: str,
    current_user: dict = Depends(get_current_active_user),
):
    """Remove a user from a family."""
    try:
        ops = _get_family_ops()

        success = ops.remove_user_from_family(userId=user_id, familyId=family_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found in family",
            )

        return {"message": "Member removed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing family member: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove family member",
        )


# ==========================================
# FAMILY RELATIONSHIPS
# ==========================================

@router.post("/relationships", status_code=status.HTTP_201_CREATED)
async def create_family_relationship(
    rel_data: FamilyRelationshipCreate,
    current_user: dict = Depends(get_current_active_user),
):
    """Create a family relationship between two users (PARENT_OF, SPOUSE_OF, etc.)."""
    try:
        ops = _get_family_ops()

        success = ops.create_family_relationship(
            user1_id=rel_data.user1_id,
            relationship_type=rel_data.relationship_type.value,
            user2_id=rel_data.user2_id,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create relationship. Users may not exist.",
            )

        return {
            "message": f"{rel_data.relationship_type.value} relationship created",
            "source": rel_data.user1_id,
            "target": rel_data.user2_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating relationship: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create relationship",
        )


# ==========================================
# FAMILY TREE
# ==========================================

@router.get("/tree/{user_id}", response_model=FamilyTreeResponse)
async def get_family_tree(
    user_id: str,
    depth: int = 2,
    current_user: dict = Depends(get_current_active_user),
):
    """Get family tree for a user up to specified depth."""
    try:
        ops = _get_family_ops()
        results = ops.get_family_tree(user_id, depth=depth)

        nodes_map = {}
        seen_rels: set = set()
        relationships = []

        for item in results:
            path_nodes = item.get("nodes", [])
            path_rels = item.get("rels", [])   # plain dicts from Cypher

            for node in path_nodes:
                node_dict = dict(node) if hasattr(node, "__iter__") else {}
                uid = node_dict.get("userId", "")
                if uid and uid not in nodes_map:
                    nodes_map[uid] = FamilyTreeNode(
                        userId=uid,
                        name=node_dict.get("name"),
                        email=node_dict.get("email"),
                    )

            for rel_dict in path_rels:
                if not isinstance(rel_dict, dict):
                    continue
                src = rel_dict.get("source") or ""
                tgt = rel_dict.get("target") or ""
                rtype = rel_dict.get("type") or ""
                if not src or not tgt:
                    continue
                key = (src, tgt, rtype)
                if key in seen_rels:
                    continue
                seen_rels.add(key)
                relationships.append(FamilyTreeRelationship(
                    source=src,
                    target=tgt,
                    type=rtype,
                ))

        return FamilyTreeResponse(
            user_id=user_id,
            nodes=list(nodes_map.values()),
            relationships=relationships,
        )
    except Exception as e:
        logger.error(f"Error getting family tree: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get family tree",
        )
