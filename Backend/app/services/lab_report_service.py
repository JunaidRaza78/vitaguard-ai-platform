"""
Lab Report Interpreter Service
AI-powered interpretation of lab results — parses values, classifies against
reference ranges, and generates plain-English summaries via the RAG chatbot.
"""

import logging
import re
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


# ==========================================
# COMMON LAB REFERENCE RANGES
# ==========================================

LAB_REFERENCE_RANGES = {
    # Complete Blood Count
    "wbc": {"name": "White Blood Cells", "unit": "K/uL", "low": 4.5, "high": 11.0, "category": "CBC"},
    "rbc": {"name": "Red Blood Cells", "unit": "M/uL", "low": 4.5, "high": 5.5, "category": "CBC"},
    "hemoglobin": {"name": "Hemoglobin", "unit": "g/dL", "low": 12.0, "high": 17.5, "category": "CBC"},
    "hematocrit": {"name": "Hematocrit", "unit": "%", "low": 36.0, "high": 50.0, "category": "CBC"},
    "platelets": {"name": "Platelets", "unit": "K/uL", "low": 150, "high": 400, "category": "CBC"},
    "mcv": {"name": "MCV", "unit": "fL", "low": 80, "high": 100, "category": "CBC"},
    "mch": {"name": "MCH", "unit": "pg", "low": 27, "high": 33, "category": "CBC"},

    # Metabolic Panel
    "glucose": {"name": "Fasting Glucose", "unit": "mg/dL", "low": 70, "high": 100, "category": "Metabolic"},
    "bun": {"name": "BUN", "unit": "mg/dL", "low": 7, "high": 20, "category": "Metabolic"},
    "creatinine": {"name": "Creatinine", "unit": "mg/dL", "low": 0.6, "high": 1.2, "category": "Metabolic"},
    "sodium": {"name": "Sodium", "unit": "mEq/L", "low": 136, "high": 145, "category": "Metabolic"},
    "potassium": {"name": "Potassium", "unit": "mEq/L", "low": 3.5, "high": 5.0, "category": "Metabolic"},
    "calcium": {"name": "Calcium", "unit": "mg/dL", "low": 8.5, "high": 10.5, "category": "Metabolic"},
    "co2": {"name": "CO2", "unit": "mEq/L", "low": 23, "high": 29, "category": "Metabolic"},
    "chloride": {"name": "Chloride", "unit": "mEq/L", "low": 98, "high": 106, "category": "Metabolic"},

    # Liver Panel
    "alt": {"name": "ALT", "unit": "U/L", "low": 7, "high": 56, "category": "Liver"},
    "ast": {"name": "AST", "unit": "U/L", "low": 10, "high": 40, "category": "Liver"},
    "alp": {"name": "Alkaline Phosphatase", "unit": "U/L", "low": 44, "high": 147, "category": "Liver"},
    "bilirubin_total": {"name": "Total Bilirubin", "unit": "mg/dL", "low": 0.1, "high": 1.2, "category": "Liver"},
    "albumin": {"name": "Albumin", "unit": "g/dL", "low": 3.5, "high": 5.0, "category": "Liver"},

    # Lipid Panel
    "total_cholesterol": {"name": "Total Cholesterol", "unit": "mg/dL", "low": 0, "high": 200, "category": "Lipid"},
    "hdl": {"name": "HDL Cholesterol", "unit": "mg/dL", "low": 40, "high": 999, "category": "Lipid"},
    "ldl": {"name": "LDL Cholesterol", "unit": "mg/dL", "low": 0, "high": 100, "category": "Lipid"},
    "triglycerides": {"name": "Triglycerides", "unit": "mg/dL", "low": 0, "high": 150, "category": "Lipid"},

    # Thyroid
    "tsh": {"name": "TSH", "unit": "mIU/L", "low": 0.4, "high": 4.0, "category": "Thyroid"},
    "t3": {"name": "T3", "unit": "ng/dL", "low": 80, "high": 200, "category": "Thyroid"},
    "t4": {"name": "T4", "unit": "ug/dL", "low": 4.5, "high": 12.0, "category": "Thyroid"},

    # Diabetes
    "hba1c": {"name": "HbA1c", "unit": "%", "low": 0, "high": 5.7, "category": "Diabetes"},

    # Inflammation
    "crp": {"name": "C-Reactive Protein", "unit": "mg/L", "low": 0, "high": 3.0, "category": "Inflammation"},
    "esr": {"name": "ESR", "unit": "mm/hr", "low": 0, "high": 20, "category": "Inflammation"},

    # Iron
    "iron": {"name": "Iron", "unit": "ug/dL", "low": 60, "high": 170, "category": "Iron"},
    "ferritin": {"name": "Ferritin", "unit": "ng/mL", "low": 12, "high": 300, "category": "Iron"},

    # Vitamins
    "vitamin_d": {"name": "Vitamin D", "unit": "ng/mL", "low": 30, "high": 100, "category": "Vitamins"},
    "vitamin_b12": {"name": "Vitamin B12", "unit": "pg/mL", "low": 200, "high": 900, "category": "Vitamins"},
}


