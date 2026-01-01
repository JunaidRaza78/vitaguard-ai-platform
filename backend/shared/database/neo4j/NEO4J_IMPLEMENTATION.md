# Neo4j Complete Implementation Guide

## Overview

Complete Neo4j graph database implementation for the Family Health Manager system with comprehensive operations across all health domains.

## ✅ Implementation Status

### Completed Components

1. **Schema & Constraints** - `schema.cypher`
   - 60+ constraints (uniqueness)
   - 49+ indexes (performance)
   - Full-text search indexes
   - Composite indexes for complex queries

2. **User & Family Operations** - `operations/user_ops.py`, `operations/family_ops.py`
   - User CRUD operations
   - Family management
   - Relationship modeling (parent, child, guardian)
   - Family member queries

3. **Health Records** - `operations/health_record_ops.py`
   - HealthRecord nodes (lab_report, prescription, imaging, consultation, vaccination)
   - LabReport tracking
   - Prescription management
   - Vaccination records
   - Full-text search across records

4. **Medical Conditions** - `operations/condition_ops.py`
   - Condition CRUD with ICD-10 codes
   - User-Condition relationships (HAS_CONDITION)
   - Symptom tracking
   - Chronic condition queries
   - Genetic condition analysis
   - Family genetic risk patterns

5. **Medications** - `operations/medication_ops.py`
   - Medication CRUD (generic name, brand name, class)
   - User-Medication relationships (TAKES)
   - Drug interaction detection (INTERACTS_WITH)
   - Side effect tracking (CAUSES → Symptom)
   - Medication-Condition linkage (TREATS)
   - Active medication safety checks

6. **Healthcare Providers** - `operations/provider_ops.py`
   - Doctor management (specialty, license, experience)
   - Hospital management with geospatial location
   - Doctor-Hospital relationships (WORKS_AT)
   - User-Doctor relationships (TREATED_BY)
   - Doctor specialization (SPECIALIZES_IN)
   - **Geospatial queries**: Find nearby hospitals using Neo4j point.distance()
   - Search doctors by specialty

7. **Appointments** - `operations/appointment_ops.py`
   - Appointment CRUD (scheduled, completed, cancelled, rescheduled)
   - User-Appointment link (SCHEDULED)
   - Doctor-Appointment link (WITH_DOCTOR)
   - Hospital-Appointment link (AT_LOCATION)
   - Follow-up tracking (FOLLOWUP_TO)
   - Health record linkage (RESULTED_IN)
   - Reminder management
   - Upcoming appointments query
   - Doctor's appointment schedule

8. **Vitals & Growth** - `operations/vitals_ops.py`
   - VitalSign tracking (blood pressure, heart rate, temperature, weight)
   - GrowthRecord for pediatric tracking (height, weight, BMI, percentiles)
   - LabResult for individual test results
   - Temporal queries (vitals in date range)
   - Latest vitals retrieval
   - Abnormal vital detection
   - Growth trend analysis
   - Family growth comparison
   - Vital statistics (min, max, avg)

9. **AI Insights** - `operations/insights_ops.py`
   - HealthInsight nodes (trend, alert, recommendation, prediction)
   - Severity levels (info, low, medium, high, critical)
   - Confidence scoring
   - Actionable recommendations
   - Insight acknowledgment tracking
   - RiskFactor management (disease, lifestyle, genetic, environmental)
   - Risk scoring and levels
   - Mitigation strategies
   - Insight-Condition linkage (RELATED_TO)
   - Insight-Medication linkage (RELATED_TO)
   - Risk-Condition prediction (MAY_LEAD_TO)
   - Family risk analysis
   - Critical insights dashboard

10. **Unified Client** - `neo4j_client.py`
    - Single client with all operation classes
    - Multiple inheritance from all ops modules
    - Connection pooling
    - Query execution helpers
    - Health check functionality

11. **Comprehensive Test Suite** - `test_all_operations.py`
    - Tests all operations end-to-end
    - Creates sample data across all domains
    - Validates relationships
    - Tests advanced queries
    - Cross-domain relationship testing

## 📊 Complete Schema Overview

### Node Types (14 Total)

