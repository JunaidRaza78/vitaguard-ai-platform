"""
Seed Data Script — Direct Database Insertion
Populates dummy data for testing all features by writing directly to
PostgreSQL (notifications) and Neo4j (vitals, medications, lab results).

Usage:
    1. Make sure PostgreSQL and Neo4j are running (docker compose up)
    2. Run:  cd Backend && python3 ../seed_data.py

Uses: test@example.com / Test1234!
"""

import sys
import os
import uuid
import random
from datetime import datetime, timedelta, timezone

# Add Backend to path so we can import project modules
BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Backend")
sys.path.insert(0, BACKEND_DIR)

# Colors for terminal output
G = "\033[92m"  # green
Y = "\033[93m"  # yellow
R = "\033[91m"  # red
B = "\033[94m"  # blue
C = "\033[96m"  # cyan
N = "\033[0m"   # reset

EMAIL = "test@example.com"
PASSWORD = "Test1234!"


def log(msg, color=G):
    print(f"{color}{'─'*55}{N}")
    print(f"{color}  {msg}{N}")


def ok(msg):
    print(f"  {G}✅ {msg}{N}")


def warn(msg):
    print(f"  {Y}⚠️  {msg}{N}")


def fail(msg):
    print(f"  {R}❌ {msg}{N}")


# ──────────────────────────────────────────────────
# Step 1: Ensure user exists in PostgreSQL
# ──────────────────────────────────────────────────

def ensure_user():
    """Make sure the test user exists and return user_id."""
    log("Checking/Creating Test User in PostgreSQL...", B)

    from shared.database.postgres.postgres_client import PostgresClient

    db = PostgresClient()
    with db:
        user = db.get_user_by_email(EMAIL)
        if user:
            user_id = str(user.user_id)
            ok(f"User exists: {EMAIL} (ID: {user_id})")
            return user_id
        else:
            # Hash the password
            from app.services.auth_service import AuthService
            auth = AuthService()
            password_hash = auth.hash_password(PASSWORD)

            new_user = db.create_user(
                email=EMAIL,
                password_hash=password_hash,
                username="test_user",
                first_name="Test",
                last_name="User",
                date_of_birth="1981-05-15",
                gender="male",
            )
            db.commit()
            user_id = str(new_user.user_id)
            ok(f"Created user: {EMAIL} (ID: {user_id})")
            return user_id


def check_existing_data(user_id):
    """Check what data already exists to avoid duplicates."""
    existing = {"vitals": 0, "notifications": 0}
    try:
        from shared.database.postgres.postgres_client import PostgresClient
        from shared.database.postgres.models import Notification
        db = PostgresClient()
        with db:
            session = db.get_session()
            existing["notifications"] = session.query(Notification).filter_by(user_id=user_id).count()
    except Exception:
        pass
    try:
        from shared.database.neo4j.neo4j_client import Neo4jClient
        from shared.database.neo4j.operations.vitals_ops import VitalsOperations
        client = Neo4jClient()
        vitals_ops = VitalsOperations(client)
        results = vitals_ops.get_user_vitals(user_id, limit=1)
        existing["vitals"] = len(results) if results else 0
    except Exception:
        pass
    return existing


# ──────────────────────────────────────────────────
# Step 2: Seed Vitals into Neo4j
# ──────────────────────────────────────────────────

