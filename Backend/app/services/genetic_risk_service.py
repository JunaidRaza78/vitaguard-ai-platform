"""
Genetic Risk Service
Analyzes family health history to calculate hereditary risk factors.
Provides risk assessments for common hereditary conditions.
"""

import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


# ==========================================
# HEREDITARY CONDITIONS & RISK FACTORS
# ==========================================

HEREDITARY_CONDITIONS = {
    "heart_disease": {
        "name": "Heart Disease",
        "keywords": ["heart disease", "heart attack", "coronary artery", "cardiac arrest", "cardiovascular"],
        "base_risk": 0.10,
        "first_degree_multiplier": 2.5,
        "second_degree_multiplier": 1.5,
        "recommendation": "Regular cardiovascular screening, lipid panels, exercise, and heart-healthy diet.",
    },
    "diabetes_type2": {
        "name": "Type 2 Diabetes",
        "keywords": ["diabetes", "type 2 diabetes", "high blood sugar", "insulin resistance"],
        "base_risk": 0.08,
        "first_degree_multiplier": 3.0,
        "second_degree_multiplier": 1.8,
        "recommendation": "Regular glucose monitoring, HbA1c tests, maintain healthy weight, balanced diet.",
    },
    "breast_cancer": {
        "name": "Breast Cancer",
        "keywords": ["breast cancer", "brca"],
        "base_risk": 0.12,
        "first_degree_multiplier": 2.0,
        "second_degree_multiplier": 1.5,
        "recommendation": "Regular mammograms, genetic counseling (BRCA testing), self-exams.",
    },
    "colorectal_cancer": {
        "name": "Colorectal Cancer",
        "keywords": ["colon cancer", "colorectal cancer", "bowel cancer"],
        "base_risk": 0.04,
        "first_degree_multiplier": 2.5,
        "second_degree_multiplier": 1.5,
        "recommendation": "Earlier screening colonoscopy, high-fiber diet, regular exercise.",
    },
    "hypertension": {
        "name": "Hypertension",
        "keywords": ["high blood pressure", "hypertension"],
        "base_risk": 0.12,
        "first_degree_multiplier": 2.0,
        "second_degree_multiplier": 1.3,
        "recommendation": "Regular blood pressure monitoring, reduced sodium, exercise, stress management.",
    },
    "alzheimers": {
        "name": "Alzheimer's Disease",
        "keywords": ["alzheimer", "dementia"],
        "base_risk": 0.05,
        "first_degree_multiplier": 3.5,
        "second_degree_multiplier": 1.5,
        "recommendation": "Mental stimulation, cardiovascular exercise, social engagement, omega-3 fatty acids.",
    },
    "asthma": {
        "name": "Asthma",
        "keywords": ["asthma", "chronic bronchitis"],
        "base_risk": 0.08,
        "first_degree_multiplier": 2.0,
        "second_degree_multiplier": 1.3,
        "recommendation": "Identify triggers, regular lung function tests, have rescue inhaler available.",
    },
    "osteoporosis": {
        "name": "Osteoporosis",
        "keywords": ["osteoporosis", "bone density", "bone loss"],
        "base_risk": 0.06,
        "first_degree_multiplier": 2.5,
        "second_degree_multiplier": 1.4,
        "recommendation": "Calcium and Vitamin D supplementation, weight-bearing exercise, DEXA scans.",
    },
    "thyroid_disorders": {
        "name": "Thyroid Disorders",
        "keywords": ["thyroid", "hypothyroid", "hyperthyroid", "hashimoto"],
        "base_risk": 0.05,
        "first_degree_multiplier": 2.5,
        "second_degree_multiplier": 1.5,
        "recommendation": "Regular thyroid panel (TSH, T3, T4), monitor for symptoms.",
    },
    "depression": {
        "name": "Depression / Mood Disorders",
        "keywords": ["depression", "bipolar", "mood disorder", "mental health"],
        "base_risk": 0.07,
        "first_degree_multiplier": 3.0,
        "second_degree_multiplier": 1.5,
        "recommendation": "Mental health screening, therapy, regular exercise, social support.",
    },
}


