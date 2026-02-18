"""
Family & Notifications Dashboard
Combined page for family management and notification center
"""

import sys
from pathlib import Path

# Ensure components are importable
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from components.auth import init_session_state, is_authenticated
from components.api_client import (
    logout,
    get_my_families,
    create_family,
    get_family_members,
    add_family_member,
    remove_family_member,
    create_family_relationship,
    get_family_tree,
    get_my_notifications,
    get_medication_reminders,
    send_test_email,
    add_medication_reminder,
    send_notification,
    send_notification_to_members,
    send_direct_email,
)

# ==========================================
# INIT
# ==========================================
init_session_state()

st.set_page_config(
    page_title="Family & Notifications",
    page_icon="👨‍👩‍👧‍👦",
    layout="wide",
)

if not is_authenticated():
    st.warning("Please login to access this page")
    st.switch_page("app.py")
    st.stop()

# Current user info
current_user = st.session_state.get("user", {})
my_user_id = current_user.get("user_id", "")
my_name = f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip()
my_email = current_user.get("email", "")
is_superuser = current_user.get("is_superuser", False)

# ==========================================
# CUSTOM CSS
# ==========================================
st.markdown("""
<style>
    /* ========== Base Styles ========== */
    .family-card {
        background: linear-gradient(135deg, #f0fdfa 0%, #ccfbf1 100%);
        border-left: 4px solid #0d9488;
        padding: 1rem 1.25rem;
        border-radius: 0.75rem;
        margin-bottom: 0.75rem;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .family-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(13,148,136,0.15);
    }
    .member-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        padding: 0.75rem 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
    .notif-card {
        background: #ffffff;
        border-left: 4px solid #6366f1;
        padding: 1rem 1.25rem;
        border-radius: 0.75rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        transition: transform 0.2s, box-shadow 0.2s;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
    .notif-card:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .notif-card.high { border-left-color: #ef4444; }
    .notif-card.medium { border-left-color: #f59e0b; }
    .notif-card.low { border-left-color: #22c55e; }
    .badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 1rem;
        font-size: 0.7rem;
        font-weight: 600;
        color: white;
        white-space: nowrap;
    }
    .badge-admin { background: #0d9488; }
    .badge-parent { background: #6366f1; }
    .badge-member { background: #64748b; }
    .badge-pending { background: #f59e0b; }
    .badge-sent { background: #22c55e; }
    .badge-failed { background: #ef4444; }
    .badge-superuser { background: #dc2626; }
    .user-info-box {
        background: #f0fdfa;
        border: 1px solid #99f6e4;
        padding: 1rem;
        border-radius: 0.75rem;
        margin-bottom: 1rem;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
    .tree-node {
        background: #f0fdfa;
        border: 2px solid #0d9488;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        margin: 0.25rem 0;
        display: inline-block;
        max-width: 100%;
        word-wrap: break-word;
    }
    .tree-rel {
        color: #6366f1;
        font-weight: 600;
        font-size: 0.85rem;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
    .page-header {
        background: linear-gradient(135deg, #0d9488 0%, #14b8a6 100%);
        padding: 1.5rem;
        border-radius: 0.75rem;
        margin-bottom: 1.5rem;
    }
    .page-header h2 {
        color: white;
        margin: 0;
        font-size: 1.5rem;
    }
    .page-header p {
        color: #ccfbf1;
        margin: 0.25rem 0 0 0;
        font-size: 0.95rem;
    }
    .stats-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 0.75rem;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .stats-card .stat-number {
        font-size: 1.75rem;
        font-weight: 700;
        color: #0d9488;
    }
    .stats-card .stat-label {
        font-size: 0.8rem;
        color: #64748b;
        margin-top: 0.25rem;
    }

    /* ========== Responsive Styles ========== */
    @media (max-width: 768px) {
        .page-header {
            padding: 1rem;
        }
        .page-header h2 {
            font-size: 1.2rem;
        }
        .page-header p {
            font-size: 0.8rem;
        }
        .family-card {
            padding: 0.75rem 1rem;
        }
        .notif-card {
            padding: 0.75rem 1rem;
        }
        .user-info-box {
            padding: 0.75rem;
            font-size: 0.85rem;
        }
        .badge {
            font-size: 0.65rem;
            padding: 0.15rem 0.4rem;
        }
        .tree-node {
            display: block;
            margin: 0.25rem 0;
        }
    }

    /* ========== Streamlit Overrides for Responsiveness ========== */
    [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap;
        gap: 0.5rem;
    }
    [data-testid="column"] {
        min-width: 200px;
    }
    /* Make tabs responsive */
    .stTabs [data-baseweb="tab-list"] {
        flex-wrap: wrap;
        gap: 0.25rem;
    }
    /* Improve input fields on mobile */
    .stTextInput input, .stSelectbox select {
        font-size: 16px !important; /* Prevents zoom on iOS */
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    st.header("👨‍👩‍👧‍👦 Family & Alerts")

    st.markdown(f"**👤 {my_name or 'User'}**")
    st.caption(my_email)
    if is_superuser:
        st.markdown('<span class="badge badge-superuser">Super User</span>', unsafe_allow_html=True)

    st.divider()

    # Show current user ID for reference
    st.markdown("**Your User ID:**")
    st.code(my_user_id, language=None)

    st.divider()

    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()

    if st.button("🚪 Logout", use_container_width=True):
        logout()
        st.switch_page("app.py")

# ==========================================
# PAGE HEADER
# ==========================================
st.markdown(f"""
<div class="page-header">
    <h2>👨‍👩‍👧‍👦 Family & Notifications</h2>
    <p>Welcome, <strong>{my_name}</strong> — Manage your family & health notifications</p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# TABS
# ==========================================
tab_family, tab_notifications = st.tabs(["👨‍👩‍👧 Family", "🔔 Notifications"])


# ==========================================================================
# TAB 1: FAMILY
# ==========================================================================
with tab_family:

    # ---------- Fetch data first ----------
    families_data = get_my_families()
    families = families_data.get("families", [])

    # ---------- Stats Overview ----------
    total_families = len(families)
    total_members = 0
    for fam in families:
        fid = fam.get("familyId", "")
        if fid:
            mem_data = get_family_members(fid)
            total_members += len(mem_data.get("members", []))

    stat1, stat2, stat3 = st.columns(3)
    with stat1:
        st.markdown(
            f'<div class="stats-card">'
            f'<div class="stat-number">{total_families}</div>'
            f'<div class="stat-label">Families</div></div>',
            unsafe_allow_html=True,
        )
    with stat2:
        st.markdown(
            f'<div class="stats-card">'
            f'<div class="stat-number">{total_members}</div>'
            f'<div class="stat-label">Total Members</div></div>',
            unsafe_allow_html=True,
        )
    with stat3:
        su_label = "Super User" if is_superuser else "Member"
        st.markdown(
            f'<div class="stats-card">'
            f'<div class="stat-number">👤</div>'
            f'<div class="stat-label">{my_name} ({su_label})</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------- My Families ----------
    st.subheader("🏠 My Families")

    if families:
        for fam in families:
            fid = fam.get("familyId", "")
            fname = fam.get("name", "Unknown")
            created_by = fam.get("createdBy", "")
            is_creator = created_by == my_user_id
            creator_badge = '<span class="badge badge-admin">Creator</span>' if is_creator else ""

            st.markdown(
                f'<div class="family-card">'
                f'<strong>{fname}</strong> '
                f'{creator_badge}<br>'
                f'<span style="font-size:0.8rem;color:#64748b;">ID: {fid[:12]}...</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # Expandable members section
            with st.expander(f"👥 Members of {fname}"):
                members_data = get_family_members(fid)
                members = members_data.get("members", [])

                if members:
                    for m in members:
                        role = m.get("role", "member") or "member"
                        m_uid = m.get("userId", "")
                        is_me = m_uid == my_user_id
                        badge_class = f"badge-{role}" if role in ("admin", "parent", "member") else "badge-member"
                        st.markdown(
                            f'<div class="member-card">'
                            f'<strong>{m.get("name", "N/A")}</strong> '
                            f'<span class="badge {badge_class}">{role}</span>'
                            f'{" ⭐ (You)" if is_me else ""}<br>'
                            f'<span style="font-size:0.8rem;color:#64748b;">'
                            f'{m.get("email", "")} | ID: {m_uid[:12]}...</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                else:
                    st.info("No members yet. Add members below.")

                # Add member form
                st.markdown("**Add Member**")
                col_uid, col_role, col_btn = st.columns([3, 2, 1])
                with col_uid:
                    new_uid = st.text_input("User ID", key=f"add_uid_{fid}", placeholder="Enter user ID to add")
                with col_role:
                    new_role = st.selectbox("Role", ["member", "parent", "admin"], key=f"add_role_{fid}")
                with col_btn:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("Add", key=f"add_btn_{fid}", use_container_width=True):
                        if new_uid:
                            with st.spinner("Adding..."):
                                result = add_family_member(fid, new_uid, new_role)
                            if result.get("error") or result.get("detail"):
                                st.error(result.get("detail", result.get("error", "Failed")))
                            else:
                                st.success("Member added!")
                                st.rerun()
                        else:
                            st.warning("Enter a user ID")
    else:
        st.info("You're not part of any family yet. Create one below!")

    st.divider()

    # ---------- Create Family ----------
    st.subheader("➕ Create New Family")
    st.caption(f"You ({my_name}) will be the admin/creator of this family")

    col_name, col_create = st.columns([4, 1])
    with col_name:
        family_name = st.text_input("Family Name", placeholder="e.g. Khan Family")
    with col_create:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Create", use_container_width=True, type="primary"):
            if family_name:
                with st.spinner("Creating family..."):
                    result = create_family(family_name)
                if result.get("familyId"):
                    st.success(f"Family '{family_name}' created! You are the admin.")
                    st.rerun()
                else:
                    st.error(result.get("detail", result.get("error", "Failed to create family")))
            else:
                st.warning("Enter a family name")

    st.divider()

    # ---------- Build known members lookup for dropdowns ----------
    known_members = {}  # {userId: "Name (email)"}
    # Add current user first
    known_members[my_user_id] = f"{my_name} ({my_email}) ⭐ You"
    # Collect members from all families
    for fam in families:
        fid = fam.get("familyId", "")
        if fid:
            mem_data = get_family_members(fid)
            for m in mem_data.get("members", []):
                uid = m.get("userId", "")
                if uid and uid not in known_members:
                    m_name = m.get("name", "Unknown")
                    m_email = m.get("email", "")
                    known_members[uid] = f"{m_name} ({m_email})"

    member_options = list(known_members.keys())
    member_labels = [known_members[uid] for uid in member_options]

    # ---------- Create Relationship ----------
    st.subheader("🔗 Create Family Relationship")
    st.caption("Link yourself or family members with relationships")

    col1, col2, col3 = st.columns(3)
    with col1:
        from_idx = st.selectbox(
            "From",
            range(len(member_options)),
            format_func=lambda i: member_labels[i],
            key="rel_from",
        )
        rel_user1 = member_options[from_idx] if member_options else ""
    with col2:
        rel_type = st.selectbox(
            "Relationship",
            ["PARENT_OF", "CHILD_OF", "SPOUSE_OF", "SIBLING_OF"],
            key="rel_type",
        )
    with col3:
        # Filter out the "from" user for the "to" dropdown
        to_options = [i for i in range(len(member_options)) if i != from_idx]
        if to_options:
            to_idx = st.selectbox(
                "To",
                to_options,
                format_func=lambda i: member_labels[i],
                key="rel_to",
            )
            rel_user2 = member_options[to_idx]
        else:
            st.info("Add more members first")
            rel_user2 = ""

    if st.button("Create Relationship", type="primary"):
        if rel_user1 and rel_user2:
            with st.spinner("Creating relationship..."):
                result = create_family_relationship(rel_user1, rel_type, rel_user2)
            if result.get("error") or result.get("detail"):
                st.error(result.get("detail", result.get("error", "Failed")))
            else:
                st.success(f"{rel_type} relationship created!")
                st.rerun()
        else:
            st.warning("Select both members")

    st.divider()

    # ---------- Family Tree ----------
    st.subheader("🌳 Family Tree")

    tree_idx = st.selectbox(
        "View tree for",
        range(len(member_options)),
        format_func=lambda i: member_labels[i],
        key="tree_member",
    )
    tree_uid = member_options[tree_idx] if member_options else my_user_id
    tree_depth = st.slider("Depth", 1, 4, 2, key="tree_depth")

    if st.button("Load Family Tree"):
        if tree_uid:
            with st.spinner("Loading family tree..."):
                tree_data = get_family_tree(tree_uid, tree_depth)

            nodes = tree_data.get("nodes", [])
            rels = tree_data.get("relationships", [])

            if nodes:
                st.markdown("**Family Members:**")
                for node in nodes:
                    is_self = node.get("userId") == my_user_id
                    label = "⭐ YOU" if is_self else ""
                    st.markdown(
                        f'<div class="tree-node">'
                        f'👤 <strong>{node.get("name", "Unknown")}</strong> {label}<br>'
                        f'<span style="font-size:0.75rem;color:#64748b;">{node.get("email", "")}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                if rels:
                    st.markdown("**Relationships:**")
                    for rel in rels:
                        # Resolve UUIDs to names
                        src_id = rel.get("source", "")
                        tgt_id = rel.get("target", "")
                        src_name = known_members.get(src_id, src_id[:12] + "...")
                        tgt_name = known_members.get(tgt_id, tgt_id[:12] + "...")
                        # Clean up display name (remove email part for brevity)
                        src_short = src_name.split(" (")[0] if " (" in src_name else src_name
                        tgt_short = tgt_name.split(" (")[0] if " (" in tgt_name else tgt_name
                        st.markdown(
                            f'<span class="tree-rel">'
                            f'{src_short} —[ {rel.get("type", "")} ]→ {tgt_short}'
                            f'</span>',
                            unsafe_allow_html=True,
                        )
            else:
                st.info("No family connections found. Create relationships first!")
        else:
            st.warning("Select a member")


# ==========================================================================
# TAB 2: NOTIFICATIONS
# ==========================================================================
with tab_notifications:

    # ---------- Fetch notification data ----------
    with st.spinner("Loading notifications..."):
        notif_data = get_my_notifications(limit=50)
    all_notifications = notif_data.get("notifications", [])

    with st.spinner("Loading medication reminders..."):
        med_data = get_medication_reminders()
    reminders = med_data.get("reminders", [])

    # Load family members for recipient selector
    _fam_list = get_my_families().get("families", [])
    _member_options = {}   # {display_name: email}
    for _fam in _fam_list:
        _fam_id = _fam.get("family_id") or _fam.get("familyId", "")
        if _fam_id:
            _members = get_family_members(_fam_id).get("members", [])
            for _m in _members:
                _email = _m.get("email", "")
                _name = _m.get("name") or _m.get("username") or _email
                if _email and _email != my_email:
                    _member_options[f"{_name} ({_email})"] = _email

    # Merge Neo4j medication reminders into notifications list
    # so medications without PostgreSQL records also appear
    existing_med_ids = {
        n.get("notification_metadata", {}).get("medication_id") or n.get("metadata", {}).get("medication_id")
        for n in all_notifications
        if n.get("type", "").lower() == "medication_reminder"
    }
    for rem in reminders:
        med_id = rem.get("medication_id") or rem.get("medicationId", "")
        if med_id not in existing_med_ids:
            times_str = ", ".join(rem.get("reminder_times") or rem.get("reminderTimes") or [])
            freq = rem.get("frequency", "")
            dosage = rem.get("dosage", "")
            med_name = rem.get("medication_name") or rem.get("name", "Medication")
            all_notifications.append({
                "type": "medication_reminder",
                "status": "pending",
                "priority": "medium",
                "title": f"💊 {med_name} — {dosage}",
                "message": f"Take {med_name} ({dosage}) {freq}. Reminder times: {times_str}.",
                "created_at": rem.get("start_date") or rem.get("startDate", ""),
                "_from_neo4j": True,
            })

    # ---------- Notification Stats ----------
    n_total = len(all_notifications)
    n_pending = sum(1 for n in all_notifications if n.get("status") == "pending")
    n_sent = sum(1 for n in all_notifications if n.get("status") == "sent")

    ns1, ns2, ns3, ns4 = st.columns(4)
    with ns1:
        st.markdown(
            f'<div class="stats-card">'
            f'<div class="stat-number">{n_total}</div>'
            f'<div class="stat-label">Total</div></div>',
            unsafe_allow_html=True,
        )
    with ns2:
        st.markdown(
            f'<div class="stats-card">'
            f'<div class="stat-number" style="color:#f59e0b;">{n_pending}</div>'
            f'<div class="stat-label">Pending</div></div>',
            unsafe_allow_html=True,
        )
    with ns3:
        st.markdown(
            f'<div class="stats-card">'
            f'<div class="stat-number" style="color:#22c55e;">{n_sent}</div>'
            f'<div class="stat-label">Sent</div></div>',
            unsafe_allow_html=True,
        )
    with ns4:
        st.markdown(
            f'<div class="stats-card">'
            f'<div class="stat-number" style="color:#ef4444;">{len(reminders)}</div>'
            f'<div class="stat-label">Med Reminders</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------- Send Test Email ----------
    st.subheader("📧 Test Email Notification")
    st.caption(f"Send a test email to: **{my_email}**")

    if st.button("📧 Send Test Email", type="primary"):
        with st.spinner("Sending test email..."):
            result = send_test_email()
        if result.get("success"):
            st.success(f"Test email sent to **{result.get('recipient', my_email)}**! Check your inbox.")
        else:
            st.error(result.get("message", result.get("error", result.get("detail", "Failed to send test email"))))

    st.divider()

    # ---------- Filters ----------
    col_type, col_status = st.columns(2)
    with col_type:
        notif_type_filter = st.selectbox(
            "Filter by Type",
            ["ALL", "MEDICATION_REMINDER", "HEALTH_ALERT", "APPOINTMENT_REMINDER", "SYSTEM"],
            key="notif_type",
        )
    with col_status:
        notif_status_filter = st.selectbox(
            "Filter by Status",
            ["ALL", "PENDING", "SENT", "FAILED"],
            key="notif_status",
        )

    st.divider()

    # ---------- Add Medication Reminder ----------
    st.subheader("➕ Add Medication Reminder")
    with st.form("add_med_form", clear_on_submit=True):
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            med_name = st.text_input("Medication Name", placeholder="e.g. Paracetamol")
            med_dosage = st.text_input("Dosage", placeholder="e.g. 500mg")
        with col_m2:
            med_freq = st.selectbox(
                "Frequency",
                ["daily", "twice_daily", "three_times_daily", "weekly", "as_needed"],
            )
            med_times = st.text_input(
                "Reminder Times (HH:MM, comma separated)",
                placeholder="e.g. 08:00, 14:00, 20:00",
            )
        med_start = st.date_input("Start Date")
        submitted_med = st.form_submit_button("💊 Add Medication Reminder", type="primary", use_container_width=True)

    if submitted_med:
        if med_name and med_dosage and med_times:
            times_list = [t.strip() for t in med_times.split(",") if t.strip()]
            if times_list:
                with st.spinner("Adding medication reminder..."):
                    result = add_medication_reminder(
                        medication_name=med_name,
                        dosage=med_dosage,
                        frequency=med_freq,
                        reminder_times=times_list,
                        start_date=str(med_start),
                    )
                if result.get("success"):
                    st.success(result.get("message", f"'{med_name}' added! Reminders: {', '.join(times_list)}"))
                    st.rerun()
                else:
                    st.error(result.get("detail", result.get("error", "Failed to add medication reminder")))
            else:
                st.warning("Enter at least one reminder time in HH:MM format")
        else:
            st.warning("Please fill in Medication Name, Dosage, and Reminder Times")

    st.divider()

    # ---------- Medication Reminders ----------
    st.subheader("💊 Medication Reminders")

    if reminders:
        for rem in reminders:
            med_name = rem.get("medication_name", "Unknown")
            dosage = rem.get("dosage", "")
            times = rem.get("reminder_times", [])
            freq = rem.get("frequency", "")
            st.markdown(
                f'<div class="notif-card high">'
                f'💊 <strong>{med_name}</strong> — {dosage}<br>'
                f'<span style="font-size:0.8rem;color:#64748b;">'
                f'Frequency: {freq} | Reminder times: {", ".join(times) if times else "Not set"}'
                f'</span></div>',
                unsafe_allow_html=True,
            )
    else:
        st.info("No active medication reminders.")

    st.divider()

    # ---------- All Notifications ----------
    st.subheader("🔔 Notifications")

    # Apply filters
    filtered = all_notifications
    if notif_status_filter != "ALL":
        filtered = [n for n in filtered if n.get("status", "").upper() == notif_status_filter]

    display_notifs = []
    for notif in filtered:
        n_type = notif.get("type", "system")
        if notif_type_filter != "ALL" and n_type.upper() != notif_type_filter:
            continue
        display_notifs.append(notif)

    if display_notifs:
        for idx, notif in enumerate(display_notifs):
            n_type = notif.get("type", "system")
            n_status = notif.get("status", "pending")
            n_priority = notif.get("priority", "medium").lower()
            n_title = notif.get("title", "Notification")
            n_message = notif.get("message", "")
            n_time = notif.get("created_at", "")
            n_id = notif.get("notification_id", "")
            from_neo4j = notif.get("_from_neo4j", False)

            priority_class = n_priority if n_priority in ("high", "medium", "low") else "medium"
            status_badge = f"badge-{n_status}" if n_status in ("pending", "sent", "failed") else "badge-pending"

            icon_map = {
                "medication_reminder": "💊",
                "health_alert": "🚨",
                "appointment_reminder": "📅",
                "system": "🔧",
            }
            icon = icon_map.get(n_type.lower(), "🔔")
            # Status circle icon
            status_icon = "🟡" if n_status == "pending" else ("🟢" if n_status == "sent" else "🔴")

            st.markdown(
                f'<div class="notif-card {priority_class}">'
                f'{icon} <strong>{n_title}</strong> '
                f'{status_icon} <span class="badge {status_badge}">{n_status}</span><br>'
                f'<span style="font-size:0.85rem;">{n_message}</span><br>'
                f'<span style="font-size:0.75rem;color:#94a3b8;">{n_time}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            # Send section — for ALL pending notifications (PostgreSQL + Neo4j)
            if n_status == "pending":
                sc1, sc2 = st.columns([3, 1])
                with sc1:
                    all_member_keys = list(_member_options.keys())
                    selected_keys = st.multiselect(
                        "📨 Send to:",
                        options=all_member_keys,
                        default=[],
                        key=f"recipients_{n_id or 'neo4j'}_{idx}",
                        placeholder="Select family members (empty = only yourself)",
                    )
                with sc2:
                    st.write("")
                    if st.button("📧 Send Now", key=f"send_notif_{n_id or 'neo4j'}_{idx}", use_container_width=True, type="primary"):
                        selected_emails = [_member_options[k] for k in selected_keys]
                        all_emails = list(set([my_email] + selected_emails))
                        with st.spinner("Sending..."):
                            if from_neo4j or not n_id:
                                # Neo4j notification — send directly via email
                                result = send_direct_email(n_title, n_message, all_emails)
                            elif selected_emails:
                                # PostgreSQL + extra recipients
                                result = send_notification_to_members(n_id, all_emails)
                            else:
                                # PostgreSQL — send to self only
                                result = send_notification(n_id)
                        if result.get("success"):
                            names = ", ".join(selected_keys) if selected_keys else "yourself"
                            st.success(f"✅ Sent to: {names}!")
                            st.rerun()
                        else:
                            st.error(result.get("message", result.get("detail", "Failed to send")))

        st.caption(f"Showing {len(display_notifs)} of {n_total} notifications")
    else:
        st.info("No notifications found matching your filters.")

# ==========================================
# FOOTER
# ==========================================
st.markdown("---")
st.caption("⚠️ This is a health management tool. Always consult your healthcare provider for medical decisions.")
