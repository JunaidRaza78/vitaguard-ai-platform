"""
Profile Page
User profile management
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from components.auth import init_session_state, is_authenticated
from components.api_client import get_profile, logout

# Initialize
init_session_state()

# Page config
st.set_page_config(
    page_title="Profile - Family Health Manager",
    page_icon="👤",
    layout="wide"
)

# Check auth
if not is_authenticated():
    st.warning("Please login to access this page")
    st.switch_page("app.py")
    st.stop()

# Custom CSS
st.markdown("""
<style>
    .profile-card {
        background: linear-gradient(135deg, #f0fdfa 0%, #ccfbf1 100%);
        padding: 2rem;
        border-radius: 1rem;
        margin-bottom: 1.5rem;
    }
    .profile-avatar {
        width: 100px;
        height: 100px;
        background: #0d9488;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 2.5rem;
        margin: 0 auto 1rem;
    }
    .stat-card {
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("👤 Profile")
    
    user = st.session_state.get("user", {})
    st.markdown(f"**👤 {user.get('first_name', 'User')}**")
    
    st.divider()
    
    if st.button("🚪 Logout", use_container_width=True, type="primary"):
        logout()
        st.switch_page("app.py")

# Main content
st.title("👤 My Profile")

# Get user data
user = st.session_state.get("user", {})

# Profile card
st.markdown("""
<div class="profile-card">
    <div class="profile-avatar">👤</div>
</div>
""", unsafe_allow_html=True)

# User info in columns
col1, col2 = st.columns(2)

with col1:
    st.markdown("### Personal Information")
    
    st.text_input(
        "First Name",
        value=user.get("first_name", ""),
        disabled=True,
        key="first_name"
    )
    
    st.text_input(
        "Last Name", 
        value=user.get("last_name", ""),
        disabled=True,
        key="last_name"
    )
    
    st.text_input(
        "Email",
        value=user.get("email", ""),
        disabled=True,
        key="email"
    )

with col2:
    st.markdown("### Account Information")
    
    st.text_input(
        "Username",
        value=user.get("username", ""),
        disabled=True,
        key="username"
    )
    
    st.text_input(
        "User ID",
        value=user.get("id", ""),
        disabled=True,
        key="user_id"
    )
    
    # Account status
    is_verified = user.get("is_verified", False)
    is_active = user.get("is_active", True)
    
    status_text = "✅ Verified" if is_verified else "⚠️ Not Verified"
    st.text_input("Verification Status", value=status_text, disabled=True)

st.divider()

# Account Actions
st.markdown("### Account Actions")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔑 Change Password", use_container_width=True):
        st.info("Password change feature coming soon!")

with col2:
    if st.button("📧 Verify Email", use_container_width=True):
        st.info("Email verification feature coming soon!")

with col3:
    if st.button("🗑️ Delete Account", use_container_width=True):
        st.warning("Account deletion requires admin confirmation.")

st.divider()

# Session info
with st.expander("🔐 Session Information"):
    st.markdown(f"""
    - **Access Token**: `{st.session_state.get('access_token', 'N/A')[:20]}...`
    - **Session Active**: ✅ Yes
    """)
    
    if st.button("🔄 Refresh Session"):
        st.info("Session refreshed!")
        st.rerun()

# Disclaimer
st.divider()
st.caption("Your data is securely stored and handled according to healthcare privacy standards.")
