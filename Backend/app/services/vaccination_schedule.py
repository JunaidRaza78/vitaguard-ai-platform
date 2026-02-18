"""
Vaccination Schedule Service
CDC-based vaccination schedule tracking for family members.
Provides schedule lookups, due/overdue detection, and reminder generation.
"""

import logging
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


# ==========================================
# CDC VACCINATION SCHEDULE (Simplified)
# ==========================================

CDC_SCHEDULE = [
    # (vaccine_name, dose, age_months_min, age_months_max, description)
    ("Hepatitis B", "Dose 1", 0, 1, "Birth dose"),
    ("Hepatitis B", "Dose 2", 1, 4, "1-2 months"),
    ("Hepatitis B", "Dose 3", 6, 18, "6-18 months"),
    ("Rotavirus", "Dose 1", 2, 3, "2 months"),
    ("Rotavirus", "Dose 2", 4, 5, "4 months"),
    ("Rotavirus", "Dose 3", 6, 7, "6 months"),
    ("DTaP", "Dose 1", 2, 3, "2 months"),
    ("DTaP", "Dose 2", 4, 5, "4 months"),
    ("DTaP", "Dose 3", 6, 7, "6 months"),
    ("DTaP", "Dose 4", 15, 18, "15-18 months"),
    ("DTaP", "Dose 5", 48, 72, "4-6 years"),
    ("Hib", "Dose 1", 2, 3, "2 months"),
    ("Hib", "Dose 2", 4, 5, "4 months"),
    ("Hib", "Dose 3", 6, 7, "6 months (if needed)"),
    ("Hib", "Dose 4", 12, 15, "12-15 months"),
    ("PCV13", "Dose 1", 2, 3, "2 months"),
    ("PCV13", "Dose 2", 4, 5, "4 months"),
    ("PCV13", "Dose 3", 6, 7, "6 months"),
    ("PCV13", "Dose 4", 12, 15, "12-15 months"),
    ("IPV", "Dose 1", 2, 3, "2 months"),
    ("IPV", "Dose 2", 4, 5, "4 months"),
    ("IPV", "Dose 3", 6, 18, "6-18 months"),
    ("IPV", "Dose 4", 48, 72, "4-6 years"),
    ("Influenza", "Annual", 6, 216, "6 months+, annually"),
    ("MMR", "Dose 1", 12, 15, "12-15 months"),
    ("MMR", "Dose 2", 48, 72, "4-6 years"),
    ("Varicella", "Dose 1", 12, 15, "12-15 months"),
    ("Varicella", "Dose 2", 48, 72, "4-6 years"),
    ("Hepatitis A", "Dose 1", 12, 23, "12-23 months"),
    ("Hepatitis A", "Dose 2", 18, 42, "6 months after dose 1"),
    ("Tdap", "Dose 1", 132, 156, "11-12 years"),
    ("HPV", "Dose 1", 108, 156, "9-12 years"),
    ("HPV", "Dose 2", 114, 180, "6-12 months after dose 1"),
    ("Meningococcal", "Dose 1", 132, 156, "11-12 years"),
    ("Meningococcal", "Booster", 192, 204, "16-17 years"),
    # Adult vaccinations
    ("Flu", "Annual", 216, 9999, "Adults, annually"),
    ("COVID-19", "Updated dose", 216, 9999, "Adults, per CDC guidance"),
    ("Shingles", "Dose 1", 600, 9999, "50+ years"),
    ("Shingles", "Dose 2", 602, 9999, "2-6 months after dose 1"),
    ("Pneumococcal", "Dose 1", 780, 9999, "65+ years"),
]


class VaccinationService:
    """Service for vaccination schedule tracking and reminders."""

    def get_age_months(self, birth_date: str) -> int:
        """Calculate age in months from birth date string."""
        try:
            if isinstance(birth_date, str):
                bd = datetime.strptime(birth_date, "%Y-%m-%d").date()
            else:
                bd = birth_date
            today = date.today()
            return (today.year - bd.year) * 12 + (today.month - bd.month)
        except Exception:
            return -1

    def get_schedule_for_age(self, age_months: int) -> List[Dict[str, Any]]:
        """Get all vaccinations applicable for a given age."""
        applicable = []
        for vaccine, dose, age_min, age_max, desc in CDC_SCHEDULE:
            if age_min <= age_months <= age_max:
                applicable.append({
                    "vaccine": vaccine,
                    "dose": dose,
                    "age_range_months": f"{age_min}-{age_max}",
                    "description": desc,
                    "status": "due",
                })
        return applicable

    def get_upcoming_vaccinations(
        self, birth_date: str, completed_vaccines: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get upcoming/due/overdue vaccinations for a person."""
        age_months = self.get_age_months(birth_date)
        if age_months < 0:
            return {"error": "Invalid birth date", "vaccines": []}

        completed = set(completed_vaccines or [])

        due = []
        upcoming = []
        overdue = []

        for vaccine, dose, age_min, age_max, desc in CDC_SCHEDULE:
            key = f"{vaccine} - {dose}"
            if key in completed:
                continue

            if age_months > age_max:
                overdue.append({
                    "vaccine": vaccine,
                    "dose": dose,
                    "description": desc,
                    "status": "overdue",
                    "was_due_at_months": age_max,
                })
            elif age_min <= age_months <= age_max:
                due.append({
                    "vaccine": vaccine,
                    "dose": dose,
                    "description": desc,
                    "status": "due",
                    "due_at_months": age_min,
                })
            elif age_months < age_min and age_min - age_months <= 6:
                upcoming.append({
                    "vaccine": vaccine,
                    "dose": dose,
                    "description": desc,
                    "status": "upcoming",
                    "due_at_months": age_min,
                    "months_until_due": age_min - age_months,
                })

        return {
            "age_months": age_months,
            "overdue": overdue,
            "due": due,
            "upcoming": upcoming,
            "total_overdue": len(overdue),
            "total_due": len(due),
            "total_upcoming": len(upcoming),
        }

    def generate_vaccination_reminders(self, family_id: str) -> List[Dict[str, Any]]:
        """Generate vaccination reminder notifications for all family members."""
        reminders = []
        try:
            from shared.database.neo4j.operations.family_ops import FamilyOperations
            family_ops = FamilyOperations()
            members = family_ops.get_family_members(family_id)

            for member in members:
                birth_date = member.get("dateOfBirth") or member.get("birthDate")
                if not birth_date:
                    continue

                user_id = member.get("userId", "")
                name = member.get("name", "Unknown")
                vacc_data = self.get_upcoming_vaccinations(birth_date)

                for v in vacc_data.get("due", []):
                    reminders.append({
                        "user_id": user_id,
                        "user_name": name,
                        "type": "vaccination_due",
                        "title": f"💉 {v['vaccine']} ({v['dose']}) due for {name}",
                        "message": f"{v['vaccine']} {v['dose']} is due. {v['description']}",
                        "priority": "high",
                    })

                for v in vacc_data.get("overdue", []):
                    reminders.append({
                        "user_id": user_id,
                        "user_name": name,
                        "type": "vaccination_overdue",
                        "title": f"⚠️ OVERDUE: {v['vaccine']} ({v['dose']}) for {name}",
                        "message": f"{v['vaccine']} {v['dose']} was due at {v['was_due_at_months']} months. Please schedule immediately.",
                        "priority": "urgent",
                    })

        except Exception as e:
            logger.error(f"Error generating vaccination reminders: {e}")

        return reminders


# Singleton
vaccination_service = VaccinationService()
