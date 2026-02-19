"""
Family Management Schemas
Pydantic models for family CRUD and relationships
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class FamilyRelationshipType(str, Enum):
    PARENT_OF = "PARENT_OF"
    CHILD_OF = "CHILD_OF"
    SPOUSE_OF = "SPOUSE_OF"
    SIBLING_OF = "SIBLING_OF"


class FamilyMemberRole(str, Enum):
    ADMIN = "admin"
    PARENT = "parent"
    MEMBER = "member"


# ==========================================
# REQUEST SCHEMAS
# ==========================================

class FamilyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)

    model_config = {"from_attributes": True}


class FamilyMemberAdd(BaseModel):
    user_id: Optional[str] = Field(default=None, min_length=1)
    email: Optional[str] = Field(default=None)
    role: FamilyMemberRole = Field(default=FamilyMemberRole.MEMBER)

    model_config = {"from_attributes": True}


class FamilyRelationshipCreate(BaseModel):
    user1_id: str = Field(..., description="Source user ID")
    relationship_type: FamilyRelationshipType
    user2_id: str = Field(..., description="Target user ID")

    model_config = {"from_attributes": True}


# ==========================================
# RESPONSE SCHEMAS
# ==========================================

class FamilyResponse(BaseModel):
    familyId: str
    name: str
    createdBy: Optional[str] = None
    createdAt: Optional[str] = None

    model_config = {"from_attributes": True}


class FamilyMemberResponse(BaseModel):
    userId: str
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    joinedAt: Optional[str] = None

    model_config = {"from_attributes": True}


class FamilyMembersListResponse(BaseModel):
    family_id: str
    members: List[FamilyMemberResponse]
    total: int

    model_config = {"from_attributes": True}


class FamilyListResponse(BaseModel):
    families: List[FamilyResponse]
    total: int

    model_config = {"from_attributes": True}


class FamilyTreeNode(BaseModel):
    userId: str
    name: Optional[str] = None
    email: Optional[str] = None

    model_config = {"from_attributes": True}


class FamilyTreeRelationship(BaseModel):
    source: str
    target: str
    type: str

    model_config = {"from_attributes": True}


class FamilyTreeResponse(BaseModel):
    user_id: str
    nodes: List[FamilyTreeNode]
    relationships: List[FamilyTreeRelationship]

    model_config = {"from_attributes": True}