def seed_vitals(user_id):
    """Seed 30 days of realistic vitals into Neo4j."""
    log("Seeding Vitals into Neo4j (30 days)...", B)

    try:
        from shared.database.neo4j.neo4j_client import Neo4jClient
        from shared.database.neo4j.operations.vitals_ops import VitalsOperations

        client = Neo4jClient()
        vitals_ops = VitalsOperations(client)
    except Exception as e:
        fail(f"Cannot connect to Neo4j: {e}")
        warn("Make sure Neo4j is running (docker compose up)")
        return

    today = datetime.now()
    vital_configs = [
        # (type, unit, low, high)
        ("blood_pressure_systolic", "mmHg", 115, 135),
        ("blood_pressure_diastolic", "mmHg", 70, 85),
        ("heart_rate", "bpm", 65, 85),
        ("temperature", "°F", 97.5, 99.0),
        ("oxygen_saturation", "%", 95, 99),
        ("weight", "lbs", 165, 175),
        ("glucose", "mg/dL", 85, 120),
        ("respiratory_rate", "breaths/min", 14, 20),
    ]

    count = 0
    for day_offset in range(30, 0, -3):  # Every 3 days
        date = (today - timedelta(days=day_offset)).strftime("%Y-%m-%d")
        time_str = f"{random.randint(7,10):02d}:{random.randint(0,59):02d}"
        for vtype, unit, low, high in vital_configs:
            value = round(random.uniform(low, high), 1)
            try:
                vitals_ops.create_vital_sign(
                    user_id=user_id,
                    vital_type=vtype,
                    value=value,
                    unit=unit,
                    date=date,
                    time=time_str,
                    notes="Routine morning check" if day_offset % 6 == 0 else None,
                )
                count += 1
            except Exception as e:
                warn(f"Vital {vtype} on {date}: {e}")

    # Anomalous readings
    print(f"  {Y}  Adding anomalous readings...{N}")
    anomalies = [
        ("blood_pressure_systolic", "mmHg", 158, "High BP after stressful meeting"),
        ("heart_rate", "bpm", 112, "Elevated after heavy exercise"),
        ("glucose", "mg/dL", 185, "Post-meal spike"),
        ("temperature", "°F", 100.8, "Feeling under the weather"),
        ("oxygen_saturation", "%", 93, "Slight dip during cold symptoms"),
    ]
    for vtype, unit, value, note in anomalies:
        try:
            vitals_ops.create_vital_sign(
                user_id=user_id, vital_type=vtype, value=value,
                unit=unit, date=today.strftime("%Y-%m-%d"),
                time="14:30", notes=note,
            )
            count += 1
        except Exception as e:
            warn(f"Anomaly {vtype}: {e}")

    ok(f"Seeded {count} vital sign records")


# ──────────────────────────────────────────────────
# Step 3: Seed Medications into Neo4j
# ──────────────────────────────────────────────────

def seed_medications(user_id):
    """Seed medications with TAKES relationships into Neo4j."""
    log("Seeding Medications into Neo4j...", B)

    try:
        from shared.database.neo4j.neo4j_client import Neo4jClient
        from shared.database.neo4j.operations.medication_ops import MedicationOperations

        client = Neo4jClient()
        med_ops = MedicationOperations(client)
    except Exception as e:
        fail(f"Cannot connect to Neo4j: {e}")
        return

    medications = [
        ("Metformin 500mg", "Metformin", "Biguanide", "500mg", "Twice daily", ["08:00", "20:00"], 90),
        ("Lisinopril 10mg", "Lisinopril", "ACE Inhibitor", "10mg", "Once daily", ["09:00"], 60),
        ("Vitamin D3 2000 IU", "Cholecalciferol", "Vitamin", "2000 IU", "Once daily", ["08:00"], 180),
        ("Atorvastatin 20mg", "Atorvastatin", "Statin", "20mg", "Once daily (bedtime)", ["21:00"], 45),
        ("Omeprazole 20mg", "Omeprazole", "Proton Pump Inhibitor", "20mg", "Once daily (before breakfast)", ["07:30"], 30),
    ]

    count = 0
    for name, generic, med_class, dosage, freq, reminder_times, days_ago in medications:
        try:
            # Create medication node
            med = med_ops.create_medication(
                name=name,
                generic_name=generic,
                medication_class=med_class,
            )
            if med:
                med_id = med.get("medication_id", str(uuid.uuid4()))
                # Create TAKES relationship
                start_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
                med_ops.add_user_medication(
                    user_id=user_id,
                    medication_id=med_id,
                    start_date=start_date,
                    dosage=dosage,
                    frequency=freq,
                    status="active",
                    reminder_times=reminder_times,
                )
                ok(f"{name} (since {start_date})")
                count += 1
        except Exception as e:
            warn(f"{name}: {e}")

    ok(f"Seeded {count} medications")


# ──────────────────────────────────────────────────
# Step 4: Seed Lab Results into Neo4j
# ──────────────────────────────────────────────────

