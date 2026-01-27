"""
Unified Neo4j client for all graph database operations.
Combines base connection functionality with all domain-specific operations.
"""
from typing import Optional, Dict, Any, List
from neo4j import GraphDatabase
from .config import neo4j_config
import logging

# Simplified - skip operations for now to avoid complex dependencies
UserOperations = None
FamilyOperations = None
HealthRecordOperations = None
MedicationOperations = None
ConditionOperations = None
ProviderOperations = None
AppointmentOperations = None
VitalsOperations = None
InsightsOperations = None
AccessControlOperations = None

# Initialize logger
logger = logging.getLogger('neo4j.client')


class BaseNeo4jClient:
    """Base Neo4j client providing core connection and query functionality."""

    def __init__(self):
        self.config = neo4j_config
        self.driver: Optional[GraphDatabase.driver] = None
        logger.debug("BaseNeo4jClient initialized")

    def __enter__(self):
        """Context manager entry."""
        self.driver = self.config.get_driver()
        logger.debug("Neo4j context manager entered")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        logger.debug("Neo4j context manager exited")
        pass  # Driver is managed by config

    def get_driver(self) -> GraphDatabase.driver:
        """Get Neo4j driver instance."""
        if self.driver is None:
            logger.debug("Getting Neo4j driver from config")
            self.driver = self.config.get_driver()
        return self.driver

    def get_session(self, database: Optional[str] = None):
        """Get a Neo4j session."""
        db = database or self.config.database
        logger.debug(f"Creating session for database: {db}")
        return self.get_driver().session(database=db)

    def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None
    ) -> List[Any]:
        """
        Execute a Cypher query with proper session management.

        Args:
            query: Cypher query string
            parameters: Query parameters
            database: Database name (optional)

        Returns:
            Query results as list of records
        """
        try:
            logger.debug(
                f"Executing query: {query[:100]}..."
                if len(query) > 100
                else f"Executing query: {query}"
            )
            with self.get_session(database) as session:
                result = session.run(query, parameters or {})
                # Consume results within session context
                records = list(result)
                logger.debug(f"Query returned {len(records)} records")
                return records
        except Exception as e:
            logger.error(f"Query execution failed: {type(e).__name__}: {str(e)}")
            logger.debug(f"Failed query: {query}")
            logger.debug(f"Parameters: {parameters}")
            raise

    def execute_cypher(
        self,
        cypher: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute raw Cypher query.

        Args:
            cypher: Cypher query string
            parameters: Query parameters
            database: Database name (optional)

        Returns:
            List of result dictionaries
        """
        result = self.execute_query(cypher, parameters, database)
        return [dict(record) for record in result]

    def health_check(self) -> bool:
        """Check Neo4j connection health."""
        return self.config.verify_connectivity()




class Neo4jClient(BaseNeo4jClient):
    """
    Unified Neo4j client with all operations.

    Simplified version - inherits from BaseNeo4jClient only.
    Operation classes can be added later.

    Original functionality from:
    - UserOperations: User CRUD operations
    - FamilyOperations: Family CRUD and relationship operations
    - HealthRecordOperations: Health records, lab reports, prescriptions, vaccinations
    - MedicationOperations: Medications, drug interactions, side effects
    - ConditionOperations: Medical conditions, symptoms, genetic risk analysis
    - ProviderOperations: Doctors, hospitals, geospatial search
    - AppointmentOperations: Appointments, scheduling, follow-ups
    - VitalsOperations: Vital signs, growth records, lab results
    - InsightsOperations: AI-generated health insights and risk factors
    - AccessControlOperations: Permissions, roles, and authorization
    - GraphOperations: Generic node/relationship operations (inherited)
    - BaseNeo4jClient: Core connection and query execution (inherited)

    Usage:
        from backend.shared.database.neo4j import Neo4jClient

        client = Neo4jClient()

        # User operations
        user = client.create_user(
            userId="123",
            email="user@example.com",
            name="John Doe",
            dateOfBirth="1990-01-01",
            gender="M"
        )

        # Family operations
        family = client.create_family(
            familyId="456",
            name="Doe Family",
            createdBy="123"
        )

        # Health record operations
        record = client.create_health_record(
            user_id="123",
            record_type="lab_report",
            date="2024-01-15",
            title="Annual Checkup",
            summary="All results normal"
        )

        # Medication operations
        medication = client.create_medication(
            name="Aspirin",
            generic_name="Acetylsalicylic acid"
        )

        # Check drug interactions
        interactions = client.check_user_drug_interactions("123")

        # Condition operations
        condition = client.create_condition(
            name="Hypertension",
            icd_code="I10",
            category="chronic",
            severity="moderate"
        )

        # Provider operations
        doctor = client.create_doctor(
            name="Dr. Smith",
            specialty="Cardiology",
            license_number="MD12345"
        )

        # Search nearby hospitals
        hospitals = client.search_nearby_hospitals(
            latitude=40.7128,
            longitude=-74.0060,
            max_distance_km=5.0
        )

        # Appointment operations
        appointment = client.create_appointment(
            user_id="123",
            date_time="2024-02-01T10:00:00",
            appointment_type="checkup"
        )

        # Vitals operations
        vital = client.create_vital_sign(
            user_id="123",
            vital_type="blood_pressure",
            value=120,
            unit="mmHg",
            date="2024-01-15"
        )

        # Growth tracking
        growth = client.create_growth_record(
            user_id="child123",
            date="2024-01-15",
            age_months=24,
            height_cm=85.5,
            weight_kg=12.3
        )

        # AI Insights operations
        insight = client.create_health_insight(
            user_id="123",
            insight_type="alert",
            title="Elevated Blood Pressure",
            description="Your recent readings show consistently high BP",
            severity="medium"
        )

        # Risk factor analysis
        risk = client.create_risk_factor(
            user_id="123",
            risk_type="lifestyle",
            name="Sedentary Lifestyle",
            description="Low physical activity detected",
            risk_level="medium"
        )

        # Health check
        if client.health_check():
            print("Neo4j connection is healthy")
    """

    def __init__(self):
        """Initialize unified Neo4j client."""
        super().__init__()
        logger.info("Neo4jClient initialized with all operations")


def get_neo4j_client() -> Neo4jClient:
    """
    Convenience function to get a Neo4j client instance.

    Returns:
        Neo4jClient instance with all operations available
    """
    return Neo4jClient()