class GeneticRiskService:
    """Service for hereditary/genetic risk analysis based on family history."""

    def analyze_family_risk(
        self, family_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze family health history for hereditary risk.

        Args:
            family_history: List of dicts with keys:
                - relationship: "parent", "sibling", "grandparent", "uncle/aunt"
                - conditions: list of condition strings

        Returns:
            Risk assessment with scores per condition
        """
        risk_results = []

        for cond_key, cond_info in HEREDITARY_CONDITIONS.items():
            first_degree_count = 0
            second_degree_count = 0
            affected_relatives = []

            for member in family_history:
                relationship = member.get("relationship", "").lower()
                conditions = [c.lower() for c in member.get("conditions", [])]

                # Check if any condition keywords match
                match = False
                for keyword in cond_info["keywords"]:
                    if any(keyword in c for c in conditions):
                        match = True
                        break

                if match:
                    is_first_degree = relationship in [
                        "parent", "mother", "father", "sibling", "brother", "sister", "child"
                    ]
                    if is_first_degree:
                        first_degree_count += 1
                    else:
                        second_degree_count += 1
                    affected_relatives.append(member.get("name", relationship))

            # Calculate risk
            base = cond_info["base_risk"]
            multiplier = 1.0
            if first_degree_count > 0:
                multiplier *= cond_info["first_degree_multiplier"] ** min(first_degree_count, 2)
            if second_degree_count > 0:
                multiplier *= cond_info["second_degree_multiplier"] ** min(second_degree_count, 2)

            risk_score = min(base * multiplier * 100, 95)  # Cap at 95%

            if first_degree_count > 0 or second_degree_count > 0:
                level = "high" if risk_score >= 40 else ("moderate" if risk_score >= 15 else "low")
            else:
                level = "population_average"
                risk_score = base * 100

            risk_results.append({
                "condition": cond_info["name"],
                "condition_key": cond_key,
                "risk_score": round(risk_score, 1),
                "risk_level": level,
                "first_degree_affected": first_degree_count,
                "second_degree_affected": second_degree_count,
                "affected_relatives": affected_relatives,
                "recommendation": cond_info["recommendation"],
            })

        # Sort by risk score
        risk_results.sort(key=lambda x: x["risk_score"], reverse=True)

        # Overall assessment
        high_risk = [r for r in risk_results if r["risk_level"] == "high"]
        moderate_risk = [r for r in risk_results if r["risk_level"] == "moderate"]

        return {
            "risk_assessments": risk_results,
            "high_risk_count": len(high_risk),
            "moderate_risk_count": len(moderate_risk),
            "overall_summary": self._generate_summary(high_risk, moderate_risk),
        }

    def _generate_summary(self, high: List, moderate: List) -> str:
        """Generate a textual summary of the genetic risk analysis."""
        if high:
            conditions = ", ".join(r["condition"] for r in high[:3])
            return (
                f"Elevated hereditary risk detected for: {conditions}. "
                f"Genetic counseling and proactive screening recommended."
            )
        elif moderate:
            conditions = ", ".join(r["condition"] for r in moderate[:3])
            return (
                f"Moderate hereditary risk for: {conditions}. "
                f"Regular monitoring and healthy lifestyle recommended."
            )
        else:
            return "No significantly elevated hereditary risks detected based on provided family history."

    def get_available_conditions(self) -> List[Dict[str, str]]:
        """Return list of all trackable hereditary conditions."""
        return [
            {"key": k, "name": v["name"], "recommendation": v["recommendation"]}
            for k, v in HEREDITARY_CONDITIONS.items()
        ]


# Singleton
genetic_risk_service = GeneticRiskService()
