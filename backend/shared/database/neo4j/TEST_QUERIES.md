# Neo4j Test Queries - Complete Guide

## 🌐 Access URLs

### Neo4j Browser (Main Interface)
```
URL: http://localhost:7474/browser/
Username: neo4j
Password: [your-password]
```

### Neo4j Bloom (Visual Exploration) - If Enabled
```
URL: http://localhost:7474/bloom/
```

### API Endpoints
```
Bolt Protocol: bolt://localhost:7687
HTTP API: http://localhost:7474
HTTPS API: https://localhost:7473
```

---

## 📊 Database Overview Queries

### 1. Check All Node Types
```cypher
// Count all node types
CALL db.labels() YIELD label
CALL apoc.cypher.run('MATCH (n:`'+label+'`) RETURN count(n) as count', {})
YIELD value
RETURN label, value.count AS count
ORDER BY count DESC;
```

**Simple Version (without APOC):**
```cypher
MATCH (n)
RETURN labels(n) AS NodeType, count(*) AS Count
ORDER BY Count DESC;
```

### 2. Check All Relationship Types
```cypher
CALL db.relationshipTypes() YIELD relationshipType
RETURN relationshipType
ORDER BY relationshipType;
```

### 3. Database Statistics
```cypher
// Complete database stats
MATCH (n)
WITH labels(n) AS labels, count(*) AS nodeCount
UNWIND labels AS label
RETURN label, sum(nodeCount) AS totalNodes
ORDER BY totalNodes DESC;
```

---

## 🧪 Test Data Creation Queries

### Create Test User
```cypher
CREATE (u:User {
    userId: 'test-user-001',
    email: 'test@example.com',
    name: 'Test User',
    dateOfBirth: date('1990-01-15'),
    gender: 'M',
    phoneNumber: '+1234567890',
    createdAt: datetime()
})
RETURN u;
```

### Create Test Family
```cypher
CREATE (f:Family {
    familyId: 'test-family-001',
    name: 'Test Family',
    createdBy: 'test-user-001',
    createdAt: datetime()
})
RETURN f;
```

### Link User to Family
```cypher
MATCH (u:User {userId: 'test-user-001'})
MATCH (f:Family {familyId: 'test-family-001'})
CREATE (u)-[r:MEMBER_OF {
    role: 'parent',
    joinedAt: datetime()
}]->(f)
RETURN u, r, f;
```

### Create Test Condition
```cypher
CREATE (c:Condition {
    conditionId: 'test-condition-001',
    name: 'Hypertension',
    icdCode: 'I10',
    category: 'chronic',
    severity: 'moderate',
    description: 'High blood pressure'
})
RETURN c;
```

### Add Condition to User
```cypher
MATCH (u:User {userId: 'test-user-001'})
MATCH (c:Condition {conditionId: 'test-condition-001'})
CREATE (u)-[r:HAS_CONDITION {
    diagnosedDate: date('2020-01-15'),
    status: 'active',
    severity: 'moderate'
}]->(c)
RETURN u, r, c;
```

### Create Test Medication
```cypher
CREATE (m:Medication {
    medicationId: 'test-med-001',
    name: 'Lisinopril',
    genericName: 'Lisinopril',
    brandName: 'Prinivil',
    class: 'ACE Inhibitor',
    fdaApproved: true,
    activeIngredients: ['Lisinopril']
})
RETURN m;
```

### Add Medication to User
```cypher
MATCH (u:User {userId: 'test-user-001'})
MATCH (m:Medication {medicationId: 'test-med-001'})
CREATE (u)-[r:TAKES {
    startDate: date('2020-02-01'),
    dosage: '10mg',
    frequency: 'daily',
    status: 'active',
    reminderTimes: ['08:00', '20:00']
}]->(m)
RETURN u, r, m;
```

