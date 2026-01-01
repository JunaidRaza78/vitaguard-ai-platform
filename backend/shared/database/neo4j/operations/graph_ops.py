"""
Generic graph operations for nodes and relationships.
Provides low-level CRUD operations that other modules can use.
"""
from typing import Optional, Dict, Any, List
from backend.shared.database.neo4j.neo4j_client import BaseNeo4jClient
from backend.shared.logging import get_logger

logger = get_logger('neo4j.graph_ops')


class GraphOperations(BaseNeo4jClient):
    """Generic graph database operations for nodes and relationships."""

    # ==================== Node Operations ====================

    def create_node(
        self,
        label: str,
        properties: Dict[str, Any],
        database: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a node.

        Args:
            label: Node label (e.g., "User", "Condition")
            properties: Node properties
            database: Database name (optional)

        Returns:
            Created node properties or None
        """
        try:
            query = f"CREATE (n:{label} $properties) RETURN n"
            logger.info(f"Creating {label} node")
            records = self.execute_query(query, {"properties": properties}, database)
            if records:
                node = dict(records[0]["n"])
                logger.info(f"{label} node created successfully")
                return node
            return None
        except Exception as e:
            logger.error(f"Failed to create {label} node: {str(e)}")
            raise

    def get_node(
        self,
        label: str,
        property_key: str,
        property_value: Any,
        database: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get a node by property.

        Args:
            label: Node label
            property_key: Property key to search by
            property_value: Property value to match
            database: Database name (optional)

        Returns:
            Node properties or None if not found
        """
        try:
            query = f"MATCH (n:{label} {{{property_key}: $value}}) RETURN n"
            logger.debug(f"Getting {label} node where {property_key}={property_value}")
            records = self.execute_query(query, {"value": property_value}, database)
            if records:
                node = dict(records[0]["n"])
                logger.debug(f"{label} node found")
                return node
            logger.debug(f"{label} node not found")
            return None
        except Exception as e:
            logger.error(f"Failed to get {label} node: {str(e)}")
            raise

    def update_node(
        self,
        label: str,
        property_key: str,
        property_value: Any,
        updates: Dict[str, Any],
        database: Optional[str] = None
    ) -> bool:
        """
        Update node properties.

        Args:
            label: Node label
            property_key: Property key to search by
            property_value: Property value to match
            updates: Dictionary of properties to update
            database: Database name (optional)

        Returns:
            True if node was updated, False otherwise
        """
        try:
            set_clause = ", ".join([f"n.{k} = ${k}" for k in updates.keys()])
            query = f"MATCH (n:{label} {{{property_key}: $value}}) SET {set_clause} RETURN n"
            params = {"value": property_value, **updates}
            logger.info(f"Updating {label} node where {property_key}={property_value}")
            records = self.execute_query(query, params, database)
            success = len(records) > 0
            if success:
                logger.info(f"{label} node updated successfully")
            else:
                logger.warning(f"{label} node not found for update")
            return success
        except Exception as e:
            logger.error(f"Failed to update {label} node: {str(e)}")
            raise

    def delete_node(
        self,
        label: str,
        property_key: str,
        property_value: Any,
        database: Optional[str] = None
    ) -> bool:
        """
        Delete a node.

        Args:
            label: Node label
            property_key: Property key to search by
            property_value: Property value to match
            database: Database name (optional)

        Returns:
            True if node was deleted, False otherwise
        """
        try:
            query = f"MATCH (n:{label} {{{property_key}: $value}}) DELETE n RETURN count(n) as deleted"
            logger.info(f"Deleting {label} node where {property_key}={property_value}")
            records = self.execute_query(query, {"value": property_value}, database)
            deleted_count = records[0]["deleted"] if records else 0
            if deleted_count > 0:
                logger.info(f"{label} node deleted successfully")
                return True
            logger.warning(f"{label} node not found for deletion")
            return False
        except Exception as e:
            logger.error(f"Failed to delete {label} node: {str(e)}")
            raise

    # ==================== Relationship Operations ====================

    def create_relationship(
        self,
        from_label: str,
        from_property: str,
        from_value: Any,
        relationship_type: str,
        to_label: str,
        to_property: str,
        to_value: Any,
        properties: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None
    ) -> bool:
        """
        Create a relationship between two nodes.

        Args:
            from_label: Source node label
            from_property: Source node property key
            from_value: Source node property value
            relationship_type: Relationship type (e.g., "FRIENDS_WITH", "HAS_CONDITION")
            to_label: Target node label
            to_property: Target node property key
            to_value: Target node property value
            properties: Relationship properties (optional)
            database: Database name (optional)

        Returns:
            True if relationship was created, False otherwise
        """
        try:
            rel_props = ""
            params = {"from_value": from_value, "to_value": to_value}

            if properties:
                params.update(properties)

            # Build relationship properties SET clause
            set_props = ""
            if properties:
                set_props = " SET " + ", ".join([f"r.{k} = ${k}" for k in properties.keys()])

            query = (
                f"MATCH (a:{from_label} {{{from_property}: $from_value}}), "
                f"(b:{to_label} {{{to_property}: $to_value}}) "
                f"CREATE (a)-[r:{relationship_type}]->(b){set_props} "
                f"RETURN r"
            )
            logger.info(f"Creating {relationship_type} relationship from {from_label} to {to_label}")
            records = self.execute_query(query, params, database)
            success = len(records) > 0
            if success:
                logger.info(f"{relationship_type} relationship created successfully")
            else:
                logger.warning(f"Failed to create {relationship_type} relationship - nodes may not exist")
            return success
        except Exception as e:
            logger.error(f"Failed to create relationship: {str(e)}")
            raise

    def get_relationships(
        self,
        from_label: str,
        from_property: str,
        from_value: Any,
        relationship_type: Optional[str] = None,
        database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get relationships from a node.

        Args:
            from_label: Source node label
            from_property: Source node property key
            from_value: Source node property value
            relationship_type: Filter by relationship type (optional)
            database: Database name (optional)

        Returns:
            List of relationship dictionaries
        """
        try:
            rel_filter = f":{relationship_type}" if relationship_type else ""
            query = (
                f"MATCH (a:{from_label} {{{from_property}: $value}})-[r{rel_filter}]->(b) "
                f"RETURN type(r) as rel_type, r, b"
            )
            logger.debug(f"Getting relationships for {from_label} where {from_property}={from_value}")
            records = self.execute_query(query, {"value": from_value}, database)
            relationships = [
                {"type": record["rel_type"], "relationship": dict(record["r"]), "node": dict(record["b"])}
                for record in records
            ]
            logger.debug(f"Found {len(relationships)} relationships")
            return relationships
        except Exception as e:
            logger.error(f"Failed to get relationships: {str(e)}")
            raise

    def delete_relationship(
        self,
        from_label: str,
        from_property: str,
        from_value: Any,
        relationship_type: str,
        to_label: str,
        to_property: str,
        to_value: Any,
        database: Optional[str] = None
    ) -> bool:
        """
        Delete a relationship.

        Args:
            from_label: Source node label
            from_property: Source node property key
            from_value: Source node property value
            relationship_type: Relationship type
            to_label: Target node label
            to_property: Target node property key
            to_value: Target node property value
            database: Database name (optional)

        Returns:
            True if relationship was deleted, False otherwise
        """
        try:
            query = (
                f"MATCH (a:{from_label} {{{from_property}: $from_value}})-[r:{relationship_type}]->"
                f"(b:{to_label} {{{to_property}: $to_value}}) "
                f"DELETE r RETURN count(r) as deleted"
            )
            logger.info(f"Deleting {relationship_type} relationship from {from_label} to {to_label}")
            records = self.execute_query(query, {"from_value": from_value, "to_value": to_value}, database)
            deleted_count = records[0]["deleted"] if records else 0
            if deleted_count > 0:
                logger.info(f"{relationship_type} relationship deleted successfully")
                return True
            logger.warning(f"{relationship_type} relationship not found for deletion")
            return False
        except Exception as e:
            logger.error(f"Failed to delete relationship: {str(e)}")
            raise

    # ==================== Knowledge Graph Operations ====================

    def find_path(
        self,
        from_label: str,
        from_id: str,
        to_label: str,
        to_id: str,
        max_depth: int = 5,
        database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Find shortest path between two nodes."""
        from_prop = f"{from_label.lower()}Id"
        to_prop = f"{to_label.lower()}Id"
        query = (
            f"MATCH path = shortestPath((a:{from_label} {{{from_prop}: $from_id}})-[*..{max_depth}]-(b:{to_label} {{{to_prop}: $to_id}})) "
            f"RETURN path, length(path) as path_length"
        )
        result = self.execute_query(query, {"from_id": from_id, "to_id": to_id}, database)
        return [{"path": record["path"], "length": record["path_length"]} for record in result]