class LabReportService:
    """Service for parsing and interpreting lab reports."""

    def classify_result(self, test_key: str, value: float) -> Dict[str, Any]:
        """Classify a single lab result as normal, low, or high."""
        ref = LAB_REFERENCE_RANGES.get(test_key.lower())
        if not ref:
            return {"status": "unknown", "message": "No reference range available"}

        if value < ref["low"]:
            return {
                "status": "low",
                "message": f"{ref['name']} is LOW ({value} {ref['unit']}). Normal: {ref['low']}-{ref['high']} {ref['unit']}",
                "severity": "warning" if value >= ref["low"] * 0.8 else "critical",
            }
        elif value > ref["high"]:
            return {
                "status": "high",
                "message": f"{ref['name']} is HIGH ({value} {ref['unit']}). Normal: {ref['low']}-{ref['high']} {ref['unit']}",
                "severity": "warning" if value <= ref["high"] * 1.2 else "critical",
            }
        else:
            return {
                "status": "normal",
                "message": f"{ref['name']} is normal ({value} {ref['unit']})",
                "severity": "normal",
            }

    def interpret_lab_results(
        self, results: Dict[str, float], user_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Interpret a set of lab results.
        Returns classified results grouped by category with an AI summary.
        """
        interpreted = {}
        abnormal = []
        normal_count = 0

        for test_key, value in results.items():
            classification = self.classify_result(test_key, value)
            ref = LAB_REFERENCE_RANGES.get(test_key.lower(), {})
            category = ref.get("category", "Other")

            entry = {
                "test": ref.get("name", test_key),
                "value": value,
                "unit": ref.get("unit", ""),
                "reference_range": f"{ref.get('low', '?')}-{ref.get('high', '?')}",
                **classification,
            }

            if category not in interpreted:
                interpreted[category] = []
            interpreted[category].append(entry)

            if classification["status"] != "normal":
                abnormal.append(entry)
            else:
                normal_count += 1

        # Generate AI summary
        ai_summary = self._generate_ai_summary(interpreted, abnormal, user_context)

        return {
            "results_by_category": interpreted,
            "abnormal_results": abnormal,
            "normal_count": normal_count,
            "abnormal_count": len(abnormal),
            "total_tests": normal_count + len(abnormal),
            "critical_count": sum(1 for a in abnormal if a.get("severity") == "critical"),
            "ai_summary": ai_summary,
            "interpreted_at": datetime.now(timezone.utc).isoformat(),
        }

    # Guidance text for each abnormal lab result
    _CLINICAL_GUIDANCE: Dict[str, Dict[str, str]] = {
        "glucose": {
            "high": "Elevated fasting glucose may indicate prediabetes or diabetes. Reduce sugar and refined carbs; consider an HbA1c test for confirmation.",
            "low": "Low blood sugar (hypoglycemia) can cause dizziness and fatigue. Eat small, frequent meals; consult your doctor if recurrent.",
        },
        "hba1c": {
            "high": "HbA1c above 5.7% suggests prediabetes (5.7–6.4%) or diabetes (≥6.5%). Dietary changes, exercise, and follow-up testing are recommended.",
            "low": "HbA1c is within a healthy range. Continue maintaining a balanced diet and regular checkups.",
        },
        "total_cholesterol": {
            "high": "Total cholesterol above 200 mg/dL increases cardiovascular risk. Adopt a heart-healthy diet (low saturated fat, high fiber), exercise regularly, and consult your doctor about lipid-lowering therapy.",
            "low": "Cholesterol is within a healthy range.",
        },
        "triglycerides": {
            "high": "Triglycerides above 150 mg/dL raise the risk of heart disease and pancreatitis. Limit alcohol, sugar, and refined carbs; increase omega-3 fatty acids.",
            "low": "Triglycerides are within a healthy range.",
        },
        "ldl": {
            "high": "High LDL ('bad') cholesterol increases arterial plaque buildup. Increase soluble fiber, exercise, and discuss statin therapy with your doctor.",
            "low": "LDL cholesterol is within a healthy range.",
        },
        "hdl": {
            "low": "Low HDL ('good') cholesterol is a cardiovascular risk factor. Regular aerobic exercise, healthy fats, and weight management can help raise it.",
            "high": "HDL cholesterol is at a protective level — this is typically beneficial.",
        },
        "hemoglobin": {
            "low": "Low hemoglobin suggests anemia. Consider iron, B12, and folate evaluation. Common causes include nutritional deficiencies and chronic disease.",
            "high": "High hemoglobin may indicate dehydration or polycythemia. Follow-up with a complete blood count is recommended.",
        },
        "wbc": {
            "high": "Elevated white blood cells may indicate infection, inflammation, or stress. Additional evaluation may be needed if persistent.",
            "low": "Low white blood cells may indicate immune suppression. Follow-up with your healthcare provider is recommended.",
        },
        "creatinine": {
            "high": "Elevated creatinine may indicate kidney function impairment. Stay well hydrated; further testing (eGFR, urine analysis) may be needed.",
            "low": "Creatinine is within a healthy range.",
        },
        "tsh": {
            "high": "Elevated TSH suggests an underactive thyroid (hypothyroidism). Common symptoms include fatigue and weight gain. Thyroid hormone replacement may be needed.",
            "low": "Low TSH may indicate an overactive thyroid (hyperthyroidism). Symptoms include anxiety and weight loss. Follow-up with free T3/T4 testing.",
        },
        "alt": {
            "high": "Elevated ALT suggests liver inflammation. Reduce alcohol, avoid hepatotoxic medications, and consider further liver evaluation.",
            "low": "ALT is within a healthy range.",
        },
        "ast": {
            "high": "Elevated AST may indicate liver or muscle damage. Consider a hepatic panel and lifestyle assessment.",
            "low": "AST is within a healthy range.",
        },
    }

    def _generate_ai_summary(
        self, results: Dict, abnormal: List[Dict], user_context: Optional[str] = None
    ) -> str:
        """Generate a plain-English summary using the RAG chatbot, with a rich fallback."""

        # ---- Try LLM first ----
        try:
            from ollama_rag.rag_chatbot import get_chatbot, ERROR_MESSAGES

            error_strings = set(ERROR_MESSAGES.values()) if ERROR_MESSAGES else set()

            abnormal_descriptions = []
            for a in abnormal:
                abnormal_descriptions.append(
                    f"- {a['test']}: {a['value']} {a['unit']} ({a['status'].upper()}, "
                    f"normal range: {a['reference_range']})"
                )

            if not abnormal_descriptions:
                return "✅ All lab results are within normal reference ranges. No immediate concerns detected. Continue with regular checkups and a balanced lifestyle."

            prompt = (
                "You are a medical assistant. Interpret these abnormal lab results in "
                "plain English for a patient. Be concise and suggest follow-up actions:\n\n"
                + "\n".join(abnormal_descriptions)
            )
            if user_context:
                prompt += f"\n\nPatient context: {user_context}"

            chatbot = get_chatbot()
            result = chatbot.chat(
                question=prompt,
                conversation_id=f"lab_interpret_{datetime.now().timestamp()}",
                stream=False,
            )
            answer = result.get("answer", "")

            # If the LLM returned a real answer (not a canned error), use it
            if answer and answer.strip() not in error_strings and "apologize" not in answer.lower():
                return answer

            # Otherwise fall through to rule-based summary
            logger.info("LLM returned a generic error response; using rule-based summary")

        except Exception as e:
            logger.warning(f"AI summary unavailable: {e}")

        # ---- Rule-based fallback ----
        return self._build_rule_based_summary(results, abnormal, user_context)

    def _build_rule_based_summary(
        self, results: Dict, abnormal: List[Dict], user_context: Optional[str] = None
    ) -> str:
        """Build a detailed, clinically useful summary without LLM."""
        if not abnormal:
            return "✅ All results are within normal ranges. Keep up your healthy lifestyle and schedule regular checkups."

        total_tests = sum(len(items) for items in results.values())
        normal_count = total_tests - len(abnormal)
        critical = [a for a in abnormal if a.get("severity") == "critical"]
        warnings = [a for a in abnormal if a.get("severity") == "warning"]

        parts = []

        # Header
        parts.append(f"📊 **Lab Report Summary** — {total_tests} tests analyzed")
        parts.append("")

        if normal_count > 0:
            parts.append(f"✅ **{normal_count} test(s)** are within normal range.")

        if critical:
            parts.append(f"🔴 **{len(critical)} CRITICAL finding(s):**")
            for c in critical:
                key = self._find_key_for_test(c["test"])
                guidance = self._CLINICAL_GUIDANCE.get(key, {}).get(c["status"], "")
                parts.append(f"  • **{c['test']}**: {c['value']} {c['unit']} "
                             f"(normal: {c['reference_range']} {c['unit']})")
                if guidance:
                    parts.append(f"    → {guidance}")

        if warnings:
            parts.append(f"⚠️ **{len(warnings)} WARNING(s):**")
            for w in warnings:
                key = self._find_key_for_test(w["test"])
                guidance = self._CLINICAL_GUIDANCE.get(key, {}).get(w["status"], "")
                parts.append(f"  • **{w['test']}**: {w['value']} {w['unit']} "
                             f"(normal: {w['reference_range']} {w['unit']})")
                if guidance:
                    parts.append(f"    → {guidance}")

        parts.append("")
        parts.append("💡 **Recommended next steps:**")

        recommendations = set()
        for a in abnormal:
            key = self._find_key_for_test(a["test"])
            if key in ("glucose", "hba1c"):
                recommendations.add("Schedule a fasting glucose or HbA1c follow-up test.")
            elif key in ("total_cholesterol", "ldl", "hdl", "triglycerides"):
                recommendations.add("Discuss lipid management and heart-healthy lifestyle changes with your doctor.")
            elif key in ("hemoglobin", "wbc", "rbc", "platelets"):
                recommendations.add("Consider a follow-up complete blood count (CBC) and iron studies.")
            elif key in ("creatinine", "bun"):
                recommendations.add("Request kidney function tests (eGFR, urinalysis).")
            elif key in ("alt", "ast", "alp", "bilirubin_total"):
                recommendations.add("Consider a comprehensive liver panel and avoid hepatotoxic substances.")
            elif key in ("tsh", "t3", "t4"):
                recommendations.add("Follow up with thyroid function testing (free T3, free T4).")
            else:
                recommendations.add(f"Discuss your {a['test']} results with your healthcare provider.")

        for rec in sorted(recommendations):
            parts.append(f"  • {rec}")

        parts.append("")
        parts.append("⚕️ *This is an automated interpretation. Please consult your healthcare provider for personalized medical advice.*")

        return "\n".join(parts)

    def _find_key_for_test(self, test_name: str) -> str:
        """Find the LAB_REFERENCE_RANGES key for a given display test name."""
        test_lower = test_name.lower()
        for key, ref in LAB_REFERENCE_RANGES.items():
            if ref["name"].lower() == test_lower or key == test_lower:
                return key
        return test_lower

    # Common aliases that map free-text test names to LAB_REFERENCE_RANGES keys
    _NAME_ALIASES: Dict[str, str] = {
        # Glucose
        "glucose": "glucose", "glucose fasting": "glucose",
        "fasting glucose": "glucose", "blood sugar": "glucose",
        "blood glucose": "glucose", "glucose (fasting)": "glucose",
        # HbA1c
        "hba1c": "hba1c", "a1c": "hba1c", "hemoglobin a1c": "hba1c",
        "hb a1c": "hba1c", "glycated hemoglobin": "hba1c",
        # Lipid panel
        "cholesterol": "total_cholesterol", "total cholesterol": "total_cholesterol",
        "lipid profile cholesterol": "total_cholesterol",
        "triglycerides": "triglycerides", "trigs": "triglycerides",
        "hdl": "hdl", "hdl cholesterol": "hdl", "hol hdl": "hdl",
        "ldl": "ldl", "ldl cholesterol": "ldl", "hol ldl": "ldl",
        # CBC
        "wbc": "wbc", "white blood cells": "wbc",
        "rbc": "rbc", "red blood cells": "rbc",
        "hemoglobin": "hemoglobin", "hgb": "hemoglobin", "hb": "hemoglobin",
        "hematocrit": "hematocrit", "hct": "hematocrit",
        "platelets": "platelets", "plt": "platelets",
        "mcv": "mcv", "mch": "mch",
        # Metabolic
        "bun": "bun", "blood urea nitrogen": "bun",
        "creatinine": "creatinine",
        "sodium": "sodium", "na": "sodium",
        "potassium": "potassium", "k": "potassium",
        "calcium": "calcium", "ca": "calcium",
        "chloride": "chloride", "cl": "chloride",
        "co2": "co2", "carbon dioxide": "co2",
        # Liver
        "alt": "alt", "sgpt": "alt", "ast": "ast", "sgot": "ast",
        "alp": "alp", "alkaline phosphatase": "alp",
        "bilirubin total": "bilirubin_total", "total bilirubin": "bilirubin_total",
        "bilirubin": "bilirubin_total",
        "albumin": "albumin",
        # Thyroid
        "tsh": "tsh", "t3": "t3", "t4": "t4",
        # Inflammation
        "crp": "crp", "c reactive protein": "crp",
        "esr": "esr",
        # Iron
        "iron": "iron", "serum iron": "iron",
        "ferritin": "ferritin",
        # Vitamins
        "vitamin d": "vitamin_d", "vit d": "vitamin_d",
        "vitamin b12": "vitamin_b12", "vit b12": "vitamin_b12",
    }

    def parse_text_report(self, text: str) -> Dict[str, float]:
        """
        Attempt to parse free-text lab report into structured results.
        Handles many common formats:
          - Glucose: 95 mg/dL
          - GLUCOSE (FASTING) (70-125) 86
          - HbA1C (4.0-6.0) 5.6
          - WBC    12.5    K/uL
        """
        results: Dict[str, float] = {}

        # Build reverse lookup: name -> key  (aliases + reference-range names)
        name_to_key: Dict[str, str] = dict(self._NAME_ALIASES)
        for key, ref in LAB_REFERENCE_RANGES.items():
            name_to_key.setdefault(ref["name"].lower(), key)
            name_to_key.setdefault(key.lower(), key)

        # --- Strategy: process each line independently ---
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            matched_key = None
            value = None

            # 1) Try structured patterns first
            #    "Name: 95 mg/dL"  or  "Name = 95 mg/dL"
            m = re.match(
                r'(?P<name>[A-Za-z][\w\s.\-/()]*?)\s*[:=]\s*(?P<value>\d+\.?\d*)',
                line, re.IGNORECASE,
            )
            if m:
                name_part = m.group("name").strip().lower()
                value = float(m.group("value"))
                matched_key = self._match_name(name_part, name_to_key)

            # 2) "Name (anything) value [unit]" — common lab report format
            if matched_key is None:
                m = re.match(
                    r'(?P<name>[A-Za-z][\w\s.\-/]*?)(?:\s*\([^)]*\))+\s*(?P<value>\d+\.?\d*)',
                    line, re.IGNORECASE,
                )
                if m:
                    name_part = m.group("name").strip().lower()
                    value = float(m.group("value"))
                    matched_key = self._match_name(name_part, name_to_key)

            # 3) Fallback: extract the last number on the line and match the
            #    text portion against known names
            if matched_key is None:
                nums = re.findall(r'(?<!\d[.\-])(\d+\.?\d*)(?!\s*[-\d])', line)
                if nums:
                    # Clean the text before the last number to get the test name
                    last_num = nums[-1]
                    text_part = line[:line.rfind(last_num)].strip()
                    # Remove parenthetical info
                    text_clean = re.sub(r'\([^)]*\)', '', text_part).strip()
                    # Remove leading dots, slashes, etc.
                    text_clean = re.sub(r'^[\s.\-/]+', '', text_clean).strip().lower()
                    if text_clean:
                        value = float(last_num)
                        matched_key = self._match_name(text_clean, name_to_key)

            if matched_key and value is not None and matched_key not in results:
                results[matched_key] = value

        return results

    @staticmethod
    def _match_name(name: str, name_to_key: Dict[str, str]) -> Optional[str]:
        """Match a cleaned test name string to a known key using exact then fuzzy lookup."""
        # Exact match
        key = name_to_key.get(name)
        if key:
            return key

        # Strip common prefixes like "lipid profile"
        for prefix in ("lipid profile", "serum", "blood", "plasma", "urine"):
            stripped = re.sub(rf'^{prefix}\s*\.?\s*', '', name).strip()
            if stripped and stripped != name:
                key = name_to_key.get(stripped)
                if key:
                    return key

        # Fuzzy: check if a known name is contained in the input or vice versa
        for known_name, known_key in name_to_key.items():
            if len(known_name) >= 3 and (known_name in name or name in known_name):
                return known_key

        return None

    def store_lab_result(
        self, user_id: str, test_key: str, value: float, report_date: str,
        report_id: Optional[str] = None
    ) -> Optional[Dict]:
        """Store a lab result in Neo4j."""
        try:
            from shared.database.neo4j.operations.vitals_ops import VitalsOperations
            from shared.database.neo4j.neo4j_client import Neo4jClient

            ref = LAB_REFERENCE_RANGES.get(test_key.lower(), {})
            client = Neo4jClient()
            vitals_ops = VitalsOperations(client)

            result = vitals_ops.create_lab_result(
                user_id=user_id,
                test_name=ref.get("name", test_key),
                value=value,
                unit=ref.get("unit", ""),
                reference_range=f"{ref.get('low', '')}-{ref.get('high', '')}",
                date=report_date,
                report_id=report_id,
            )
            return result
        except Exception as e:
            logger.error(f"Error storing lab result: {e}")
            return None


# Singleton
lab_report_service = LabReportService()