### Link Medication to Condition
```cypher
MATCH (m:Medication {medicationId: 'test-med-001'})
MATCH (c:Condition {conditionId: 'test-condition-001'})
CREATE (m)-[r:TREATS {
    effectiveness: 0.85,
    primaryTreatment: true
}]->(c)
RETURN m, r, c;
```

### Create Test Doctor
```cypher
CREATE (d:Doctor {
    doctorId: 'test-doctor-001',
    name: 'Dr. Sarah Smith',
    specialty: 'Cardiology',
    licenseNumber: 'MD123456',
    phoneNumber: '+1234567891',
    email: 'dr.smith@hospital.com',
    yearsOfExperience: 15
})
RETURN d;
```

### Create Test Hospital (with Geospatial Location)
```cypher
CREATE (h:Hospital {
    hospitalId: 'test-hospital-001',
    name: 'Central Hospital',
    address: '123 Main St, New York, NY',
    location: point({latitude: 40.7128, longitude: -74.0060}),
    phoneNumber: '+1234567892',
    emergencyAvailable: true,
    rating: 4.5
})
RETURN h;
```

### Link Doctor to Hospital
```cypher
MATCH (d:Doctor {doctorId: 'test-doctor-001'})
MATCH (h:Hospital {hospitalId: 'test-hospital-001'})
CREATE (d)-[r:WORKS_AT {
    startDate: date('2015-01-01'),
    isPrimary: true
}]->(h)
RETURN d, r, h;
```

### Create Test Appointment
```cypher
MATCH (u:User {userId: 'test-user-001'})
CREATE (a:Appointment {
    appointmentId: 'test-appt-001',
    dateTime: datetime('2024-02-01T10:00:00'),
    type: 'checkup',
    status: 'scheduled',
    reason: 'Annual checkup',
    notes: 'Bring previous lab reports',
    reminderSent: false,
    createdAt: datetime()
})
CREATE (u)-[:SCHEDULED]->(a)
RETURN u, a;
```

### Link Appointment to Doctor and Hospital
```cypher
MATCH (a:Appointment {appointmentId: 'test-appt-001'})
MATCH (d:Doctor {doctorId: 'test-doctor-001'})
MATCH (h:Hospital {hospitalId: 'test-hospital-001'})
CREATE (a)-[:WITH_DOCTOR]->(d)
CREATE (a)-[:AT_LOCATION]->(h)
RETURN a, d, h;
```

### Create Test Vital Sign
```cypher
MATCH (u:User {userId: 'test-user-001'})
CREATE (v:VitalSign {
    vitalId: 'test-vital-001',
    type: 'blood_pressure_systolic',
    value: 120.0,
    unit: 'mmHg',
    date: date('2024-01-15'),
    time: time('08:00:00'),
    notes: 'Morning reading',
    createdAt: datetime()
})
CREATE (u)-[:HAS_VITAL]->(v)
RETURN u, v;
```

### Create Test Health Insight
```cypher
MATCH (u:User {userId: 'test-user-001'})
CREATE (i:HealthInsight {
    insightId: 'test-insight-001',
    type: 'alert',
    title: 'Elevated Blood Pressure Trend',
    description: 'Your BP has been consistently above normal',
    severity: 'medium',
    category: 'vitals',
    confidenceScore: 0.85,
    actionable: true,
    recommendations: ['Monitor BP daily', 'Reduce sodium intake'],
    dataSources: ['VitalSign readings'],
    status: 'active',
    createdAt: datetime()
})
CREATE (u)-[r:HAS_INSIGHT {
    acknowledged: false
}]->(i)
RETURN u, r, i;
```

---

## 🔍 Advanced Query Tests