```cypher
// Core Entities
(:User)            - User profiles and demographics
(:Family)          - Family groups
(:Conversation)    - Chat conversations
(:ChatMessage)     - Individual chat messages

// Health Records
(:HealthRecord)    - General health records
(:LabReport)       - Laboratory test reports
(:Prescription)    - Medication prescriptions
(:Vaccination)     - Vaccination records

// Medical Knowledge
(:Condition)       - Medical conditions (ICD-10)
(:Symptom)         - Symptoms
(:Medication)      - Medications and drugs

// Healthcare Providers
(:Doctor)          - Healthcare providers
(:Hospital)        - Medical facilities

// Appointments & Vitals
(:Appointment)     - Scheduled appointments
(:VitalSign)       - Vital measurements
(:GrowthRecord)    - Pediatric growth tracking
(:LabResult)       - Individual lab test results

// AI Insights
(:HealthInsight)   - AI-generated insights
(:RiskFactor)      - Health risk factors
```

---

## 👤 User Schema

### User Node Properties
```cypher
(:User {
    userId: String (Unique ID),
    email: String (Unique Email),
    name: String,
    dateOfBirth: Date,
    gender: String (M/F/Other),
    phoneNumber: String,
    bloodGroup: String,
    height: Float (cm),
    weight: Float (kg),
    emergencyContact: String,
    emergencyPhone: String,
    profilePicture: String (URL),
    address: String,
    city: String,
    state: String,
    country: String,
    zipCode: String,
    createdAt: DateTime,
    updatedAt: DateTime,
    lastLogin: DateTime,
    isActive: Boolean
})
```

### User Relationships (Complete)
```cypher
// Family & Access Control
(User)-[:MEMBER_OF {role, joinedAt, addedBy}]->(Family)
(User)-[:GUARDIAN_OF {relationshipType, canViewData, canModifyData}]->(User)

// Health Data
(User)-[:HAS_RECORD]->(HealthRecord)
(User)-[:HAS_CONDITION {diagnosedDate, status, severity}]->(Condition)
(User)-[:TAKES {startDate, endDate, dosage, frequency, status}]->(Medication)
(User)-[:HAS_VITAL]->(VitalSign)
(User)-[:HAS_GROWTH_RECORD]->(GrowthRecord)
(User)-[:HAS_LAB_RESULT]->(LabResult)
(User)-[:RECEIVED {date, administeredBy, location}]->(Vaccination)

// Healthcare Providers
(User)-[:TREATED_BY {firstVisit, lastVisit, visitCount, primaryCare}]->(Doctor)
(User)-[:SCHEDULED]->(Appointment)

// AI Insights
(User)-[:HAS_INSIGHT {acknowledged, acknowledgedAt}]->(HealthInsight)
(User)-[:HAS_RISK_FACTOR]->(RiskFactor)

// Conversations
(User)-[:HAD_CONVERSATION]->(Conversation)
```

### User Query Examples
```cypher
// Get complete user profile with all connections
MATCH (u:User {userId: 'user-123'})-[r]->(connected)
RETURN u, type(r) AS relationship, connected
LIMIT 50;

// Get user's family members
MATCH (u:User {userId: 'user-123'})-[:MEMBER_OF]->(f:Family)<-[:MEMBER_OF]-(member:User)
RETURN member.name AS FamilyMember, member.email;

// Get user's guardians
MATCH (guardian:User)-[:GUARDIAN_OF]->(u:User {userId: 'child-123'})
RETURN guardian.name, guardian.email;

// Get user's complete health summary
MATCH (u:User {userId: 'user-123'})
OPTIONAL MATCH (u)-[:HAS_CONDITION]->(c:Condition)
OPTIONAL MATCH (u)-[:TAKES]->(m:Medication)
OPTIONAL MATCH (u)-[:HAS_VITAL]->(v:VitalSign)
RETURN
    u.name AS Name,
    collect(DISTINCT c.name) AS Conditions,
    collect(DISTINCT m.name) AS Medications,
    count(DISTINCT v) AS VitalReadings;
```

---

## 👨‍👩‍👧‍👦 Family Schema

### Family Node Properties
```cypher
(:Family {
    familyId: String (Unique ID),
    name: String,
    createdBy: String (User ID),
    createdAt: DateTime,
    description: String,
    isActive: Boolean
})
```

### Family Relationships
```cypher
// Family Members with Roles
(User)-[:MEMBER_OF {
    role: String,           // admin, parent, child, member
    joinedAt: DateTime,
    addedBy: String,        // User ID who added
    roleUpdatedAt: DateTime,
    roleUpdatedBy: String
}]->(Family)

// Guardian Relationships
(User)-[:GUARDIAN_OF {
    relationshipType: String,  // parent, legal_guardian, caretaker
    createdAt: DateTime,
    canViewData: Boolean,
    canModifyData: Boolean
}]->(User)
```

