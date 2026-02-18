"""
Seed Family Health Data
Populates Neo4j with a 3-generation family (grandparents, parents, children)
including conditions, medications, and relationships.
Also populates PostgreSQL with health events for the timeline.

Usage:
    python -m scripts.seed_family_data
    # or from Backend directory:
    python scripts/seed_family_data.py
"""

import sys
import os
import uuid
from datetime import datetime, timezone, timedelta

# Ensure project root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.database.neo4j.operations.user_ops import UserOperations
from shared.database.neo4j.operations.family_ops import FamilyOperations
from shared.database.neo4j.operations.graph_ops import GraphOperations


# ==================== IDs ====================

FAMILY_ID = "family-001"

# Grandparents
GRANDFATHER_ID = "user-gf-001"
GRANDMOTHER_ID = "user-gm-001"

# Parents
FATHER_ID = "user-father-001"
MOTHER_ID = "user-mother-001"

# Children
SON_ID = "user-son-001"
DAUGHTER_ID = "user-daughter-001"

# Conditions
COND_DIABETES = "cond-001"
COND_HYPERTENSION = "cond-002"
COND_ASTHMA = "cond-003"
COND_ARTHRITIS = "cond-004"
COND_HIGH_CHOLESTEROL = "cond-005"
COND_MIGRAINE = "cond-006"
COND_HEART_DISEASE = "cond-007"

# Medications
MED_METFORMIN = "med-001"
MED_LISINOPRIL = "med-002"
MED_ALBUTEROL = "med-003"
MED_ATORVASTATIN = "med-004"
MED_IBUPROFEN = "med-005"
MED_ASPIRIN = "med-006"


def clear_existing_data():
    """Remove all existing nodes and relationships."""
    print("Clearing existing Neo4j data...")
    ops = GraphOperations()
    ops.execute_query("MATCH (n) DETACH DELETE n")
    print("  Neo4j data cleared.")


def seed_users():
    """Create User nodes for the family."""
    print("\nCreating User nodes...")
    user_ops = UserOperations()

    users = [
        {
            "userId": GRANDFATHER_ID,
            "email": "robert.khan@example.com",
            "name": "Robert Khan",
            "dateOfBirth": "1945-03-15",
            "gender": "M",
            "bloodType": "A+",
            "phoneNumber": "+1-555-0101",
        },
        {
            "userId": GRANDMOTHER_ID,
            "email": "margaret.khan@example.com",
            "name": "Margaret Khan",
            "dateOfBirth": "1948-07-22",
            "gender": "F",
            "bloodType": "O+",
            "phoneNumber": "+1-555-0102",
        },
        {
            "userId": FATHER_ID,
            "email": "ahmed.khan@example.com",
            "name": "Ahmed Khan",
            "dateOfBirth": "1975-11-08",
            "gender": "M",
            "bloodType": "A+",
            "phoneNumber": "+1-555-0201",
        },
        {
            "userId": MOTHER_ID,
            "email": "sarah.khan@example.com",
            "name": "Sarah Khan",
            "dateOfBirth": "1978-04-12",
            "gender": "F",
            "bloodType": "B+",
            "phoneNumber": "+1-555-0202",
        },
        {
            "userId": SON_ID,
            "email": "ali.khan@example.com",
            "name": "Ali Khan",
            "dateOfBirth": "2005-09-20",
            "gender": "M",
            "bloodType": "A+",
            "phoneNumber": "+1-555-0301",
        },
        {
            "userId": DAUGHTER_ID,
            "email": "fatima.khan@example.com",
            "name": "Fatima Khan",
            "dateOfBirth": "2008-01-15",
            "gender": "F",
            "bloodType": "AB+",
            "phoneNumber": "+1-555-0302",
        },
    ]

    for u in users:
        user_ops.create_user(**u)
        print(f"  Created: {u['name']} ({u['userId']})")