### 1. Get User's Complete Health Profile
```cypher
MATCH (u:User {userId: 'test-user-001'})
OPTIONAL MATCH (u)-[:MEMBER_OF]->(f:Family)
OPTIONAL MATCH (u)-[hc:HAS_CONDITION]->(c:Condition)
OPTIONAL MATCH (u)-[t:TAKES]->(m:Medication)
OPTIONAL MATCH (u)-[tb:TREATED_BY]->(d:Doctor)
OPTIONAL MATCH (u)-[:SCHEDULED]->(a:Appointment)
RETURN u.name AS Name,
       f.name AS Family,
       collect(DISTINCT c.name) AS Conditions,
       collect(DISTINCT m.name) AS Medications,
       collect(DISTINCT d.name) AS Doctors,
       count(DISTINCT a) AS TotalAppointments;
```

### 2. Check Drug Interactions for User
```cypher
MATCH (u:User {userId: 'test-user-001'})-[t1:TAKES]->(m1:Medication)
MATCH (u)-[t2:TAKES]->(m2:Medication)
MATCH (m1)-[r:INTERACTS_WITH]-(m2)
WHERE t1.status = 'active' AND t2.status = 'active'
AND m1.medicationId < m2.medicationId
RETURN m1.name AS Medication1,
       m2.name AS Medication2,
       r.severity AS Severity,
       r.effect AS Effect,
       r.recommendation AS Recommendation;
```

### 3. Find Nearby Hospitals (Geospatial Search)
```cypher
// Find hospitals within 10km of a location
MATCH (h:Hospital)
WITH h,
     point.distance(h.location, point({latitude: 40.7128, longitude: -74.0060})) / 1000.0 as distance
WHERE distance <= 10.0
RETURN h.name AS Hospital,
       h.address AS Address,
       distance AS DistanceKM,
       h.emergencyAvailable AS HasEmergency,
       h.rating AS Rating
ORDER BY distance ASC;
```

### 4. Get User's Medication Timeline
```cypher
MATCH (u:User {userId: 'test-user-001'})-[t:TAKES]->(m:Medication)
RETURN m.name AS Medication,
       t.dosage AS Dosage,
       t.frequency AS Frequency,
       t.startDate AS StartDate,
       t.endDate AS EndDate,
       t.status AS Status
ORDER BY t.startDate DESC;
```

### 5. Get User's Vital Signs Trend
```cypher
MATCH (u:User {userId: 'test-user-001'})-[:HAS_VITAL]->(v:VitalSign)
WHERE v.type = 'blood_pressure_systolic'
RETURN v.date AS Date,
       v.time AS Time,
       v.value AS Value,
       v.unit AS Unit
ORDER BY v.date DESC, v.time DESC
LIMIT 30;
```

### 6. Get Critical Health Insights
```cypher
MATCH (u:User {userId: 'test-user-001'})-[r:HAS_INSIGHT]->(i:HealthInsight)
WHERE i.status = 'active'
AND i.severity IN ['high', 'critical']
AND r.acknowledged = false
RETURN i.title AS Title,
       i.description AS Description,
       i.severity AS Severity,
       i.recommendations AS Recommendations,
       i.createdAt AS CreatedAt
ORDER BY
    CASE i.severity
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        ELSE 3
    END,
    i.createdAt DESC;
```

### 7. Family Genetic Risk Analysis
```cypher
MATCH (u:User)-[:MEMBER_OF]->(f:Family {familyId: 'test-family-001'})
MATCH (u)-[:HAS_CONDITION]->(c:Condition)
WHERE c.category = 'genetic' OR c.category = 'chronic'
WITH c, count(DISTINCT u) as affectedMembers, collect(DISTINCT u.name) as members
WHERE affectedMembers > 1
RETURN c.name AS Condition,
       c.category AS Category,
       affectedMembers AS AffectedMembers,
       members AS FamilyMembers
ORDER BY affectedMembers DESC;
```

### 8. Doctor's Appointment Schedule
```cypher
MATCH (a:Appointment)-[:WITH_DOCTOR]->(d:Doctor {doctorId: 'test-doctor-001'})
OPTIONAL MATCH (u:User)-[:SCHEDULED]->(a)
WHERE a.status = 'scheduled'
AND a.dateTime >= datetime()
RETURN a.dateTime AS DateTime,
       u.name AS PatientName,
       a.type AS AppointmentType,
       a.reason AS Reason
ORDER BY a.dateTime ASC;
```

