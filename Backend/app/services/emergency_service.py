"""
Emergency Detection Service
Analyzes chat messages and vitals for emergency indicators.
Triggers urgent notifications and provides emergency response guidance.
"""

import logging
import re
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


# ==========================================
# EMERGENCY KEYWORDS & PATTERNS
# ==========================================

EMERGENCY_KEYWORDS = {
    "critical": [
        "heart attack", "cardiac arrest", "stroke", "seizure", "anaphylaxis",
        "can't breathe", "cannot breathe", "difficulty breathing", "choking",
        "severe bleeding", "hemorrhage", "unconscious", "unresponsive",
        "overdose", "poisoning", "suicide", "suicidal", "chest pain",
        "severe allergic reaction", "not breathing", "loss of consciousness",
    ],
    "urgent": [
        "high fever", "fever over 104", "severe headache", "worst headache",
        "sudden numbness", "sudden weakness", "slurred speech", "vision loss",
        "severe abdominal pain", "coughing blood", "blood in stool",
        "broken bone", "fracture", "deep cut", "severe burn",
        "allergic reaction", "swelling throat", "fainting", "passed out",
        "diabetic emergency", "low blood sugar", "high blood sugar",
    ],
    "moderate": [
        "persistent pain", "high blood pressure", "rapid heartbeat",
        "shortness of breath", "dizziness", "vomiting blood",
        "severe nausea", "dehydration", "confusion", "disorientation",
    ],
}

EMERGENCY_VITAL_THRESHOLDS = {
    "blood_pressure_systolic": {"critical_high": 180, "critical_low": 70},
    "blood_pressure_diastolic": {"critical_high": 120, "critical_low": 40},
    "heart_rate": {"critical_high": 150, "critical_low": 40},
    "oxygen_saturation": {"critical_low": 90},
    "temperature": {"critical_high": 104.0, "critical_low": 95.0},
    "respiratory_rate": {"critical_high": 30, "critical_low": 8},
    "glucose": {"critical_high": 400, "critical_low": 50},
}


class EmergencyService:
    """Service for detecting medical emergencies from text and vitals."""

    def analyze_message(self, message: str) -> Dict[str, Any]:
        """
        Analyze a chat message for emergency indicators.
        Returns severity level and emergency response if detected.
        """
        message_lower = message.lower()
        detected = {"critical": [], "urgent": [], "moderate": []}

        for level, keywords in EMERGENCY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in message_lower:
                    detected[level].append(keyword)

        if detected["critical"]:
            return {
                "is_emergency": True,
                "severity": "critical",
                "detected_keywords": detected["critical"],
                "response": self._get_emergency_response("critical", detected["critical"]),
                "call_911": True,
            }
        elif detected["urgent"]:
            return {
                "is_emergency": True,
                "severity": "urgent",
                "detected_keywords": detected["urgent"],
                "response": self._get_emergency_response("urgent", detected["urgent"]),
                "call_911": False,
            }
        elif detected["moderate"]:
            return {
                "is_emergency": False,
                "severity": "moderate",
                "detected_keywords": detected["moderate"],
                "response": self._get_emergency_response("moderate", detected["moderate"]),
                "call_911": False,
            }

        return {
            "is_emergency": False,
            "severity": "none",
            "detected_keywords": [],
            "response": None,
            "call_911": False,
        }

    def check_vital_emergency(self, vital_type: str, value: float) -> Dict[str, Any]:
        """Check if a vital sign value is at emergency level."""
        thresholds = EMERGENCY_VITAL_THRESHOLDS.get(vital_type)
        if not thresholds:
            return {"is_emergency": False, "severity": "none"}

        critical_high = thresholds.get("critical_high")
        critical_low = thresholds.get("critical_low")

        if critical_high and value >= critical_high:
            return {
                "is_emergency": True,
                "severity": "critical",
                "message": f"⚠️ EMERGENCY: {vital_type.replace('_', ' ').title()} is critically high at {value}. Seek immediate medical attention.",
                "call_911": True,
            }
        elif critical_low and value <= critical_low:
            return {
                "is_emergency": True,
                "severity": "critical",
                "message": f"⚠️ EMERGENCY: {vital_type.replace('_', ' ').title()} is critically low at {value}. Seek immediate medical attention.",
                "call_911": True,
            }

        return {"is_emergency": False, "severity": "none"}

    def _get_emergency_response(self, severity: str, keywords: List[str]) -> str:
        """Generate appropriate emergency response message."""
        keyword_str = ", ".join(keywords[:3])

        if severity == "critical":
            return (
                f"🚨 **MEDICAL EMERGENCY DETECTED**\n\n"
                f"Keywords detected: {keyword_str}\n\n"
                f"**CALL 911 (or your local emergency number) IMMEDIATELY.**\n\n"
                f"While waiting for help:\n"
                f"• Stay calm and stay with the person\n"
                f"• Do not move them unless in danger\n"
                f"• If trained, perform CPR if the person is not breathing\n"
                f"• Keep airways clear\n"
                f"• Note the time symptoms started\n\n"
                f"⚠️ This is an AI system — it cannot replace emergency medical services."
            )
        elif severity == "urgent":
            return (
                f"🔴 **URGENT MEDICAL CONCERN**\n\n"
                f"Indicators detected: {keyword_str}\n\n"
                f"**Seek medical attention immediately:**\n"
                f"• Visit your nearest emergency room or urgent care\n"
                f"• Call your doctor's emergency line\n"
                f"• If symptoms worsen, call 911\n\n"
                f"⚠️ This AI provides guidance only — consult a medical professional."
            )
        else:
            return (
                f"🟡 **Health Concern Noted**\n\n"
                f"Indicators: {keyword_str}\n\n"
                f"• Contact your healthcare provider within 24 hours\n"
                f"• Monitor symptoms closely\n"
                f"• If symptoms worsen, seek immediate care\n\n"
                f"I can still answer your medical questions, but please consult a doctor."
            )

    def create_emergency_notification(
        self, user_id: str, severity: str, message: str
    ) -> Optional[Dict]:
        """Create an urgent notification for emergency detection."""
        try:
            from app.services.notification_service import notification_service
            from app.schemas.notification import NotificationType, NotificationPriority

            priority = NotificationPriority.URGENT if severity == "critical" else NotificationPriority.HIGH
            n_type = NotificationType.HEALTH_ALERT

            result = notification_service.create_notification(
                user_id=user_id,
                notification_type=n_type,
                title=f"🚨 Emergency Alert — {severity.upper()}",
                message=message,
                priority=priority,
            )
            return result
        except Exception as e:
            logger.error(f"Error creating emergency notification: {e}")
            return None


# Singleton
emergency_service = EmergencyService()