def seed_family():
    """Create Family node and MEMBER_OF relationships."""
    print("\nCreating Family node and memberships...")
    family_ops = FamilyOperations()

    family_ops.create_family(
        familyId=FAMILY_ID,
        name="Khan Family",
        createdBy=FATHER_ID,
    )
    print(f"  Created family: Khan Family ({FAMILY_ID})")

    members = [
        (GRANDFATHER_ID, "elder", "Robert Khan", "robert.khan@example.com"),
        (GRANDMOTHER_ID, "elder", "Margaret Khan", "margaret.khan@example.com"),
        (FATHER_ID, "admin", "Ahmed Khan", "ahmed.khan@example.com"),
        (MOTHER_ID, "member", "Sarah Khan", "sarah.khan@example.com"),
        (SON_ID, "member", "Ali Khan", "ali.khan@example.com"),
        (DAUGHTER_ID, "member", "Fatima Khan", "fatima.khan@example.com"),
    ]

    for user_id, role, name, email in members:
        family_ops.add_user_to_family(
            userId=user_id, familyId=FAMILY_ID, role=role, name=name, email=email
        )
        print(f"  Added {name} as {role}")


def seed_family_relationships():
    """Create PARENT_OF relationships for the family tree."""
    print("\nCreating family tree relationships (PARENT_OF)...")
    family_ops = FamilyOperations()

    relationships = [
        # Grandparents -> Father
        (GRANDFATHER_ID, "PARENT_OF", FATHER_ID),
        (GRANDMOTHER_ID, "PARENT_OF", FATHER_ID),
        # Parents -> Children
        (FATHER_ID, "PARENT_OF", SON_ID),
        (FATHER_ID, "PARENT_OF", DAUGHTER_ID),
        (MOTHER_ID, "PARENT_OF", SON_ID),
        (MOTHER_ID, "PARENT_OF", DAUGHTER_ID),
        # Spouses
        (GRANDFATHER_ID, "SPOUSE_OF", GRANDMOTHER_ID),
        (FATHER_ID, "SPOUSE_OF", MOTHER_ID),
        # Siblings
        (SON_ID, "SIBLING_OF", DAUGHTER_ID),
    ]

    for user1, rel_type, user2 in relationships:
        family_ops.create_family_relationship(user1, rel_type, user2)
        print(f"  {user1} -[{rel_type}]-> {user2}")


def seed_conditions():
    """Create Condition nodes."""
    print("\nCreating Condition nodes...")
    ops = GraphOperations()

    conditions = [
        {
            "conditionId": COND_DIABETES,
            "name": "Type 2 Diabetes",
            "category": "chronic",
            "icdCode": "E11",
            "description": "A chronic condition that affects the way the body processes blood sugar.",
        },
        {
            "conditionId": COND_HYPERTENSION,
            "name": "Hypertension",
            "category": "chronic",
            "icdCode": "I10",
            "description": "Persistently elevated blood pressure in the arteries.",
        },
        {
            "conditionId": COND_ASTHMA,
            "name": "Asthma",
            "category": "chronic",
            "icdCode": "J45",
            "description": "A condition in which airways narrow and swell, producing extra mucus.",
        },
        {
            "conditionId": COND_ARTHRITIS,
            "name": "Rheumatoid Arthritis",
            "category": "chronic",
            "icdCode": "M06",
            "description": "An autoimmune disorder that primarily affects joints.",
        },
        {
            "conditionId": COND_HIGH_CHOLESTEROL,
            "name": "High Cholesterol",
            "category": "chronic",
            "icdCode": "E78",
            "description": "Elevated levels of cholesterol in the blood.",
        },
        {
            "conditionId": COND_MIGRAINE,
            "name": "Migraine",
            "category": "hereditary",
            "icdCode": "G43",
            "description": "A headache disorder characterized by recurrent attacks.",
        },
        {
            "conditionId": COND_HEART_DISEASE,
            "name": "Coronary Heart Disease",
            "category": "genetic",
            "icdCode": "I25",
            "description": "A disease caused by plaque buildup in coronary arteries.",
        },
    ]

    for c in conditions:
        ops.create_node("Condition", c)
        print(f"  Created: {c['name']} ({c['icdCode']})")