### 9. Find Specialists for Condition
```cypher
MATCH (d:Doctor)-[s:SPECIALIZES_IN]->(c:Condition {name: 'Hypertension'})
OPTIONAL MATCH (d)-[:WORKS_AT]->(h:Hospital)
RETURN d.name AS Doctor,
       d.specialty AS Specialty,
       s.yearsExperience AS YearsExperience,
       s.certification AS Certification,
       h.name AS Hospital
ORDER BY s.yearsExperience DESC;
```

### 10. Upcoming Appointments for User
```cypher
MATCH (u:User {userId: 'test-user-001'})-[:SCHEDULED]->(a:Appointment)
OPTIONAL MATCH (a)-[:WITH_DOCTOR]->(d:Doctor)
OPTIONAL MATCH (a)-[:AT_LOCATION]->(h:Hospital)
WHERE a.status = 'scheduled'
AND a.dateTime >= datetime()
RETURN a.dateTime AS DateTime,
       a.type AS Type,
       a.reason AS Reason,
       d.name AS Doctor,
       h.name AS Hospital,
       h.address AS Location
ORDER BY a.dateTime ASC
LIMIT 5;
```

---

## 🧹 Cleanup Queries

### Delete Test Data
```cypher
// Delete specific test user and all relationships
MATCH (u:User {userId: 'test-user-001'})
DETACH DELETE u;
```

### Delete All Test Nodes
```cypher
// Delete all nodes with 'test-' prefix in IDs
MATCH (n)
WHERE
    (n.userId STARTS WITH 'test-' OR
     n.familyId STARTS WITH 'test-' OR
     n.conditionId STARTS WITH 'test-' OR
     n.medicationId STARTS WITH 'test-' OR
     n.doctorId STARTS WITH 'test-' OR
     n.hospitalId STARTS WITH 'test-' OR
     n.appointmentId STARTS WITH 'test-' OR
     n.vitalId STARTS WITH 'test-' OR
     n.insightId STARTS WITH 'test-')
DETACH DELETE n;
```

### Delete ALL Data (⚠️ USE WITH CAUTION)
```cypher
// Delete everything in database
MATCH (n)
DETACH DELETE n;
```

---

## 📈 Performance Testing Queries

### Count All Nodes
```cypher
MATCH (n)
RETURN count(n) AS TotalNodes;
```

### Count All Relationships
```cypher
MATCH ()-[r]->()
RETURN count(r) AS TotalRelationships;
```

### Check Index Usage
```cypher
CALL db.indexes() YIELD name, state, type, entityType, labelsOrTypes, properties
RETURN name, state, type, entityType, labelsOrTypes, properties
ORDER BY name;
```

### Check Constraints
```cypher
CALL db.constraints() YIELD name, type, labelsOrTypes, properties
RETURN name, type, labelsOrTypes, properties
ORDER BY name;
```

### Query Performance Profile
```cypher
// Profile a query to see execution plan
PROFILE
MATCH (u:User {userId: 'test-user-001'})-[:HAS_CONDITION]->(c:Condition)
RETURN u, c;
```

---

## 🎯 Quick Test Script

Run this complete test in Neo4j Browser:

```cypher
// 1. Create test user
CREATE (u:User {
    userId: 'quick-test-001',
    email: 'quick@test.com',
    name: 'Quick Test User',
    dateOfBirth: date('1990-01-01'),
    gender: 'M'
});

// 2. Create condition
CREATE (c:Condition {
    conditionId: 'quick-cond-001',
    name: 'Test Condition',
    icdCode: 'T00',
    category: 'chronic',
    severity: 'mild'
});

// 3. Link them
MATCH (u:User {userId: 'quick-test-001'})
MATCH (c:Condition {conditionId: 'quick-cond-001'})
CREATE (u)-[r:HAS_CONDITION {
    diagnosedDate: date(),
    status: 'active'
}]->(c);

// 4. Verify
MATCH (u:User {userId: 'quick-test-001'})-[r:HAS_CONDITION]->(c:Condition)
RETURN u.name, c.name, r.diagnosedDate;

// 5. Cleanup
MATCH (u:User {userId: 'quick-test-001'})
DETACH DELETE u;

MATCH (c:Condition {conditionId: 'quick-cond-001'})
DETACH DELETE c;
```

