"""
Family Health Manager - Streamlit Frontend
Main application entry point with authentication
"""

import streamlit as st
import sys
from pathlib import Path

# Add components to path
sys.path.insert(0, str(Path(__file__).parent))

from components.auth import init_session_state, is_authenticated, auth_page
from components.api_client import health_check

# Page config
st.set_page_config(
    page_title="Family Health Manager",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #0d9488;
        --secondary-color: #14b8a6;
        --background-color: #f0fdfa;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #0d9488 0%, #14b8a6 100%);
        padding: 2rem;
        border-radius: 1rem;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Card styling */
    .info-card {
        background: white;
        padding: 1.5rem;
        border-radius: 0.75rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-bottom: 1rem;
        border-left: 4px solid #0d9488;
    }
    
    /* Metrics styling */
    .metric-card {
        background: linear-gradient(135deg, #f0fdfa 0%, #ccfbf1 100%);
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 0.5rem;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Sidebar user info */
    .user-info {
        background: #f0fdfa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
init_session_state()

# Check authentication
if not is_authenticated():
    auth_page()
else:
    # Welcome page for authenticated users
    user = st.session_state.get("user", {})
    
    # Sidebar with user info
    with st.sidebar:
        st.markdown(f"""
        <div class="user-info">
            <strong>👤 {user.get('first_name', '')} {user.get('last_name', '')}</strong><br>
            <small style="color: #666;">{user.get('email', '')}</small>
        </div>
        """, unsafe_allow_html=True)
        
        # API Status
        if st.button("🔄 Check API Status", use_container_width=True):
            status = health_check()
            if status.get("status") == "healthy":
                st.success("All systems operational")
            else:
                st.warning("Some services may be unavailable")
    
    # Main content
    st.markdown("""
    <div class="main-header">
        <h1>🏥 Family Health Manager</h1>
        <p>AI-Powered Healthcare Assistant for Your Family</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="info-card">
            <h3>💬 Medical Chat</h3>
            <p>Chat with our AI assistant for medical information and guidance.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Go to Chat", key="chat_btn", use_container_width=True):
            st.switch_page("pages/1_💬_Chat.py")
    
    with col2:
        st.markdown("""
        <div class="info-card">
            <h3>📄 Documents</h3>
            <p>Upload medical PDFs and search through your health records.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Go to Documents", key="docs_btn", use_container_width=True):
            st.switch_page("pages/2_📄_Documents.py")
    
    with col3:
        st.markdown("""
        <div class="info-card">
            <h3>👤 Profile</h3>
            <p>Manage your account settings and preferences.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Go to Profile", key="profile_btn", use_container_width=True):
            st.switch_page("pages/3_👤_Profile.py")
    
    # Health tips section
    st.markdown("---")
    st.subheader("💡 Health Tips")
    
    tips = [
        "🥗 Eat a balanced diet with plenty of fruits and vegetables",
        "🏃 Aim for at least 30 minutes of physical activity daily",
        "💤 Get 7-9 hours of quality sleep each night",
        "💧 Stay hydrated by drinking 8 glasses of water daily",
        "🧘 Practice stress management through meditation or yoga"
    ]
    
    for tip in tips:
        st.info(tip)
    
    # Disclaimer
    st.markdown("---")
    st.caption("""
    ⚠️ **Medical Disclaimer**: This application provides medical information only. 
    It does not diagnose or prescribe treatment. Always consult a licensed healthcare professional 
    for medical advice, diagnosis, or treatment.
    """)
