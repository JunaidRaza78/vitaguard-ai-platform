"""
Provider Operations for Neo4j
Handles Doctor and Hospital nodes and relationships
"""
from typing import Dict, List, Optional, Any
import uuid


class ProviderOperations:
    """Provider (Doctor & Hospital) operations for Neo4j."""

    def __init__(self, client):
        """Initialize with Neo4j client."""
        self.client = client

    # ==================== Doctor CRUD ====================

    def create_doctor(
        self,
        name: str,
        specialty: str,
        license_number: str,
        phone_number: Optional[str] = None,
        email: Optional[str] = None,
        years_of_experience: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a Doctor node.

        Args:
            name: Doctor name
            specialty: Medical specialty
            license_number: Medical license number
            phone_number: Contact phone
            email: Contact email
            years_of_experience: Years of experience

        Returns:
            Created doctor data
        """
        doctor_id = str(uuid.uuid4())

        query = """
        CREATE (d:Doctor {
            doctorId: $doctorId,
            name: $name,
            specialty: $specialty,
            licenseNumber: $licenseNumber,
            phoneNumber: $phoneNumber,
            email: $email,
            yearsOfExperience: $yearsOfExperience
        })
        RETURN d
        """

        params = {
            "doctorId": doctor_id,
            "name": name,
            "specialty": specialty,
            "licenseNumber": license_number,
            "phoneNumber": phone_number,
            "email": email,
            "yearsOfExperience": years_of_experience
        }

        result = self.client.execute_query(query, params)
        return dict(result[0]["d"]) if result else None

    def get_doctor(self, doctor_id: str) -> Optional[Dict[str, Any]]:
        """Get doctor by ID."""
        query = """
        MATCH (d:Doctor {doctorId: $doctorId})
        RETURN d
        """
        result = self.client.execute_query(query, {"doctorId": doctor_id})
        return dict(result[0]["d"]) if result else None

    def search_doctors(
        self,
        specialty: Optional[str] = None,
        search_text: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search doctors by specialty or name."""
        if search_text:
            # Full-text search
            query = """
            CALL db.index.fulltext.queryNodes('doctor_search', $searchText)
            YIELD node, score
            WHERE $specialty IS NULL OR node.specialty = $specialty
            RETURN node as d, score
            ORDER BY score DESC
            LIMIT $limit
            """
            params = {"searchText": search_text, "specialty": specialty, "limit": limit}
        else:
            # Specialty filter
            query = """
            MATCH (d:Doctor)
            WHERE $specialty IS NULL OR d.specialty = $specialty
            RETURN d
            ORDER BY d.name
            LIMIT $limit
            """
            params = {"specialty": specialty, "limit": limit}

        result = self.client.execute_query(query, params)
        return [dict(r["d"]) for r in result]

    # ==================== Hospital CRUD ====================

    def create_hospital(
        self,
        name: str,
        address: str,
        latitude: float,
        longitude: float,
        phone_number: Optional[str] = None,
        emergency_available: bool = True,
        rating: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a Hospital node with geospatial location.

        Args:
            name: Hospital name
            address: Full address
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            phone_number: Contact phone
            emergency_available: Emergency services available
            rating: Hospital rating (0-5)

        Returns:
            Created hospital data
        """
        hospital_id = str(uuid.uuid4())

        query = """
        CREATE (h:Hospital {
            hospitalId: $hospitalId,
            name: $name,
            address: $address,
            location: point({latitude: $latitude, longitude: $longitude}),
            phoneNumber: $phoneNumber,
            emergencyAvailable: $emergencyAvailable,
            rating: $rating
        })
        RETURN h
        """

        params = {
            "hospitalId": hospital_id,
            "name": name,
            "address": address,
            "latitude": latitude,
            "longitude": longitude,
            "phoneNumber": phone_number,
            "emergencyAvailable": emergency_available,
            "rating": rating
        }

        result = self.client.execute_query(query, params)
        return dict(result[0]["h"]) if result else None

    def get_hospital(self, hospital_id: str) -> Optional[Dict[str, Any]]:
        """Get hospital by ID."""
        query = """
        MATCH (h:Hospital {hospitalId: $hospitalId})
        RETURN h
        """
        result = self.client.execute_query(query, {"hospitalId": hospital_id})
        return dict(result[0]["h"]) if result else None

    def search_nearby_hospitals(
        self,
        latitude: float,
        longitude: float,
        max_distance_km: float = 10.0,
        emergency_only: bool = False,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find hospitals near a location using geospatial search.

        Args:
            latitude: Search latitude
            longitude: Search longitude
            max_distance_km: Maximum distance in kilometers
            emergency_only: Only show hospitals with emergency services
            limit: Maximum results

        Returns:
            List of nearby hospitals with distance
        """
        query = """
        MATCH (h:Hospital)
        WHERE $emergencyOnly = false OR h.emergencyAvailable = true
        WITH h,
             point.distance(h.location, point({latitude: $latitude, longitude: $longitude})) / 1000.0 as distance
        WHERE distance <= $maxDistance
        RETURN h, distance
        ORDER BY distance ASC
        LIMIT $limit
        """

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "maxDistance": max_distance_km,
            "emergencyOnly": emergency_only,
            "limit": limit
        }

        result = self.client.execute_query(query, params)
        return [{"hospital": dict(r["h"]), "distance_km": r["distance"]} for r in result]

    # ==================== Doctor-Hospital Relationships ====================

    def link_doctor_to_hospital(
        self,
        doctor_id: str,
        hospital_id: str,
        start_date: str,
        is_primary: bool = True
    ) -> bool:
        """Create WORKS_AT relationship between Doctor and Hospital."""
        query = """
        MATCH (d:Doctor {doctorId: $doctorId})
        MATCH (h:Hospital {hospitalId: $hospitalId})
        MERGE (d)-[r:WORKS_AT {
            startDate: date($startDate),
            isPrimary: $isPrimary
        }]->(h)
        RETURN count(r) as created
        """

        params = {
            "doctorId": doctor_id,
            "hospitalId": hospital_id,
            "startDate": start_date,
            "isPrimary": is_primary
        }

        result = self.client.execute_query(query, params)
        return result[0]["created"] > 0 if result else False

    def get_doctor_hospitals(self, doctor_id: str) -> List[Dict[str, Any]]:
        """Get all hospitals where a doctor works."""
        query = """
        MATCH (d:Doctor {doctorId: $doctorId})-[r:WORKS_AT]->(h:Hospital)
        RETURN h, r
        ORDER BY r.isPrimary DESC, r.startDate DESC
        """
        result = self.client.execute_query(query, {"doctorId": doctor_id})
        return [{"hospital": dict(r["h"]), "relationship": dict(r["r"])} for r in result]

    def get_hospital_doctors(
        self,
        hospital_id: str,
        specialty: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all doctors working at a hospital, optionally filtered by specialty."""
        query = """
        MATCH (d:Doctor)-[r:WORKS_AT]->(h:Hospital {hospitalId: $hospitalId})
        WHERE $specialty IS NULL OR d.specialty = $specialty
        RETURN d, r
        ORDER BY d.name
        """

        params = {"hospitalId": hospital_id, "specialty": specialty}
        result = self.client.execute_query(query, params)
        return [{"doctor": dict(r["d"]), "relationship": dict(r["r"])} for r in result]

    # ==================== User-Provider Relationships ====================

    def link_user_to_doctor(
        self,
        user_id: str,
        doctor_id: str,
        first_visit: str,
        is_primary_care: bool = False
    ) -> bool:
        """Create TREATED_BY relationship between User and Doctor."""
        query = """
        MATCH (u:User {userId: $userId})
        MATCH (d:Doctor {doctorId: $doctorId})
        MERGE (u)-[r:TREATED_BY {
            firstVisit: date($firstVisit),
            lastVisit: date($firstVisit),
            visitCount: 1,
            primaryCare: $primaryCare
        }]->(d)
        RETURN count(r) as created
        """

        params = {
            "userId": user_id,
            "doctorId": doctor_id,
            "firstVisit": first_visit,
            "primaryCare": is_primary_care
        }

        result = self.client.execute_query(query, params)
        return result[0]["created"] > 0 if result else False

    def update_doctor_visit(
        self,
        user_id: str,
        doctor_id: str,
        visit_date: str
    ) -> bool:
        """Update visit count and last visit date for user-doctor relationship."""
        query = """
        MATCH (u:User {userId: $userId})-[r:TREATED_BY]->(d:Doctor {doctorId: $doctorId})
        SET r.lastVisit = date($visitDate),
            r.visitCount = r.visitCount + 1
        RETURN count(r) as updated
        """

        params = {
            "userId": user_id,
            "doctorId": doctor_id,
            "visitDate": visit_date
        }

        result = self.client.execute_query(query, params)
        return result[0]["updated"] > 0 if result else False

    def get_user_doctors(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all doctors treating a user."""
        query = """
        MATCH (u:User {userId: $userId})-[r:TREATED_BY]->(d:Doctor)
        RETURN d, r
        ORDER BY r.primaryCare DESC, r.lastVisit DESC
        """
        result = self.client.execute_query(query, {"userId": user_id})
        return [{"doctor": dict(r["d"]), "relationship": dict(r["r"])} for r in result]

    # ==================== Doctor Specialization ====================

    def link_doctor_specialization(
        self,
        doctor_id: str,
        condition_id: str,
        years_experience: int,
        certification: Optional[str] = None
    ) -> bool:
        """Create SPECIALIZES_IN relationship between Doctor and Condition."""
        query = """
        MATCH (d:Doctor {doctorId: $doctorId})
        MATCH (c:Condition {conditionId: $conditionId})
        MERGE (d)-[r:SPECIALIZES_IN {
            yearsExperience: $yearsExperience,
            certification: $certification
        }]->(c)
        RETURN count(r) as created
        """

        params = {
            "doctorId": doctor_id,
            "conditionId": condition_id,
            "yearsExperience": years_experience,
            "certification": certification
        }

        result = self.client.execute_query(query, params)
        return result[0]["created"] > 0 if result else False

    def find_specialists(
        self,
        condition_id: str,
        min_experience: int = 0,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Find doctors who specialize in a specific condition."""
        query = """
        MATCH (d:Doctor)-[r:SPECIALIZES_IN]->(c:Condition {conditionId: $conditionId})
        WHERE r.yearsExperience >= $minExperience
        RETURN d, r
        ORDER BY r.yearsExperience DESC
        LIMIT $limit
        """

        params = {
            "conditionId": condition_id,
            "minExperience": min_experience,
            "limit": limit
        }

        result = self.client.execute_query(query, params)
        return [{"doctor": dict(r["d"]), "specialization": dict(r["r"])} for r in result]