---

## 📱 Access Instructions

### 1. Start Neo4j
```bash
# If using Docker Compose
docker-compose up neo4j

# Or if using Docker directly
docker start neo4j
```

### 2. Open Browser
```
Navigate to: http://localhost:7474
```

### 3. Login
```
Username: neo4j
Password: [check your .env file or docker-compose.yml]
```

### 4. Run Queries
- Paste queries in the top input box
- Press Ctrl+Enter (or Cmd+Enter on Mac) to execute
- View results in table, graph, or text format

---

## 🎨 Complete Schema Visualization

### Full Schema Test - Create Complete Health Network
```cypher
// ========================================
// COMPLETE SCHEMA DEMONSTRATION
// Creates all node types and relationships
// ========================================

// 1. Create Family
CREATE (f:Family {
    familyId: 'demo-family-001',
    name: 'Demo Health Family',
    createdBy: 'demo-parent-001',
    createdAt: datetime()
});

// 2. Create Parent User
CREATE (parent:User {
    userId: 'demo-parent-001',
    email: 'parent@demo.com',
    name: 'John Doe',
    dateOfBirth: date('1980-01-15'),
    gender: 'M',
    phoneNumber: '+1234567890',
    createdAt: datetime()
});

// 3. Create Child User
CREATE (child:User {
    userId: 'demo-child-001',
    email: 'child@demo.com',
    name: 'Jane Doe',
    dateOfBirth: date('2015-06-20'),
    gender: 'F',
    createdAt: datetime()
});

// 3b. Create Another Existing User (to test adding existing member)
CREATE (uncle:User {
    userId: 'demo-uncle-001',
    email: 'uncle@demo.com',
    name: 'Bob Smith',
    dateOfBirth: date('1975-03-10'),
    gender: 'M',
    createdAt: datetime()
});

// 4. Link to Family
MATCH (parent:User {userId: 'demo-parent-001'})
MATCH (child:User {userId: 'demo-child-001'})
MATCH (uncle:User {userId: 'demo-uncle-001'})
MATCH (f:Family {familyId: 'demo-family-001'})
CREATE (parent)-[:MEMBER_OF {role: 'parent', joinedAt: datetime(), addedBy: 'demo-parent-001'}]->(f)
CREATE (child)-[:MEMBER_OF {role: 'child', joinedAt: datetime(), addedBy: 'demo-parent-001'}]->(f)
CREATE (uncle)-[:MEMBER_OF {role: 'member', joinedAt: datetime(), addedBy: 'demo-parent-001'}]->(f);

// 5. Create Guardian Relationship
MATCH (parent:User {userId: 'demo-parent-001'})
MATCH (child:User {userId: 'demo-child-001'})
CREATE (parent)-[:GUARDIAN_OF {
    relationshipType: 'parent',
    createdAt: datetime(),
    canViewData: true,
    canModifyData: true
}]->(child);

// 6. Create Condition
CREATE (c:Condition {
    conditionId: 'demo-condition-001',
    name: 'Type 1 Diabetes',
    icdCode: 'E10',
    category: 'chronic',
    severity: 'moderate',
    description: 'Insulin-dependent diabetes'
});

// 7. Link Child to Condition
MATCH (child:User {userId: 'demo-child-001'})
MATCH (c:Condition {conditionId: 'demo-condition-001'})
CREATE (child)-[:HAS_CONDITION {
    diagnosedDate: date('2020-03-15'),
    status: 'active',
    severity: 'moderate'
}]->(c);

// 8. Create Medication
CREATE (m:Medication {
    medicationId: 'demo-med-001',
    name: 'Insulin',
    genericName: 'Insulin',
    brandName: 'Humalog',
    class: 'Antidiabetic',
    fdaApproved: true
});

// 9. Link Medication to Condition
MATCH (m:Medication {medicationId: 'demo-med-001'})
MATCH (c:Condition {conditionId: 'demo-condition-001'})
CREATE (m)-[:TREATS {
    effectiveness: 0.95,
    primaryTreatment: true
}]->(c);

// 10. Child Takes Medication
MATCH (child:User {userId: 'demo-child-001'})
MATCH (m:Medication {medicationId: 'demo-med-001'})
CREATE (child)-[:TAKES {
    startDate: date('2020-03-20'),
    dosage: '10 units',
    frequency: 'three_times_daily',
    status: 'active',
    reminderTimes: ['08:00', '13:00', '19:00']
}]->(m);

// 11. Create Doctor
CREATE (d:Doctor {
    doctorId: 'demo-doctor-001',
    name: 'Dr. Emily Smith',
    specialty: 'Endocrinology',
    licenseNumber: 'MD987654',
    yearsOfExperience: 12
});

// 12. Create Hospital
CREATE (h:Hospital {
    hospitalId: 'demo-hospital-001',
    name: 'City Children Hospital',
    address: '456 Medical Ave',
    location: point({latitude: 40.7580, longitude: -73.9855}),
    emergencyAvailable: true,
    rating: 4.7
});

// 13. Doctor Works at Hospital
MATCH (d:Doctor {doctorId: 'demo-doctor-001'})
MATCH (h:Hospital {hospitalId: 'demo-hospital-001'})
CREATE (d)-[:WORKS_AT {
    startDate: date('2015-01-01'),
    isPrimary: true
}]->(h);

// 14. Doctor Specializes in Condition
MATCH (d:Doctor {doctorId: 'demo-doctor-001'})
MATCH (c:Condition {conditionId: 'demo-condition-001'})
CREATE (d)-[:SPECIALIZES_IN {
    yearsExperience: 12,
    certification: 'Board Certified Endocrinologist'
}]->(c);

// 15. Child Treated by Doctor
MATCH (child:User {userId: 'demo-child-001'})
MATCH (d:Doctor {doctorId: 'demo-doctor-001'})
CREATE (child)-[:TREATED_BY {
    firstVisit: date('2020-03-15'),
    lastVisit: date('2024-01-10'),
    visitCount: 15,
    primaryCare: true
}]->(d);

// 16. Create Appointment
CREATE (appt:Appointment {
    appointmentId: 'demo-appt-001',
    dateTime: datetime('2024-02-15T10:00:00'),
    type: 'followup',
    status: 'scheduled',
    reason: 'Diabetes checkup',
    reminderSent: false
});

// 17. Link Appointment
MATCH (child:User {userId: 'demo-child-001'})
MATCH (appt:Appointment {appointmentId: 'demo-appt-001'})
MATCH (d:Doctor {doctorId: 'demo-doctor-001'})
MATCH (h:Hospital {hospitalId: 'demo-hospital-001'})
CREATE (child)-[:SCHEDULED]->(appt)
CREATE (appt)-[:WITH_DOCTOR]->(d)
CREATE (appt)-[:AT_LOCATION]->(h);

// 18. Create Vital Sign
CREATE (v:VitalSign {
    vitalId: 'demo-vital-001',
    type: 'blood_glucose',
    value: 120.0,
    unit: 'mg/dL',
    date: date('2024-01-15'),
    time: time('08:00:00')
});

// 19. Link Vital to Child
MATCH (child:User {userId: 'demo-child-001'})
MATCH (v:VitalSign {vitalId: 'demo-vital-001'})
CREATE (child)-[:HAS_VITAL]->(v);

// 20. Create Health Record
CREATE (hr:HealthRecord {
    recordId: 'demo-record-001',
    type: 'lab_report',
    date: date('2024-01-10'),
    title: 'HbA1c Test',
    summary: 'Good diabetes control - HbA1c at 6.5%',
    createdAt: datetime()
});

// 21. Link Record to Child
MATCH (child:User {userId: 'demo-child-001'})
MATCH (hr:HealthRecord {recordId: 'demo-record-001'})
CREATE (child)-[:HAS_RECORD]->(hr);

// 22. Create Health Insight
CREATE (insight:HealthInsight {
    insightId: 'demo-insight-001',
    type: 'recommendation',
    title: 'Excellent Blood Sugar Control',
    description: 'Blood glucose levels have been stable',
    severity: 'info',
    category: 'vitals',
    confidenceScore: 0.92,
    actionable: true,
    recommendations: ['Continue current regimen', 'Monitor daily'],
    status: 'active',
    createdAt: datetime()
});

// 23. Link Insight to Child
MATCH (child:User {userId: 'demo-child-001'})
MATCH (insight:HealthInsight {insightId: 'demo-insight-001'})
CREATE (child)-[:HAS_INSIGHT {acknowledged: false}]->(insight);

// 24. Link Insight to Condition
MATCH (insight:HealthInsight {insightId: 'demo-insight-001'})
MATCH (c:Condition {conditionId: 'demo-condition-001'})
CREATE (insight)-[:RELATED_TO]->(c);

// Done!
RETURN 'Complete schema created successfully!' AS status;
```

