"""
Authentication Components for Streamlit
"""

import streamlit as st
from components.api_client import login, register


def init_session_state():
    """Initialize session state variables"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "access_token" not in st.session_state:
        st.session_state.access_token = None
    if "refresh_token" not in st.session_state:
        st.session_state.refresh_token = None
    if "user" not in st.session_state:
        st.session_state.user = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = None


def is_authenticated() -> bool:
    """Check if user is authenticated"""
    return st.session_state.get("authenticated", False) and st.session_state.get("access_token")


def login_form():
    """Display login form"""
    st.subheader("🔐 Login")
    
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        submit = st.form_submit_button("Login", use_container_width=True, type="primary")
        
        if submit:
            if not email or not password:
                st.error("Please fill in all fields")
                return
            
            with st.spinner("Logging in..."):
                result = login(email, password)
            
            if result.get("success"):
                st.success("Login successful!")
                st.rerun()
            else:
                st.error(result.get("error", "Login failed"))


def register_form():
    """Display registration form"""
    st.subheader("📝 Create Account")
    
    with st.form("register_form"):
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("First Name", placeholder="John")
        with col2:
            last_name = st.text_input("Last Name", placeholder="Doe")
        
        email = st.text_input("Email", placeholder="you@example.com")
        username = st.text_input("Username", placeholder="johndoe")
        password = st.text_input("Password", type="password", placeholder="Min 8 chars, upper, lower, digit, special")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        submit = st.form_submit_button("Register", use_container_width=True, type="primary")
        
        if submit:
            if not all([email, username, password, confirm_password]):
                st.error("Please fill in all required fields")
                return
            
            if password != confirm_password:
                st.error("Passwords do not match")
                return
            
            if len(password) < 8:
                st.error("Password must be at least 8 characters")
                return
            
            with st.spinner("Creating account..."):
                result = register(email, username, password, first_name, last_name)
            
            if result.get("success"):
                st.success("Registration successful! Please login.")
            else:
                st.error(result.get("error", "Registration failed"))


def auth_page():
    """Display authentication page with login/register tabs"""
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1>🏥 Family Health Manager</h1>
        <p style="color: #666; font-size: 1.1rem;">AI-Powered Healthcare Assistant</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        login_form()
    
    with tab2:
        register_form()
    
    st.divider()
    st.caption("⚠️ Medical Disclaimer: This app provides health information only. Always consult a healthcare professional.")
