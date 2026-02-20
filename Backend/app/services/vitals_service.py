"""
Vitals Service
Aggregates vitals data from Neo4j, performs anomaly detection, and calculates risk scores.
Provides chart-ready trend data for the dashboard.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from app.schemas.vitals import (
    VitalRecordResponse,
    VitalTrendPoint,
    VitalTrendResponse,
    AnomalyAlert,
    AnomalyResponse,
    AnomalyLevel,
    RiskScoreItem,
    RiskScoreResponse as VitalsRiskScoreResponse,
    RiskCategory,
    LatestVitalsResponse,
    DashboardSummaryResponse,
    FamilyTimelineEntry,
    FamilyTimelineResponse,
)

logger = logging.getLogger(__name__)


# ==========================================
# CLINICAL REFERENCE RANGES
# ==========================================

CLINICAL_RANGES = {
    "blood_pressure_systolic": {
        "unit": "mmHg",
        "normal": (90, 120),
        "warning": (121, 139),
        "critical_high": 140,
        "critical_low": 89,
        "label": "Systolic BP",
    },
    "blood_pressure_diastolic": {
        "unit": "mmHg",
        "normal": (60, 80),
        "warning": (81, 89),
        "critical_high": 90,
        "critical_low": 59,
        "label": "Diastolic BP",
    },
    "heart_rate": {
        "unit": "bpm",
        "normal": (60, 100),
        "warning": (101, 120),
        "critical_high": 121,
        "critical_low": 49,
        "label": "Heart Rate",
    },
    "glucose": {
        "unit": "mg/dL",
        "normal": (70, 100),
        "warning": (101, 125),
        "critical_high": 126,
        "critical_low": 69,
        "label": "Fasting Glucose",
    },
    "temperature": {
        "unit": "°F",
        "normal": (97.0, 99.0),
        "warning": (99.1, 100.3),
        "critical_high": 100.4,
        "critical_low": 96.9,
        "label": "Temperature",
    },
    "oxygen_saturation": {
        "unit": "%",
        "normal": (95, 100),
        "warning": (90, 94),
        "critical_high": None,
        "critical_low": 89,
        "label": "SpO2",
    },
    "respiratory_rate": {
        "unit": "breaths/min",
        "normal": (12, 20),
        "warning": (21, 25),
        "critical_high": 26,
        "critical_low": 11,
        "label": "Respiratory Rate",
    },
    "bmi": {
        "unit": "kg/m²",
        "normal": (18.5, 24.9),
        "warning": (25.0, 29.9),
        "critical_high": 30.0,
        "critical_low": 18.4,
        "label": "BMI",
    },
    "weight": {
        "unit": "kg",
        "normal": (0, 999),  # No anomaly detection for weight alone
        "warning": (0, 0),
        "critical_high": None,
        "critical_low": None,
        "label": "Weight",
    },
}


class VitalsService:
    """Service for vitals tracking, anomaly detection, and risk scoring."""

    @staticmethod
    def _safe_str(val) -> str:
        """Convert neo4j.time.Date / DateTime / Time (or any object) to a plain string."""
        if val is None:
            return ""
        return str(val)

    @staticmethod
    def _sanitize_neo4j(obj):
        """Recursively convert any neo4j temporal types in dicts/lists to plain Python types."""
        if isinstance(obj, dict):
            return {k: VitalsService._sanitize_neo4j(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [VitalsService._sanitize_neo4j(item) for item in obj]
        # Check for neo4j temporal types by module name to avoid import issues
        type_module = getattr(type(obj), '__module__', '')
        if type_module.startswith('neo4j.time'):
            return str(obj)
        return obj

    # ==================== Anomaly Detection ====================

    def _classify_vital(self, vital_type: str, value: float) -> AnomalyLevel:
        """Classify a single vital sign reading as normal, warning, or critical."""
        ranges = CLINICAL_RANGES.get(vital_type)
        if not ranges:
            return AnomalyLevel.NORMAL

        normal_low, normal_high = ranges["normal"]
        critical_high = ranges.get("critical_high")
        critical_low = ranges.get("critical_low")

        # Critical check
        if critical_high is not None and value >= critical_high:
            return AnomalyLevel.CRITICAL
        if critical_low is not None and value <= critical_low:
            return AnomalyLevel.CRITICAL

        # Warning check
        warning = ranges.get("warning", (0, 0))
        if warning != (0, 0):
            warn_low, warn_high = warning
            if warn_low <= value <= warn_high:
                return AnomalyLevel.WARNING

        # Normal check
        if normal_low <= value <= normal_high:
            return AnomalyLevel.NORMAL

        # If outside normal but not in warning or critical, treat as warning
        return AnomalyLevel.WARNING

    def _build_anomaly_message(self, vital_type: str, value: float, level: AnomalyLevel) -> str:
        """Build a human-readable anomaly message."""
        ranges = CLINICAL_RANGES.get(vital_type, {})
        label = ranges.get("label", vital_type.replace("_", " ").title())
        unit = ranges.get("unit", "")
        normal = ranges.get("normal", (0, 0))

        if level == AnomalyLevel.CRITICAL:
            return f"⚠️ CRITICAL: {label} reading of {value} {unit} is significantly outside normal range ({normal[0]}-{normal[1]} {unit})"
        elif level == AnomalyLevel.WARNING:
            return f"⚡ WARNING: {label} reading of {value} {unit} is slightly elevated/low. Normal range: {normal[0]}-{normal[1]} {unit}"
        return f"✅ {label} is within normal range"

    # ==================== Vitals CRUD ====================

    def record_vital(
        self,
        user_id: str,
        vital_type: str,
        value: float,
        unit: str,
        date: str,
        time: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Optional[VitalRecordResponse]:
        """Record a new vital sign and return it with anomaly status."""
        from shared.database.neo4j.operations.vitals_ops import VitalsOperations
        from shared.database.neo4j.neo4j_client import Neo4jClient

        try:
            client = Neo4jClient()
            vitals_ops = VitalsOperations(client)
            result = vitals_ops.create_vital_sign(
                user_id=user_id,
                vital_type=vital_type,
                value=value,
                unit=unit,
                date=date,
                time=time,
                notes=notes,
            )

            if not result:
                return None

            status = self._classify_vital(vital_type, value)

            return VitalRecordResponse(
                vital_id=result.get("vitalId", ""),
                vital_type=vital_type,
                value=value,
                unit=unit,
                date=date,
                time=time,
                notes=notes,
                status=status,
            )
        except Exception as e:
            logger.error(f"Error recording vital: {e}")
            return None

    def record_blood_pressure(
        self,
        user_id: str,
        systolic: float,
        diastolic: float,
        date: str,
        heart_rate: Optional[float] = None,
        time: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> List[VitalRecordResponse]:
        """Record blood pressure (creates 2-3 vital nodes: systolic, diastolic, optional HR)."""
        results = []

        sys_result = self.record_vital(user_id, "blood_pressure_systolic", systolic, "mmHg", date, time, notes)
        if sys_result:
            results.append(sys_result)

        dia_result = self.record_vital(user_id, "blood_pressure_diastolic", diastolic, "mmHg", date, time, notes)
        if dia_result:
            results.append(dia_result)

        if heart_rate is not None:
            hr_result = self.record_vital(user_id, "heart_rate", heart_rate, "bpm", date, time, notes)
            if hr_result:
                results.append(hr_result)

        return results

    # ==================== Trend Data ====================

    def get_vitals_trend(
        self,
        user_id: str,
        vital_type: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> VitalTrendResponse:
        """Get chart-ready trend data for a specific vital type."""
        from shared.database.neo4j.operations.vitals_ops import VitalsOperations
        from shared.database.neo4j.neo4j_client import Neo4jClient

        try:
            client = Neo4jClient()
            vitals_ops = VitalsOperations(client)

            if start_date and end_date:
                raw_vitals = vitals_ops.get_vitals_in_range(user_id, vital_type, start_date, end_date)
            else:
                raw_vitals = vitals_ops.get_user_vitals(user_id, vital_type, limit=200)
                raw_vitals.reverse()  # Ascending order for charts

            ranges = CLINICAL_RANGES.get(vital_type, {})
            unit = ranges.get("unit", "")
            normal = ranges.get("normal", (0, 0))

            data_points = []
            values = []
            for v in raw_vitals:
                val = v.get("value", 0)
                values.append(val)
                d = self._safe_str(v.get("date", ""))
                t = self._safe_str(v.get("time")) if v.get("time") else None
                status = self._classify_vital(vital_type, val)
                data_points.append(VitalTrendPoint(date=d, time=t, value=val, status=status))

            # Compute statistics
            stats = {}
            if values:
                stats = {
                    "min": round(min(values), 1),
                    "max": round(max(values), 1),
                    "avg": round(sum(values) / len(values), 1),
                    "latest": round(values[-1], 1),
                    "count": len(values),
                }

            return VitalTrendResponse(
                user_id=user_id,
                vital_type=vital_type,
                unit=unit,
                data_points=data_points,
                statistics=stats,
                normal_range={"low": normal[0], "high": normal[1]},
                total_readings=len(data_points),
            )
        except Exception as e:
            logger.error(f"Error getting vitals trend: {e}")
            return VitalTrendResponse(user_id=user_id, vital_type=vital_type, unit="")

    # ==================== Anomaly Detection ====================

    def detect_anomalies(self, user_id: str, limit: int = 50) -> AnomalyResponse:
        """Detect all anomalous vital readings for a user."""
        from shared.database.neo4j.operations.vitals_ops import VitalsOperations
        from shared.database.neo4j.neo4j_client import Neo4jClient

        try:
            client = Neo4jClient()
            vitals_ops = VitalsOperations(client)
            raw_vitals = vitals_ops.get_user_vitals(user_id, limit=limit)

            alerts = []
            seen_types = set()  # deduplicate: one alert per vital type (most recent)
            for v in raw_vitals:
                vital_type = v.get("type", "")
                if vital_type in seen_types:
                    continue
                value = v.get("value", 0)
                level = self._classify_vital(vital_type, value)

                if level in (AnomalyLevel.WARNING, AnomalyLevel.CRITICAL):
                    ranges = CLINICAL_RANGES.get(vital_type, {})
                    normal = ranges.get("normal", (0, 0))
                    unit = ranges.get("unit", "")

                    alerts.append(AnomalyAlert(
                        vital_id=v.get("vitalId", ""),
                        vital_type=vital_type,
                        value=value,
                        unit=unit,
                        date=self._safe_str(v.get("date", "")),
                        level=level,
                        message=self._build_anomaly_message(vital_type, value, level),
                        normal_range=f"{normal[0]}-{normal[1]} {unit}",
                    ))
                seen_types.add(vital_type)

            critical = sum(1 for a in alerts if a.level == AnomalyLevel.CRITICAL)
            warning = sum(1 for a in alerts if a.level == AnomalyLevel.WARNING)

            return AnomalyResponse(
                user_id=user_id,
                alerts=alerts,
                total_alerts=len(alerts),
                critical_count=critical,
                warning_count=warning,
            )
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return AnomalyResponse(user_id=user_id)

    # ==================== Risk Scoring ====================

    def calculate_risk_scores(self, user_id: str) -> VitalsRiskScoreResponse:
        """Calculate health risk scores based on latest vitals."""
        from shared.database.neo4j.operations.vitals_ops import VitalsOperations
        from shared.database.neo4j.neo4j_client import Neo4jClient

        try:
            client = Neo4jClient()
            vitals_ops = VitalsOperations(client)
            latest = vitals_ops.get_latest_vitals(user_id)

            risk_scores = []

            sys_data = latest.get("blood_pressure_systolic", {})
            dia_data = latest.get("blood_pressure_diastolic", {})
            hr_data = latest.get("heart_rate", {})
            temp_data = latest.get("temperature", {})

            # --- Cardiovascular Risk (Systolic BP + Heart Rate) ---
            cv_factors = []
            cv_score = 0
            if sys_data:
                sys_val = sys_data.get("value", 0)
                if sys_val >= 140:
                    cv_score += 50
                    cv_factors.append(f"High systolic BP: {sys_val} mmHg")
                elif sys_val >= 130:
                    cv_score += 35
                    cv_factors.append(f"Elevated systolic BP: {sys_val} mmHg")
                elif sys_val >= 121:
                    cv_score += 15
                    cv_factors.append(f"Borderline high systolic BP: {sys_val} mmHg")
                elif sys_val < 90 and sys_val > 0:
                    cv_score += 40
                    cv_factors.append(f"Low systolic BP (hypotension): {sys_val} mmHg")
                elif sys_val < 100 and sys_val > 0:
                    cv_score += 20
                    cv_factors.append(f"Borderline low systolic BP: {sys_val} mmHg")

            if hr_data:
                hr_val = hr_data.get("value", 0)
                if hr_val > 120 or hr_val < 40:
                    cv_score += 40
                    cv_factors.append(f"Critical heart rate: {hr_val} bpm")
                elif hr_val > 100 or hr_val < 50:
                    cv_score += 20
                    cv_factors.append(f"Abnormal heart rate: {hr_val} bpm")

            cv_level = (
                AnomalyLevel.CRITICAL if cv_score >= 50
                else AnomalyLevel.WARNING if cv_score >= 20
                else AnomalyLevel.NORMAL
            )
            cv_rec = (
                "Consult a cardiologist immediately" if cv_score >= 50
                else "Monitor blood pressure and heart rate regularly" if cv_score >= 20
                else "Cardiovascular health within normal parameters"
            )
            risk_scores.append(RiskScoreItem(
                category=RiskCategory.CARDIOVASCULAR,
                score=min(cv_score, 100),
                level=cv_level,
                contributing_factors=cv_factors,
                recommendation=cv_rec,
            ))

            # --- Hypertension Risk (Systolic + Diastolic BP) ---
            ht_factors = []
            ht_score = 0
            if sys_data:
                sys_val = sys_data.get("value", 0)
                if sys_val >= 140:
                    ht_score += 50
                    ht_factors.append(f"Stage 2 hypertension: {sys_val} mmHg")
                elif sys_val >= 130:
                    ht_score += 30
                    ht_factors.append(f"Stage 1 hypertension: {sys_val} mmHg")
                elif sys_val >= 121:
                    ht_score += 15
                    ht_factors.append(f"Elevated blood pressure: {sys_val} mmHg")
                elif sys_val < 90 and sys_val > 0:
                    ht_score += 35
                    ht_factors.append(f"Critically low systolic BP (hypotension): {sys_val} mmHg")

            if dia_data:
                dia_val = dia_data.get("value", 0)
                if dia_val >= 90:
                    ht_score += 40
                    ht_factors.append(f"High diastolic BP: {dia_val} mmHg")
                elif dia_val >= 81:
                    ht_score += 20
                    ht_factors.append(f"Elevated diastolic BP: {dia_val} mmHg")
                elif dia_val < 60 and dia_val > 0:
                    ht_score += 35
                    ht_factors.append(f"Critically low diastolic BP: {dia_val} mmHg")
                elif dia_val < 70 and dia_val > 0:
                    ht_score += 15
                    ht_factors.append(f"Low diastolic BP: {dia_val} mmHg")

            ht_level = (
                AnomalyLevel.CRITICAL if ht_score >= 50
                else AnomalyLevel.WARNING if ht_score >= 20
                else AnomalyLevel.NORMAL
            )
            ht_rec = (
                "Seek immediate medical attention for blood pressure abnormality" if ht_score >= 50
                else "Monitor blood pressure closely, consult your doctor" if ht_score >= 20
                else "Blood pressure within healthy range"
            )
            risk_scores.append(RiskScoreItem(
                category=RiskCategory.HYPERTENSION,
                score=min(ht_score, 100),
                level=ht_level,
                contributing_factors=ht_factors,
                recommendation=ht_rec,
            ))

            # --- Fever Risk (Temperature) ---
            fv_factors = []
            fv_score = 0
            if temp_data:
                temp_val = temp_data.get("value", 0)
                if temp_val >= 103:
                    fv_score += 80
                    fv_factors.append(f"High fever: {temp_val} °F")
                elif temp_val >= 101:
                    fv_score += 55
                    fv_factors.append(f"Moderate fever: {temp_val} °F")
                elif temp_val >= 99.5:
                    fv_score += 30
                    fv_factors.append(f"Low-grade fever: {temp_val} °F")
                elif temp_val < 96 and temp_val > 0:
                    fv_score += 50
                    fv_factors.append(f"Hypothermia risk: {temp_val} °F")
                elif temp_val < 97 and temp_val > 0:
                    fv_score += 20
                    fv_factors.append(f"Below normal temperature: {temp_val} °F")

            fv_level = (
                AnomalyLevel.CRITICAL if fv_score >= 50
                else AnomalyLevel.WARNING if fv_score >= 20
                else AnomalyLevel.NORMAL
            )
            fv_rec = (
                "Seek medical attention immediately for high fever" if fv_score >= 50
                else "Rest, stay hydrated, monitor temperature" if fv_score >= 20
                else "Body temperature within normal range"
            )
            risk_scores.append(RiskScoreItem(
                category=RiskCategory.FEVER,
                score=min(fv_score, 100),
                level=fv_level,
                contributing_factors=fv_factors,
                recommendation=fv_rec,
            ))

            # --- Heart Rate Risk ---
            hr_factors = []
            hr_score = 0
            if hr_data:
                hr_val = hr_data.get("value", 0)
                if hr_val > 120 or hr_val < 40:
                    hr_score += 70
                    hr_factors.append(f"Critical heart rate: {hr_val} bpm")
                elif hr_val > 100:
                    hr_score += 40
                    hr_factors.append(f"Tachycardia (fast heart rate): {hr_val} bpm")
                elif hr_val < 50:
                    hr_score += 35
                    hr_factors.append(f"Bradycardia (slow heart rate): {hr_val} bpm")
                elif hr_val > 90:
                    hr_score += 15
                    hr_factors.append(f"Slightly elevated heart rate: {hr_val} bpm")

            hr_level = (
                AnomalyLevel.CRITICAL if hr_score >= 50
                else AnomalyLevel.WARNING if hr_score >= 20
                else AnomalyLevel.NORMAL
            )
            hr_rec = (
                "Seek immediate medical attention for abnormal heart rate" if hr_score >= 50
                else "Monitor heart rate, avoid strenuous activity" if hr_score >= 20
                else "Heart rate within normal parameters"
            )
            risk_scores.append(RiskScoreItem(
                category=RiskCategory.HEART_RATE,
                score=min(hr_score, 100),
                level=hr_level,
                contributing_factors=hr_factors,
                recommendation=hr_rec,
            ))

            # Overall risk
            max_score = max((r.score for r in risk_scores), default=0)
            overall = (
                AnomalyLevel.CRITICAL if max_score >= 50
                else AnomalyLevel.WARNING if max_score >= 20
                else AnomalyLevel.NORMAL
            )

            return VitalsRiskScoreResponse(
                user_id=user_id,
                risk_scores=risk_scores,
                overall_risk_level=overall,
                generated_at=datetime.now(timezone.utc),
            )
        except Exception as e:
            logger.error(f"Error calculating risk scores: {e}")
            return VitalsRiskScoreResponse(
                user_id=user_id,
                overall_risk_level=AnomalyLevel.NORMAL,
                generated_at=datetime.now(timezone.utc),
            )

    # ==================== Latest Vitals ====================

    def get_latest_vitals(self, user_id: str) -> LatestVitalsResponse:
        """Get the most recent reading for each vital type."""
        from shared.database.neo4j.operations.vitals_ops import VitalsOperations
        from shared.database.neo4j.neo4j_client import Neo4jClient

        try:
            client = Neo4jClient()
            vitals_ops = VitalsOperations(client)
            latest = vitals_ops.get_latest_vitals(user_id)

            vitals_map = {}
            for vtype, vdata in latest.items():
                value = vdata.get("value", 0)
                ranges = CLINICAL_RANGES.get(vtype, {})
                unit = ranges.get("unit", vdata.get("unit", ""))
                status = self._classify_vital(vtype, value)

                vitals_map[vtype] = VitalRecordResponse(
                    vital_id=vdata.get("vitalId", ""),
                    vital_type=vtype,
                    value=value,
                    unit=unit,
                    date=self._safe_str(vdata.get("date", "")),
                    time=self._safe_str(vdata.get("time")) if vdata.get("time") else None,
                    notes=vdata.get("notes"),
                    status=status,
                )

            return LatestVitalsResponse(
                user_id=user_id,
                vitals=vitals_map,
                last_updated=datetime.now(timezone.utc),
            )
        except Exception as e:
            logger.error(f"Error getting latest vitals: {e}")
            return LatestVitalsResponse(user_id=user_id)

    # ==================== Family Timeline ====================

    def get_family_timeline(
        self, family_id: str, limit: int = 50
    ) -> FamilyTimelineResponse:
        """Get unified family health timeline from PostgreSQL health events."""
        from shared.database.postgres.postgres_client import PostgresClient
        from shared.database.postgres.models import HealthEvent, User
        from shared.database.neo4j.operations.family_ops import FamilyOperations

        try:
            # Get family members from Neo4j
            family_ops = FamilyOperations()
            members = family_ops.get_family_members(family_id)
            member_ids = [m.get("userId") for m in members if m.get("userId")]

            if not member_ids:
                return FamilyTimelineResponse(family_id=family_id)

            # Get health events for all members from PostgreSQL
            with PostgresClient() as db:
                session = db.get_session()
                events = (
                    session.query(HealthEvent)
                    .filter(HealthEvent.user_id.in_(member_ids))
                    .order_by(HealthEvent.event_date.desc())
                    .limit(limit)
                    .all()
                )

                # Build a map of user names
                users = session.query(User).filter(User.user_id.in_(member_ids)).all()
                name_map = {}
                for u in users:
                    name = f"{u.first_name or ''} {u.last_name or ''}".strip()
                    name_map[u.user_id] = name or u.email

                entries = []
                for e in events:
                    entries.append(FamilyTimelineEntry(
                        user_id=e.user_id,
                        user_name=name_map.get(e.user_id, "Unknown"),
                        event_type=e.event_type,
                        title=e.title,
                        description=e.description,
                        date=e.event_date.isoformat() if e.event_date else "",
                        severity=e.severity,
                    ))

                return FamilyTimelineResponse(
                    family_id=family_id,
                    entries=entries,
                    total=len(entries),
                )
        except Exception as e:
            logger.error(f"Error getting family timeline: {e}")
            return FamilyTimelineResponse(family_id=family_id)

    # ==================== Dashboard Summary ====================

    def get_dashboard_summary(self, user_id: str) -> DashboardSummaryResponse:
        """Aggregate all dashboard data for a user."""
        try:
            latest = self.get_latest_vitals(user_id)
            anomalies = self.detect_anomalies(user_id, limit=10)
            risk = self.calculate_risk_scores(user_id)

            # Get active medications from Neo4j
            active_meds = []
            try:
                from shared.database.neo4j.operations.medication_ops import MedicationOperations
                from shared.database.neo4j.neo4j_client import Neo4jClient
                client = Neo4jClient()
                med_ops = MedicationOperations(client)
                meds = med_ops.get_user_medications(user_id, status="active")
                active_meds = meds if meds else []
            except Exception as e:
                logger.warning(f"Could not load medications: {e}")

            # Get upcoming appointments from Neo4j
            upcoming = []
            try:
                from shared.database.neo4j.operations.appointment_ops import AppointmentOperations
                from shared.database.neo4j.neo4j_client import Neo4jClient
                client = Neo4jClient()
                appt_ops = AppointmentOperations(client)
                appointments = appt_ops.get_upcoming_appointments(user_id, limit=5)
                upcoming = appointments if appointments else []
            except Exception as e:
                logger.warning(f"Could not load appointments: {e}")

            # Convert latest vitals to dict for response
            vitals_dict = {}
            for vtype, vresp in latest.vitals.items():
                vitals_dict[vtype] = {
                    "value": vresp.value,
                    "unit": vresp.unit,
                    "date": self._safe_str(vresp.date) if vresp.date else None,
                    "status": vresp.status.value if hasattr(vresp.status, 'value') else str(vresp.status),
                }

            return DashboardSummaryResponse(
                user_id=user_id,
                latest_vitals=vitals_dict,
                active_medications=self._sanitize_neo4j(active_meds),
                upcoming_appointments=self._sanitize_neo4j(upcoming),
                recent_anomalies=anomalies.alerts[:5],
                risk_scores=risk.risk_scores,
                overall_health_status=risk.overall_risk_level,
            )
        except Exception as e:
            logger.error(f"Error building dashboard summary: {e}")
            return DashboardSummaryResponse(user_id=user_id)


# Singleton instance
vitals_service = VitalsService()