def seed_lab_results(user_id):
    """Seed lab results into Neo4j."""
    log("Seeding Lab Results into Neo4j...", B)

    try:
        from shared.database.neo4j.neo4j_client import Neo4jClient
        from shared.database.neo4j.operations.vitals_ops import VitalsOperations

        client = Neo4jClient()
        vitals_ops = VitalsOperations(client)
    except Exception as e:
        fail(f"Cannot connect to Neo4j: {e}")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    labs = [
        # (test_name, date, value, unit, ref_range, status)
        ("Glucose, Fasting", today, "132", "mg/dL", "70-100", "high"),
        ("Hemoglobin A1c", today, "6.8", "%", "<5.7", "high"),
        ("Total Cholesterol", today, "215", "mg/dL", "<200", "high"),
        ("HDL Cholesterol", today, "48", "mg/dL", ">40", "normal"),
        ("LDL Cholesterol", today, "142", "mg/dL", "<100", "high"),
        ("Triglycerides", today, "165", "mg/dL", "<150", "high"),
        ("TSH", today, "5.8", "mIU/L", "0.4-4.0", "high"),
        ("Hemoglobin", today, "13.5", "g/dL", "13.5-17.5", "normal"),
        ("WBC", today, "7.2", "K/uL", "4.5-11.0", "normal"),
        ("RBC", today, "4.8", "M/uL", "4.5-5.5", "normal"),
        ("Platelets", today, "245", "K/uL", "150-400", "normal"),
        ("Creatinine", today, "1.1", "mg/dL", "0.7-1.3", "normal"),
        ("BUN", today, "18", "mg/dL", "7-20", "normal"),
        ("ALT", today, "32", "U/L", "7-56", "normal"),
        ("AST", today, "28", "U/L", "10-40", "normal"),
        ("Vitamin D", today, "28", "ng/mL", "30-100", "low"),
        ("Iron", today, "85", "mcg/dL", "60-170", "normal"),
        ("Sodium", today, "140", "mEq/L", "136-145", "normal"),
        ("Potassium", today, "4.2", "mEq/L", "3.5-5.0", "normal"),
        ("Calcium", today, "9.5", "mg/dL", "8.5-10.5", "normal"),
        ("Hematocrit", today, "41", "%", "38.3-48.6", "normal"),
        # Older results for trend comparison
        ("Glucose, Fasting", week_ago, "128", "mg/dL", "70-100", "high"),
        ("Hemoglobin A1c", week_ago, "6.2", "%", "<5.7", "high"),
        ("Total Cholesterol", week_ago, "210", "mg/dL", "<200", "high"),
        ("TSH", week_ago, "4.2", "mIU/L", "0.4-4.0", "high"),
    ]

    report_id = str(uuid.uuid4())
    count = 0
    for test_name, date, value, unit, ref_range, status in labs:
        try:
            vitals_ops.create_lab_result(
                user_id=user_id,
                test_name=test_name,
                date=date,
                result_value=value,
                unit=unit,
                reference_range=ref_range,
                status=status,
                lab_report_id=report_id if date == today else None,
            )
            count += 1
        except Exception as e:
            warn(f"Lab {test_name}: {e}")

    ok(f"Seeded {count} lab results ({len([l for l in labs if l[5] != 'normal'])} abnormal)")


# ──────────────────────────────────────────────────
# Step 5: Seed Notifications into PostgreSQL
# ──────────────────────────────────────────────────

def seed_notifications(user_id):
    """Seed notifications directly in PostgreSQL."""
    log("Seeding Notifications into PostgreSQL...", B)

    from shared.database.postgres.postgres_client import PostgresClient
    from shared.database.postgres.models import Notification

    db = PostgresClient()
    now = datetime.now(timezone.utc)

    notifications = [
        ("medication_reminder", "Time for Metformin",
         "Take your Metformin 500mg morning dose. Take with food.", "medium"),
        ("health_alert", "Blood Pressure Elevated",
         "Your systolic BP reading of 158 mmHg is above normal (90-130). Consider resting and re-checking.", "high"),
        ("appointment_reminder", "Annual Physical - Dr. Smith",
         "Your annual physical is scheduled for next Monday at 10:00 AM. Remember to fast 12 hours before blood work.", "medium"),
        ("health_alert", "Lab Results Available",
         "Your recent bloodwork results are ready for review in the Lab Reports section.", "low"),
        ("system", "Welcome to Family Health Manager!",
         "Your account is set up. Start by recording your vitals and adding medications for personalized health insights.", "low"),
        ("vaccination_reminder", "Flu Vaccine - Annual Reminder",
         "It's flu season! Schedule your annual influenza vaccine. Last vaccination was over 12 months ago.", "medium"),
        ("proactive_alert", "Glucose Trending Upward",
         "Your fasting glucose has been trending upward (avg 115 to 128). Consider dietary adjustments.", "high"),
        ("medication_reminder", "Time for Atorvastatin",
         "Take your Atorvastatin 20mg bedtime dose.", "medium"),
        ("health_alert", "Vitamin D Level Low",
         "Your Vitamin D level is 28 ng/mL (below the normal range of 30-100). Consider supplementation.", "medium"),
    ]

    count = 0
    with db:
        session = db.get_session()
        for ntype, title, message, priority in notifications:
            try:
                notif = Notification(
                    notification_id=str(uuid.uuid4()),
                    user_id=user_id,
                    type=ntype,
                    title=title,
                    message=message,
                    status="pending",
                    priority=priority,
                    scheduled_at=now - timedelta(hours=random.randint(0, 48)),
                    created_at=now - timedelta(hours=random.randint(0, 72)),
                    notification_metadata={},
                    retry_count=0,
                )
                session.add(notif)
                count += 1
            except Exception as e:
                warn(f"Notification '{title}': {e}")
        session.commit()

    ok(f"Seeded {count} notifications")


