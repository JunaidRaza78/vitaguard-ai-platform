"""
Quick test script to check Neo4j health records implementation.
"""
import sys
import uuid
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.shared.database.neo4j import Neo4jClient


def quick_test():
    """Quick test of health record operations."""
    client = Neo4jClient()
    
    print("=" * 60)
    print("Quick Health Records Test")
    print("=" * 60)
    
    # Test connection
    if not client.health_check():
        print("❌ Neo4j connection failed!")
        return False
    
    print("✅ Connection successful!\n")
    
    # Create a test user
    userId = str(uuid.uuid4())
    print(f"Creating test user: {userId}")
    user = client.create_user(
        userId=userId,
        email=f"test_{uuid.uuid4().hex[:8]}@example.com",
        name="Test User",
        dateOfBirth="1990-01-01",
        gender="M"
    )
    print(f"✅ User created: {user['name']}\n")
    
    # Test HealthRecord
    print("Testing HealthRecord...")
    recordId = str(uuid.uuid4())
    hr = client.create_health_record(
        recordId=recordId,
        type="consultation",
        date="2024-01-15",
        title="Test Consultation"
    )
    client.add_health_record_to_user(userId, recordId)
    print(f"✅ HealthRecord created: {hr['title']}")
    
    # Test LabReport
    print("Testing LabReport...")
    reportId = str(uuid.uuid4())
    lr = client.create_lab_report(
        reportId=reportId,
        testName="Blood Test",
        date="2024-01-20"
    )
    client.add_lab_report_to_user(userId, reportId)
    print(f"✅ LabReport created: {lr['testName']}")
    
    # Test Prescription
    print("Testing Prescription...")
    prescId = str(uuid.uuid4())
    presc = client.create_prescription(
        prescriptionId=prescId,
        date="2024-01-22",
        doctorName="Dr. Test"
    )
    client.add_prescription_to_user(userId, prescId)
    print(f"✅ Prescription created: {presc.get('doctorName', 'N/A')}")
    
    # Test Vaccination
    print("Testing Vaccination...")
    vaccId = str(uuid.uuid4())
    vacc = client.create_vaccination(
        vaccinationId=vaccId,
        vaccineName="Test Vaccine",
        type="Test Type",
        doseNumber=1
    )
    client.add_vaccination_to_user(userId, vaccId)
    print(f"✅ Vaccination created: {vacc['vaccineName']}")
    
    # Get all records
    print("\n" + "-" * 60)
    print("Retrieving records...")
    all_records = client.get_user_health_records(userId)
    print(f"✅ Total Health Records: {len(all_records)}")
    
    lab_reports = client.get_user_lab_reports(userId)
    print(f"✅ Lab Reports: {len(lab_reports)}")
    
    prescriptions = client.get_user_prescriptions(userId)
    print(f"✅ Prescriptions: {len(prescriptions)}")
    
    vaccinations = client.get_user_vaccinations(userId)
    print(f"✅ Vaccinations: {len(vaccinations)}")
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    try:
        quick_test()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

