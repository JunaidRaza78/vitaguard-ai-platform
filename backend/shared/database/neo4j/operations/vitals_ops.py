"""
Vitals & Growth Record Operations for Neo4j
Handles CRUD operations for VitalSign, GrowthRecord, and LabResult nodes
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid


class VitalsOperations:
    """Vitals and growth record operations for Neo4j."""

    def __init__(self, client):
        """Initialize with Neo4j client."""
        self.client = client

    # ==================== VitalSign CRUD ====================

    def create_vital_sign(
        self,
        user_id: str,
        vital_type: str,
        value: float,
        unit: str,
        date: str,
        time: Optional[str] = None,
        notes: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a VitalSign node and link to User.

        Args:
            user_id: User UUID
            vital_type: Type (blood_pressure, heart_rate, temperature, weight, etc.)
            value: Numeric value
            unit: Unit of measurement
            date: Date of measurement (YYYY-MM-DD)
            time: Time of measurement (HH:MM:SS)
            notes: Additional notes

        Returns:
            Created vital sign data
        """
        vital_id = str(uuid.uuid4())

        query = """
        MERGE (u:User {userId: $userId})
        ON CREATE SET u.createdAt = datetime()
        CREATE (vs:VitalSign {
            vitalId: $vitalId,
            type: $type,
            value: $value,
            unit: $unit,
            date: date($date),
            time: CASE WHEN $time IS NOT NULL THEN time($time) ELSE NULL END,
            notes: $notes,
            createdAt: datetime()
        })
        CREATE (u)-[:HAS_VITAL]->(vs)
        RETURN vs
        """

        params = {
            "userId": user_id,
            "vitalId": vital_id,
            "type": vital_type,
            "value": value,
            "unit": unit,
            "date": date,
            "time": time,
            "notes": notes
        }

        result = self.client.execute_query(query, params)
        return dict(result[0]["vs"]) if result else None

    def get_vital_sign(self, vital_id: str) -> Optional[Dict[str, Any]]:
        """Get vital sign by ID."""
        query = """
        MATCH (vs:VitalSign {vitalId: $vitalId})
        RETURN vs
        """
        result = self.client.execute_query(query, {"vitalId": vital_id})
        return dict(result[0]["vs"]) if result else None

    def get_user_vitals(
        self,
        user_id: str,
        vital_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get all vital signs for a user, optionally filtered by type."""
        query = """
        MATCH (u:User {userId: $userId})-[:HAS_VITAL]->(vs:VitalSign)
        WHERE $type IS NULL OR vs.type = $type
        RETURN vs
        ORDER BY vs.date DESC, vs.time DESC
        LIMIT $limit
        """

        params = {
            "userId": user_id,
            "type": vital_type,
            "limit": limit
        }

        result = self.client.execute_query(query, params)
        return [dict(r["vs"]) for r in result]

    def get_vitals_in_range(
        self,
        user_id: str,
        vital_type: str,
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """Get vital signs for a user within a date range."""
        query = """
        MATCH (u:User {userId: $userId})-[:HAS_VITAL]->(vs:VitalSign)
        WHERE vs.type = $type
        AND vs.date >= date($startDate)
        AND vs.date <= date($endDate)
        RETURN vs
        ORDER BY vs.date ASC, vs.time ASC
        """

        params = {
            "userId": user_id,
            "type": vital_type,
            "startDate": start_date,
            "endDate": end_date
        }

        result = self.client.execute_query(query, params)
        return [dict(r["vs"]) for r in result]

    def get_latest_vitals(self, user_id: str) -> Dict[str, Any]:
        """Get the most recent vital sign of each type for a user."""
        query = """
        MATCH (u:User {userId: $userId})-[:HAS_VITAL]->(vs:VitalSign)
        WITH vs.type as vitalType, vs
        ORDER BY vs.date DESC, vs.time DESC
        WITH vitalType, collect(vs)[0] as latestVital
        RETURN vitalType, latestVital
        """

        result = self.client.execute_query(query, {"userId": user_id})

        vitals = {}
        for r in result:
            vitals[r["vitalType"]] = dict(r["latestVital"])

        return vitals

    def delete_vital_sign(self, vital_id: str) -> bool:
        """Delete vital sign."""
        query = """
        MATCH (vs:VitalSign {vitalId: $vitalId})
        DETACH DELETE vs
        RETURN count(vs) as deleted
        """
        result = self.client.execute_query(query, {"vitalId": vital_id})
        return result[0]["deleted"] > 0 if result else False

    # ==================== GrowthRecord CRUD ====================

    def create_growth_record(
        self,
        user_id: str,
        date: str,
        age_months: int,
        height_cm: Optional[float] = None,
        weight_kg: Optional[float] = None,
        head_circumference_cm: Optional[float] = None,
        bmi: Optional[float] = None,
        percentiles: Optional[Dict[str, float]] = None,
        notes: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a GrowthRecord node for tracking child growth.

        Args:
            user_id: User UUID
            date: Date of measurement (YYYY-MM-DD)
            age_months: Age in months
            height_cm: Height in centimeters
            weight_kg: Weight in kilograms
            head_circumference_cm: Head circumference in cm
            bmi: Body Mass Index
            percentiles: Growth percentiles (height, weight, etc.)
            notes: Additional notes

        Returns:
            Created growth record data
        """
        record_id = str(uuid.uuid4())

        query = """
        MERGE (u:User {userId: $userId})
        ON CREATE SET u.createdAt = datetime()
        CREATE (gr:GrowthRecord {
            recordId: $recordId,
            date: date($date),
            ageMonths: $ageMonths,
            heightCm: $heightCm,
            weightKg: $weightKg,
            headCircumferenceCm: $headCircumferenceCm,
            bmi: $bmi,
            percentiles: $percentiles,
            notes: $notes,
            createdAt: datetime()
        })
        CREATE (u)-[:HAS_GROWTH_RECORD]->(gr)
        RETURN gr
        """

        params = {
            "userId": user_id,
            "recordId": record_id,
            "date": date,
            "ageMonths": age_months,
            "heightCm": height_cm,
            "weightKg": weight_kg,
            "headCircumferenceCm": head_circumference_cm,
            "bmi": bmi,
            "percentiles": percentiles,
            "notes": notes
        }

        result = self.client.execute_query(query, params)
        return dict(result[0]["gr"]) if result else None

    def get_growth_record(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Get growth record by ID."""
        query = """
        MATCH (gr:GrowthRecord {recordId: $recordId})
        RETURN gr
        """
        result = self.client.execute_query(query, {"recordId": record_id})
        return dict(result[0]["gr"]) if result else None

    def get_user_growth_records(
        self,
        user_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get all growth records for a user."""
        query = """
        MATCH (u:User {userId: $userId})-[:HAS_GROWTH_RECORD]->(gr:GrowthRecord)
        RETURN gr
        ORDER BY gr.date DESC
        LIMIT $limit
        """

        result = self.client.execute_query(query, {"userId": user_id, "limit": limit})
        return [dict(r["gr"]) for r in result]

    def get_growth_trend(
        self,
        user_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get growth trend data for a user."""
        query = """
        MATCH (u:User {userId: $userId})-[:HAS_GROWTH_RECORD]->(gr:GrowthRecord)
        WHERE ($startDate IS NULL OR gr.date >= date($startDate))
        AND ($endDate IS NULL OR gr.date <= date($endDate))
        RETURN gr
        ORDER BY gr.date ASC
        """

        params = {
            "userId": user_id,
            "startDate": start_date,
            "endDate": end_date
        }

        result = self.client.execute_query(query, params)
        return [dict(r["gr"]) for r in result]

    # ==================== LabResult CRUD ====================

    def create_lab_result(
        self,
        user_id: str,
        test_name: str,
        date: str,
        result_value: str,
        unit: Optional[str] = None,
        reference_range: Optional[str] = None,
        status: str = "normal",
        lab_report_id: Optional[str] = None,
        notes: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a LabResult node for individual lab test results.

        Args:
            user_id: User UUID
            test_name: Name of the test
            date: Date of test (YYYY-MM-DD)
            result_value: Result value
            unit: Unit of measurement
            reference_range: Normal reference range
            status: normal/abnormal/critical
            lab_report_id: Optional link to LabReport
            notes: Additional notes

        Returns:
            Created lab result data
        """
        result_id = str(uuid.uuid4())

        query = """
        MERGE (u:User {userId: $userId})
        ON CREATE SET u.createdAt = datetime()
        CREATE (lr:LabResult {
            resultId: $resultId,
            testName: $testName,
            date: date($date),
            resultValue: $resultValue,
            unit: $unit,
            referenceRange: $referenceRange,
            status: $status,
            notes: $notes,
            createdAt: datetime()
        })
        CREATE (u)-[:HAS_LAB_RESULT]->(lr)
        RETURN lr
        """

        params = {
            "userId": user_id,
            "resultId": result_id,
            "testName": test_name,
            "date": date,
            "resultValue": result_value,
            "unit": unit,
            "referenceRange": reference_range,
            "status": status,
            "notes": notes
        }

        result = self.client.execute_query(query, params)

        # Link to LabReport if provided
        if result and lab_report_id:
            self.link_lab_result_to_report(result_id, lab_report_id)

        return dict(result[0]["lr"]) if result else None

    def get_lab_result(self, result_id: str) -> Optional[Dict[str, Any]]:
        """Get lab result by ID."""
        query = """
        MATCH (lr:LabResult {resultId: $resultId})
        RETURN lr
        """
        result = self.client.execute_query(query, {"resultId": result_id})
        return dict(result[0]["lr"]) if result else None

    def get_user_lab_results(
        self,
        user_id: str,
        test_name: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get all lab results for a user."""
        query = """
        MATCH (u:User {userId: $userId})-[:HAS_LAB_RESULT]->(lr:LabResult)
        WHERE ($testName IS NULL OR lr.testName = $testName)
        AND ($status IS NULL OR lr.status = $status)
        RETURN lr
        ORDER BY lr.date DESC
        LIMIT $limit
        """

        params = {
            "userId": user_id,
            "testName": test_name,
            "status": status,
            "limit": limit
        }

        result = self.client.execute_query(query, params)
        return [dict(r["lr"]) for r in result]

    def link_lab_result_to_report(
        self,
        result_id: str,
        report_id: str
    ) -> bool:
        """Link lab result to a lab report."""
        query = """
        MATCH (lr:LabResult {resultId: $resultId})
        MATCH (report:LabReport {reportId: $reportId})
        MERGE (lr)-[r:PART_OF]->(report)
        RETURN count(r) as created
        """

        params = {
            "resultId": result_id,
            "reportId": report_id
        }

        result = self.client.execute_query(query, params)
        return result[0]["created"] > 0 if result else False

    def get_lab_report_results(self, report_id: str) -> List[Dict[str, Any]]:
        """Get all lab results for a specific lab report."""
        query = """
        MATCH (lr:LabResult)-[:PART_OF]->(report:LabReport {reportId: $reportId})
        RETURN lr
        ORDER BY lr.testName ASC
        """
        result = self.client.execute_query(query, {"reportId": report_id})
        return [dict(r["lr"]) for r in result]

    # ==================== Advanced Queries ====================

    def get_abnormal_vitals(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get abnormal vital signs based on predefined thresholds.
        This is a simplified version - real implementation would use actual medical thresholds.
        """
        query = """
        MATCH (u:User {userId: $userId})-[:HAS_VITAL]->(vs:VitalSign)
        WHERE (vs.type = 'blood_pressure_systolic' AND (vs.value > 140 OR vs.value < 90))
        OR (vs.type = 'heart_rate' AND (vs.value > 100 OR vs.value < 60))
        OR (vs.type = 'temperature' AND (vs.value > 38 OR vs.value < 36))
        RETURN vs
        ORDER BY vs.date DESC
        LIMIT $limit
        """

        result = self.client.execute_query(query, {"userId": user_id, "limit": limit})
        return [dict(r["vs"]) for r in result]

    def get_abnormal_lab_results(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get all abnormal or critical lab results for a user."""
        query = """
        MATCH (u:User {userId: $userId})-[:HAS_LAB_RESULT]->(lr:LabResult)
        WHERE lr.status IN ['abnormal', 'critical']
        RETURN lr
        ORDER BY lr.date DESC
        LIMIT $limit
        """

        result = self.client.execute_query(query, {"userId": user_id, "limit": limit})
        return [dict(r["lr"]) for r in result]

    def compare_growth_with_family(
        self,
        user_id: str,
        family_id: str
    ) -> Dict[str, Any]:
        """Compare child's growth with family members at similar ages."""
        query = """
        MATCH (u:User {userId: $userId})-[:HAS_GROWTH_RECORD]->(gr:GrowthRecord)
        WITH gr.ageMonths as targetAge, avg(gr.heightCm) as userAvgHeight, avg(gr.weightKg) as userAvgWeight
        MATCH (f:Family {familyId: $familyId})<-[:MEMBER_OF]-(other:User)
        WHERE other.userId <> $userId
        MATCH (other)-[:HAS_GROWTH_RECORD]->(otherGr:GrowthRecord)
        WHERE otherGr.ageMonths = targetAge
        RETURN targetAge,
               userAvgHeight,
               userAvgWeight,
               avg(otherGr.heightCm) as familyAvgHeight,
               avg(otherGr.weightKg) as familyAvgWeight,
               count(DISTINCT other) as familyMemberCount
        """

        params = {
            "userId": user_id,
            "familyId": family_id
        }

        result = self.client.execute_query(query, params)
        return [dict(r) for r in result]

    def get_vital_statistics(
        self,
        user_id: str,
        vital_type: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get statistical summary of a vital sign over a period."""
        query = """
        MATCH (u:User {userId: $userId})-[:HAS_VITAL]->(vs:VitalSign {type: $vitalType})
        WHERE vs.date >= date() - duration({days: $days})
        RETURN
            min(vs.value) as min,
            max(vs.value) as max,
            avg(vs.value) as avg,
            count(vs) as count,
            collect(vs.value) as values
        """

        params = {
            "userId": user_id,
            "vitalType": vital_type,
            "days": days
        }

        result = self.client.execute_query(query, params)
        return dict(result[0]) if result else None