# ──────────────────────────────────────────────────
# Step 6: Seed Health Events into PostgreSQL
# ──────────────────────────────────────────────────

def seed_health_events(user_id):
    """Seed health events (appointments, visits) into PostgreSQL."""
    log("Seeding Health Events into PostgreSQL...", B)

    from shared.database.postgres.postgres_client import PostgresClient
    from shared.database.postgres.models import HealthEvent

    db = PostgresClient()
    now = datetime.now(timezone.utc)

    events = [
        ("visit", "Annual Physical Exam", "Routine annual check-up with Dr. Smith. All vitals normal.",
         now - timedelta(days=90), "Dr. Smith", "City Medical Center", "normal"),
        ("lab_result", "Comprehensive Metabolic Panel", "Blood work for pre-diabetes monitoring.",
         now - timedelta(days=7), "Quest Diagnostics", "Quest Lab - Main St", "warning"),
        ("visit", "Cardiology Follow-up", "Follow-up for elevated BP. Lisinopril prescribed.",
         now - timedelta(days=60), "Dr. Johnson", "Heart Care Clinic", "warning"),
        ("vaccination", "COVID-19 Booster", "Received updated COVID-19 booster shot.",
         now - timedelta(days=120), "CVS Pharmacy", "CVS - Oak Ave", "normal"),
        ("medication_change", "Metformin Started", "Started Metformin 500mg twice daily for pre-diabetes management.",
         now - timedelta(days=90), "Dr. Smith", "City Medical Center", "critical"),
        ("visit", "Eye Exam", "Annual diabetic eye screening. No retinopathy detected.",
         now - timedelta(days=45), "Dr. Lee", "Vision Care Associates", "normal"),
    ]

    count = 0
    with db:
        session = db.get_session()
        for etype, title, desc, event_date, provider, location, severity in events:
            try:
                event = HealthEvent(
                    event_id=str(uuid.uuid4()),
                    user_id=user_id,
                    event_type=etype,
                    title=title,
                    description=desc,
                    event_date=event_date,
                    provider_name=provider,
                    location=location,
                    severity=severity,
                )
                session.add(event)
                count += 1
            except Exception as e:
                warn(f"Event '{title}': {e}")
        session.commit()

    ok(f"Seeded {count} health events")


# ──────────────────────────────────────────────────
# Step 7: Seed Family & Conditions into Neo4j
# ──────────────────────────────────────────────────

