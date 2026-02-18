"""
Lab Reports Page
AI-powered lab result interpretation, free-text parsing, and reference ranges.
"""

import streamlit as st
import sys
import plotly.graph_objects as go
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from components.auth import init_session_state, is_authenticated
from components.api_client import authenticated_request, API_BASE_URL, logout

# Initialize
init_session_state()

st.set_page_config(
    page_title="Lab Reports - Family Health Manager",
    page_icon="🧪",
    layout="wide",
)

if not is_authenticated():
    st.warning("Please login to access this page")
    st.switch_page("app.py")
    st.stop()


# ==========================================
# API HELPERS
# ==========================================

def interpret_lab_results(results: dict, context: str = None):
    payload = {"results": results}
    if context:
        payload["user_context"] = context
    return authenticated_request("post", f"{API_BASE_URL}/api/v1/labs/interpret", json=payload)


def parse_text_report(text: str, context: str = None):
    payload = {"text": text}
    if context:
        payload["user_context"] = context
    return authenticated_request("post", f"{API_BASE_URL}/api/v1/labs/parse-text", json=payload)


def get_reference_ranges():
    return authenticated_request("get", f"{API_BASE_URL}/api/v1/labs/reference-ranges")


def check_emergency(message: str):
    return authenticated_request("post", f"{API_BASE_URL}/api/v1/labs/emergency-check", json={"message": message})


