"""
User operations for Neo4j database.
Handles all CRUD operations for User nodes.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from backend.shared.database.neo4j.operations.graph_ops import GraphOperations
from backend.shared.logging import get_logger

logger = get_logger('neo4j.user_ops')


class UserOperations(GraphOperations):
    """User-specific database operations."""

    def create_user(
        self,
        userId: str,
        email: str,
        name: str,
        dateOfBirth: str,
        gender: str,
        bloodType: Optional[str] = None,
        phoneNumber: Optional[str] = None,
        emergencyContact: Optional[str] = None,
        createdAt: Optional[str] = None,
        updatedAt: Optional[str] = None,
        database: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a User node.

        Args:
            userId: UUID unique identifier
            email: User email (indexed)
            name: User full name
            dateOfBirth: Date of birth (YYYY-MM-DD format)
            gender: Gender (M/F/O)
            bloodType: Blood type (optional)
            phoneNumber: Phone number (optional)
            emergencyContact: Emergency contact info (optional)
            createdAt: Creation timestamp (optional, defaults to now)
            updatedAt: Update timestamp (optional, defaults to now)
            database: Database name (optional)

        Returns:
            Created user node or None
        """
        try:
            properties = {
                "userId": userId,
                "email": email,
                "name": name,
                "dateOfBirth": dateOfBirth,
                "gender": gender,
                "createdAt": createdAt or datetime.now(timezone.utc).isoformat(),
                "updatedAt": updatedAt or datetime.now(timezone.utc).isoformat()
            }

            if bloodType:
                properties["bloodType"] = bloodType
            if phoneNumber:
                properties["phoneNumber"] = phoneNumber
            if emergencyContact:
                properties["emergencyContact"] = emergencyContact

            query = "CREATE (u:User $properties) RETURN u"
            logger.info(f"Creating User node for {email}")
            records = self.execute_query(query, {"properties": properties}, database)

            if records:
                user = dict(records[0]["u"])
                logger.info(f"User created successfully: {userId}")
                return user

            logger.warning("User creation returned no data")
            return None
        except Exception as e:
            logger.error(f"Failed to create user: {str(e)}")
            raise

    def get_user_by_id(
        self,
        userId: str,
        database: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get user by userId."""
        return self.get_node("User", "userId", userId, database)

    def get_user_by_email(
        self,
        email: str,
        database: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        try:
            query = "MATCH (u:User {email: $email}) RETURN u"
            logger.debug(f"Getting user by email: {email}")
            records = self.execute_query(query, {"email": email}, database)

            if records:
                user = dict(records[0]["u"])
                logger.debug("User found by email")
                return user

            logger.debug("User not found by email")
            return None
        except Exception as e:
            logger.error(f"Failed to get user by email: {str(e)}")
            raise

    def update_user(
        self,
        userId: str,
        updates: Dict[str, Any],
        database: Optional[str] = None
    ) -> bool:
        """
        Update user properties.

        Args:
            userId: User ID
            updates: Dictionary of properties to update
            database: Database name (optional)

        Returns:
            True if updated, False otherwise
        """
        try:
            # Always update updatedAt timestamp
            updates["updatedAt"] = datetime.now(timezone.utc).isoformat()

            set_clause = ", ".join([f"u.{k} = ${k}" for k in updates.keys()])
            query = f"MATCH (u:User {{userId: $userId}}) SET {set_clause} RETURN u"
            params = {"userId": userId, **updates}

            logger.info(f"Updating user: {userId}")
            records = self.execute_query(query, params, database)
            success = len(records) > 0

            if success:
                logger.info(f"User updated successfully: {userId}")
            else:
                logger.warning(f"User not found for update: {userId}")

            return success
        except Exception as e:
            logger.error(f"Failed to update user: {str(e)}")
            raise

    def delete_user(
        self,
        userId: str,
        database: Optional[str] = None
    ) -> bool:
        """
        Delete a user node and all its relationships.

        Args:
            userId: User ID
            database: Database name (optional)

        Returns:
            True if deleted, False otherwise
        """
        try:
            query = """
            MATCH (u:User {userId: $userId})
            DETACH DELETE u
            RETURN count(u) as deleted
            """
            logger.info(f"Deleting user: {userId}")
            records = self.execute_query(query, {"userId": userId}, database)
            deleted_count = records[0]["deleted"] if records else 0

            if deleted_count > 0:
                logger.info(f"User deleted successfully: {userId}")
                return True

            logger.warning(f"User not found for deletion: {userId}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete user: {str(e)}")
            raise

    def get_all_users(
        self,
        limit: int = 100,
        database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all users.

        Args:
            limit: Maximum number of users to return
            database: Database name (optional)

        Returns:
            List of user dictionaries
        """
        try:
            query = "MATCH (u:User) RETURN u LIMIT $limit"
            logger.debug(f"Getting all users (limit: {limit})")
            records = self.execute_query(query, {"limit": limit}, database)
            users = [dict(record["u"]) for record in records]
            logger.debug(f"Found {len(users)} users")
            return users
        except Exception as e:
            logger.error(f"Failed to get all users: {str(e)}")
            raise