### Family Member Roles & Permissions

| Role | Add Members | Remove Members | View All Data | Modify All Data | Change Roles |
|------|-------------|----------------|---------------|-----------------|--------------|
| **admin** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **parent** | ✅ | ✅ | ✅ | ❌ | ❌ |
| **child** | ❌ | ❌ | ❌ (own only) | ❌ (own only) | ❌ |
| **member** | ❌ | ❌ | ❌ (own only) | ❌ (own only) | ❌ |
| **creator** | ✅ | ✅ | ✅ | ✅ | ✅ |

### Family Query Examples
```cypher
// Get all family members with roles
MATCH (f:Family {familyId: 'family-001'})<-[r:MEMBER_OF]-(u:User)
RETURN
    u.name AS Member,
    u.email AS Email,
    r.role AS Role,
    r.joinedAt AS JoinedDate,
    CASE
        WHEN f.createdBy = u.userId THEN 'Creator'
        ELSE 'Member'
    END AS Status
ORDER BY
    CASE r.role
        WHEN 'admin' THEN 1
        WHEN 'parent' THEN 2
        WHEN 'child' THEN 3
        ELSE 4
    END;

// Get family hierarchy with guardian relationships
MATCH (f:Family {familyId: 'family-001'})<-[:MEMBER_OF]-(u:User)
OPTIONAL MATCH (u)-[g:GUARDIAN_OF]->(ward:User)
RETURN
    u.name AS Member,
    collect(ward.name) AS Guardianship;

// Get family health overview
MATCH (f:Family {familyId: 'family-001'})<-[:MEMBER_OF]-(u:User)
OPTIONAL MATCH (u)-[:HAS_CONDITION]->(c:Condition)
RETURN
    f.name AS Family,
    count(DISTINCT u) AS TotalMembers,
    count(DISTINCT c) AS TotalConditions,
    collect(DISTINCT c.name) AS CommonConditions;

// Check who can add members to family
MATCH (f:Family {familyId: 'family-001'})
MATCH (u:User)-[r:MEMBER_OF]->(f)
RETURN
    u.name AS User,
    r.role AS Role,
    CASE
        WHEN f.createdBy = u.userId THEN 'YES - Creator'
        WHEN r.role IN ['admin', 'parent'] THEN 'YES - Has Permission'
        ELSE 'NO - Insufficient Permission'
    END AS CanAddMembers;
```

---

## 🔗 User-Family-Member Complete Schema

### Complete Graph Pattern
```cypher
// Full family health network pattern
MATCH (family:Family {familyId: 'family-001'})
MATCH (family)<-[member_rel:MEMBER_OF]-(user:User)
OPTIONAL MATCH (user)-[guardian_rel:GUARDIAN_OF]->(ward:User)
OPTIONAL MATCH (user)-[condition_rel:HAS_CONDITION]->(condition:Condition)
OPTIONAL MATCH (user)-[med_rel:TAKES]->(medication:Medication)
OPTIONAL MATCH (user)-[doctor_rel:TREATED_BY]->(doctor:Doctor)
OPTIONAL MATCH (user)-[appt_rel:SCHEDULED]->(appointment:Appointment)
OPTIONAL MATCH (user)-[vital_rel:HAS_VITAL]->(vital:VitalSign)
RETURN *;
```