def seed_medications():
    """Create Medication nodes."""
    print("\nCreating Medication nodes...")
    ops = GraphOperations()

    medications = [
        {
            "medicationId": MED_METFORMIN,
            "name": "Metformin",
            "genericName": "Metformin Hydrochloride",
            "category": "antidiabetic",
            "description": "First-line medication for type 2 diabetes.",
        },
        {
            "medicationId": MED_LISINOPRIL,
            "name": "Lisinopril",
            "genericName": "Lisinopril",
            "category": "antihypertensive",
            "description": "ACE inhibitor used to treat high blood pressure.",
        },
        {
            "medicationId": MED_ALBUTEROL,
            "name": "Albuterol",
            "genericName": "Salbutamol",
            "category": "bronchodilator",
            "description": "Quick-relief inhaler for asthma symptoms.",
        },
        {
            "medicationId": MED_ATORVASTATIN,
            "name": "Atorvastatin",
            "genericName": "Atorvastatin Calcium",
            "category": "statin",
            "description": "Lowers cholesterol and reduces risk of heart disease.",
        },
        {
            "medicationId": MED_IBUPROFEN,
            "name": "Ibuprofen",
            "genericName": "Ibuprofen",
            "category": "nsaid",
            "description": "Nonsteroidal anti-inflammatory drug for pain and inflammation.",
        },
        {
            "medicationId": MED_ASPIRIN,
            "name": "Aspirin",
            "genericName": "Acetylsalicylic Acid",
            "category": "antiplatelet",
            "description": "Used for blood thinning and heart disease prevention.",
        },
    ]

    for m in medications:
        ops.create_node("Medication", m)
        print(f"  Created: {m['name']}")


def seed_has_condition_relationships():
    """Create HAS_CONDITION relationships between users and conditions."""
    print("\nCreating HAS_CONDITION relationships...")
    ops = GraphOperations()

    relationships = [
        # Grandfather: diabetes, hypertension, heart disease
        (GRANDFATHER_ID, COND_DIABETES, {"severity": "moderate", "status": "active", "diagnosedDate": "2005-06-10"}),
        (GRANDFATHER_ID, COND_HYPERTENSION, {"severity": "mild", "status": "active", "diagnosedDate": "2000-03-20"}),
        (GRANDFATHER_ID, COND_HEART_DISEASE, {"severity": "moderate", "status": "active", "diagnosedDate": "2015-11-05"}),
        # Grandmother: arthritis, high cholesterol, migraine
        (GRANDMOTHER_ID, COND_ARTHRITIS, {"severity": "moderate", "status": "active", "diagnosedDate": "2010-08-14"}),
        (GRANDMOTHER_ID, COND_HIGH_CHOLESTEROL, {"severity": "mild", "status": "active", "diagnosedDate": "2008-02-28"}),
        (GRANDMOTHER_ID, COND_MIGRAINE, {"severity": "mild", "status": "managed", "diagnosedDate": "1980-05-01"}),
        # Father: hypertension, high cholesterol (inherited risks)
        (FATHER_ID, COND_HYPERTENSION, {"severity": "mild", "status": "active", "diagnosedDate": "2020-01-15"}),
        (FATHER_ID, COND_HIGH_CHOLESTEROL, {"severity": "mild", "status": "active", "diagnosedDate": "2021-06-22"}),
        # Mother: asthma, migraine
        (MOTHER_ID, COND_ASTHMA, {"severity": "mild", "status": "active", "diagnosedDate": "1995-09-10"}),
        (MOTHER_ID, COND_MIGRAINE, {"severity": "moderate", "status": "active", "diagnosedDate": "2010-03-08"}),
        # Son: asthma (inherited from mother)
        (SON_ID, COND_ASTHMA, {"severity": "mild", "status": "active", "diagnosedDate": "2012-04-20"}),
    ]

    for user_id, cond_id, props in relationships:
        query = """
        MATCH (u:User {userId: $userId}), (c:Condition {conditionId: $condId})
        CREATE (u)-[r:HAS_CONDITION]->(c)
        SET r.severity = $severity, r.status = $status, r.diagnosedDate = $diagnosedDate
        RETURN r
        """
        params = {"userId": user_id, "condId": cond_id, **props}
        ops.execute_query(query, params)
        print(f"  {user_id} -[HAS_CONDITION]-> {cond_id} (severity={props['severity']})")


