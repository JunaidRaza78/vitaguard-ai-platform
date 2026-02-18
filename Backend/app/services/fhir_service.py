"""
FHIR R4 Interoperability Service
Converts internal health data to/from FHIR R4 resources.
Supports Patient, Observation, MedicationStatement, and Condition resources.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class FHIRService:
    """Service for FHIR R4 data interoperability."""

    # ==========================================
    # EXPORT (Internal -> FHIR)
    # ==========================================

    def create_patient_resource(self, user: Dict) -> Dict:
        """Convert internal user to FHIR Patient resource."""
        return {
            "resourceType": "Patient",
            "id": user.get("user_id", str(uuid.uuid4())),
            "meta": {"lastUpdated": datetime.now(timezone.utc).isoformat()},
            "active": True,
            "name": [{
                "use": "official",
                "family": user.get("last_name", ""),
                "given": [user.get("first_name", "")],
            }],
            "gender": user.get("gender", "unknown"),
            "birthDate": user.get("date_of_birth", ""),
            "telecom": [
                {"system": "email", "value": user.get("email", ""), "use": "home"}
            ] if user.get("email") else [],
        }

    def create_observation_resource(
        self, vital: Dict, patient_id: str
    ) -> Dict:
        """Convert a vital sign reading to FHIR Observation resource."""
        # LOINC codes for common vitals
        loinc_map = {
            "blood_pressure_systolic": {"code": "8480-6", "display": "Systolic blood pressure"},
            "blood_pressure_diastolic": {"code": "8462-4", "display": "Diastolic blood pressure"},
            "heart_rate": {"code": "8867-4", "display": "Heart rate"},
            "temperature": {"code": "8310-5", "display": "Body temperature"},
            "oxygen_saturation": {"code": "2708-6", "display": "Oxygen saturation"},
            "respiratory_rate": {"code": "9279-1", "display": "Respiratory rate"},
            "weight": {"code": "29463-7", "display": "Body weight"},
            "bmi": {"code": "39156-5", "display": "Body mass index"},
            "glucose": {"code": "2339-0", "display": "Glucose"},
        }

        vital_type = vital.get("vital_type", "")
        loinc = loinc_map.get(vital_type, {"code": "unknown", "display": vital_type})

        observation = {
            "resourceType": "Observation",
            "id": vital.get("vital_id", str(uuid.uuid4())),
            "status": "final",
            "category": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "vital-signs",
                    "display": "Vital Signs",
                }]
            }],
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": loinc["code"],
                    "display": loinc["display"],
                }]
            },
            "subject": {"reference": f"Patient/{patient_id}"},
            "effectiveDateTime": vital.get("date", ""),
            "valueQuantity": {
                "value": vital.get("value", 0),
                "unit": vital.get("unit", ""),
                "system": "http://unitsofmeasure.org",
            },
        }
        return observation

    def create_medication_statement(
        self, medication: Dict, patient_id: str
    ) -> Dict:
        """Convert medication to FHIR MedicationStatement resource."""
        return {
            "resourceType": "MedicationStatement",
            "id": medication.get("medication_id", str(uuid.uuid4())),
            "status": "active",
            "medicationCodeableConcept": {
                "text": medication.get("medication_name", ""),
            },
            "subject": {"reference": f"Patient/{patient_id}"},
            "dosage": [{
                "text": medication.get("dosage", ""),
                "timing": {"code": {"text": medication.get("frequency", "")}},
            }],
        }

    def create_condition_resource(
        self, condition: Dict, patient_id: str
    ) -> Dict:
        """Convert a health condition to FHIR Condition resource."""
        return {
            "resourceType": "Condition",
            "id": str(uuid.uuid4()),
            "clinicalStatus": {
                "coding": [{"code": condition.get("status", "active")}]
            },
            "code": {"text": condition.get("name", "")},
            "subject": {"reference": f"Patient/{patient_id}"},
            "onsetDateTime": condition.get("onset_date", ""),
            "note": [{"text": condition.get("notes", "")}] if condition.get("notes") else [],
        }

    def create_bundle(self, resources: List[Dict]) -> Dict:
        """Create a FHIR Bundle containing multiple resources."""
        return {
            "resourceType": "Bundle",
            "id": str(uuid.uuid4()),
            "type": "collection",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total": len(resources),
            "entry": [
                {"resource": r, "fullUrl": f"urn:uuid:{r.get('id', '')}"}
                for r in resources
            ],
        }

    # ==========================================
    # IMPORT (FHIR -> Internal)
    # ==========================================

    def parse_patient(self, fhir_patient: Dict) -> Dict:
        """Parse FHIR Patient resource into internal format."""
        names = fhir_patient.get("name", [{}])
        name = names[0] if names else {}
        emails = [t["value"] for t in fhir_patient.get("telecom", []) if t.get("system") == "email"]

        return {
            "fhir_id": fhir_patient.get("id", ""),
            "first_name": name.get("given", [""])[0] if name.get("given") else "",
            "last_name": name.get("family", ""),
            "gender": fhir_patient.get("gender", ""),
            "date_of_birth": fhir_patient.get("birthDate", ""),
            "email": emails[0] if emails else "",
        }

    def parse_observation(self, fhir_obs: Dict) -> Dict:
        """Parse FHIR Observation resource into internal vital format."""
        value_qty = fhir_obs.get("valueQuantity", {})
        code = fhir_obs.get("code", {}).get("coding", [{}])[0]
        return {
            "fhir_id": fhir_obs.get("id", ""),
            "vital_type": code.get("display", ""),
            "value": value_qty.get("value", 0),
            "unit": value_qty.get("unit", ""),
            "date": fhir_obs.get("effectiveDateTime", ""),
        }

    def export_user_data(self, user_id: str) -> Dict:
        """Export all user health data as a FHIR Bundle."""
        resources = []
        try:
            from shared.database.neo4j.operations.vitals_ops import VitalsOperations
            from shared.database.neo4j.neo4j_client import Neo4jClient

            client = Neo4jClient()
            vitals_ops = VitalsOperations(client)

            # Export vitals as Observations
            latest = vitals_ops.get_latest_vitals(user_id)
            for vtype, vdata in latest.items():
                obs = self.create_observation_resource(
                    {"vital_type": vtype, **vdata}, user_id
                )
                resources.append(obs)

        except Exception as e:
            logger.error(f"Error exporting user data: {e}")

        return self.create_bundle(resources)


# Singleton
fhir_service = FHIRService()
