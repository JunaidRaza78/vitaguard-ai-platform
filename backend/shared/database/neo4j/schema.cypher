-- Neo4j Schema Initialization Script
-- Creates indexes and constraints for User and Family nodes

-- ==================== Constraints ====================
-- Ensure uniqueness of userId
CREATE CONSTRAINT userId_unique IF NOT EXISTS
FOR (u:User) REQUIRE u.userId IS UNIQUE;

-- Ensure uniqueness of email
CREATE CONSTRAINT user_email_unique IF NOT EXISTS
FOR (u:User) REQUIRE u.email IS UNIQUE;

-- Ensure uniqueness of familyId
CREATE CONSTRAINT familyId_unique IF NOT EXISTS
FOR (f:Family) REQUIRE f.familyId IS UNIQUE;

-- ==================== Indexes ====================
-- Index on User.userId (for faster lookups)
CREATE INDEX userId_index IF NOT EXISTS
FOR (u:User) ON (u.userId);

-- Index on User.email (for faster email lookups)
CREATE INDEX user_email_index IF NOT EXISTS
FOR (u:User) ON (u.email);

-- Index on User.name (for name searches)
CREATE INDEX user_name_index IF NOT EXISTS
FOR (u:User) ON (u.name);

-- Index on Family.familyId (for faster lookups)
CREATE INDEX familyId_index IF NOT EXISTS
FOR (f:Family) ON (f.familyId);

-- Index on Family.name (for name searches)
CREATE INDEX family_name_index IF NOT EXISTS
FOR (f:Family) ON (f.name);

-- Index on Family.createdBy (for finding families by creator)
CREATE INDEX family_createdBy_index IF NOT EXISTS
FOR (f:Family) ON (f.createdBy);

-- Composite index for User queries (userId + email)
CREATE INDEX user_id_email_index IF NOT EXISTS
FOR (u:User) ON (u.userId, u.email);

-- ==================== Health Record Constraints ====================
-- Ensure uniqueness of recordId
CREATE CONSTRAINT recordId_unique IF NOT EXISTS
FOR (hr:HealthRecord) REQUIRE hr.recordId IS UNIQUE;

-- Ensure uniqueness of reportId
CREATE CONSTRAINT reportId_unique IF NOT EXISTS
FOR (lr:LabReport) REQUIRE lr.reportId IS UNIQUE;

-- Ensure uniqueness of prescriptionId
CREATE CONSTRAINT prescriptionId_unique IF NOT EXISTS
FOR (p:Prescription) REQUIRE p.prescriptionId IS UNIQUE;

-- Ensure uniqueness of vaccinationId
CREATE CONSTRAINT vaccinationId_unique IF NOT EXISTS
FOR (v:Vaccination) REQUIRE v.vaccinationId IS UNIQUE;

-- ==================== Health Record Indexes ====================
-- Index on HealthRecord.recordId
CREATE INDEX health_record_recordId_index IF NOT EXISTS
FOR (hr:HealthRecord) ON (hr.recordId);

-- Index on HealthRecord.date (for date-based queries)
CREATE INDEX health_record_date_index IF NOT EXISTS
FOR (hr:HealthRecord) ON (hr.date);

-- Index on HealthRecord.type (for filtering by type)
CREATE INDEX health_record_type_index IF NOT EXISTS
FOR (hr:HealthRecord) ON (hr.type);

-- Index on LabReport.reportId
CREATE INDEX lab_report_reportId_index IF NOT EXISTS
FOR (lr:LabReport) ON (lr.reportId);

-- Index on LabReport.date
CREATE INDEX lab_report_date_index IF NOT EXISTS
FOR (lr:LabReport) ON (lr.date);

-- Index on LabReport.testName (for searching tests)
CREATE INDEX lab_report_testName_index IF NOT EXISTS
FOR (lr:LabReport) ON (lr.testName);

