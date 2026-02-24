"""
Family operations for Neo4j database.
Handles all CRUD operations for Family nodes and family relationships.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from shared.database.neo4j.operations.graph_ops import GraphOperations
from shared.logging import get_logger

logger = get_logger('neo4j.family_ops')


class FamilyOperations(GraphOperations):
    """Family-specific database operations."""

    # ==================== Family Node Operations ====================

    def create_family(
        self,
        familyId: str,
        name: str,
        createdBy: str,
        createdAt: Optional[str] = None,
        database: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a Family node.

        Args:
            familyId: UUID unique identifier
            name: Family name
            createdBy: User ID who created the family
            createdAt: Creation timestamp (optional, defaults to now)
            database: Database name (optional)

        Returns:
            Created family node or None
        """
        try:
            properties = {
                "familyId": familyId,
                "name": name,
                "createdBy": createdBy,
                "createdAt": createdAt or datetime.now(timezone.utc).isoformat()
            }

            query = "CREATE (f:Family $properties) RETURN f"
            logger.info(f"Creating Family node: {name}")
            records = self.execute_query(query, {"properties": properties}, database)

            if records:
                family = dict(records[0]["f"])
                logger.info(f"Family created successfully: {familyId}")
                return family

            logger.warning("Family creation returned no data")
            return None
        except Exception as e:
            logger.error(f"Failed to create family: {str(e)}")
            raise

    def get_family_by_id(
        self,
        familyId: str,
        database: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get family by familyId."""
        return self.get_node("Family", "familyId", familyId, database)

    def update_family(
        self,
        familyId: str,
        updates: Dict[str, Any],
        database: Optional[str] = None
    ) -> bool:
        """Update family properties."""
        try:
            set_clause = ", ".join([f"f.{k} = ${k}" for k in updates.keys()])
            query = f"MATCH (f:Family {{familyId: $familyId}}) SET {set_clause} RETURN f"
            params = {"familyId": familyId, **updates}

            logger.info(f"Updating family: {familyId}")
            records = self.execute_query(query, params, database)
            success = len(records) > 0

            if success:
                logger.info(f"Family updated successfully: {familyId}")
            else:
                logger.warning(f"Family not found for update: {familyId}")

            return success
        except Exception as e:
            logger.error(f"Failed to update family: {str(e)}")
            raise

    def delete_family(
        self,
        familyId: str,
        database: Optional[str] = None
    ) -> bool:
        """Delete a family node and all its relationships."""
        try:
            query = """
            MATCH (f:Family {familyId: $familyId})
            DETACH DELETE f
            RETURN count(f) as deleted
            """
            logger.info(f"Deleting family: {familyId}")
            records = self.execute_query(query, {"familyId": familyId}, database)
            deleted_count = records[0]["deleted"] if records else 0

            if deleted_count > 0:
                logger.info(f"Family deleted successfully: {familyId}")
                return True

            logger.warning(f"Family not found for deletion: {familyId}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete family: {str(e)}")
            raise

    def get_all_families(
        self,
        limit: int = 100,
        database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all families."""
        try:
            query = "MATCH (f:Family) RETURN f LIMIT $limit"
            logger.debug(f"Getting all families (limit: {limit})")
            records = self.execute_query(query, {"limit": limit}, database)
            families = [dict(record["f"]) for record in records]
            logger.debug(f"Found {len(families)} families")
            return families
        except Exception as e:
            logger.error(f"Failed to get all families: {str(e)}")
            raise

    # ==================== User-Family Relationship Operations ====================

    def add_user_to_family(
        self,
        userId: str,
        familyId: str,
        role: Optional[str] = None,
        joinedAt: Optional[str] = None,
        name: Optional[str] = None,
        email: Optional[str] = None,
        database: Optional[str] = None
    ) -> bool:
        """
        Add a user to a family (create MEMBER_OF relationship).
        Uses MERGE so the User node is created in Neo4j if it doesn't exist yet.

        Args:
            userId: User ID
            familyId: Family ID
            role: User role in family (admin/member, optional)
            joinedAt: Join date (ISO format, optional, defaults to now)
            name: User full name (optional, stored on User node)
            email: User email (optional, stored on User node)
            database: Database name (optional)

        Returns:
            True if relationship created, False otherwise
        """
        try:
            joined = joinedAt or datetime.now(timezone.utc).isoformat()
            params: Dict[str, Any] = {
                "userId": userId,
                "familyId": familyId,
                "joined": joined,
            }

            # Build SET clause for user node properties
            user_set_parts = []
            if name:
                user_set_parts.append("u.name = $name")
                params["name"] = name
            if email:
                user_set_parts.append("u.email = $email")
                params["email"] = email
            user_set_clause = ("SET " + ", ".join(user_set_parts)) if user_set_parts else ""

            # Build SET clause for relationship properties
            rel_set_parts = ["r.joinedAt = $joined"]
            if role:
                rel_set_parts.append("r.role = $role")
                params["role"] = role
            rel_set_clause = "SET " + ", ".join(rel_set_parts)

            query = f"""
            MERGE (u:User {{userId: $userId}})
            {user_set_clause}
            WITH u
            MATCH (f:Family {{familyId: $familyId}})
            MERGE (u)-[r:MEMBER_OF]->(f)
            {rel_set_clause}
            RETURN r
            """

            logger.info(f"Adding user {userId} to family {familyId} with role={role}")
            records = self.execute_query(query, params, database)
            success = len(records) > 0
            if success:
                logger.info(f"User {userId} added to family {familyId} successfully")
            else:
                logger.warning(f"Failed to add user {userId} to family {familyId} — family may not exist")
            return success
        except Exception as e:
            logger.error(f"Failed to add user to family: {str(e)}")
            raise

    def remove_user_from_family(
        self,
        userId: str,
        familyId: str,
        database: Optional[str] = None
    ) -> bool:
        """Remove a user from a family (delete MEMBER_OF relationship)."""
        logger.info(f"Removing user {userId} from family {familyId}")
        return self.delete_relationship(
            "User", "userId", userId,
            "MEMBER_OF",
            "Family", "familyId", familyId,
            database
        )

    def get_family_members(
        self,
        familyId: str,
        database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all members of a family."""
        try:
            query = """
            MATCH (u:User)-[r:MEMBER_OF]->(f:Family {familyId: $familyId})
            RETURN u, r
            ORDER BY r.joinedAt
            """
            logger.debug(f"Getting members of family: {familyId}")
            records = self.execute_query(query, {"familyId": familyId}, database)
            members = [
                {"user": dict(record["u"]), "relationship": dict(record["r"])}
                for record in records
            ]
            logger.debug(f"Found {len(members)} family members")
            return members
        except Exception as e:
            logger.error(f"Failed to get family members: {str(e)}")
            raise

    def get_user_families(
        self,
        userId: str,
        database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all families a user belongs to."""
        try:
            query = """
            MATCH (u:User {userId: $userId})-[r:MEMBER_OF]->(f:Family)
            RETURN f, r
            ORDER BY r.joinedAt DESC
            """
            logger.debug(f"Getting families for user: {userId}")
            records = self.execute_query(query, {"userId": userId}, database)
            families = [
                {"family": dict(record["f"]), "relationship": dict(record["r"])}
                for record in records
            ]
            logger.debug(f"Found {len(families)} families for user")
            return families
        except Exception as e:
            logger.error(f"Failed to get user families: {str(e)}")
            raise

    def create_family_creator_relationship(
        self,
        userId: str,
        familyId: str,
        database: Optional[str] = None
    ) -> bool:
        """Create CREATED_BY relationship between user and family."""
        logger.info(f"Creating CREATED_BY relationship: {userId} -> {familyId}")
        return self.create_relationship(
            "User", "userId", userId,
            "CREATED_BY",
            "Family", "familyId", familyId,
            None,
            database
        )

    # ==================== Family Tree Operations ====================

    def get_family_member_relationships(
        self,
        familyId: str,
        database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all PARENT_OF / CHILD_OF / SPOUSE_OF / SIBLING_OF relationships
        that exist between members of a specific family.
        Works regardless of which member initiated the relationship.
        """
        try:
            query = """
            MATCH (u1:User)-[:MEMBER_OF]->(:Family {familyId: $familyId})<-[:MEMBER_OF]-(u2:User)
            MATCH (u1)-[r:PARENT_OF|CHILD_OF|SPOUSE_OF|SIBLING_OF]->(u2)
            RETURN u1.userId AS source, type(r) AS type, u2.userId AS target
            """
            logger.debug(f"Getting member relationships for family: {familyId}")
            records = self.execute_query(query, {"familyId": familyId}, database)
            return [
                {"source": rec["source"], "type": rec["type"], "target": rec["target"]}
                for rec in records
            ]
        except Exception as e:
            logger.error(f"Failed to get family member relationships: {str(e)}")
            raise

    def create_family_relationship(
        self,
        user1_id: str,
        relationship_type: str,
        user2_id: str,
        properties: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None
    ) -> bool:
        """
        Create family relationship between users.

        Relationship types: PARENT_OF, CHILD_OF, SPOUSE_OF, SIBLING_OF

        Args:
            user1_id: First user ID
            relationship_type: Type of relationship
            user2_id: Second user ID
            properties: Additional properties (optional)
            database: Database name (optional)

        Returns:
            True if relationship created, False otherwise
        """
        logger.info(f"Creating {relationship_type} relationship: {user1_id} -> {user2_id}")
        return self.create_relationship(
            "User", "userId", user1_id,
            relationship_type,
            "User", "userId", user2_id,
            properties,
            database
        )

    def get_family_tree(
        self,
        user_id: str,
        depth: int = 2,
        database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get family tree up to specified depth.

        Args:
            user_id: User ID to start from
            depth: Maximum depth of relationships to traverse
            database: Database name (optional)

        Returns:
            List of path dictionaries
        """
        try:
            # Only traverse family relationship types (not MEMBER_OF).
            # Use Cypher's startNode()/endNode() + type() to extract source/target
            # directly as plain values — avoids Python-driver Node attribute issues.
            query = f"""
            MATCH path = (a:User {{userId: $userId}})
                         -[r:PARENT_OF|CHILD_OF|SPOUSE_OF|SIBLING_OF*1..{depth}]-
                         (b:User)
            WITH nodes(path) as pathNodes, relationships(path) as pathRels
            RETURN
                pathNodes as nodes,
                [rel in pathRels | {{
                    source: startNode(rel).userId,
                    target: endNode(rel).userId,
                    type:   type(rel)
                }}] as rels
            """
            logger.debug(f"Getting family tree for user {user_id} (depth: {depth})")
            records = self.execute_query(query, {"userId": user_id}, database)
            tree = [
                {
                    "nodes": record["nodes"],
                    "rels":  record["rels"],
                }
                for record in records
            ]
            logger.debug(f"Found {len(tree)} paths in family tree")
            return tree
        except Exception as e:
            logger.error(f"Failed to get family tree: {str(e)}")
            raise
