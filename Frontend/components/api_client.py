"""
API Client for Family Health Manager Backend
Handles all HTTP requests with automatic token refresh
"""

import requests
import streamlit as st
from typing import Optional, Dict, Any

API_BASE_URL = "http://localhost:8000"


def get_headers() -> Dict[str, str]:
    """Get headers with auth token if available"""
    headers = {"Content-Type": "application/json"}
    if "access_token" in st.session_state and st.session_state.access_token:
        headers["Authorization"] = f"Bearer {st.session_state.access_token}"
    return headers


def handle_response(response: requests.Response) -> Dict[str, Any]:
    """Handle API response and errors"""
    try:
        data = response.json()
    except:
        data = {"error": response.text}
    
    if response.status_code == 401:
        # Token expired, try refresh
        if refresh_token():
            return None  # Signal to retry
        else:
            st.session_state.clear()
            st.error("Session expired. Please login again.")
    
    return data


# ==========================================
# AUTHENTICATION
# ==========================================

def register(email: str, username: str, password: str, first_name: str = "", last_name: str = "") -> Dict:
    """Register a new user"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/auth/register",
            json={
                "email": email,
                "username": username,
                "password": password,
                "first_name": first_name,
                "last_name": last_name
            },
            timeout=30
        )
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


def login(email: str, password: str) -> Dict:
    """Login and get JWT tokens"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/auth/login",
            json={"email": email, "password": password},
            timeout=30
        )
        data = response.json()
        
        # Check for successful login - backend returns access_token on success
        if response.status_code == 200 and data.get("access_token"):
            st.session_state.access_token = data.get("access_token")
            st.session_state.refresh_token = data.get("refresh_token")
            st.session_state.user = data.get("user")
            st.session_state.authenticated = True
            data["success"] = True  # Add success flag for frontend
        else:
            data["success"] = False
            if "error" not in data:
                data["error"] = data.get("detail", "Login failed")
        
        return data
    except Exception as e:
        return {"success": False, "error": str(e)}


def refresh_token() -> bool:
    """Refresh access token using refresh token"""
    if "refresh_token" not in st.session_state:
        return False
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/auth/refresh",
            json={"refresh_token": st.session_state.refresh_token},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            st.session_state.access_token = data.get("access_token")
            st.session_state.refresh_token = data.get("refresh_token")
            return True
        return False
    except:
        return False


def logout() -> bool:
    """Logout and revoke tokens"""
    try:
        requests.post(
            f"{API_BASE_URL}/api/v1/auth/logout",
            json={"refresh_token": st.session_state.get("refresh_token")},
            headers=get_headers(),
            timeout=10
        )
    except:
        pass
    
    st.session_state.clear()
    return True


def get_profile() -> Dict:
    """Get current user profile"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/auth/me",
            headers=get_headers(),
            timeout=10
        )
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==========================================
# CHAT
# ==========================================

def send_message(
    message: str,
    conversation_id: Optional[str] = None,
    specialty: Optional[str] = None,
    top_k: int = 5
) -> Dict:
    """Send a chat message to the medical AI"""
    try:
        payload = {
            "message": message,
            "conversation_id": conversation_id,
            "top_k": top_k,
            "temperature": 0.3
        }
        
        if specialty:
            payload["specialty"] = specialty
        
        if "user" in st.session_state and st.session_state.user:
            payload["user_id"] = st.session_state.user.get("id")
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/chat",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=180
        )
        return response.json()
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ==========================================
# DOCUMENTS
# ==========================================

def upload_document(file) -> Dict:
    """Upload a PDF document"""
    try:
        files = {"file": (file.name, file.getvalue(), "application/pdf")}
        response = requests.post(
            f"{API_BASE_URL}/api/v1/documents/upload",
            files=files,
            timeout=60
        )
        return response.json()
    except Exception as e:
        return {"status": "error", "error": str(e)}


def search_documents(query: str, specialty: Optional[str] = None, top_k: int = 5) -> Dict:
    """Search documents using hybrid search"""
    try:
        payload = {"query": query, "top_k": top_k}
        if specialty:
            payload["agent"] = specialty
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/documents/search",
            json=payload,
            timeout=30
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}


# ==========================================
# HEALTH CHECK
# ==========================================

def health_check() -> Dict:
    """Check API health status"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.json()
    except Exception as e:
        return {"status": "error", "error": str(e)}
