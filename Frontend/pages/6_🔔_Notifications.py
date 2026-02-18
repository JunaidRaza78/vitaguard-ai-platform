"""
Notifications Center Page
View, manage, and act on notifications — medication reminders,
vaccination alerts, and proactive health alerts.
"""

import streamlit as st
import sys
from datetime import datetime, date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from components.auth import init_session_state, is_authenticated
from components.api_client import (
    get_my_notifications,
    get_medication_reminders,
    add_medication_reminder,
    send_notification,
    send_test_email,
    logout,
)

# Initialize
init_session_state()

# Page config
st.set_page_config(
    page_title="Notifications - Family Health Manager",
    page_icon="🔔",
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
    .notif-card {
        padding: 1rem;
        border-radius: 0.75rem;
        margin-bottom: 0.75rem;
        border-left: 4px solid;
        background: #f8fafc;
    }
    .notif-medication { border-color: #3b82f6; }
    .notif-vaccination { border-color: #8b5cf6; }
    .notif-health_alert { border-color: #ef4444; }
    .notif-proactive { border-color: #f59e0b; }
    .notif-system { border-color: #6b7280; }
    .notif-title { font-weight: 600; font-size: 1rem; margin-bottom: 0.25rem; }
    .notif-body { color: #475569; font-size: 0.9rem; }
    .notif-meta { color: #94a3b8; font-size: 0.75rem; margin-top: 0.5rem; }
    .status-badge {
        display: inline-block;
        padding: 0.15rem 0.5rem;
        border-radius: 1rem;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    .badge-pending { background: #fef3c7; color: #92400e; }
    .badge-sent { background: #d1fae5; color: #065f46; }
    .badge-failed { background: #fee2e2; color: #991b1b; }
    .badge-scheduled { background: #dbeafe; color: #1e40af; }
    .med-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 0.75rem;
        margin-bottom: 0.75rem;
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
    st.header("🔔 Notifications")

    user = st.session_state.get("user", {})
    st.markdown(f"**👤 {user.get('first_name', 'User')}**")

    st.divider()

    view = st.radio(
        "📋 View",
        ["All Notifications", "Medication Reminders", "Add Medication"],
        index=0,
    )

    st.divider()

    # Quick actions
    st.subheader("⚡ Quick Actions")
    if st.button("📧 Send Test Email", use_container_width=True):
        result = send_test_email()
        if result.get("success") or result.get("status") == "sent":
            st.success("Test email sent!")
        else:
            st.error(result.get("error", "Failed"))

    st.divider()

    if st.button("🚪 Logout", use_container_width=True):
        logout()
        st.switch_page("app.py")


# ==========================================
# HELPER: Render Notification Card
# ==========================================
def render_notification(notif: dict):
    """Render a single notification card."""
    ntype = notif.get("type", "system")
    css_type = "medication" if "medication" in ntype else (
        "vaccination" if "vaccination" in ntype else (
        "health_alert" if "alert" in ntype or "health" in ntype else (
        "proactive" if "proactive" in ntype else "system"
    )))

    status = notif.get("status", "pending")
    badge_class = f"badge-{status}" if status in ("pending", "sent", "failed", "scheduled") else "badge-pending"

    icon_map = {
        "medication_reminder": "💊",
        "vaccination_reminder": "💉",
        "health_alert": "🚨",
        "proactive_alert": "⚡",
        "appointment_reminder": "📅",
        "system": "🔔",
    }
    icon = icon_map.get(ntype, "🔔")

    title = notif.get("title", "Notification")
    message = notif.get("message", "")
    created = notif.get("created_at", "")
    if isinstance(created, str) and len(created) > 16:
        created = created[:16].replace("T", " ")

    st.markdown(f"""
    <div class="notif-card notif-{css_type}">
        <div class="notif-title">{icon} {title}</div>
        <div class="notif-body">{message}</div>
        <div class="notif-meta">
            {created} &nbsp;|&nbsp;
            <span class="status-badge {badge_class}">{status}</span> &nbsp;|&nbsp;
            {ntype.replace('_', ' ').title()}
        </div>
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# MAIN CONTENT
# ==========================================
st.title("🔔 Notifications Center")


# ------------------------------------------
# ALL NOTIFICATIONS
# ------------------------------------------
if view == "All Notifications":
    st.markdown('<div class="section-header">📬 Recent Notifications</div>', unsafe_allow_html=True)

    # Filters
    col1, col2 = st.columns([1, 3])
    with col1:
        status_filter = st.selectbox("Status", ["ALL", "pending", "sent", "failed", "scheduled"])

    with st.spinner("Loading notifications..."):
        result = get_my_notifications(status_filter=status_filter, limit=50)

    if isinstance(result, dict) and result.get("error"):
        st.info("No notifications yet.")
    else:
        notifications = []
        if isinstance(result, dict):
            notifications = result.get("notifications", [])
        elif isinstance(result, list):
            notifications = result

        if not notifications:
            st.info("No notifications found. Medication reminders and health alerts will appear here.")
        else:
            # Summary metrics
            m1, m2, m3, m4 = st.columns(4)
            pending = sum(1 for n in notifications if n.get("status") == "pending")
            sent = sum(1 for n in notifications if n.get("status") == "sent")
            failed = sum(1 for n in notifications if n.get("status") == "failed")
            m1.metric("Total", len(notifications))
            m2.metric("⏳ Pending", pending)
            m3.metric("✅ Sent", sent)
            m4.metric("❌ Failed", failed)

            st.divider()

            for notif in notifications:
                render_notification(notif)

                # Action button for pending notifications
                if notif.get("status") == "pending":
                    nid = notif.get("notification_id", "")
                    if nid and st.button(f"📤 Send Now", key=f"send_{nid}"):
                        send_result = send_notification(nid)
                        if send_result.get("success"):
                            st.success("Sent!")
                            st.rerun()
                        else:
                            st.error(send_result.get("error", "Failed to send"))


# ------------------------------------------
# MEDICATION REMINDERS
# ------------------------------------------
elif view == "Medication Reminders":
    st.markdown('<div class="section-header">💊 Active Medication Reminders</div>', unsafe_allow_html=True)

    with st.spinner("Loading medication reminders..."):
        result = get_medication_reminders()

    if isinstance(result, dict) and result.get("error"):
        st.info("No medication data available.")
    else:
        reminders = []
        if isinstance(result, dict):
            reminders = result.get("reminders", [])
        elif isinstance(result, list):
            reminders = result

        if not reminders:
            st.info("No active medications with reminders. Add a medication in the **Add Medication** tab.")
        else:
            st.markdown(f"**{len(reminders)} active medications**")

            for med in reminders:
                name = med.get("medication_name", "Unknown")
                dosage = med.get("dosage", "")
                frequency = med.get("frequency", "")
                times = med.get("reminder_times", [])
                times_str = ", ".join(times) if times else "No times set"

                st.markdown(f"""
                <div class="med-card">
                    <div style="font-size: 1.1rem; font-weight: 600;">💊 {name}</div>
                    <div style="opacity: 0.9; margin-top: 0.25rem;">
                        {dosage} — {frequency}
                    </div>
                    <div style="opacity: 0.8; font-size: 0.85rem; margin-top: 0.5rem;">
                        ⏰ Reminder times: {times_str}
                    </div>
                </div>
                """, unsafe_allow_html=True)


# ------------------------------------------
# ADD MEDICATION
# ------------------------------------------
elif view == "Add Medication":
    st.markdown('<div class="section-header">➕ Add Medication Reminder</div>', unsafe_allow_html=True)

    with st.form("add_med_form"):
        med_name = st.text_input("Medication Name", placeholder="e.g., Metformin")
        dosage = st.text_input("Dosage", placeholder="e.g., 500mg")

        frequency = st.selectbox("Frequency", [
            "Once daily",
            "Twice daily",
            "Three times daily",
            "Every 8 hours",
            "Every 12 hours",
            "Once weekly",
            "As needed",
        ])

        st.markdown("**Reminder Times** (select times for daily reminders)")
        time_cols = st.columns(3)
        times = []
        with time_cols[0]:
            t1 = st.time_input("Time 1", value=None, key="t1")
            if t1:
                times.append(t1.strftime("%H:%M"))
        with time_cols[1]:
            t2 = st.time_input("Time 2 (optional)", value=None, key="t2")
            if t2:
                times.append(t2.strftime("%H:%M"))
        with time_cols[2]:
            t3 = st.time_input("Time 3 (optional)", value=None, key="t3")
            if t3:
                times.append(t3.strftime("%H:%M"))

        start_date = st.date_input("Start Date", value=date.today())

        submitted = st.form_submit_button("💾 Add Medication", use_container_width=True, type="primary")

        if submitted:
            if not med_name or not dosage:
                st.warning("Please fill in medication name and dosage.")
            elif not times:
                st.warning("Please set at least one reminder time.")
            else:
                with st.spinner("Adding medication..."):
                    result = add_medication_reminder(
                        medication_name=med_name,
                        dosage=dosage,
                        frequency=frequency,
                        reminder_times=times,
                        start_date=str(start_date),
                    )
                if result.get("success") or result.get("medication_id"):
                    st.success(f"✅ {med_name} added with {len(times)} reminder(s)!")
                    st.balloons()
                elif result.get("error"):
                    st.error(f"Error: {result.get('error')}")
                else:
                    st.error("Failed to add medication.")


# ==========================================
# FOOTER
# ==========================================
st.divider()
st.caption("Notifications are sent via email when configured. Check your inbox for medication reminders.")