### Complete Demo Data Creation
```cypher
// Create complete family health network
// 1. Create Family
CREATE (f:Family {
    familyId: 'family-001',
    name: 'Smith Family',
    createdBy: 'user-parent-001',
    createdAt: datetime()
});

// 2. Create Parent (Admin/Creator)
CREATE (parent:User {
    userId: 'user-parent-001',
    email: 'john.smith@email.com',
    name: 'John Smith',
    dateOfBirth: date('1980-05-15'),
    gender: 'M',
    phoneNumber: '+1234567890',
    bloodGroup: 'O+',
    createdAt: datetime()
});

// 3. Create Child
CREATE (child:User {
    userId: 'user-child-001',
    email: 'jane.smith@email.com',
    name: 'Jane Smith',
    dateOfBirth: date('2015-08-20'),
    gender: 'F',
    bloodGroup: 'O+',
    createdAt: datetime()
});

// 4. Create Spouse (Parent role)
CREATE (spouse:User {
    userId: 'user-spouse-001',
    email: 'mary.smith@email.com',
    name: 'Mary Smith',
    dateOfBirth: date('1982-03-10'),
    gender: 'F',
    phoneNumber: '+1234567891',
    bloodGroup: 'A+',
    createdAt: datetime()
});

// 5. Create Uncle (Member role)
CREATE (uncle:User {
    userId: 'user-uncle-001',
    email: 'bob.smith@email.com',
    name: 'Bob Smith',
    dateOfBirth: date('1975-11-05'),
    gender: 'M',
    bloodGroup: 'B+',
    createdAt: datetime()
});

// 6. Link all to Family with roles
MATCH (parent:User {userId: 'user-parent-001'})
MATCH (spouse:User {userId: 'user-spouse-001'})
MATCH (child:User {userId: 'user-child-001'})
MATCH (uncle:User {userId: 'user-uncle-001'})
MATCH (f:Family {familyId: 'family-001'})
CREATE (parent)-[:MEMBER_OF {role: 'admin', joinedAt: datetime(), addedBy: 'user-parent-001'}]->(f)
CREATE (spouse)-[:MEMBER_OF {role: 'parent', joinedAt: datetime(), addedBy: 'user-parent-001'}]->(f)
CREATE (child)-[:MEMBER_OF {role: 'child', joinedAt: datetime(), addedBy: 'user-parent-001'}]->(f)
CREATE (uncle)-[:MEMBER_OF {role: 'member', joinedAt: datetime(), addedBy: 'user-parent-001'}]->(f);

// 7. Create Guardian Relationships
MATCH (parent:User {userId: 'user-parent-001'})
MATCH (spouse:User {userId: 'user-spouse-001'})
MATCH (child:User {userId: 'user-child-001'})
CREATE (parent)-[:GUARDIAN_OF {
    relationshipType: 'parent',
    createdAt: datetime(),
    canViewData: true,
    canModifyData: true
}]->(child)
CREATE (spouse)-[:GUARDIAN_OF {
    relationshipType: 'parent',
    createdAt: datetime(),
    canViewData: true,
    canModifyData: true
}]->(child);

// 8. Visualize complete family network
MATCH path = (f:Family {familyId: 'family-001'})<-[:MEMBER_OF]-(u:User)
OPTIONAL MATCH guardian_path = (u)-[:GUARDIAN_OF]->(ward:User)
RETURN path, guardian_path;
```

### Access Control Examples
```cypher
// Check Parent's access to Child's data
MATCH (parent:User {userId: 'user-parent-001'})
MATCH (child:User {userId: 'user-child-001'})
OPTIONAL MATCH (parent)-[g:GUARDIAN_OF]->(child)
OPTIONAL MATCH (parent)-[:MEMBER_OF]->(f:Family)<-[:MEMBER_OF]-(child)
RETURN
    parent.name AS Requestor,
    child.name AS Target,
    CASE
        WHEN parent.userId = child.userId THEN 'Own Data'
        WHEN g IS NOT NULL THEN 'Guardian Access'
        WHEN f IS NOT NULL THEN 'Family Member'
        ELSE 'No Access'
    END AS AccessType,
    CASE
        WHEN g IS NOT NULL OR parent.userId = child.userId THEN true
        ELSE false
    END AS CanModify;

// Check Uncle's access to Child's data (should be denied)
MATCH (uncle:User {userId: 'user-uncle-001'})
MATCH (child:User {userId: 'user-child-001'})
OPTIONAL MATCH (uncle)-[g:GUARDIAN_OF]->(child)
OPTIONAL MATCH (uncle)-[r:MEMBER_OF]->(f:Family)<-[:MEMBER_OF]-(child)
RETURN
    uncle.name AS Requestor,
    child.name AS Target,
    r.role AS UncleRole,
    CASE
        WHEN g IS NOT NULL THEN 'YES - Guardian'
        WHEN r.role = 'admin' THEN 'YES - Admin'
        ELSE 'NO - Insufficient Permission'
    END AS CanModifyData;
```

---

## Relationship Types (30+ Total)

### User Relationships
```cypher
(User)-[:MEMBER_OF]->(Family)
(User)-[:HAS_RECORD]->(HealthRecord|LabReport|Prescription)
(User)-[:RECEIVED]->(Vaccination)
(User)-[:HAS_CONDITION]->(Condition)
(User)-[:TAKES]->(Medication)
(User)-[:TREATED_BY]->(Doctor)
(User)-[:SCHEDULED]->(Appointment)
(User)-[:HAS_VITAL]->(VitalSign)
(User)-[:HAS_GROWTH_RECORD]->(GrowthRecord)
(User)-[:HAS_LAB_RESULT]->(LabResult)
(User)-[:HAS_INSIGHT]->(HealthInsight)
(User)-[:HAS_RISK_FACTOR]->(RiskFactor)
(User)-[:HAD_CONVERSATION]->(Conversation)
```