### Test Access Control - Add Member Permission Check
```cypher
// ========================================
// ACCESS CONTROL DEMONSTRATION
// Test who can add members to family
// ========================================

// Test 1: Check if Parent can add members (Should succeed - Parent role)
MATCH (f:Family {familyId: 'demo-family-001'})
MATCH (parent:User {userId: 'demo-parent-001'})-[r:MEMBER_OF]->(f)
RETURN
    'Parent Permission Check' AS Test,
    parent.name AS User,
    r.role AS Role,
    CASE
        WHEN f.createdBy = parent.userId THEN 'YES - Family Creator'
        WHEN r.role IN ['admin', 'parent'] THEN 'YES - Has Parent/Admin Role'
        ELSE 'NO - Insufficient Permissions'
    END AS CanAddMembers;

// Test 2: Check if Child can add members (Should fail - Child role)
MATCH (f:Family {familyId: 'demo-family-001'})
MATCH (child:User {userId: 'demo-child-001'})-[r:MEMBER_OF]->(f)
RETURN
    'Child Permission Check' AS Test,
    child.name AS User,
    r.role AS Role,
    CASE
        WHEN f.createdBy = child.userId THEN 'YES - Family Creator'
        WHEN r.role IN ['admin', 'parent'] THEN 'YES - Has Parent/Admin Role'
        ELSE 'NO - Insufficient Permissions'
    END AS CanAddMembers;

// Test 3: Check if Uncle can add members (Should fail - Member role)
MATCH (f:Family {familyId: 'demo-family-001'})
MATCH (uncle:User {userId: 'demo-uncle-001'})-[r:MEMBER_OF]->(f)
RETURN
    'Uncle Permission Check' AS Test,
    uncle.name AS User,
    r.role AS Role,
    CASE
        WHEN f.createdBy = uncle.userId THEN 'YES - Family Creator'
        WHEN r.role IN ['admin', 'parent'] THEN 'YES - Has Parent/Admin Role'
        ELSE 'NO - Insufficient Permissions'
    END AS CanAddMembers;

// Test 4: Check Guardian permissions (Parent can view/modify Child data)
MATCH (parent:User {userId: 'demo-parent-001'})-[g:GUARDIAN_OF]->(child:User {userId: 'demo-child-001'})
RETURN
    'Guardian Permission Check' AS Test,
    parent.name AS Guardian,
    child.name AS Ward,
    g.canViewData AS CanView,
    g.canModifyData AS CanModify,
    'YES - Full Access to Ward Data' AS Status;

// Test 5: Check Family Member Data Access
MATCH (parent:User {userId: 'demo-parent-001'})-[:MEMBER_OF]->(f:Family)<-[:MEMBER_OF]-(uncle:User {userId: 'demo-uncle-001'})
RETURN
    'Family Member Access Check' AS Test,
    parent.name AS Requestor,
    uncle.name AS Target,
    'Same Family' AS Relationship,
    CASE
        WHEN parent.userId = uncle.userId THEN 'YES - Own Data'
        ELSE 'NO - Not Guardian or Admin'
    END AS CanModifyData;
```