# ==========================================
# CSS
# ==========================================
st.markdown("""
<style>
    .lab-normal { background: #d1fae5; border-left: 4px solid #10b981; padding: 0.75rem; border-radius: 0 0.5rem 0.5rem 0; margin-bottom: 0.5rem; }
    .lab-high { background: #fee2e2; border-left: 4px solid #ef4444; padding: 0.75rem; border-radius: 0 0.5rem 0.5rem 0; margin-bottom: 0.5rem; }
    .lab-low { background: #fef3c7; border-left: 4px solid #f59e0b; padding: 0.75rem; border-radius: 0 0.5rem 0.5rem 0; margin-bottom: 0.5rem; }
    .lab-name { font-weight: 600; }
    .lab-value { font-size: 1.1rem; font-weight: 700; }
    .lab-ref { color: #64748b; font-size: 0.8rem; }
    .summary-box { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.5rem; border-radius: 0.75rem; margin: 1rem 0; }
    .emergency-box { background: #fef2f2; border: 2px solid #ef4444; padding: 1.5rem; border-radius: 0.75rem; margin: 1rem 0; }
    .section-header { font-size: 1.3rem; font-weight: 600; color: #1e293b; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 2px solid #e2e8f0; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    st.header("🧪 Lab Reports")
    view = st.radio("📋 View", ["Enter Lab Values", "Paste Report Text", "Reference Ranges", "Emergency Check"], index=0)
    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        logout()
        st.switch_page("app.py")


# ==========================================
# MAIN
# ==========================================
st.title("🧪 Lab Report Interpreter")


# ------------------------------------------
# ENTER LAB VALUES
# ------------------------------------------
if view == "Enter Lab Values":
    st.markdown('<div class="section-header">📊 Enter Lab Results</div>', unsafe_allow_html=True)

    # Fetch available tests
    ref_data = get_reference_ranges()
    tests = ref_data.get("tests", {}) if isinstance(ref_data, dict) else {}

    if not tests:
        st.warning("Could not load reference ranges from server. Using built-in list.")
        tests = {
            "glucose": {"name": "Fasting Glucose", "unit": "mg/dL"},
            "hemoglobin": {"name": "Hemoglobin", "unit": "g/dL"},
            "wbc": {"name": "WBC", "unit": "K/uL"},
            "platelets": {"name": "Platelets", "unit": "K/uL"},
            "tsh": {"name": "TSH", "unit": "mIU/L"},
            "total_cholesterol": {"name": "Total Cholesterol", "unit": "mg/dL"},
            "hdl": {"name": "HDL", "unit": "mg/dL"},
            "ldl": {"name": "LDL", "unit": "mg/dL"},
            "creatinine": {"name": "Creatinine", "unit": "mg/dL"},
            "alt": {"name": "ALT", "unit": "U/L"},
            "hba1c": {"name": "HbA1c", "unit": "%"},
        }

    # Group by category
    categories = {}
    for key, info in tests.items():
        cat = info.get("category", "Other")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append((key, info))

    with st.form("lab_form"):
        results = {}
        context = st.text_area("Patient Context (optional)", placeholder="e.g., 45-year-old male, diabetes history")

        for cat, items in categories.items():
            st.subheader(cat)
            cols = st.columns(3)
            for i, (key, info) in enumerate(items):
                with cols[i % 3]:
                    val = st.number_input(
                        f"{info['name']} ({info.get('unit', '')})",
                        min_value=0.0, max_value=9999.0, value=0.0, step=0.1,
                        key=f"lab_{key}",
                    )
                    if val > 0:
                        results[key] = val

        submitted = st.form_submit_button("🔬 Interpret Results", use_container_width=True, type="primary")

    if submitted and results:
        with st.spinner("Analyzing lab results with AI..."):
            interpretation = interpret_lab_results(results, context if context else None)

        if interpretation.get("error"):
            st.error(f"Error: {interpretation.get('error')}")
        else:
            # Summary
            st.markdown(f"""
            <div class="summary-box">
                <div style="font-size: 1.2rem; font-weight: 600; margin-bottom: 0.5rem;">🤖 AI Summary</div>
                {interpretation.get("ai_summary", "No summary available.")}
            </div>
            """, unsafe_allow_html=True)

            # Metrics
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Tests", interpretation.get("total_tests", 0))
            m2.metric("Normal", interpretation.get("normal_count", 0))
            m3.metric("Abnormal", interpretation.get("abnormal_count", 0))
            m4.metric("🔴 Critical", interpretation.get("critical_count", 0))

            # Results by category
            for cat, items in interpretation.get("results_by_category", {}).items():
                st.subheader(cat)
                for item in items:
                    css = f"lab-{item['status']}"
                    st.markdown(f"""
                    <div class="{css}">
                        <span class="lab-name">{item['test']}</span>:
                        <span class="lab-value">{item['value']} {item['unit']}</span>
                        <span style="margin-left: 1rem;">{item['status'].upper()}</span>
                        <div class="lab-ref">Reference: {item['reference_range']} {item['unit']}</div>
                    </div>
                    """, unsafe_allow_html=True)

    elif submitted:
        st.warning("Enter at least one lab value.")


# ------------------------------------------
# PASTE REPORT TEXT
# ------------------------------------------
elif view == "Paste Report Text":
    st.markdown('<div class="section-header">📋 Paste Lab Report</div>', unsafe_allow_html=True)
    st.info("Paste raw text from your lab report — the AI will extract and interpret the values.")

    text = st.text_area("Lab Report Text", height=300, placeholder="Paste your lab report text here...\n\nExample:\nGlucose: 125 mg/dL\nHemoglobin: 10.5 g/dL\nTSH: 6.2 mIU/L\nWBC: 12.5 K/uL")

    context = st.text_input("Patient Context (optional)")

    if st.button("🔬 Parse & Interpret", use_container_width=True, type="primary"):
        if not text.strip():
            st.warning("Please paste lab report text.")
        else:
            with st.spinner("Parsing and analyzing..."):
                result = parse_text_report(text, context if context else None)

            if result.get("error"):
                st.error(f"Error: {result.get('error')}")
            else:
                parsed = result.get("parsed_results", {})
                interp = result.get("interpretation", {})

                if not parsed:
                    st.warning("No lab values could be extracted. Try the manual entry form instead.")
                else:
                    st.success(f"Extracted **{len(parsed)} lab values** from text")

                    # Show extracted values
                    with st.expander("📋 Extracted Values", expanded=False):
                        for k, v in parsed.items():
                            st.write(f"• **{k}**: {v}")

                    # Show interpretation
                    if interp:
                        st.markdown(f"""
                        <div class="summary-box">
                            <div style="font-size: 1.2rem; font-weight: 600; margin-bottom: 0.5rem;">🤖 AI Summary</div>
                            {interp.get("ai_summary", "No summary available.")}
                        </div>
                        """, unsafe_allow_html=True)

                        for cat, items in interp.get("results_by_category", {}).items():
                            st.subheader(cat)
                            for item in items:
                                css = f"lab-{item['status']}"
                                st.markdown(f"""
                                <div class="{css}">
                                    <span class="lab-name">{item['test']}</span>:
                                    <span class="lab-value">{item['value']} {item['unit']}</span>
                                    <span>{item['status'].upper()}</span>
                                    <div class="lab-ref">Reference: {item['reference_range']} {item['unit']}</div>
                                </div>
                                """, unsafe_allow_html=True)


# ------------------------------------------
# REFERENCE RANGES
# ------------------------------------------
elif view == "Reference Ranges":
    st.markdown('<div class="section-header">📚 Lab Test Reference Ranges</div>', unsafe_allow_html=True)

    ref_data = get_reference_ranges()
    tests = ref_data.get("tests", {}) if isinstance(ref_data, dict) else {}

    if not tests:
        st.info("Reference ranges not available from server.")
    else:
        categories = {}
        for key, info in tests.items():
            cat = info.get("category", "Other")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(info)

        for cat, items in categories.items():
            st.subheader(f"🏷️ {cat}")
            rows = []
            for info in items:
                rows.append({
                    "Test": info["name"],
                    "Unit": info["unit"],
                    "Low": info["low"],
                    "High": info["high"],
                })
            st.table(rows)


# ------------------------------------------
# EMERGENCY CHECK
# ------------------------------------------
elif view == "Emergency Check":
    st.markdown('<div class="section-header">🚨 Emergency Symptom Checker</div>', unsafe_allow_html=True)
    st.warning("This tool checks for emergency medical indicators in text. **It is NOT a substitute for calling 911.**")

    message = st.text_area("Describe symptoms or situation", height=150, placeholder="e.g., My father has severe chest pain and difficulty breathing")

    if st.button("🔍 Check for Emergency Indicators", use_container_width=True, type="primary"):
        if not message.strip():
            st.warning("Please describe the symptoms.")
        else:
            with st.spinner("Analyzing..."):
                result = check_emergency(message)

            if result.get("error"):
                st.error(f"Error: {result.get('error')}")
            elif result.get("is_emergency"):
                severity = result.get("severity", "urgent")
                response = result.get("response", "")
                if result.get("call_911"):
                    st.markdown(f"""
                    <div class="emergency-box">
                        <div style="font-size: 1.5rem; font-weight: 700; color: #ef4444; margin-bottom: 0.75rem;">
                            🚨 EMERGENCY DETECTED — CALL 911
                        </div>
                        {response.replace(chr(10), '<br>')}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error(f"**Urgent concern detected!**\n\n{response}")

                detected = result.get("detected_keywords", [])
                if detected:
                    st.caption(f"Detected indicators: {', '.join(detected)}")
            else:
                severity = result.get("severity", "none")
                if severity == "moderate":
                    response = result.get("response", "")
                    st.warning(f"Moderate concern detected.\n\n{response}")
                else:
                    st.success("✅ No emergency indicators detected. If you still have concerns, please consult your healthcare provider.")


# Footer
st.divider()
st.caption("⚠️ Lab interpretations are for informational purposes only. Always consult your healthcare provider for medical decisions.")