### Medical Entity Relationships
```cypher
(Medication)-[:TREATS]->(Condition)
(Medication)-[:INTERACTS_WITH]-(Medication)
(Medication)-[:CAUSES]->(Symptom)
(Doctor)-[:SPECIALIZES_IN]->(Condition)
(Doctor)-[:WORKS_AT]->(Hospital)
```

### Appointment Relationships
```cypher
(Appointment)-[:WITH_DOCTOR]->(Doctor)
(Appointment)-[:AT_LOCATION]->(Hospital)
(Appointment)-[:FOLLOWUP_TO]->(Appointment)
(Appointment)-[:RESULTED_IN]->(HealthRecord)
```

### AI Insights Relationships
```cypher
(HealthInsight)-[:RELATED_TO]->(Condition|Medication)
(RiskFactor)-[:MAY_LEAD_TO]->(Condition)
```

### Other Relationships
```cypher
(LabResult)-[:PART_OF]->(LabReport)
(ChatMessage)-[:IN_CONVERSATION]->(Conversation)
(ChatMessage)-[:ASKED_ABOUT]->(HealthRecord)
(ChatMessage)-[:DISCUSSED_MEDICATION]->(Medication)
```

## Key Features

### 1. Geospatial Search
```python
# Find hospitals within 5km
hospitals = client.search_nearby_hospitals(
    latitude=40.7128,
    longitude=-74.0060,
    max_distance_km=5.0,
    emergency_only=True
)
```

### 2. Drug Interaction Detection
```python
# Check all active medications for interactions
interactions = client.check_user_drug_interactions(user_id="123")
# Returns: severity, effect, recommendation
```

### 3. Genetic Risk Analysis
```python
# Find conditions affecting multiple family members
risks = client.analyze_family_genetic_risk(family_id="456")
# Returns: condition, affected_count, member_names
```

### 4. Temporal Queries
```python
# Get vitals in date range
vitals = client.get_vitals_in_range(
    user_id="123",
    vital_type="blood_pressure",
    start_date="2024-01-01",
    end_date="2024-12-31"
)
```

### 5. AI Insights Dashboard
```python
# Get critical health alerts
critical = client.get_critical_insights(user_id="123")
# Returns: high/critical severity insights

# Get actionable recommendations
actionable = client.get_actionable_insights(user_id="123")
```

### 6. Pediatric Growth Tracking
```python
# Track child growth with percentiles
growth = client.create_growth_record(
    user_id="child123",
    age_months=24,
    height_cm=85.5,
    weight_kg=12.3,
    percentiles={"height": 75, "weight": 60}
)
```

## Usage Examples

### Complete Workflow
```python
from backend.shared.database.neo4j import Neo4jClient

# Initialize client
client = Neo4jClient()

# 1. Create user and family
user = client.create_user(
    email="john@example.com",
    name="John Doe",
    date_of_birth="1980-05-15",
    gender="M"
)

family = client.create_family(
    name="Doe Family",
    created_by=user['userId']
)

client.add_user_to_family(user['userId'], family['familyId'], role="parent")

# 2. Add medical condition
condition = client.create_condition(
    name="Hypertension",
    icd_code="I10",
    category="chronic",
    severity="moderate"
)

client.add_user_condition(
    user['userId'],
    condition['conditionId'],
    diagnosed_date="2020-01-15"
)

# 3. Add medication
medication = client.create_medication(
    name="Lisinopril",
    generic_name="Lisinopril",
    medication_class="ACE Inhibitor"
)

client.add_user_medication(
    user['userId'],
    medication['medicationId'],
    start_date="2020-02-01",
    dosage="10mg",
    frequency="daily"
)

# 4. Link medication to condition
client.link_medication_to_condition(
    medication['medicationId'],
    condition['conditionId'],
    effectiveness=0.85,
    primary_treatment=True
)

# 5. Add doctor and hospital
doctor = client.create_doctor(
    name="Dr. Sarah Smith",
    specialty="Cardiology",
    license_number="MD123456"
)

hospital = client.create_hospital(
    name="Central Hospital",
    address="123 Main St",
    latitude=40.7128,
    longitude=-74.0060
)

client.link_doctor_to_hospital(doctor['doctorId'], hospital['hospitalId'])
client.link_user_to_doctor(user['userId'], doctor['doctorId'], first_visit="2020-01-15")

# 6. Schedule appointment
appointment = client.create_appointment(
    user_id=user['userId'],
    date_time="2024-02-01T10:00:00",
    appointment_type="checkup",
    reason="Annual checkup"
)

client.link_appointment_to_doctor(appointment['appointmentId'], doctor['doctorId'])
client.link_appointment_to_hospital(appointment['appointmentId'], hospital['hospitalId'])

# 7. Track vitals
vital = client.create_vital_sign(
    user_id=user['userId'],
    vital_type="blood_pressure_systolic",
    value=120,
    unit="mmHg",
    date="2024-01-15"
)

# 8. Create AI insight
insight = client.create_health_insight(
    user_id=user['userId'],
    insight_type="alert",
    title="Blood Pressure Monitoring",
    description="Continue monitoring BP daily",
    severity="medium",
    recommendations=["Monitor daily", "Reduce sodium"]
)

# 9. Advanced queries
# Check drug interactions
interactions = client.check_user_drug_interactions(user['userId'])

# Find family genetic risks
genetic_risks = client.analyze_family_genetic_risk(family['familyId'])

# Get critical insights
critical = client.get_critical_insights(user['userId'])

# Find nearby hospitals
nearby = client.search_nearby_hospitals(40.7128, -74.0060, max_distance_km=5.0)
```