### Show Family Structure with Roles
```cypher
// Display complete family hierarchy with roles
MATCH (f:Family {familyId: 'demo-family-001'})<-[r:MEMBER_OF]-(u:User)
RETURN
    f.name AS Family,
    u.name AS Member,
    r.role AS Role,
    r.addedBy AS AddedBy,
    CASE
        WHEN f.createdBy = u.userId THEN 'Creator'
        ELSE 'Member'
    END AS Status,
    CASE
        WHEN r.role IN ['admin', 'parent'] THEN 'Can Add/Remove Members'
        ELSE 'Cannot Add/Remove Members'
    END AS Permissions
ORDER BY
    CASE r.role
        WHEN 'admin' THEN 1
        WHEN 'parent' THEN 2
        WHEN 'child' THEN 3
        ELSE 4
    END;
```

---

### Visualize Complete Schema
```cypher
// See everything in one beautiful graph!
MATCH path = (f:Family {familyId: 'demo-family-001'})<-[:MEMBER_OF]-(u:User)-[*1..2]-(related)
RETURN path
LIMIT 300;
```

### Alternative: Focused User Network View
```cypher
// Child's complete health network
MATCH path = (child:User {userId: 'demo-child-001'})-[*1..2]-(connected)
RETURN path
LIMIT 200;
```