def seed_takes_medication_relationships():
    """Create TAKES relationships between users and medications."""
    print("\nCreating TAKES (medication) relationships...")
    ops = GraphOperations()

    relationships = [
        # Grandfather
        (GRANDFATHER_ID, MED_METFORMIN, {"dosage": "500mg", "frequency": "twice daily", "status": "active", "startDate": "2005-07-01"}),
        (GRANDFATHER_ID, MED_LISINOPRIL, {"dosage": "10mg", "frequency": "once daily", "status": "active", "startDate": "2000-04-15"}),
        (GRANDFATHER_ID, MED_ASPIRIN, {"dosage": "81mg", "frequency": "once daily", "status": "active", "startDate": "2015-12-01"}),
        # Grandmother
        (GRANDMOTHER_ID, MED_IBUPROFEN, {"dosage": "400mg", "frequency": "as needed", "status": "active", "startDate": "2010-09-01"}),
        (GRANDMOTHER_ID, MED_ATORVASTATIN, {"dosage": "20mg", "frequency": "once daily", "status": "active", "startDate": "2008-03-15"}),
        # Father
        (FATHER_ID, MED_LISINOPRIL, {"dosage": "5mg", "frequency": "once daily", "status": "active", "startDate": "2020-02-01"}),
        (FATHER_ID, MED_ATORVASTATIN, {"dosage": "10mg", "frequency": "once daily", "status": "active", "startDate": "2021-07-10"}),
        # Mother
        (MOTHER_ID, MED_ALBUTEROL, {"dosage": "90mcg", "frequency": "as needed", "status": "active", "startDate": "1995-10-01"}),
        # Son
        (SON_ID, MED_ALBUTEROL, {"dosage": "90mcg", "frequency": "as needed", "status": "active", "startDate": "2012-05-01"}),
    ]

    for user_id, med_id, props in relationships:
        query = """
        MATCH (u:User {userId: $userId}), (m:Medication {medicationId: $medId})
        CREATE (u)-[r:TAKES]->(m)
        SET r.dosage = $dosage, r.frequency = $frequency, r.status = $status, r.startDate = $startDate
        RETURN r
        """
        params = {"userId": user_id, "medId": med_id, **props}
        ops.execute_query(query, params)
        print(f"  {user_id} -[TAKES {props['dosage']}]-> {med_id}")


