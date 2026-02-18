"""
Medical Chat Page
AI-powered medical assistant with RAG
"""

import streamlit as st
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from components.auth import init_session_state, is_authenticated
from components.api_client import send_message, authenticated_request, API_BASE_URL, logout

# Initialize
init_session_state()

# Page config
st.set_page_config(
    page_title="Medical Chat - Family Health Manager",
    page_icon="💬",
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
    .chat-message {
        padding: 1rem;
        border-radius: 0.75rem;
        margin-bottom: 0.75rem;
    }
    .user-message {
        background: #e0f2fe;
        margin-left: 20%;
    }
    .assistant-message {
        background: #f0fdf4;
        margin-right: 20%;
    }
    .source-badge {
        display: inline-block;
        background: #0d9488;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.8rem;
        margin-right: 0.5rem;
        margin-top: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("💬 Chat Settings")
    
    user = st.session_state.get("user", {})
    st.markdown(f"**👤 {user.get('first_name', 'User')}**")
    
    st.divider()
    
    # Specialty filter
    specialties = [
        "All Specialties",
        "cardiology",
        "endocrinology",
        "neurology",
        "oncology",
        "pediatrics",
        "gastroenterology",
        "infectious_disease",
        "pulmonology",
        "dermatology",
        "orthopedics"
    ]
    
    specialty = st.selectbox("🏥 Medical Specialty", specialties)
    if specialty == "All Specialties":
        specialty = None
    
    # Advanced settings
    with st.expander("⚙️ Advanced Settings"):
        top_k = st.slider("Documents to retrieve", 1, 10, 5)
        st.caption("Temperature is locked at 0.3 for medical safety")
    
    st.divider()
    
    # Conversation management
    if st.button("🔄 New Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.conversation_id = str(uuid.uuid4())
        st.rerun()
    
    st.divider()
    
    if st.button("🚪 Logout", use_container_width=True):
        logout()
        st.switch_page("app.py")

# Main content
st.title("💬 Medical Chat")
st.markdown("Ask questions about health conditions, symptoms, treatments, and more.")

# Initialize conversation
if "conversation_id" not in st.session_state or not st.session_state.conversation_id:
    st.session_state.conversation_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        # Show sources if available
        if msg.get("sources") and len(msg["sources"]) > 0:
            with st.expander("📚 Sources"):
                for source in msg["sources"]:
                    file_name = source.get("file", "Unknown")
                    relevance = source.get("relevance", 0)
                    st.markdown(f"**{file_name}** - Relevance: {relevance:.1f}%")

# Chat input
if prompt := st.chat_input("Ask a medical question..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # ---- EMERGENCY DETECTION ----
    try:
        emg = authenticated_request("post", f"{API_BASE_URL}/api/v1/labs/emergency-check", json={"message": prompt})
        if emg.get("is_emergency"):
            severity = emg.get("severity", "urgent")
            emg_response = emg.get("response", "")
            if emg.get("call_911"):
                st.error("🚨 **EMERGENCY DETECTED — CALL 911 IMMEDIATELY**")
            else:
                st.warning(f"🔴 Urgent medical concern detected.")
            with st.expander("🚨 Emergency Guidance", expanded=True):
                st.markdown(emg_response)
    except Exception:
        pass  # Non-blocking — don't prevent chat on failure

    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            start_time = time.time()
            
            result = send_message(
                message=prompt,
                conversation_id=st.session_state.conversation_id,
                specialty=specialty,
                top_k=top_k
            )
            
            elapsed = time.time() - start_time
        
        if result.get("status") == "success":
            answer = result.get("answer", "I couldn't generate a response.")
            sources = result.get("sources", [])
            context_used = result.get("context_used", False)
            storage = result.get("storage", "unknown")
            
            st.markdown(answer)
            
            # Metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("⏱️ Response Time", f"{elapsed:.1f}s")
            col2.metric("📚 Context Used", "Yes" if context_used else "No")
            col3.metric("💾 Source", storage)
            
            # Sources
            if sources:
                with st.expander("📚 Sources"):
                    for source in sources:
                        file_name = source.get("file", "Unknown")
                        relevance = source.get("relevance", 0)
                        st.markdown(f"**{file_name}** - Relevance: {relevance:.1f}%")
            
            # Save to history
            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "sources": sources
            })
        else:
            error_msg = result.get("error", "An error occurred")
            st.error(f"Error: {error_msg}")

# Disclaimer
st.divider()
st.caption("""
⚠️ **Medical Disclaimer**: This AI provides medical information only. 
It does not diagnose or prescribe treatment. Always consult a healthcare professional.
""")