### Cleanup Demo Data
```cypher
// Remove all demo data when done
MATCH (n)
WHERE n.familyId = 'demo-family-001'
   OR n.userId STARTS WITH 'demo-'
   OR n.conditionId STARTS WITH 'demo-'
   OR n.medicationId STARTS WITH 'demo-'
   OR n.doctorId STARTS WITH 'demo-'
   OR n.hospitalId STARTS WITH 'demo-'
   OR n.appointmentId STARTS WITH 'demo-'
   OR n.vitalId STARTS WITH 'demo-'
   OR n.recordId STARTS WITH 'demo-'
   OR n.insightId STARTS WITH 'demo-'
DETACH DELETE n;
```

---

## 🎨 Original Visualization Tips

### Graph View
```cypher
// Visualize user's health network
MATCH path = (u:User {userId: 'test-user-001'})-[*1..2]-(related)
RETURN path
LIMIT 100;
```

### Family Network
```cypher
// Visualize entire family and their health data
MATCH path = (f:Family {familyId: 'test-family-001'})<-[:MEMBER_OF]-(u:User)-[*1]-(related)
RETURN path
LIMIT 200;
```

### Medication Network
```cypher
// Visualize medications and their interactions
MATCH path = (m1:Medication)-[:INTERACTS_WITH]-(m2:Medication)
RETURN path;
```

---

## 🔧 Troubleshooting

### If No Results:
```cypher
// Check if database is empty
MATCH (n) RETURN count(n) AS totalNodes;
```

### If Connection Fails:
1. Check Docker: `docker ps | grep neo4j`
2. Check logs: `docker logs neo4j`
3. Restart: `docker restart neo4j`

### Reset Password (if locked out):
```bash
docker exec -it neo4j cypher-shell -u neo4j -p oldpassword
:exit
```
