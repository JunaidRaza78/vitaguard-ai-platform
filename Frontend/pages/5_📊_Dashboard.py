"""
Health Dashboard Page
Interactive vitals tracking, anomaly alerts, risk scoring, and family timeline
"""

import streamlit as st
import sys
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from components.auth import init_session_state, is_authenticated
from components.api_client import (
    get_dashboard_summary,
    get_vitals_trend,
    get_latest_vitals,
    detect_anomalies,
    get_risk_scores,
    record_vital,
    record_blood_pressure,
    get_my_families,
    get_family_timeline,
    logout,
)

# Initialize
init_session_state()

# Page config
st.set_page_config(
    page_title="Health Dashboard - Family Health Manager",
    page_icon="📊",
    layout="wide",
)

# Check auth
if not is_authenticated():
    st.warning("Please login to access this page")
    st.switch_page("app.py")
    st.stop()


# ==========================================
# CUSTOM CSS
# ==========================================
st.markdown("""
<style>
    .kpi-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.2rem;
        border-radius: 0.75rem;
        text-align: center;
        margin-bottom: 0.5rem;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    .kpi-card.normal { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); box-shadow: 0 4px 15px rgba(17, 153, 142, 0.3); }
    .kpi-card.warning { background: linear-gradient(135deg, #f7971e 0%, #ffd200 100%); color: #333; box-shadow: 0 4px 15px rgba(247, 151, 30, 0.3); }
    .kpi-card.critical { background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); box-shadow: 0 4px 15px rgba(235, 51, 73, 0.3); }
    .kpi-value { font-size: 2rem; font-weight: 700; margin: 0.25rem 0; }
    .kpi-label { font-size: 0.85rem; opacity: 0.9; }
    .kpi-unit { font-size: 0.75rem; opacity: 0.7; }
    .alert-banner {
        padding: 0.75rem 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
        border-left: 4px solid;
    }
    .alert-critical { background: #fef2f2; border-color: #ef4444; color: #991b1b; }
    .alert-warning { background: #fffbeb; border-color: #f59e0b; color: #92400e; }
    .risk-gauge { text-align: center; }
    .timeline-entry {
        padding: 0.75rem;
        border-left: 3px solid #667eea;
        margin-bottom: 0.75rem;
        background: #f8fafc;
        border-radius: 0 0.5rem 0.5rem 0;
    }
    .section-header {
        font-size: 1.3rem;
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    st.header("📊 Dashboard")

    user = st.session_state.get("user", {})
    st.markdown(f"**👤 {user.get('first_name', 'User')} {user.get('last_name', '')}**")

    st.divider()

    # View selector
    view = st.radio(
        "📋 View",
        ["Overview", "Vitals Trends", "Record Vitals", "Family Timeline"],
        index=0,
    )

    st.divider()

    if st.button("🚪 Logout", use_container_width=True):
        logout()
        st.switch_page("app.py")


# ==========================================
# HELPER: CREATE PLOTLY CHARTS
# ==========================================

def create_trend_chart(trend_data: dict, title: str = "") -> go.Figure:
    """Create a Plotly line chart from trend data."""
    data_points = trend_data.get("data_points", [])
    normal_range = trend_data.get("normal_range", {})

    if not data_points:
        fig = go.Figure()
        fig.add_annotation(text="No data available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=16, color="#94a3b8"))
        fig.update_layout(height=300)
        return fig

    dates = [p.get("date", "") for p in data_points]
    values = [p.get("value", 0) for p in data_points]
    statuses = [p.get("status", "normal") for p in data_points]

    colors = []
    for s in statuses:
        if s == "critical":
            colors.append("#ef4444")
        elif s == "warning":
            colors.append("#f59e0b")
        else:
            colors.append("#10b981")

    fig = go.Figure()

    # Normal range band
    if normal_range.get("low") is not None and normal_range.get("high") is not None:
        fig.add_hrect(
            y0=normal_range["low"], y1=normal_range["high"],
            fillcolor="rgba(16, 185, 129, 0.1)",
            line_width=0,
            annotation_text="Normal range",
            annotation_position="top left",
        )

    # Main line
    fig.add_trace(go.Scatter(
        x=dates, y=values,
        mode="lines+markers",
        line=dict(color="#667eea", width=2.5),
        marker=dict(color=colors, size=8, line=dict(color="white", width=1.5)),
        name=title or trend_data.get("vital_type", ""),
        hovertemplate="%{y:.1f} " + trend_data.get("unit", "") + "<br>%{x}<extra></extra>",
    ))

    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title=trend_data.get("unit", ""),
        height=350,
        margin=dict(l=50, r=30, t=50, b=40),
        template="plotly_white",
        hovermode="x unified",
    )

    return fig


def create_risk_gauge(score: float, label: str, level: str) -> go.Figure:
    """Create a Plotly gauge chart for risk score."""
    color_map = {"normal": "#10b981", "warning": "#f59e0b", "critical": "#ef4444"}
    color = color_map.get(level, "#94a3b8")

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": label, "font": {"size": 14}},
        number={"suffix": "%", "font": {"size": 24}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1},
            "bar": {"color": color},
            "steps": [
                {"range": [0, 30], "color": "rgba(16, 185, 129, 0.2)"},
                {"range": [30, 60], "color": "rgba(245, 158, 11, 0.2)"},
                {"range": [60, 100], "color": "rgba(239, 68, 68, 0.2)"},
            ],
            "threshold": {
                "line": {"color": color, "width": 3},
                "thickness": 0.8,
                "value": score,
            },
        },
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
    return fig


# ==========================================
# MAIN CONTENT
# ==========================================

st.title("📊 Health Dashboard")
user_id = user.get("user_id", "")


# ------------------------------------------
# OVERVIEW VIEW
# ------------------------------------------
if view == "Overview":
    st.markdown('<div class="section-header">🏥 Health Overview</div>', unsafe_allow_html=True)

    with st.spinner("Loading dashboard..."):
        summary = get_dashboard_summary(user_id) if user_id else {}

    if summary.get("error"):
        st.info("No health data available yet. Start by recording some vitals!")
    else:
        # --- KPI Cards ---
        vitals = summary.get("latest_vitals", {})
        vital_labels = {
            "blood_pressure_systolic": ("Systolic BP", "mmHg"),
            "blood_pressure_diastolic": ("Diastolic BP", "mmHg"),
            "heart_rate": ("Heart Rate", "bpm"),
            "glucose": ("Glucose", "mg/dL"),
            "temperature": ("Temperature", "°F"),
            "oxygen_saturation": ("SpO2", "%"),
            "weight": ("Weight", "kg"),
            "bmi": ("BMI", "kg/m²"),
        }

        if vitals:
            cols = st.columns(min(len(vitals), 4))
            for i, (vtype, vdata) in enumerate(vitals.items()):
                label, unit = vital_labels.get(vtype, (vtype.replace("_", " ").title(), ""))
                status = vdata.get("status", "normal")
                value = vdata.get("value", 0)
                with cols[i % 4]:
                    st.markdown(f"""
                    <div class="kpi-card {status}">
                        <div class="kpi-label">{label}</div>
                        <div class="kpi-value">{value:.0f}</div>
                        <div class="kpi-unit">{unit}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No vitals recorded yet. Go to **Record Vitals** to add your first reading.")

        # --- Anomaly Alerts ---
        anomalies = summary.get("recent_anomalies", [])
        if anomalies:
            st.markdown('<div class="section-header">⚠️ Active Alerts</div>', unsafe_allow_html=True)
            for alert in anomalies:
                level = alert.get("level", "warning")
                css_class = "alert-critical" if level == "critical" else "alert-warning"
                st.markdown(f"""
                <div class="alert-banner {css_class}">
                    {alert.get('message', 'Unknown alert')} — <strong>{alert.get('date', '')}</strong>
                </div>
                """, unsafe_allow_html=True)

        # --- Risk Scores ---
        risk_scores = summary.get("risk_scores", [])
        if risk_scores:
            st.markdown('<div class="section-header">🎯 Health Risk Assessment</div>', unsafe_allow_html=True)
            risk_cols = st.columns(len(risk_scores))
            for i, rs in enumerate(risk_scores):
                with risk_cols[i]:
                    fig = create_risk_gauge(
                        rs.get("score", 0),
                        rs.get("category", "").replace("_", " ").title(),
                        rs.get("level", "normal"),
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    # Recommendation
                    rec = rs.get("recommendation", "")
                    if rec:
                        st.caption(rec)

        # --- Active Medications ---
        meds = summary.get("active_medications", [])
        if meds:
            st.markdown('<div class="section-header">💊 Active Medications</div>', unsafe_allow_html=True)
            for m in meds:
                name = m.get("name", "Unknown")
                dosage = m.get("dosage", "")
                freq = m.get("frequency", "")
                st.markdown(f"• **{name}** — {dosage} ({freq})")


# ------------------------------------------
# VITALS TRENDS VIEW
# ------------------------------------------
elif view == "Vitals Trends":
    st.markdown('<div class="section-header">📈 Vitals Trends</div>', unsafe_allow_html=True)

    # Vital type selector
    vital_options = {
        "Blood Pressure (Systolic)": "blood_pressure_systolic",
        "Blood Pressure (Diastolic)": "blood_pressure_diastolic",
        "Heart Rate": "heart_rate",
        "Glucose": "glucose",
        "Temperature": "temperature",
        "Weight": "weight",
        "BMI": "bmi",
        "SpO2": "oxygen_saturation",
    }

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        selected_label = st.selectbox("Select Vital", list(vital_options.keys()))
    with col2:
        start = st.date_input("Start Date", value=date.today() - timedelta(days=90))
    with col3:
        end = st.date_input("End Date", value=date.today())

    vital_type = vital_options[selected_label]

    with st.spinner("Loading trend data..."):
        trend = get_vitals_trend(user_id, vital_type, str(start), str(end))

    if trend.get("error") or not trend.get("data_points"):
        st.info(f"No {selected_label} data found. Record some measurements first!")
    else:
        # Chart
        fig = create_trend_chart(trend, selected_label)
        st.plotly_chart(fig, use_container_width=True)

        # Statistics
        stats = trend.get("statistics", {})
        if stats:
            stat_cols = st.columns(5)
            stat_cols[0].metric("Latest", f"{stats.get('latest', 0):.1f}")
            stat_cols[1].metric("Average", f"{stats.get('avg', 0):.1f}")
            stat_cols[2].metric("Min", f"{stats.get('min', 0):.1f}")
            stat_cols[3].metric("Max", f"{stats.get('max', 0):.1f}")
            stat_cols[4].metric("Readings", stats.get("count", 0))

    # Anomalies section
    st.markdown('<div class="section-header">⚠️ Anomaly Detection</div>', unsafe_allow_html=True)
    with st.spinner("Scanning for anomalies..."):
        anomaly_data = detect_anomalies(user_id)

    if anomaly_data.get("error"):
        st.info("No anomaly data available.")
    else:
        alerts = anomaly_data.get("alerts", [])
        crit = anomaly_data.get("critical_count", 0)
        warn = anomaly_data.get("warning_count", 0)

        mcol1, mcol2, mcol3 = st.columns(3)
        mcol1.metric("Total Alerts", len(alerts))
        mcol2.metric("🔴 Critical", crit)
        mcol3.metric("🟡 Warning", warn)

        if alerts:
            for a in alerts[:10]:
                level = a.get("level", "warning")
                css = "alert-critical" if level == "critical" else "alert-warning"
                st.markdown(f"""
                <div class="alert-banner {css}">
                    {a.get('message', '')} — {a.get('date', '')}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ All vitals are within normal range!")


# ------------------------------------------
# RECORD VITALS VIEW
# ------------------------------------------
elif view == "Record Vitals":
    st.markdown('<div class="section-header">📝 Record New Vital Signs</div>', unsafe_allow_html=True)

    record_type = st.radio("What would you like to record?", ["Blood Pressure", "Single Vital"], horizontal=True)

    if record_type == "Blood Pressure":
        with st.form("bp_form"):
            st.subheader("🩸 Blood Pressure Reading")
            c1, c2, c3 = st.columns(3)
            with c1:
                systolic = st.number_input("Systolic (mmHg)", min_value=40, max_value=300, value=120)
            with c2:
                diastolic = st.number_input("Diastolic (mmHg)", min_value=20, max_value=200, value=80)
            with c3:
                heart_rate = st.number_input("Heart Rate (bpm, optional)", min_value=0, max_value=300, value=72)

            bp_date = st.date_input("Date", value=date.today())
            bp_time = st.time_input("Time")
            bp_notes = st.text_input("Notes (optional)")

            submitted = st.form_submit_button("💾 Save Blood Pressure", use_container_width=True, type="primary")
            if submitted:
                with st.spinner("Recording..."):
                    result = record_blood_pressure(
                        systolic=systolic,
                        diastolic=diastolic,
                        date=str(bp_date),
                        heart_rate=heart_rate if heart_rate > 0 else None,
                        time=str(bp_time),
                    )
                if isinstance(result, list) and len(result) > 0:
                    st.success("✅ Blood pressure recorded successfully!")
                    for r in result:
                        status = r.get("status", "normal")
                        if status == "critical":
                            st.error(f"⚠️ {r.get('vital_type', '').replace('_', ' ').title()}: {r.get('value', 0)} is CRITICAL")
                        elif status == "warning":
                            st.warning(f"⚡ {r.get('vital_type', '').replace('_', ' ').title()}: {r.get('value', 0)} is elevated")
                elif result.get("error"):
                    st.error(f"Error: {result.get('error')}")
                else:
                    st.error("Failed to record blood pressure.")

    else:
        with st.form("vital_form"):
            st.subheader("📋 Single Vital Sign")
            vital_type_options = {
                "Heart Rate": ("heart_rate", "bpm"),
                "Fasting Glucose": ("glucose", "mg/dL"),
                "Temperature": ("temperature", "°F"),
                "Weight": ("weight", "kg"),
                "BMI": ("bmi", "kg/m²"),
                "SpO2": ("oxygen_saturation", "%"),
                "Respiratory Rate": ("respiratory_rate", "breaths/min"),
            }

            selected = st.selectbox("Vital Type", list(vital_type_options.keys()))
            vtype, vunit = vital_type_options[selected]

            value = st.number_input(f"Value ({vunit})", min_value=0.0, max_value=999.0, value=0.0, step=0.1)
            v_date = st.date_input("Date", value=date.today())
            v_time = st.time_input("Time")
            v_notes = st.text_input("Notes (optional)")

            submitted = st.form_submit_button("💾 Save Vital Sign", use_container_width=True, type="primary")
            if submitted:
                if value == 0:
                    st.warning("Please enter a value.")
                else:
                    with st.spinner("Recording..."):
                        result = record_vital(
                            vital_type=vtype,
                            value=value,
                            unit=vunit,
                            date=str(v_date),
                            time=str(v_time),
                            notes=v_notes if v_notes else None,
                        )
                    if result.get("vital_id"):
                        st.success("✅ Vital sign recorded!")
                        status = result.get("status", "normal")
                        if status == "critical":
                            st.error(f"⚠️ Reading is CRITICAL! Normal range shown in your dashboard.")
                        elif status == "warning":
                            st.warning("⚡ Reading is slightly outside normal range.")
                    elif result.get("error"):
                        st.error(f"Error: {result.get('error')}")
                    else:
                        st.error("Failed to record vital sign.")


# ------------------------------------------
# FAMILY TIMELINE VIEW
# ------------------------------------------
elif view == "Family Timeline":
    st.markdown('<div class="section-header">👨‍👩‍👧‍👦 Family Health Timeline</div>', unsafe_allow_html=True)

    # Get families
    with st.spinner("Loading families..."):
        families_response = get_my_families()

    families = families_response if isinstance(families_response, list) else families_response.get("families", [])

    if not families:
        st.info("You haven't joined any families yet. Go to **Family** page to create or join one.")
    else:
        family_names = {f.get("family_id", f.get("familyId", "")): f.get("name", "Unknown") for f in families}
        selected_family = st.selectbox(
            "Select Family",
            list(family_names.keys()),
            format_func=lambda x: family_names.get(x, x),
        )

        if selected_family:
            with st.spinner("Loading timeline..."):
                timeline = get_family_timeline(selected_family)

            entries = timeline.get("entries", [])

            if not entries:
                st.info("No health events recorded for this family yet.")
            else:
                st.markdown(f"**{len(entries)} events**")
                for entry in entries:
                    severity = entry.get("severity", "")
                    border_color = "#ef4444" if severity == "critical" else "#f59e0b" if severity == "warning" else "#667eea"
                    st.markdown(f"""
                    <div class="timeline-entry" style="border-color: {border_color}">
                        <strong>{entry.get('user_name', 'Unknown')}</strong> — {entry.get('title', '')}
                        <br><small>📅 {entry.get('date', '')[:10]} &nbsp;|&nbsp; {entry.get('event_type', '').replace('_', ' ').title()}</small>
                        {"<br><small>" + entry.get('description', '') + "</small>" if entry.get('description') else ""}
                    </div>
                    """, unsafe_allow_html=True)


# ==========================================
# FOOTER
# ==========================================
st.divider()
st.caption("""
⚠️ **Disclaimer**: Risk scores and anomaly alerts are based on general clinical guidelines
and should not be used as a substitute for professional medical advice.
""")
