"""
Condition & Symptom Operations for Neo4j
Handles medical conditions, symptoms, and their relationships
"""
from typing import Dict, List, Optional, Any
import uuid


class ConditionOperations:
    """Condition and symptom operations for Neo4j."""

    def __init__(self, client):
        """Initialize with Neo4j client."""
        self.client = client

    # ==================== Condition CRUD ====================

    def create_condition(
        self,
        name: str,
        icd_code: str,
        category: str,
        severity: str,
        description: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a Condition node.

        Args:
            name: Condition name
            icd_code: ICD-10 code
            category: chronic/acute/genetic
            severity: mild/moderate/severe
            description: Condition description

        Returns:
            Created condition data
        """
        condition_id = str(uuid.uuid4())

        query = """
        CREATE (c:Condition {
            conditionId: $conditionId,
            name: $name,
            icdCode: $icdCode,
            category: $category,
            severity: $severity,
            description: $description
        })
        RETURN c
        """

        params = {
            "conditionId": condition_id,
            "name": name,
            "icdCode": icd_code,
            "category": category,
            "severity": severity,
            "description": description
        }

        result = self.client.execute_query(query, params)
        return dict(result[0]["c"]) if result else None

    def get_condition(self, condition_id: str) -> Optional[Dict[str, Any]]:
        """Get condition by ID."""
        query = """
        MATCH (c:Condition {conditionId: $conditionId})
        RETURN c
        """
        result = self.client.execute_query(query, {"conditionId": condition_id})
        return dict(result[0]["c"]) if result else None

    def get_condition_by_icd(self, icd_code: str) -> Optional[Dict[str, Any]]:
        """Get condition by ICD code."""
        query = """
        MATCH (c:Condition {icdCode: $icdCode})
        RETURN c
        """
        result = self.client.execute_query(query, {"icdCode": icd_code})
        return dict(result[0]["c"]) if result else None

    def search_conditions(self, search_text: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Full-text search for conditions."""
        query = """
        CALL db.index.fulltext.queryNodes('condition_text_index', $searchText)
        YIELD node, score
        RETURN node as c, score
        ORDER BY score DESC
        LIMIT $limit
        """
        result = self.client.execute_query(query, {"searchText": search_text, "limit": limit})
        return [{"condition": dict(r["c"]), "score": r["score"]} for r in result]

    # ==================== User-Condition Relationships ====================

    def add_user_condition(
        self,
        user_id: str,
        condition_id: str,
        diagnosed_date: str,
        status: str = "active",
        severity: str = "moderate",
        **kwargs
    ) -> bool:
        """
        Create HAS_CONDITION relationship between User and Condition.

        Args:
            user_id: User UUID
            condition_id: Condition UUID
            diagnosed_date: Diagnosis date (YYYY-MM-DD)
            status: active/resolved/chronic
            severity: mild/moderate/severe

        Returns:
            Success status
        """
        query = """
        MATCH (u:User {userId: $userId})
        MATCH (c:Condition {conditionId: $conditionId})
        CREATE (u)-[:HAS_CONDITION {
            diagnosedDate: date($diagnosedDate),
            status: $status,
            severity: $severity
        }]->(c)
        RETURN count(*) as created
        """

        params = {
            "userId": user_id,
            "conditionId": condition_id,
            "diagnosedDate": diagnosed_date,
            "status": status,
            "severity": severity
        }

        result = self.client.execute_query(query, params)
        return result[0]["created"] > 0 if result else False

    def get_user_conditions(
        self,
        user_id: str,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all conditions for a user, optionally filtered by status."""
        query = """
        MATCH (u:User {userId: $userId})-[r:HAS_CONDITION]->(c:Condition)
        WHERE $status IS NULL OR r.status = $status
        RETURN c, r
        ORDER BY r.diagnosedDate DESC
        """

        params = {"userId": user_id, "status": status}
        result = self.client.execute_query(query, params)

        conditions = []
        for r in result:
            cond_data = dict(r["c"])
            cond_data["relationship"] = dict(r["r"])
            conditions.append(cond_data)

        return conditions

    def update_condition_status(
        self,
        user_id: str,
        condition_id: str,
        status: str,
        severity: Optional[str] = None
    ) -> bool:
        """Update condition status and severity for a user."""
        query = """
        MATCH (u:User {userId: $userId})-[r:HAS_CONDITION]->(c:Condition {conditionId: $conditionId})
        SET r.status = $status
        SET r.severity = CASE WHEN $severity IS NOT NULL THEN $severity ELSE r.severity END
        RETURN count(r) as updated
        """

        params = {
            "userId": user_id,
            "conditionId": condition_id,
            "status": status,
            "severity": severity
        }

        result = self.client.execute_query(query, params)
        return result[0]["updated"] > 0 if result else False

    # ==================== Symptom CRUD ====================

    def create_symptom(
        self,
        name: str,
        description: Optional[str] = None,
        severity: str = "mild",
        **kwargs
    ) -> Dict[str, Any]:
        """Create a Symptom node."""
        symptom_id = str(uuid.uuid4())

        query = """
        CREATE (s:Symptom {
            symptomId: $symptomId,
            name: $name,
            description: $description,
            severity: $severity
        })
        RETURN s
        """

        params = {
            "symptomId": symptom_id,
            "name": name,
            "description": description,
            "severity": severity
        }

        result = self.client.execute_query(query, params)
        return dict(result[0]["s"]) if result else None

    def get_symptom(self, symptom_id: str) -> Optional[Dict[str, Any]]:
        """Get symptom by ID."""
        query = """
        MATCH (s:Symptom {symptomId: $symptomId})
        RETURN s
        """
        result = self.client.execute_query(query, {"symptomId": symptom_id})
        return dict(result[0]["s"]) if result else None

    # ==================== Condition-Related Queries ====================

    def get_condition_treatments(self, condition_id: str) -> List[Dict[str, Any]]:
        """Get all medications that treat a condition."""
        query = """
        MATCH (m:Medication)-[r:TREATS]->(c:Condition {conditionId: $conditionId})
        RETURN m, r
        ORDER BY r.effectiveness DESC, r.primaryTreatment DESC
        """
        result = self.client.execute_query(query, {"conditionId": condition_id})
        return [{"medication": dict(r["m"]), "treatment": dict(r["r"])} for r in result]

    def get_family_condition_history(
        self,
        family_id: str,
        condition_id: str
    ) -> List[Dict[str, Any]]:
        """Get all family members with a specific condition."""
        query = """
        MATCH (u:User)-[:MEMBER_OF]->(f:Family {familyId: $familyId})
        MATCH (u)-[r:HAS_CONDITION]->(c:Condition {conditionId: $conditionId})
        RETURN u, r
        """

        params = {
            "familyId": family_id,
            "conditionId": condition_id
        }

        result = self.client.execute_query(query, params)
        return [{"user": dict(r["u"]), "condition_info": dict(r["r"])} for r in result]

    def get_chronic_conditions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all chronic conditions for a user."""
        query = """
        MATCH (u:User {userId: $userId})-[r:HAS_CONDITION]->(c:Condition)
        WHERE c.category = 'chronic' OR r.status = 'chronic'
        RETURN c, r
        """
        result = self.client.execute_query(query, {"userId": user_id})
        return [{"condition": dict(r["c"]), "info": dict(r["r"])} for r in result]

    # ==================== Genetic Conditions ====================

    def get_genetic_conditions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get genetic conditions for a user."""
        query = """
        MATCH (u:User {userId: $userId})-[r:HAS_CONDITION]->(c:Condition {category: 'genetic'})
        RETURN c, r
        """
        result = self.client.execute_query(query, {"userId": user_id})
        return [{"condition": dict(r["c"]), "info": dict(r["r"])} for r in result]

    def analyze_family_genetic_risk(self, family_id: str) -> List[Dict[str, Any]]:
        """
        Analyze genetic condition patterns in family.

        Returns conditions that appear in multiple family members (genetic risk).
        """
        query = """
        MATCH (u:User)-[:MEMBER_OF]->(f:Family {familyId: $familyId})
        MATCH (u)-[:HAS_CONDITION]->(c:Condition)
        WHERE c.category = 'genetic' OR c.category = 'chronic'
        WITH c, count(DISTINCT u) as affected_members, collect(DISTINCT u.name) as members
        WHERE affected_members > 1
        RETURN c, affected_members, members
        ORDER BY affected_members DESC
        """

        result = self.client.execute_query(query, {"familyId": family_id})

        risks = []
        for r in result:
            risks.append({
                "condition": dict(r["c"]),
                "affected_count": r["affected_members"],
                "affected_members": r["members"]
            })

        return risks