def seed_family(user_id):
    """Create family with members and health conditions in Neo4j."""
    log("Seeding Family & Conditions into Neo4j...", B)

    try:
        from shared.database.neo4j.neo4j_client import Neo4jClient
        from shared.database.neo4j.operations.family_ops import FamilyOperations
        from shared.database.neo4j.operations.condition_ops import ConditionOperations

        client = Neo4jClient()
        family_ops = FamilyOperations()   # Inherits from BaseNeo4jClient, no args
        condition_ops = ConditionOperations(client)  # Takes a client instance
    except Exception as e:
        fail(f"Cannot connect to Neo4j: {e}")
        return

    # Create family
    family_id = str(uuid.uuid4())
    try:
        family_ops.create_family(
            familyId=family_id,
            name="User Family",
            createdBy=user_id,
        )
        family_ops.add_user_to_family(
            userId=user_id,
            familyId=family_id,
            role="admin",
            name="Test User",
            email=EMAIL,
        )
        ok(f"Created family (ID: {family_id[:8]}...)")
    except Exception as e:
        warn(f"Family creation: {e}")

    # Add family members
    members = [
        ("father_" + uuid.uuid4().hex[:8], "Father", "Robert User", "parent",
         ["Heart Disease", "Type 2 Diabetes", "Hypertension"]),
        ("mother_" + uuid.uuid4().hex[:8], "Mother", "Mary User", "parent",
         ["Breast Cancer", "Osteoporosis"]),
        ("sister_" + uuid.uuid4().hex[:8], "Sister", "Sarah User", "sibling",
         ["Asthma", "Depression"]),
        ("spouse_" + uuid.uuid4().hex[:8], "Spouse", "Jane User", "spouse",
         []),
        ("child_" + uuid.uuid4().hex[:8], "Child", "Alex User", "child",
         []),
    ]

    for member_id, role_name, name, relationship_type, conditions in members:
        try:
            family_ops.add_user_to_family(
                userId=member_id,
                familyId=family_id,
                role="member",
                name=name,
            )
            # Create relationship
            rel_type_map = {
                "parent": "PARENT_OF",
                "sibling": "SIBLING_OF",
                "spouse": "SPOUSE_OF",
                "child": "CHILD_OF",
            }
            neo4j_rel = rel_type_map.get(relationship_type, "RELATED_TO")
            if relationship_type == "parent":
                family_ops.create_family_relationship(member_id, neo4j_rel, user_id)
            elif relationship_type == "child":
                family_ops.create_family_relationship(user_id, "PARENT_OF", member_id)
            elif relationship_type == "spouse":
                family_ops.create_family_relationship(user_id, neo4j_rel, member_id)
            elif relationship_type == "sibling":
                family_ops.create_family_relationship(user_id, neo4j_rel, member_id)

            ok(f"{role_name}: {name} ({len(conditions)} conditions)")

            # Add conditions
            for cond_name in conditions:
                try:
                    condition_ops.create_condition(
                        name=cond_name,
                        icd_code="N/A",
                        category="hereditary",
                        severity="moderate",
                    )
                except Exception:
                    pass  # Condition may already exist

        except Exception as e:
            warn(f"Member {name}: {e}")

    # Add user's own conditions
    user_conditions = [
        ("Pre-Diabetes", "metabolic", "active", "moderate"),
        ("Hypertension (Mild)", "cardiovascular", "active", "moderate"),
        ("Vitamin D Deficiency", "nutritional", "active", "low"),
    ]
    for cond_name, category, cond_status, severity in user_conditions:
        try:
            condition_ops.create_condition(
                name=cond_name,
                icd_code="N/A",
                category=category,
                severity=severity,
            )
        except Exception:
            pass

    ok("Family hierarchy and conditions seeded")


# ──────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────

def main():
    print(f"\n{C}{'═'*55}{N}")
    print(f"{C}  🏥 Family Health Manager — Seed Data{N}")
    print(f"{C}  Direct database insertion (no server required){N}")
    print(f"{C}  User: {EMAIL} / {PASSWORD}{N}")
    print(f"{C}{'═'*55}{N}\n")

    try:
        user_id = ensure_user()
    except Exception as e:
        fail(f"Cannot connect to PostgreSQL: {e}")
        print(f"\n  {Y}Make sure PostgreSQL is running:{N}")
        print(f"  {Y}  docker compose up -d{N}")
        return
    print()

    # Check existing data to skip already-seeded sections
    existing = check_existing_data(user_id)
    if existing["vitals"] > 0:
        warn(f"Vitals already exist ({existing['vitals']} found). Skipping vitals, meds, labs.")
    else:
        seed_vitals(user_id)
        print()
        seed_medications(user_id)
        print()
        seed_lab_results(user_id)
        print()

    if existing["notifications"] > 0:
        warn(f"Notifications already exist ({existing['notifications']} found). Skipping.")
    else:
        seed_notifications(user_id)
        print()

    seed_health_events(user_id)
    print()
    seed_family(user_id)

    print(f"\n{G}{'═'*55}{N}")
    print(f"{G}  🎉 ALL SEED DATA INSERTED SUCCESSFULLY!{N}")
    print(f"{G}{'═'*55}{N}")
    print(f"\n  Next steps:")
    print(f"  1. Start backend:   cd Backend && uvicorn main:app --reload")
    print(f"  2. Start frontend:  cd Frontend && streamlit run app.py")
    print(f"  3. Login with:      {EMAIL} / {PASSWORD}")
    print(f"  4. Check pages:     Dashboard, Notifications, Lab Reports, Chat")
    print()


if __name__ == "__main__":
    main()