-- Index on Prescription.prescriptionId
CREATE INDEX prescription_prescriptionId_index IF NOT EXISTS
FOR (p:Prescription) ON (p.prescriptionId);

-- Index on Prescription.date
CREATE INDEX prescription_date_index IF NOT EXISTS
FOR (p:Prescription) ON (p.date);

-- Index on Vaccination.vaccinationId
CREATE INDEX vaccination_vaccinationId_index IF NOT EXISTS
FOR (v:Vaccination) ON (v.vaccinationId);

-- Index on Vaccination.vaccineName
CREATE INDEX vaccination_vaccineName_index IF NOT EXISTS
FOR (v:Vaccination) ON (v.vaccineName);

-- Index on Vaccination.nextDueDate (for upcoming vaccinations)
CREATE INDEX vaccination_nextDueDate_index IF NOT EXISTS
FOR (v:Vaccination) ON (v.nextDueDate);

-- ==================== Medical Entity Constraints ====================
-- Ensure uniqueness of medicationId
CREATE CONSTRAINT medicationId_unique IF NOT EXISTS
FOR (m:Medication) REQUIRE m.medicationId IS UNIQUE;

-- Ensure uniqueness of conditionId
CREATE CONSTRAINT conditionId_unique IF NOT EXISTS
FOR (c:Condition) REQUIRE c.conditionId IS UNIQUE;

-- Ensure uniqueness of symptomId
CREATE CONSTRAINT symptomId_unique IF NOT EXISTS
FOR (s:Symptom) REQUIRE s.symptomId IS UNIQUE;

-- ==================== Medical Entity Indexes ====================
-- Index on Medication.medicationId
CREATE INDEX medication_medicationId_index IF NOT EXISTS
FOR (m:Medication) ON (m.medicationId);

-- Index on Medication.name (for searching)
CREATE INDEX medication_name_index IF NOT EXISTS
FOR (m:Medication) ON (m.name);

-- Index on Condition.conditionId
CREATE INDEX condition_conditionId_index IF NOT EXISTS
FOR (c:Condition) ON (c.conditionId);

-- Index on Condition.name (for searching)
CREATE INDEX condition_name_index IF NOT EXISTS
FOR (c:Condition) ON (c.name);

-- Index on Condition.icdCode (for ICD code lookups)
CREATE INDEX condition_icdCode_index IF NOT EXISTS
FOR (c:Condition) ON (c.icdCode);

-- Index on Symptom.symptomId
CREATE INDEX symptom_symptomId_index IF NOT EXISTS
FOR (s:Symptom) ON (s.symptomId);

-- Index on Symptom.name (for searching)
CREATE INDEX symptom_name_index IF NOT EXISTS
FOR (s:Symptom) ON (s.name);

-- ==================== Provider Constraints ====================
-- Ensure uniqueness of doctorId
CREATE CONSTRAINT doctorId_unique IF NOT EXISTS
FOR (d:Doctor) REQUIRE d.doctorId IS UNIQUE;

-- Ensure uniqueness of hospitalId
CREATE CONSTRAINT hospitalId_unique IF NOT EXISTS
FOR (h:Hospital) REQUIRE h.hospitalId IS UNIQUE;

-- ==================== Provider Indexes ====================
-- Index on Doctor.doctorId
CREATE INDEX doctor_doctorId_index IF NOT EXISTS
FOR (d:Doctor) ON (d.doctorId);

-- Index on Doctor.specialty (for filtering by specialty)
CREATE INDEX doctor_specialty_index IF NOT EXISTS
FOR (d:Doctor) ON (d.specialty);

-- Index on Hospital.hospitalId
CREATE INDEX hospital_hospitalId_index IF NOT EXISTS
FOR (h:Hospital) ON (h.hospitalId);

-- Index on Hospital.name (for searching)
CREATE INDEX hospital_name_index IF NOT EXISTS
FOR (h:Hospital) ON (h.name);

-- Index on Hospital.location (for geospatial queries)
CREATE INDEX hospital_location_index IF NOT EXISTS
FOR (h:Hospital) ON (h.location);