## Performance Optimizations

### Indexes Created
- Unique constraints on all primary IDs
- Single-field indexes on commonly queried fields
- Composite indexes for multi-field queries
- Full-text search indexes for text fields
- Geospatial index for hospital locations

### Query Optimization
- Connection pooling via Neo4j driver
- Parameter binding for all queries
- LIMIT clauses on large result sets
- Strategic use of OPTIONAL MATCH
- WHERE clauses before WITH/RETURN

## Testing

```bash
# Run comprehensive test suite
cd backend/shared/database/neo4j
python test_all_operations.py

# Expected output:
# ✓ Neo4j connection successful
# ✓ Created users: 2
# ✓ Created conditions: 2
# ✓ Created medications: 2
# ✓ Checked drug interactions
# ✓ Found genetic risk patterns
# ✓ All tests passed!
```

## File Structure

```
backend/shared/database/neo4j/
├── neo4j_client.py              # Unified client (main entry point)
├── config.py                    # Neo4j configuration
├── schema.cypher                # Database schema, constraints, indexes
├── operations/
│   ├── __init__.py
│   ├── graph_ops.py            # Base graph operations
│   ├── user_ops.py             # User CRUD
│   ├── family_ops.py           # Family operations
│   ├── health_record_ops.py    # Health records, labs, prescriptions
│   ├── medication_ops.py       # Medications, interactions
│   ├── condition_ops.py        # Conditions, symptoms, genetic risk
│   ├── provider_ops.py         # Doctors, hospitals, geospatial
│   ├── appointment_ops.py      # Appointments, scheduling
│   ├── vitals_ops.py          # Vitals, growth, lab results
│   └── insights_ops.py        # AI insights, risk factors
├── test_all_operations.py      # Comprehensive test suite
└── NEO4J_IMPLEMENTATION.md     # This file
```

## Next Steps

### Potential Enhancements
1. **Chatbot Integration**
   - Create conversation_ops.py for chat operations
   - Link messages to entities (ASKED_ABOUT, DISCUSSED_MEDICATION)

2. **Advanced Analytics**
   - Time-series analysis for vital trends
   - Machine learning integration for predictions
   - Anomaly detection in vitals

3. **Performance Monitoring**
   - Query profiling
   - Slow query logging
   - Index usage statistics

4. **Additional Features**
   - Allergy tracking
   - Immunization schedules
   - Care plan management
   - Medical device integration

## Troubleshooting

### Common Issues

**Connection Failed**
```bash
# Check Neo4j is running
docker ps | grep neo4j

# Restart Neo4j
docker-compose restart neo4j
```

**Schema Not Loaded**
```bash
# Load schema manually
cat schema.cypher | docker exec -i neo4j cypher-shell -u neo4j -p password
```

**Import Errors**
```python
# Ensure backend path is in PYTHONPATH
import sys
sys.path.insert(0, '/path/to/backend')
```

## Contributing

When adding new operations:
1. Create new operation class in `operations/`
2. Inherit from `BaseNeo4jClient`
3. Add class to `Neo4jClient` multiple inheritance
4. Update this documentation
5. Add tests to `test_all_operations.py`

## License

MIT License - See main project LICENSE file
