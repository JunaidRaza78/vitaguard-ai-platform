"""
Health Record Operations for Neo4j
Handles CRUD operations for HealthRecord, LabReport, Prescription, and Vaccination nodes
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid


class HealthRecordOperations:
    """Health record operations for Neo4j."""

    def __init__(self, client):
        """Initialize with Neo4j client."""
        self.client = client

    # ==================== HealthRecord Operations ====================

    def create_health_record(
        self,
        user_id: str,
        record_type: str,
        date: str,
        title: str,
        summary: str,
        file_url: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a HealthRecord node and link to User.

        Args:
            user_id: User UUID
            record_type: Type (lab_report, prescription, imaging, consultation, vaccination)
            date: Record date (YYYY-MM-DD)
            title: Record title
            summary: Record summary
            file_url: Optional file URL
            **kwargs: Additional properties

        Returns:
            Created health record data
        """
        record_id = str(uuid.uuid4())

        query = """
        MATCH (u:User {userId: $userId})
        CREATE (hr:HealthRecord {
            recordId: $recordId,
            type: $type,
            date: date($date),
            title: $title,
            summary: $summary,
            fileUrl: $fileUrl,
            createdAt: datetime()
        })
        CREATE (u)-[:HAS_RECORD {visibility: $visibility}]->(hr)
        RETURN hr
        """

        params = {
            "userId": user_id,
            "recordId": record_id,
            "type": record_type,
            "date": date,
            "title": title,
            "summary": summary,
            "fileUrl": file_url,
            "visibility": kwargs.get("visibility", "private")
        }

        result = self.client.execute_query(query, params)
        return dict(result[0]["hr"]) if result else None

    def get_health_record(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Get health record by ID."""
        query = """
        MATCH (hr:HealthRecord {recordId: $recordId})
        RETURN hr
        """
        result = self.client.execute_query(query, {"recordId": record_id})
        return dict(result[0]["hr"]) if result else None

    def get_user_health_records(
        self,
        user_id: str,
        record_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get all health records for a user, optionally filtered by type."""
        query = """
        MATCH (u:User {userId: $userId})-[:HAS_RECORD]->(hr:HealthRecord)
        WHERE $type IS NULL OR hr.type = $type
        RETURN hr
        ORDER BY hr.date DESC
        LIMIT $limit
        """

        params = {
            "userId": user_id,
            "type": record_type,
            "limit": limit
        }

        result = self.client.execute_query(query, params)
        return [dict(r["hr"]) for r in result]

    def update_health_record(
        self,
        record_id: str,
        **updates
    ) -> Optional[Dict[str, Any]]:
        """Update health record properties."""
        if not updates:
            return self.get_health_record(record_id)

        # Build SET clause
        set_clause = ", ".join([f"hr.{key} = ${key}" for key in updates.keys()])

        query = f"""
        MATCH (hr:HealthRecord {{recordId: $recordId}})
        SET {set_clause}
        RETURN hr
        """

        params = {"recordId": record_id, **updates}
        result = self.client.execute_query(query, params)
        return dict(result[0]["hr"]) if result else None

    def delete_health_record(self, record_id: str) -> bool:
        """Delete health record and all relationships."""
        query = """
        MATCH (hr:HealthRecord {recordId: $recordId})
        DETACH DELETE hr
        RETURN count(hr) as deleted
        """
        result = self.client.execute_query(query, {"recordId": record_id})
        return result[0]["deleted"] > 0 if result else False

    # ==================== LabReport Operations ====================

    def create_lab_report(
        self,
        user_id: str,
        test_name: str,
        date: str,
        laboratory: str,
        doctor_ordered: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a LabReport node."""
        report_id = str(uuid.uuid4())

        query = """
        MATCH (u:User {userId: $userId})
        CREATE (lr:LabReport {
            reportId: $reportId,
            testName: $testName,
            date: date($date),
            laboratory: $laboratory,
            doctorOrdered: $doctorOrdered
        })
        CREATE (u)-[:HAS_RECORD]->(lr)
        RETURN lr
        """

        params = {
            "userId": user_id,
            "reportId": report_id,
            "testName": test_name,
            "date": date,
            "laboratory": laboratory,
            "doctorOrdered": doctor_ordered
        }

        result = self.client.execute_query(query, params)
        return dict(result[0]["lr"]) if result else None

    def get_user_lab_reports(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all lab reports for a user."""
        query = """
        MATCH (u:User {userId: $userId})-[:HAS_RECORD]->(lr:LabReport)
        RETURN lr
        ORDER BY lr.date DESC
        LIMIT $limit
        """
        result = self.client.execute_query(query, {"userId": user_id, "limit": limit})
        return [dict(r["lr"]) for r in result]

    # ==================== Prescription Operations ====================

    def create_prescription(
        self,
        user_id: str,
        date: str,
        doctor_name: str,
        specialty: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a Prescription node."""
        prescription_id = str(uuid.uuid4())

        query = """
        MATCH (u:User {userId: $userId})
        CREATE (p:Prescription {
            prescriptionId: $prescriptionId,
            date: date($date),
            doctorName: $doctorName,
            specialty: $specialty
        })
        CREATE (u)-[:HAS_RECORD]->(p)
        RETURN p
        """

        params = {
            "userId": user_id,
            "prescriptionId": prescription_id,
            "date": date,
            "doctorName": doctor_name,
            "specialty": specialty
        }

        result = self.client.execute_query(query, params)
        return dict(result[0]["p"]) if result else None

    def get_user_prescriptions(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all prescriptions for a user."""
        query = """
        MATCH (u:User {userId: $userId})-[:HAS_RECORD]->(p:Prescription)
        RETURN p
        ORDER BY p.date DESC
        LIMIT $limit
        """
        result = self.client.execute_query(query, {"userId": user_id, "limit": limit})
        return [dict(r["p"]) for r in result]

    # ==================== Vaccination Operations ====================

    def create_vaccination(
        self,
        user_id: str,
        vaccine_name: str,
        date: str,
        vaccine_type: str,
        manufacturer: str,
        dose_number: int,
        lot_number: Optional[str] = None,
        next_due_date: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a Vaccination node."""
        vaccination_id = str(uuid.uuid4())

        query = """
        MATCH (u:User {userId: $userId})
        CREATE (v:Vaccination {
            vaccinationId: $vaccinationId,
            vaccineName: $vaccineName,
            type: $type,
            manufacturer: $manufacturer,
            doseNumber: $doseNumber,
            lotNumber: $lotNumber,
            nextDueDate: CASE WHEN $nextDueDate IS NOT NULL THEN date($nextDueDate) ELSE NULL END
        })
        CREATE (u)-[:RECEIVED {
            date: date($date),
            location: $location,
            administeredBy: $administeredBy
        }]->(v)
        RETURN v
        """

        params = {
            "userId": user_id,
            "vaccinationId": vaccination_id,
            "vaccineName": vaccine_name,
            "date": date,
            "type": vaccine_type,
            "manufacturer": manufacturer,
            "doseNumber": dose_number,
            "lotNumber": lot_number,
            "nextDueDate": next_due_date,
            "location": kwargs.get("location"),
            "administeredBy": kwargs.get("administered_by")
        }

        result = self.client.execute_query(query, params)
        return dict(result[0]["v"]) if result else None

    def get_user_vaccinations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all vaccinations for a user."""
        query = """
        MATCH (u:User {userId: $userId})-[r:RECEIVED]->(v:Vaccination)
        RETURN v, r.date as receivedDate
        ORDER BY r.date DESC
        """
        result = self.client.execute_query(query, {"userId": user_id})
        return [dict(r["v"]) for r in result]

    def get_upcoming_vaccinations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get upcoming vaccinations (where nextDueDate is in the future)."""
        query = """
        MATCH (u:User {userId: $userId})-[:RECEIVED]->(v:Vaccination)
        WHERE v.nextDueDate >= date()
        RETURN v
        ORDER BY v.nextDueDate ASC
        """
        result = self.client.execute_query(query, {"userId": user_id})
        return [dict(r["v"]) for r in result]

    # ==================== Search Operations ====================

    def search_health_records(
        self,
        user_id: str,
        search_text: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Full-text search across health records."""
        query = """
        MATCH (u:User {userId: $userId})-[:HAS_RECORD]->(hr:HealthRecord)
        CALL db.index.fulltext.queryNodes('health_record_text_index', $searchText)
        YIELD node, score
        WHERE node = hr
        RETURN hr, score
        ORDER BY score DESC
        LIMIT $limit
        """

        params = {
            "userId": user_id,
            "searchText": search_text,
            "limit": limit
        }

        result = self.client.execute_query(query, params)
        return [{"record": dict(r["hr"]), "score": r["score"]} for r in result]