def seed_health_events_postgres():
    """Seed health events into PostgreSQL for the timeline."""
    print("\nCreating health events in PostgreSQL...")

    from shared.database.postgres.postgres_client import PostgresClient
    from shared.database.postgres.models import HealthEvent

    now = datetime.now(timezone.utc)

    events = [
        # Grandfather events
        HealthEvent(
            event_id=str(uuid.uuid4()),
            user_id=GRANDFATHER_ID,
            event_type="visit",
            title="Annual Cardiology Checkup",
            description="Routine cardiac evaluation. ECG normal. Blood pressure slightly elevated at 145/90.",
            event_date=now - timedelta(days=30),
            provider_name="Dr. James Wilson",
            location="City Heart Center",
            severity="normal",
        ),
        HealthEvent(
            event_id=str(uuid.uuid4()),
            user_id=GRANDFATHER_ID,
            event_type="lab_result",
            title="HbA1c Test",
            description="HbA1c level at 7.2%. Slightly above target range of 7.0%.",
            event_date=now - timedelta(days=25),
            provider_name="LabCorp",
            location="Downtown Lab",
            event_data={"hba1c": 7.2, "target": 7.0, "unit": "%"},
            severity="warning",
        ),
        HealthEvent(
            event_id=str(uuid.uuid4()),
            user_id=GRANDFATHER_ID,
            event_type="medication_change",
            title="Metformin Dosage Adjusted",
            description="Increased Metformin from 500mg to 750mg twice daily due to elevated HbA1c.",
            event_date=now - timedelta(days=20),
            provider_name="Dr. James Wilson",
            severity="normal",
        ),
        # Grandmother events
        HealthEvent(
            event_id=str(uuid.uuid4()),
            user_id=GRANDMOTHER_ID,
            event_type="visit",
            title="Rheumatology Follow-up",
            description="Joint stiffness improved with current medication. Continue current regimen.",
            event_date=now - timedelta(days=45),
            provider_name="Dr. Lisa Chen",
            location="Arthritis Care Clinic",
            severity="normal",
        ),
        HealthEvent(
            event_id=str(uuid.uuid4()),
            user_id=GRANDMOTHER_ID,
            event_type="lab_result",
            title="Lipid Panel",
            description="Total cholesterol 215 mg/dL. LDL 130 mg/dL. HDL 55 mg/dL.",
            event_date=now - timedelta(days=40),
            provider_name="LabCorp",
            event_data={"total_cholesterol": 215, "ldl": 130, "hdl": 55, "triglycerides": 150},
            severity="warning",
        ),
        # Father events
        HealthEvent(
            event_id=str(uuid.uuid4()),
            user_id=FATHER_ID,
            event_type="visit",
            title="Annual Physical Exam",
            description="Overall health good. Blood pressure 138/88 - borderline high. Weight stable.",
            event_date=now - timedelta(days=15),
            provider_name="Dr. Michael Brown",
            location="Family Medical Center",
            severity="normal",
        ),
        HealthEvent(
            event_id=str(uuid.uuid4()),
            user_id=FATHER_ID,
            event_type="vital_reading",
            title="Blood Pressure Check",
            description="Home BP reading: 135/85 mmHg. Slightly elevated.",
            event_date=now - timedelta(days=5),
            event_data={"systolic": 135, "diastolic": 85, "pulse": 72},
            severity="warning",
        ),
        HealthEvent(
            event_id=str(uuid.uuid4()),
            user_id=FATHER_ID,
            event_type="lab_result",
            title="Lipid Panel Results",
            description="LDL cholesterol at 145 mg/dL. Above recommended <130 mg/dL.",
            event_date=now - timedelta(days=10),
            provider_name="Quest Diagnostics",
            event_data={"total_cholesterol": 230, "ldl": 145, "hdl": 50, "triglycerides": 175},
            severity="warning",
        ),
        # Mother events
        HealthEvent(
            event_id=str(uuid.uuid4()),
            user_id=MOTHER_ID,
            event_type="visit",
            title="Pulmonology Checkup",
            description="Asthma well-controlled. Peak flow at 85% of personal best.",
            event_date=now - timedelta(days=60),
            provider_name="Dr. Rachel Green",
            location="Respiratory Health Center",
            severity="normal",
        ),
        HealthEvent(
            event_id=str(uuid.uuid4()),
            user_id=MOTHER_ID,
            event_type="vital_reading",
            title="Peak Flow Reading",
            description="Morning peak flow: 380 L/min. Within normal range.",
            event_date=now - timedelta(days=3),
            event_data={"peak_flow": 380, "personal_best": 450, "percentage": 84, "unit": "L/min"},
            severity="normal",
        ),
        # Son events
        HealthEvent(
            event_id=str(uuid.uuid4()),
            user_id=SON_ID,
            event_type="visit",
            title="Pediatric Asthma Review",
            description="Asthma mild and intermittent. No nighttime symptoms. Continue rescue inhaler as needed.",
            event_date=now - timedelta(days=90),
            provider_name="Dr. Emily Park",
            location="Children's Health Clinic",
            severity="normal",
        ),
        HealthEvent(
            event_id=str(uuid.uuid4()),
            user_id=SON_ID,
            event_type="vaccination",
            title="Flu Vaccine 2025-2026",
            description="Seasonal influenza vaccine administered. No adverse reactions.",
            event_date=now - timedelta(days=120),
            provider_name="Dr. Emily Park",
            location="Children's Health Clinic",
            severity="normal",
        ),
        # Daughter events
        HealthEvent(
            event_id=str(uuid.uuid4()),
            user_id=DAUGHTER_ID,
            event_type="visit",
            title="Annual Wellness Visit",
            description="Healthy. Growth on track. No concerns.",
            event_date=now - timedelta(days=75),
            provider_name="Dr. Emily Park",
            location="Children's Health Clinic",
            severity="normal",
        ),
        HealthEvent(
            event_id=str(uuid.uuid4()),
            user_id=DAUGHTER_ID,
            event_type="vaccination",
            title="HPV Vaccine - Dose 1",
            description="First dose of HPV vaccine administered. Next dose in 6 months.",
            event_date=now - timedelta(days=70),
            provider_name="Dr. Emily Park",
            location="Children's Health Clinic",
            severity="normal",
        ),
    ]

    try:
        with PostgresClient() as db:
            session = db.get_session()
            for event in events:
                session.add(event)
            session.commit()
            print(f"  Created {len(events)} health events in PostgreSQL.")
    except Exception as e:
        print(f"  Error seeding PostgreSQL: {e}")
        print("  (This is OK if users don't exist in PG yet - events reference Neo4j user IDs)")


