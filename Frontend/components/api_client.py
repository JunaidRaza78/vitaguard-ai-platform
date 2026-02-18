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


def authenticated_request(method: str, url: str, **kwargs) -> Dict[str, Any]:
    """Make an authenticated request with automatic token refresh on 401.

    Args:
        method: HTTP method (get, post, delete, put, patch)
        url: Full URL to request
        **kwargs: Additional arguments passed to requests (json, params, timeout, etc.)

    Returns:
        Response JSON as dict
    """
    kwargs.setdefault("timeout", 15)

    # First attempt with current token
    kwargs["headers"] = get_headers()
    try:
        response = getattr(requests, method)(url, **kwargs)
    except Exception as e:
        return {"error": str(e)}

    # If 401, try refreshing token and retry once
    if response.status_code == 401:
        if refresh_token():
            kwargs["headers"] = get_headers()
            try:
                response = getattr(requests, method)(url, **kwargs)
            except Exception as e:
                return {"error": str(e)}
        else:
            st.session_state.clear()
            return {"error": "Session expired. Please login again."}

    try:
        return response.json()
    except:
        return {"error": response.text}


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
    return authenticated_request("get", f"{API_BASE_URL}/api/v1/auth/me", timeout=10)


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
            payload["user_id"] = st.session_state.user.get("user_id")
        
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
# FAMILIES
# ==========================================

def create_family(name: str) -> Dict:
    """Create a new family"""
    return authenticated_request("post", f"{API_BASE_URL}/api/v1/families/", json={"name": name})


def get_my_families() -> Dict:
    """Get all families for the current user"""
    return authenticated_request("get", f"{API_BASE_URL}/api/v1/families/me")


def get_family_members(family_id: str) -> Dict:
    """Get members of a family"""
    return authenticated_request("get", f"{API_BASE_URL}/api/v1/families/{family_id}/members")


def add_family_member(family_id: str, user_id: str, role: str = "member") -> Dict:
    """Add a user to a family"""
    return authenticated_request("post", f"{API_BASE_URL}/api/v1/families/{family_id}/members", json={"user_id": user_id, "role": role})


def remove_family_member(family_id: str, user_id: str) -> Dict:
    """Remove a user from a family"""
    return authenticated_request("delete", f"{API_BASE_URL}/api/v1/families/{family_id}/members/{user_id}")


def create_family_relationship(user1_id: str, relationship_type: str, user2_id: str) -> Dict:
    """Create relationship between two users (PARENT_OF, CHILD_OF, SPOUSE_OF, SIBLING_OF)"""
    return authenticated_request("post", f"{API_BASE_URL}/api/v1/families/relationships", json={
        "user1_id": user1_id,
        "relationship_type": relationship_type,
        "user2_id": user2_id,
    })


def get_family_tree(user_id: str, depth: int = 2) -> Dict:
    """Get family tree for a user"""
    return authenticated_request("get", f"{API_BASE_URL}/api/v1/families/tree/{user_id}", params={"depth": depth})


# ==========================================
# NOTIFICATIONS
# ==========================================

def get_my_notifications(status_filter: Optional[str] = None, limit: int = 20) -> Dict:
    """Get notifications for the current user"""
    params = {"limit": limit}
    if status_filter and status_filter != "ALL":
        params["status"] = status_filter.lower()
    return authenticated_request("get", f"{API_BASE_URL}/api/v1/notifications/me", params=params)


def get_medication_reminders() -> Dict:
    """Get medication reminders from Neo4j"""
    return authenticated_request("get", f"{API_BASE_URL}/api/v1/notifications/me/medications")


def send_test_email() -> Dict:
    """Send a test notification email to the current user"""
    return authenticated_request("post", f"{API_BASE_URL}/api/v1/notifications/test-email")


def send_notification(notification_id: str) -> Dict:
    """Send a pending notification immediately by ID"""
    return authenticated_request("post", f"{API_BASE_URL}/api/v1/notifications/send/{notification_id}")


def send_notification_to_members(notification_id: str, recipient_emails: list) -> Dict:
    """Send a notification to selected family member emails"""
    return authenticated_request(
        "post",
        f"{API_BASE_URL}/api/v1/notifications/send-to-members",
        json={"notification_id": notification_id, "recipient_emails": recipient_emails}
    )


def send_direct_email(title: str, message: str, recipient_emails: list) -> Dict:
    """Send email directly without notification_id (for Neo4j-only reminders)"""
    return authenticated_request(
        "post",
        f"{API_BASE_URL}/api/v1/notifications/send-direct",
        json={"title": title, "message": message, "recipient_emails": recipient_emails}
    )


def add_medication_reminder(
    medication_name: str,
    dosage: str,
    frequency: str,
    reminder_times: list,
    start_date: str = "",
) -> Dict:
    """Add a medication with reminder times to Neo4j"""
    payload = {
        "medication_name": medication_name,
        "dosage": dosage,
        "frequency": frequency,
        "reminder_times": reminder_times,
    }
    if start_date:
        payload["start_date"] = start_date
    return authenticated_request(
        "post", f"{API_BASE_URL}/api/v1/notifications/add-medication", json=payload
    )


# ==========================================
# HEALTH CHECK
# ==========================================

def forgot_password(email: str) -> Dict:
    """Send password reset email"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/auth/forgot-password",
            json={"email": email},
            timeout=15,
        )
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


def reset_password(token: str, new_password: str, confirm_password: str) -> Dict:
    """Reset password using token received via email"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/auth/reset-password",
            json={"token": token, "new_password": new_password, "confirm_password": confirm_password},
            timeout=15,
        )
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


def health_check() -> Dict:
    """Check API health status"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.json()
    except Exception as e:
        return {"status": "error", "error": str(e)}
