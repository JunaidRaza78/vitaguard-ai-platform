"""
Appointment Operations for Neo4j
Handles CRUD operations for Appointment nodes and relationships
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid


class AppointmentOperations:
    """Appointment operations for Neo4j."""

    def __init__(self, client):
        """Initialize with Neo4j client."""
        self.client = client

    # ==================== Appointment CRUD ====================

    def create_appointment(
        self,
        user_id: str,
        date_time: str,
        appointment_type: str,
        status: str = "scheduled",
        reason: Optional[str] = None,
        notes: Optional[str] = None,
        reminder_sent: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create an Appointment node and link to User.

        Args:
            user_id: User UUID
            date_time: Appointment date and time (ISO format)
            appointment_type: Type (checkup, followup, emergency, consultation)
            status: scheduled/completed/cancelled/rescheduled
            reason: Reason for appointment
            notes: Additional notes
            reminder_sent: Whether reminder was sent

        Returns:
            Created appointment data
        """
        appointment_id = str(uuid.uuid4())

        query = """
        MATCH (u:User {userId: $userId})
        CREATE (a:Appointment {
            appointmentId: $appointmentId,
            dateTime: datetime($dateTime),
            type: $type,
            status: $status,
            reason: $reason,
            notes: $notes,
            reminderSent: $reminderSent,
            createdAt: datetime()
        })
        CREATE (u)-[:SCHEDULED]->(a)
        RETURN a
        """

        params = {
            "userId": user_id,
            "appointmentId": appointment_id,
            "dateTime": date_time,
            "type": appointment_type,
            "status": status,
            "reason": reason,
            "notes": notes,
            "reminderSent": reminder_sent
        }

        result = self.client.execute_query(query, params)
        return dict(result[0]["a"]) if result else None

    def get_appointment(self, appointment_id: str) -> Optional[Dict[str, Any]]:
        """Get appointment by ID."""
        query = """
        MATCH (a:Appointment {appointmentId: $appointmentId})
        RETURN a
        """
        result = self.client.execute_query(query, {"appointmentId": appointment_id})
        return dict(result[0]["a"]) if result else None

    def get_user_appointments(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get all appointments for a user, optionally filtered by status."""
        query = """
        MATCH (u:User {userId: $userId})-[:SCHEDULED]->(a:Appointment)
        WHERE $status IS NULL OR a.status = $status
        RETURN a
        ORDER BY a.dateTime DESC
        LIMIT $limit
        """

        params = {
            "userId": user_id,
            "status": status,
            "limit": limit
        }

        result = self.client.execute_query(query, params)
        return [dict(r["a"]) for r in result]

    def get_upcoming_appointments(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get upcoming appointments for a user."""
        query = """
        MATCH (u:User {userId: $userId})-[:SCHEDULED]->(a:Appointment)
        WHERE a.dateTime >= datetime() AND a.status = 'scheduled'
        RETURN a
        ORDER BY a.dateTime ASC
        LIMIT $limit
        """

        result = self.client.execute_query(query, {"userId": user_id, "limit": limit})
        return [dict(r["a"]) for r in result]

    def update_appointment_status(
        self,
        appointment_id: str,
        status: str,
        notes: Optional[str] = None
    ) -> bool:
        """Update appointment status."""
        query = """
        MATCH (a:Appointment {appointmentId: $appointmentId})
        SET a.status = $status
        SET a.notes = CASE WHEN $notes IS NOT NULL THEN $notes ELSE a.notes END
        SET a.updatedAt = datetime()
        RETURN count(a) as updated
        """

        params = {
            "appointmentId": appointment_id,
            "status": status,
            "notes": notes
        }

        result = self.client.execute_query(query, params)
        return result[0]["updated"] > 0 if result else False

    def update_reminder_status(
        self,
        appointment_id: str,
        reminder_sent: bool = True
    ) -> bool:
        """Mark reminder as sent for an appointment."""
        query = """
        MATCH (a:Appointment {appointmentId: $appointmentId})
        SET a.reminderSent = $reminderSent
        RETURN count(a) as updated
        """

        params = {
            "appointmentId": appointment_id,
            "reminderSent": reminder_sent
        }

        result = self.client.execute_query(query, params)
        return result[0]["updated"] > 0 if result else False

    def delete_appointment(self, appointment_id: str) -> bool:
        """Delete appointment and all relationships."""
        query = """
        MATCH (a:Appointment {appointmentId: $appointmentId})
        DETACH DELETE a
        RETURN count(a) as deleted
        """
        result = self.client.execute_query(query, {"appointmentId": appointment_id})
        return result[0]["deleted"] > 0 if result else False

    # ==================== Doctor Relationships ====================

    def link_appointment_to_doctor(
        self,
        appointment_id: str,
        doctor_id: str
    ) -> bool:
        """Create WITH_DOCTOR relationship between Appointment and Doctor."""
        query = """
        MATCH (a:Appointment {appointmentId: $appointmentId})
        MATCH (d:Doctor {doctorId: $doctorId})
        MERGE (a)-[r:WITH_DOCTOR]->(d)
        RETURN count(r) as created
        """

        params = {
            "appointmentId": appointment_id,
            "doctorId": doctor_id
        }

        result = self.client.execute_query(query, params)
        return result[0]["created"] > 0 if result else False

    def get_appointment_doctor(self, appointment_id: str) -> Optional[Dict[str, Any]]:
        """Get doctor for an appointment."""
        query = """
        MATCH (a:Appointment {appointmentId: $appointmentId})-[:WITH_DOCTOR]->(d:Doctor)
        RETURN d
        """
        result = self.client.execute_query(query, {"appointmentId": appointment_id})
        return dict(result[0]["d"]) if result else None

    def get_doctor_appointments(
        self,
        doctor_id: str,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get all appointments for a doctor."""
        query = """
        MATCH (a:Appointment)-[:WITH_DOCTOR]->(d:Doctor {doctorId: $doctorId})
        WHERE $status IS NULL OR a.status = $status
        OPTIONAL MATCH (u:User)-[:SCHEDULED]->(a)
        RETURN a, u
        ORDER BY a.dateTime DESC
        LIMIT $limit
        """

        params = {
            "doctorId": doctor_id,
            "status": status,
            "limit": limit
        }

        result = self.client.execute_query(query, params)
        return [{
            "appointment": dict(r["a"]),
            "user": dict(r["u"]) if r.get("u") else None
        } for r in result]

    # ==================== Hospital Relationships ====================

    def link_appointment_to_hospital(
        self,
        appointment_id: str,
        hospital_id: str
    ) -> bool:
        """Create AT_LOCATION relationship between Appointment and Hospital."""
        query = """
        MATCH (a:Appointment {appointmentId: $appointmentId})
        MATCH (h:Hospital {hospitalId: $hospitalId})
        MERGE (a)-[r:AT_LOCATION]->(h)
        RETURN count(r) as created
        """

        params = {
            "appointmentId": appointment_id,
            "hospitalId": hospital_id
        }

        result = self.client.execute_query(query, params)
        return result[0]["created"] > 0 if result else False

    def get_appointment_location(self, appointment_id: str) -> Optional[Dict[str, Any]]:
        """Get hospital location for an appointment."""
        query = """
        MATCH (a:Appointment {appointmentId: $appointmentId})-[:AT_LOCATION]->(h:Hospital)
        RETURN h
        """
        result = self.client.execute_query(query, {"appointmentId": appointment_id})
        return dict(result[0]["h"]) if result else None

    # ==================== Follow-up Relationships ====================

    def link_followup_appointment(
        self,
        original_appointment_id: str,
        followup_appointment_id: str,
        followup_reason: Optional[str] = None
    ) -> bool:
        """Create FOLLOWUP_TO relationship between appointments."""
        query = """
        MATCH (followup:Appointment {appointmentId: $followupId})
        MATCH (original:Appointment {appointmentId: $originalId})
        MERGE (followup)-[r:FOLLOWUP_TO {
            reason: $reason,
            createdAt: datetime()
        }]->(original)
        RETURN count(r) as created
        """

        params = {
            "followupId": followup_appointment_id,
            "originalId": original_appointment_id,
            "reason": followup_reason
        }

        result = self.client.execute_query(query, params)
        return result[0]["created"] > 0 if result else False

    def get_appointment_followups(self, appointment_id: str) -> List[Dict[str, Any]]:
        """Get all follow-up appointments for an appointment."""
        query = """
        MATCH (followup:Appointment)-[r:FOLLOWUP_TO]->(original:Appointment {appointmentId: $appointmentId})
        RETURN followup, r
        ORDER BY followup.dateTime ASC
        """
        result = self.client.execute_query(query, {"appointmentId": appointment_id})
        return [{
            "appointment": dict(r["followup"]),
            "relationship": dict(r["r"])
        } for r in result]

    # ==================== Health Record Relationships ====================

    def link_appointment_to_health_record(
        self,
        appointment_id: str,
        record_id: str
    ) -> bool:
        """Create RESULTED_IN relationship (Appointment -> HealthRecord)."""
        query = """
        MATCH (a:Appointment {appointmentId: $appointmentId})
        MATCH (hr:HealthRecord {recordId: $recordId})
        MERGE (a)-[r:RESULTED_IN {createdAt: datetime()}]->(hr)
        RETURN count(r) as created
        """

        params = {
            "appointmentId": appointment_id,
            "recordId": record_id
        }

        result = self.client.execute_query(query, params)
        return result[0]["created"] > 0 if result else False

    def get_appointment_records(self, appointment_id: str) -> List[Dict[str, Any]]:
        """Get all health records resulting from an appointment."""
        query = """
        MATCH (a:Appointment {appointmentId: $appointmentId})-[:RESULTED_IN]->(hr:HealthRecord)
        RETURN hr
        ORDER BY hr.date DESC
        """
        result = self.client.execute_query(query, {"appointmentId": appointment_id})
        return [dict(r["hr"]) for r in result]

    # ==================== Advanced Queries ====================

    def get_appointment_full_details(self, appointment_id: str) -> Dict[str, Any]:
        """Get complete appointment details with all relationships."""
        query = """
        MATCH (a:Appointment {appointmentId: $appointmentId})
        OPTIONAL MATCH (u:User)-[:SCHEDULED]->(a)
        OPTIONAL MATCH (a)-[:WITH_DOCTOR]->(d:Doctor)
        OPTIONAL MATCH (a)-[:AT_LOCATION]->(h:Hospital)
        OPTIONAL MATCH (a)-[:RESULTED_IN]->(hr:HealthRecord)
        OPTIONAL MATCH (followup:Appointment)-[:FOLLOWUP_TO]->(a)
        RETURN a, u, d, h, collect(DISTINCT hr) as records, collect(DISTINCT followup) as followups
        """

        result = self.client.execute_query(query, {"appointmentId": appointment_id})

        if not result:
            return None

        r = result[0]
        return {
            "appointment": dict(r["a"]),
            "user": dict(r["u"]) if r.get("u") else None,
            "doctor": dict(r["d"]) if r.get("d") else None,
            "hospital": dict(r["h"]) if r.get("h") else None,
            "records": [dict(rec) for rec in r["records"]] if r.get("records") else [],
            "followups": [dict(f) for f in r["followups"]] if r.get("followups") else []
        }

    def get_appointments_needing_reminders(
        self,
        hours_before: int = 24
    ) -> List[Dict[str, Any]]:
        """Get appointments that need reminders sent."""
        query = """
        MATCH (u:User)-[:SCHEDULED]->(a:Appointment)
        WHERE a.status = 'scheduled'
        AND a.reminderSent = false
        AND a.dateTime >= datetime()
        AND a.dateTime <= datetime() + duration({hours: $hoursBefore})
        RETURN a, u
        ORDER BY a.dateTime ASC
        """

        result = self.client.execute_query(query, {"hoursBefore": hours_before})
        return [{
            "appointment": dict(r["a"]),
            "user": dict(r["u"])
        } for r in result]

    def get_family_appointments(
        self,
        family_id: str,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get all appointments for a family."""
        query = """
        MATCH (u:User)-[:MEMBER_OF]->(f:Family {familyId: $familyId})
        MATCH (u)-[:SCHEDULED]->(a:Appointment)
        WHERE $status IS NULL OR a.status = $status
        OPTIONAL MATCH (a)-[:WITH_DOCTOR]->(d:Doctor)
        RETURN a, u, d
        ORDER BY a.dateTime DESC
        LIMIT $limit
        """

        params = {
            "familyId": family_id,
            "status": status,
            "limit": limit
        }

        result = self.client.execute_query(query, params)
        return [{
            "appointment": dict(r["a"]),
            "user": dict(r["u"]),
            "doctor": dict(r["d"]) if r.get("d") else None
        } for r in result]
