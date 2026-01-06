"""
Medication Operations for Neo4j
Handles CRUD operations for Medication nodes and relationships
"""
from typing import Dict, List, Optional, Any
import uuid


class MedicationOperations:
    """Medication operations for Neo4j."""

    def __init__(self, client):
        """Initialize with Neo4j client."""
        self.client = client

    # ==================== Medication CRUD ====================

    def create_medication(
        self,
        name: str,
        generic_name: Optional[str] = None,
        brand_name: Optional[str] = None,
        medication_class: Optional[str] = None,
        fda_approved: bool = True,
        active_ingredients: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a Medication node.

        Args:
            name: Medication name
            generic_name: Generic name
            brand_name: Brand name
            medication_class: Drug class
            fda_approved: FDA approval status
            active_ingredients: List of active ingredients

        Returns:
            Created medication data
        """
        medication_id = str(uuid.uuid4())

        query = """
        CREATE (m:Medication {
            medicationId: $medicationId,
            name: $name,
            genericName: $genericName,
            brandName: $brandName,
            class: $class,
            fdaApproved: $fdaApproved,
            activeIngredients: $activeIngredients
        })
        RETURN m
        """

        params = {
            "medicationId": medication_id,
            "name": name,
            "genericName": generic_name,
            "brandName": brand_name,
            "class": medication_class,
            "fdaApproved": fda_approved,
            "activeIngredients": active_ingredients or []
        }

        result = self.client.execute_query(query, params)
        return dict(result[0]["m"]) if result else None

    def get_medication(self, medication_id: str) -> Optional[Dict[str, Any]]:
        """Get medication by ID."""
        query = """
        MATCH (m:Medication {medicationId: $medicationId})
        RETURN m
        """
        result = self.client.execute_query(query, {"medicationId": medication_id})
        return dict(result[0]["m"]) if result else None

    def search_medications(self, search_text: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Full-text search for medications."""
        query = """
        CALL db.index.fulltext.queryNodes('medication_text_index', $searchText)
        YIELD node, score
        RETURN node as m, score
        ORDER BY score DESC
        LIMIT $limit
        """
        result = self.client.execute_query(query, {"searchText": search_text, "limit": limit})
        return [{"medication": dict(r["m"]), "score": r["score"]} for r in result]

    # ==================== User Medication Relationships ====================

    def add_user_medication(
        self,
        user_id: str,
        medication_id: str,
        start_date: str,
        dosage: str,
        frequency: str,
        end_date: Optional[str] = None,
        status: str = "active",
        reminder_times: Optional[List[str]] = None,
        **kwargs
    ) -> bool:
        """
        Create TAKES relationship between User and Medication.

        Args:
            user_id: User UUID
            medication_id: Medication UUID
            start_date: Start date (YYYY-MM-DD)
            dosage: Dosage information
            frequency: Frequency (daily, twice_daily, etc.)
            end_date: Optional end date
            status: active/completed/discontinued
            reminder_times: List of reminder times (HH:MM)

        Returns:
            Success status
        """
        query = """
        MATCH (u:User {userId: $userId})
        MATCH (m:Medication {medicationId: $medicationId})
        CREATE (u)-[:TAKES {
            startDate: date($startDate),
            endDate: CASE WHEN $endDate IS NOT NULL THEN date($endDate) ELSE NULL END,
            dosage: $dosage,
            frequency: $frequency,
            status: $status,
            reminderTimes: $reminderTimes
        }]->(m)
        RETURN count(*) as created
        """

        params = {
            "userId": user_id,
            "medicationId": medication_id,
            "startDate": start_date,
            "endDate": end_date,
            "dosage": dosage,
            "frequency": frequency,
            "status": status,
            "reminderTimes": reminder_times or []
        }

        result = self.client.execute_query(query, params)
        return result[0]["created"] > 0 if result else False

    def get_user_medications(
        self,
        user_id: str,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all medications for a user, optionally filtered by status."""
        query = """
        MATCH (u:User {userId: $userId})-[r:TAKES]->(m:Medication)
        WHERE $status IS NULL OR r.status = $status
        RETURN m, r
        ORDER BY r.startDate DESC
        """

        params = {"userId": user_id, "status": status}
        result = self.client.execute_query(query, params)

        medications = []
        for r in result:
            med_data = dict(r["m"])
            med_data["relationship"] = dict(r["r"])
            medications.append(med_data)

        return medications

    def update_medication_status(
        self,
        user_id: str,
        medication_id: str,
        status: str,
        end_date: Optional[str] = None
    ) -> bool:
        """Update medication status for a user."""
        query = """
        MATCH (u:User {userId: $userId})-[r:TAKES]->(m:Medication {medicationId: $medicationId})
        SET r.status = $status
        SET r.endDate = CASE WHEN $endDate IS NOT NULL THEN date($endDate) ELSE r.endDate END
        RETURN count(r) as updated
        """

        params = {
            "userId": user_id,
            "medicationId": medication_id,
            "status": status,
            "endDate": end_date
        }

        result = self.client.execute_query(query, params)
        return result[0]["updated"] > 0 if result else False

    # ==================== Medication-Condition Relationships ====================

    def link_medication_to_condition(
        self,
        medication_id: str,
        condition_id: str,
        effectiveness: float = 0.0,
        primary_treatment: bool = False
    ) -> bool:
        """Create TREATS relationship between Medication and Condition."""
        query = """
        MATCH (m:Medication {medicationId: $medicationId})
        MATCH (c:Condition {conditionId: $conditionId})
        MERGE (m)-[r:TREATS {
            effectiveness: $effectiveness,
            primaryTreatment: $primaryTreatment
        }]->(c)
        RETURN count(r) as created
        """

        params = {
            "medicationId": medication_id,
            "conditionId": condition_id,
            "effectiveness": effectiveness,
            "primaryTreatment": primary_treatment
        }

        result = self.client.execute_query(query, params)
        return result[0]["created"] > 0 if result else False

    def get_medication_conditions(self, medication_id: str) -> List[Dict[str, Any]]:
        """Get all conditions treated by a medication."""
        query = """
        MATCH (m:Medication {medicationId: $medicationId})-[r:TREATS]->(c:Condition)
        RETURN c, r
        """
        result = self.client.execute_query(query, {"medicationId": medication_id})
        return [{"condition": dict(r["c"]), "relationship": dict(r["r"])} for r in result]

    # ==================== Drug Interactions ====================

    def add_drug_interaction(
        self,
        medication_id_1: str,
        medication_id_2: str,
        severity: str,
        effect: str,
        recommendation: str
    ) -> bool:
        """
        Create INTERACTS_WITH relationship between two medications.

        Args:
            medication_id_1: First medication ID
            medication_id_2: Second medication ID
            severity: minor/moderate/severe
            effect: Interaction effect description
            recommendation: Recommendation for management

        Returns:
            Success status
        """
        query = """
        MATCH (m1:Medication {medicationId: $medicationId1})
        MATCH (m2:Medication {medicationId: $medicationId2})
        MERGE (m1)-[r:INTERACTS_WITH {
            severity: $severity,
            effect: $effect,
            recommendation: $recommendation
        }]-(m2)
        RETURN count(r) as created
        """

        params = {
            "medicationId1": medication_id_1,
            "medicationId2": medication_id_2,
            "severity": severity,
            "effect": effect,
            "recommendation": recommendation
        }

        result = self.client.execute_query(query, params)
        return result[0]["created"] > 0 if result else False

    def get_medication_interactions(self, medication_id: str) -> List[Dict[str, Any]]:
        """Get all drug interactions for a medication."""
        query = """
        MATCH (m1:Medication {medicationId: $medicationId})-[r:INTERACTS_WITH]-(m2:Medication)
        RETURN m2, r
        """
        result = self.client.execute_query(query, {"medicationId": medication_id})
        return [{"medication": dict(r["m2"]), "interaction": dict(r["r"])} for r in result]

    def check_user_drug_interactions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Check for drug interactions in user's current medications.

        Returns list of interactions found.
        """
        query = """
        MATCH (u:User {userId: $userId})-[t1:TAKES]->(m1:Medication)
        MATCH (u)-[t2:TAKES]->(m2:Medication)
        MATCH (m1)-[r:INTERACTS_WITH]-(m2)
        WHERE t1.status = 'active' AND t2.status = 'active'
        AND m1.medicationId < m2.medicationId
        RETURN m1, m2, r
        """

        result = self.client.execute_query(query, {"userId": user_id})

        interactions = []
        for r in result:
            interactions.append({
                "medication1": dict(r["m1"]),
                "medication2": dict(r["m2"]),
                "interaction": dict(r["r"])
            })

        return interactions

    # ==================== Side Effects ====================

    def add_side_effect(
        self,
        medication_id: str,
        symptom_id: str,
        frequency: str,
        severity: str
    ) -> bool:
        """Create CAUSES relationship (medication causes symptom as side effect)."""
        query = """
        MATCH (m:Medication {medicationId: $medicationId})
        MATCH (s:Symptom {symptomId: $symptomId})
        MERGE (m)-[r:CAUSES {
            frequency: $frequency,
            severity: $severity
        }]->(s)
        RETURN count(r) as created
        """

        params = {
            "medicationId": medication_id,
            "symptomId": symptom_id,
            "frequency": frequency,
            "severity": severity
        }

        result = self.client.execute_query(query, params)
        return result[0]["created"] > 0 if result else False

    def get_medication_side_effects(self, medication_id: str) -> List[Dict[str, Any]]:
        """Get all side effects for a medication."""
        query = """
        MATCH (m:Medication {medicationId: $medicationId})-[r:CAUSES]->(s:Symptom)
        RETURN s, r
        ORDER BY r.frequency DESC, r.severity DESC
        """
        result = self.client.execute_query(query, {"medicationId": medication_id})
        return [{"symptom": dict(r["s"]), "sideEffect": dict(r["r"])} for r in result]