-- ==================== Appointment Constraints ====================
-- Ensure uniqueness of appointmentId
CREATE CONSTRAINT appointmentId_unique IF NOT EXISTS
FOR (a:Appointment) REQUIRE a.appointmentId IS UNIQUE;

-- ==================== Appointment Indexes ====================
-- Index on Appointment.appointmentId
CREATE INDEX appointment_appointmentId_index IF NOT EXISTS
FOR (a:Appointment) ON (a.appointmentId);

-- Index on Appointment.dateTime (for date-based queries)
CREATE INDEX appointment_dateTime_index IF NOT EXISTS
FOR (a:Appointment) ON (a.dateTime);

-- Index on Appointment.status (for filtering by status)
CREATE INDEX appointment_status_index IF NOT EXISTS
FOR (a:Appointment) ON (a.status);

-- ==================== Growth Record Constraints ====================
-- Ensure uniqueness of GrowthRecord.recordId
CREATE CONSTRAINT growth_record_recordId_unique IF NOT EXISTS
FOR (gr:GrowthRecord) REQUIRE gr.recordId IS UNIQUE;

-- ==================== Growth Record Indexes ====================
-- Index on GrowthRecord.recordId
CREATE INDEX growth_record_recordId_index IF NOT EXISTS
FOR (gr:GrowthRecord) ON (gr.recordId);

-- Index on GrowthRecord.date (for date-based queries)
CREATE INDEX growth_record_date_index IF NOT EXISTS
FOR (gr:GrowthRecord) ON (gr.date);

-- ==================== Vital Sign Constraints ====================
-- Ensure uniqueness of vitalId
CREATE CONSTRAINT vitalId_unique IF NOT EXISTS
FOR (vs:VitalSign) REQUIRE vs.vitalId IS UNIQUE;

-- ==================== Vital Sign Indexes ====================
-- Index on VitalSign.vitalId
CREATE INDEX vital_sign_vitalId_index IF NOT EXISTS
FOR (vs:VitalSign) ON (vs.vitalId);

-- Index on VitalSign.date (for date-based queries)
CREATE INDEX vital_sign_date_index IF NOT EXISTS
FOR (vs:VitalSign) ON (vs.date);

-- Index on VitalSign.type (for filtering by type)
CREATE INDEX vital_sign_type_index IF NOT EXISTS
FOR (vs:VitalSign) ON (vs.type);

-- ==================== Full-Text Search Indexes ====================
-- Full-text index on HealthRecord (title, summary)
CREATE FULLTEXT INDEX health_record_text_index IF NOT EXISTS
FOR (hr:HealthRecord) ON EACH [hr.title, hr.summary];

-- Full-text index on Condition (name, description)
CREATE FULLTEXT INDEX condition_text_index IF NOT EXISTS
FOR (c:Condition) ON EACH [c.name, c.description];

-- Full-text index on Medication (name, genericName)
CREATE FULLTEXT INDEX medication_text_index IF NOT EXISTS
FOR (m:Medication) ON EACH [m.name, m.genericName];

-- Full-text index on ChatMessage (content)
CREATE FULLTEXT INDEX chat_message_text_index IF NOT EXISTS
FOR (cm:ChatMessage) ON EACH [cm.content];

-- ==================== Composite Indexes ====================
-- Composite index for HealthRecord queries (type, date)
CREATE INDEX health_record_type_date_index IF NOT EXISTS
FOR (hr:HealthRecord) ON (hr.type, hr.date);

-- Composite index for Appointment queries (status, dateTime)
CREATE INDEX appointment_status_datetime_index IF NOT EXISTS
FOR (a:Appointment) ON (a.status, a.dateTime);

-- Composite index for Conversation queries (status, startTime)
CREATE INDEX conversation_status_startTime_index IF NOT EXISTS
FOR (c:Conversation) ON (c.status, c.startTime);