def seed_postgres_users():
    """Create matching user records in PostgreSQL so FK constraints pass for health_events."""
    print("\nCreating matching users in PostgreSQL...")

    from shared.database.postgres.postgres_client import PostgresClient
    from shared.database.postgres.models import User

    users = [
        User(user_id=GRANDFATHER_ID, email="robert.khan@example.com", username="robert.khan", password_hash="seeded", first_name="Robert", last_name="Khan", gender="M", date_of_birth="1945-03-15"),
        User(user_id=GRANDMOTHER_ID, email="margaret.khan@example.com", username="margaret.khan", password_hash="seeded", first_name="Margaret", last_name="Khan", gender="F", date_of_birth="1948-07-22"),
        User(user_id=FATHER_ID, email="ahmed.khan@example.com", username="ahmed.khan", password_hash="seeded", first_name="Ahmed", last_name="Khan", gender="M", date_of_birth="1975-11-08"),
        User(user_id=MOTHER_ID, email="sarah.khan@example.com", username="sarah.khan", password_hash="seeded", first_name="Sarah", last_name="Khan", gender="F", date_of_birth="1978-04-12"),
        User(user_id=SON_ID, email="ali.khan@example.com", username="ali.khan", password_hash="seeded", first_name="Ali", last_name="Khan", gender="M", date_of_birth="2005-09-20"),
        User(user_id=DAUGHTER_ID, email="fatima.khan@example.com", username="fatima.khan", password_hash="seeded", first_name="Fatima", last_name="Khan", gender="F", date_of_birth="2008-01-15"),
    ]

    try:
        with PostgresClient() as db:
            session = db.get_session()
            for user in users:
                session.merge(user)  # merge = insert or update
            session.commit()
            print(f"  Created/updated {len(users)} users in PostgreSQL.")
    except Exception as e:
        print(f"  Error seeding PG users: {e}")


def print_summary():
    """Print summary of seeded data."""
    print("\n" + "=" * 60)
    print("SEED DATA SUMMARY")
    print("=" * 60)
    print(f"""
Family: Khan Family ({FAMILY_ID})

Members (3 generations):
  Grandparents:
    - Robert Khan (grandfather)  — Diabetes, Hypertension, Heart Disease
    - Margaret Khan (grandmother) — Arthritis, High Cholesterol, Migraine

  Parents:
    - Ahmed Khan (father)  — Hypertension, High Cholesterol
    - Sarah Khan (mother)  — Asthma, Migraine

  Children:
    - Ali Khan (son)       — Asthma
    - Fatima Khan (daughter) — Healthy

Relationships:
  Robert & Margaret -> Ahmed (PARENT_OF)
  Ahmed & Sarah -> Ali, Fatima (PARENT_OF)
  Robert <-> Margaret (SPOUSE_OF)
  Ahmed <-> Sarah (SPOUSE_OF)
  Ali <-> Fatima (SIBLING_OF)

Conditions: 7 (Diabetes, Hypertension, Asthma, Arthritis, High Cholesterol, Migraine, Heart Disease)
Medications: 6 (Metformin, Lisinopril, Albuterol, Atorvastatin, Ibuprofen, Aspirin)
Health Events: 14 (visits, lab results, vitals, vaccinations, medication changes)

Dashboard Endpoints to Test:
  GET /api/v1/dashboard/family/{FAMILY_ID}
  GET /api/v1/dashboard/family/{FAMILY_ID}/conditions
  GET /api/v1/dashboard/member/{FATHER_ID}
  GET /api/v1/dashboard/timeline/{GRANDFATHER_ID}
  GET /api/v1/dashboard/risk/{SON_ID}
  GET /api/v1/dashboard/risk/{FATHER_ID}
""")


def main():
    print("=" * 60)
    print("SEEDING FAMILY HEALTH DATA")
    print("=" * 60)

    clear_existing_data()
    seed_users()
    seed_family()
    seed_family_relationships()
    seed_conditions()
    seed_medications()
    seed_has_condition_relationships()
    seed_takes_medication_relationships()
    seed_postgres_users()
    seed_health_events_postgres()
    print_summary()

    print("Seed complete!")


if __name__ == "__main__":
    main()
