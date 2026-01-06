# Authentication System Documentation

Complete guide to the Family Health Manager authentication system.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Authentication Flow](#authentication-flow)
4. [API Endpoints](#api-endpoints)
5. [Security Features](#security-features)
6. [Usage Examples](#usage-examples)
7. [Configuration](#configuration)
8. [Testing](#testing)
9. [Troubleshooting](#troubleshooting)

## Overview

The authentication system provides secure user authentication and authorization using JWT tokens, session management, rate limiting, and comprehensive security features.

### Key Features

- ✅ User registration with email verification
- ✅ Secure login with bcrypt password hashing (12 rounds)
- ✅ JWT access tokens (30 min expiry)
- ✅ JWT refresh tokens (30-90 day expiry with rotation)
- ✅ Session management with Redis caching
- ✅ Rate limiting with Redis sliding window algorithm
- ✅ Account lockout after failed login attempts
- ✅ Password reset with secure tokens
- ✅ Role-based access control (RBAC)
- ✅ Security audit logging

### Technology Stack

- **FastAPI** - Web framework
- **JWT (PyJWT)** - Token-based authentication
- **bcrypt** - Password hashing
- **PostgreSQL** - User and session storage
- **Redis** - Session caching and rate limiting
- **Pydantic** - Data validation

## Architecture

### Component Layers

```
┌─────────────────────────────────────────┐
│          API Endpoints Layer            │
│    (app/api/auth.py)                   │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│        Middleware Layer                 │
│  - Auth Middleware (token validation)   │
│  - Rate Limiting (request throttling)   │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│        Services Layer                   │
│  - AuthenticationService                │
│  - JWTService                          │
│  - PasswordService                     │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│         Data Layer                      │
│  - PostgreSQL (users, sessions, tokens) │
│  - Redis (session cache, rate limits)   │
│  - Neo4j (user relationship graph)      │
└─────────────────────────────────────────┘
```

### Directory Structure

```
Backend/app/
├── auth/
│   ├── __init__.py
│   ├── jwt.py              # JWT token service
│   ├── password.py         # Password hashing service
│   └── README.md           # This file
├── models/
│   └── user.py             # User and auth models
├── schemas/
│   └── auth.py             # API request/response schemas
├── services/
│   └── auth_service.py     # Authentication business logic
├── middleware/
│   ├── auth.py             # Authentication middleware
│   └── rate_limit.py       # Rate limiting middleware
└── api/
    └── auth.py             # Authentication endpoints
```

## Authentication Flow

### Registration Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant AuthService
    participant Database
    participant Email

    Client->>API: POST /api/v1/auth/register
    API->>API: Rate limit check
    API->>AuthService: register_user()
    AuthService->>Database: Check if email exists
    AuthService->>AuthService: Hash password (bcrypt)
    AuthService->>Database: Create user (PostgreSQL)
    AuthService->>Database: Create user node (Neo4j)
    AuthService->>AuthService: Generate verification token
    AuthService->>Email: Send verification email (TODO)
    AuthService-->>API: User + token
    API-->>Client: Success message
```

### Login Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant AuthService
    participant Database
    participant Redis

    Client->>API: POST /api/v1/auth/login
    API->>API: Rate limit check
    API->>AuthService: login_user()
    AuthService->>Database: Get user by email
    AuthService->>AuthService: Check account lockout
    AuthService->>AuthService: Verify password
    AuthService->>AuthService: Generate JWT tokens
    AuthService->>Database: Store refresh token
    AuthService->>Database: Create session
    AuthService->>Redis: Cache session
    AuthService->>Database: Log login attempt
    AuthService-->>API: TokenResponse
    API-->>Client: Access token + Refresh token
```

### Token Refresh Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant AuthService
    participant Database

    Client->>API: POST /api/v1/auth/refresh
    API->>AuthService: refresh_access_token()
    AuthService->>AuthService: Verify refresh token
    AuthService->>Database: Check token in database
    AuthService->>AuthService: Generate new tokens
    AuthService->>Database: Revoke old refresh token
    AuthService->>Database: Store new refresh token
    AuthService-->>API: New TokenResponse
    API-->>Client: New access + refresh tokens
```

### Protected Endpoint Access

```mermaid
sequenceDiagram
    participant Client
    participant Middleware
    participant Redis
    participant Database
    participant Endpoint

    Client->>Middleware: Request with Bearer token
    Middleware->>Middleware: Verify JWT signature
    Middleware->>Redis: Check session cache
    alt Cache hit
        Redis-->>Middleware: Session data
    else Cache miss
        Middleware->>Database: Verify session
        Database-->>Middleware: Session data
        Middleware->>Redis: Update cache
    end
    Middleware->>Database: Get user data
    Middleware->>Endpoint: Forward request + user
    Endpoint-->>Client: Response
```

## API Endpoints

Base URL: `/api/v1/auth`

### Registration

**POST** `/register`

Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "john_doe",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Validation Rules:**
- Email: Valid email format, unique
- Username: 3-50 characters, alphanumeric + underscore, unique
- Password: Minimum 8 characters, must contain:
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one digit
  - At least one special character

**Response:** `201 Created`
```json
{
  "message": "Registration successful! Please check your email to verify your account.",
  "success": true
}
```

**Rate Limit:** 5 requests per 5 minutes per IP

---

### Login

**POST** `/login`

Authenticate user and receive JWT tokens.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "remember_me": false
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "username": "john_doe",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true,
    "is_verified": true,
    "is_superuser": false
  }
}
```

**Errors:**
- `401 Unauthorized` - Invalid credentials
- `403 Forbidden` - Account locked (too many failed attempts)
- `429 Too Many Requests` - Rate limit exceeded

**Rate Limit:** 5 requests per 5 minutes per IP

---

### Token Refresh

**POST** `/refresh`

Get a new access token using refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": { ... }
}
```

**Note:** Token rotation is implemented - the old refresh token is revoked and a new one is issued.

---

### Logout

**POST** `/logout`

Logout user and revoke tokens.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body (Optional):**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:** `200 OK`
```json
{
  "message": "Logged out successfully",
  "success": true
}
```

---

### Email Verification

**POST** `/verify-email`

Verify user's email address.

**Request Body:**
```json
{
  "token": "email_verification_token_here"
}
```

**Response:** `200 OK`
```json
{
  "message": "Email verified successfully! You can now login.",
  "success": true
}
```

---

### Get Current User

**GET** `/me`

Get authenticated user's profile.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "username": "john_doe",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+1234567890",
  "date_of_birth": "1990-01-01",
  "is_active": true,
  "is_verified": true,
  "is_superuser": false,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

---

### Update User Profile

**PATCH** `/me`

Update authenticated user's profile.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body (all fields optional):**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+1234567890",
  "date_of_birth": "1990-01-01"
}
```

**Response:** `200 OK` - Returns updated user object

---

### Change Password

**POST** `/change-password`

Change user's password.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "current_password": "OldPass123!",
  "new_password": "NewPass456!",
  "confirm_password": "NewPass456!"
}
```

**Response:** `200 OK`
```json
{
  "message": "Password changed successfully. Please login again.",
  "success": true
}
```

**Note:** All active sessions and refresh tokens are revoked after password change.

---

### Forgot Password

**POST** `/forgot-password`

Request password reset email.

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response:** `200 OK` (always returns success to prevent email enumeration)
```json
{
  "message": "If the email exists, a password reset link has been sent.",
  "success": true
}
```

---

### Reset Password

**POST** `/reset-password`

Reset password using reset token.

**Request Body:**
```json
{
  "token": "password_reset_token_here",
  "new_password": "NewPass456!",
  "confirm_password": "NewPass456!"
}
```

**Response:** `200 OK`
```json
{
  "message": "Password reset successful. Please login with your new password.",
  "success": true
}
```

## Security Features

### Password Security

**Hashing Algorithm:** bcrypt with 12 rounds
```python
# Password is hashed on registration/password change
password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))
```

**Password Strength Requirements:**
- Minimum 8 characters, maximum 128 characters
- At least one uppercase letter (A-Z)
- At least one lowercase letter (a-z)
- At least one digit (0-9)
- At least one special character (!@#$%^&*(),.?":{}|<>)

### JWT Tokens

**Access Token:**
- Expiry: 30 minutes
- Algorithm: HS256
- Contains: user_id, email, username, is_superuser
- Stored in session for validation

**Refresh Token:**
- Expiry: 30 days (90 days with "remember me")
- Algorithm: HS256
- Token rotation: Old token revoked when refreshed
- Stored hashed in database

**Token Payload Example:**
```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "username": "john_doe",
  "is_superuser": false,
  "type": "access",
  "iat": 1704067200,
  "exp": 1704068400,
  "nbf": 1704067200
}
```

### Rate Limiting

**Implementation:** Redis-based sliding window algorithm

**Rate Limit Tiers:**

| Endpoint Type | Limit | Window |
|--------------|-------|--------|
| Authentication (login/register) | 5 requests | 5 minutes |
| Token Refresh | 10 requests | 1 minute |
| General API | 100 requests | 1 minute |
| General API (hourly) | 1000 requests | 1 hour |

**Headers:**
```
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 4
X-RateLimit-Reset: 1704067500
```

**Response on Limit Exceeded:** `429 Too Many Requests`
```json
{
  "detail": "Rate limit exceeded. Try again in 45 seconds."
}
```

### Account Lockout

**Trigger:** 5 consecutive failed login attempts

**Lockout Duration:** 30 minutes

**Reset:** Counter resets on successful login

**Implementation:**
```python
MAX_LOGIN_ATTEMPTS = 5
ACCOUNT_LOCKOUT_MINUTES = 30

# Locked if:
if user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
    if user.account_locked_until and user.account_locked_until > datetime.utcnow():
        # Account is locked
        raise HTTPException(403, "Account locked due to too many failed attempts")
```

### Session Management

**Session Storage:**
- PostgreSQL: Persistent session records
- Redis: Fast session cache (30 min TTL)

**Session Validation:**
1. Verify JWT signature and expiration
2. Check session exists in Redis (fast path)
3. If not in cache, verify in PostgreSQL
4. Validate session hasn't expired
5. Cache session data in Redis

**Session Revocation:**
- Manual logout
- Password change (revokes all sessions)
- Token expiration
- Admin action

### Audit Logging

**Login Attempts Table:**
Logs all login attempts (successful and failed) with:
- User ID (if exists)
- Email attempted
- Success/failure status
- Failure reason
- IP address
- User agent
- Timestamp

**Query Recent Failed Attempts:**
```sql
SELECT * FROM login_attempts
WHERE email = 'user@example.com'
  AND success = FALSE
  AND attempted_at > NOW() - INTERVAL '1 hour'
ORDER BY attempted_at DESC;
```

## Usage Examples

### Python Client

```python
import httpx
import asyncio

API_URL = "http://localhost:8000/api/v1/auth"

async def register_user():
    """Register a new user"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "SecurePass123!",
                "first_name": "New",
                "last_name": "User"
            }
        )
        print(response.json())

async def login_user():
    """Login and get tokens"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/login",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "remember_me": False
            }
        )
        data = response.json()
        return data["access_token"], data["refresh_token"]

async def get_profile(access_token):
    """Get user profile"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_URL}/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        print(response.json())

async def refresh_token(refresh_token):
    """Refresh access token"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/refresh",
            json={"refresh_token": refresh_token}
        )
        data = response.json()
        return data["access_token"], data["refresh_token"]

# Run examples
asyncio.run(register_user())
access_token, refresh_token = asyncio.run(login_user())
asyncio.run(get_profile(access_token))
```

### JavaScript/TypeScript Client

```typescript
const API_URL = 'http://localhost:8000/api/v1/auth';

// Register user
async function registerUser() {
  const response = await fetch(`${API_URL}/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: 'newuser@example.com',
      username: 'newuser',
      password: 'SecurePass123!',
      first_name: 'New',
      last_name: 'User'
    })
  });
  return response.json();
}

// Login
async function login() {
  const response = await fetch(`${API_URL}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: 'newuser@example.com',
      password: 'SecurePass123!',
      remember_me: false
    })
  });
  const data = await response.json();

  // Store tokens
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);

  return data;
}

// Get profile
async function getProfile() {
  const token = localStorage.getItem('access_token');
  const response = await fetch(`${API_URL}/me`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return response.json();
}

// Refresh token
async function refreshToken() {
  const refresh = localStorage.getItem('refresh_token');
  const response = await fetch(`${API_URL}/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refresh })
  });
  const data = await response.json();

  // Update stored tokens
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);

  return data;
}

// Auto-refresh on 401
async function apiRequest(url, options = {}) {
  const token = localStorage.getItem('access_token');
  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`
    }
  });

  // If token expired, refresh and retry
  if (response.status === 401) {
    await refreshToken();
    return apiRequest(url, options);
  }

  return response.json();
}
```

### Protected Endpoint Example

```python
from fastapi import APIRouter, Depends
from app.middleware.auth import (
    get_current_user,
    get_current_active_user,
    get_current_verified_user,
    get_current_superuser
)

router = APIRouter()

# Any authenticated user
@router.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    return {"user": current_user}

# Active users only
@router.get("/dashboard")
async def get_dashboard(current_user: dict = Depends(get_current_active_user)):
    return {"message": "Welcome to dashboard"}

# Verified users only
@router.post("/create-post")
async def create_post(current_user: dict = Depends(get_current_verified_user)):
    return {"message": "Post created"}

# Superusers only
@router.get("/admin")
async def admin_panel(current_user: dict = Depends(get_current_superuser)):
    return {"message": "Admin panel"}
```

## Configuration

### Environment Variables

Create a `.env` file in the Backend directory:

```bash
# JWT Configuration
SECRET_KEY=your-secret-key-here-change-in-production-min-32-chars
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/health_manager
NEO4J_URI=neo4j://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Rate Limiting
RATE_LIMIT_ENABLED=true
AUTH_RATE_LIMIT_REQUESTS=5
AUTH_RATE_LIMIT_WINDOW_SECONDS=300
API_RATE_LIMIT_REQUESTS_PER_MINUTE=100
API_RATE_LIMIT_REQUESTS_PER_HOUR=1000

# Security
ACCOUNT_LOCKOUT_ATTEMPTS=5
ACCOUNT_LOCKOUT_MINUTES=30
PASSWORD_HASH_ROUNDS=12

# Email (TODO: Configure when email service is implemented)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@healthmanager.com
```

### Generating Secure Secret Key

```python
import secrets

# Generate a secure secret key (64 characters)
secret_key = secrets.token_urlsafe(48)
print(f"SECRET_KEY={secret_key}")
```

Or use openssl:
```bash
openssl rand -base64 48
```

## Testing

### Unit Tests

```python
import pytest
from app.auth.password import password_service
from app.auth.jwt import jwt_service

def test_password_hashing():
    """Test password hashing and verification"""
    password = "SecurePass123!"

    # Hash password
    hashed = password_service.hash_password(password)

    # Verify correct password
    assert password_service.verify_password(password, hashed) is True

    # Verify incorrect password
    assert password_service.verify_password("WrongPass!", hashed) is False

def test_jwt_tokens():
    """Test JWT token creation and validation"""
    from uuid import uuid4

    user_id = uuid4()
    email = "test@example.com"
    username = "testuser"

    # Create access token
    token = jwt_service.create_access_token(user_id, email, username)

    # Verify token
    payload = jwt_service.verify_access_token(token)
    assert payload is not None
    assert payload["sub"] == str(user_id)
    assert payload["email"] == email
    assert payload["type"] == "access"

@pytest.mark.asyncio
async def test_user_registration(client):
    """Test user registration endpoint"""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "SecurePass123!",
            "first_name": "Test",
            "last_name": "User"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "verify your account" in data["message"]
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_full_auth_flow(client):
    """Test complete authentication flow"""

    # 1. Register
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "flow@example.com",
            "username": "flowuser",
            "password": "SecurePass123!"
        }
    )
    assert register_response.status_code == 201

    # 2. Login (will fail - email not verified)
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "flow@example.com",
            "password": "SecurePass123!"
        }
    )
    assert login_response.status_code == 403  # Not verified

    # 3. Verify email (simulate)
    # ... verification logic ...

    # 4. Login (should succeed now)
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "flow@example.com",
            "password": "SecurePass123!"
        }
    )
    assert login_response.status_code == 200
    tokens = login_response.json()
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    # 5. Access protected endpoint
    profile_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert profile_response.status_code == 200

    # 6. Refresh token
    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert refresh_response.status_code == 200
    new_tokens = refresh_response.json()

    # 7. Logout
    logout_response = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {new_tokens['access_token']}"},
        json={"refresh_token": new_tokens["refresh_token"]}
    )
    assert logout_response.status_code == 200
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
pytest Backend/tests/

# Run specific test file
pytest Backend/tests/test_auth.py

# Run with coverage
pytest --cov=Backend/app/auth Backend/tests/
```

## Troubleshooting

### Common Issues

#### 1. "Invalid or expired token"

**Cause:** Token has expired or is malformed

**Solution:**
- Check token expiration time
- Use refresh token to get new access token
- Verify SECRET_KEY is consistent across restarts

#### 2. "Account locked due to too many failed attempts"

**Cause:** 5+ failed login attempts

**Solution:**
- Wait 30 minutes for automatic unlock
- Or manually reset in database:
```sql
UPDATE users
SET failed_login_attempts = 0, account_locked_until = NULL
WHERE email = 'user@example.com';
```

#### 3. "Rate limit exceeded"

**Cause:** Too many requests in short time

**Solution:**
- Wait for rate limit window to expire
- Check X-RateLimit-Reset header
- Implement exponential backoff in client

#### 4. "Session not found or expired"

**Cause:** Session was revoked or expired

**Solution:**
- Login again to create new session
- Check if password was recently changed (revokes all sessions)

#### 5. "Email not verified"

**Cause:** Trying to access verified-user-only endpoints

**Solution:**
- Complete email verification process
- Check email for verification link
- Request new verification email

### Debug Mode

Enable detailed logging:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Database Queries for Debugging

```sql
-- Check user status
SELECT user_id, email, is_active, is_verified, failed_login_attempts, account_locked_until
FROM users
WHERE email = 'user@example.com';

-- Check active sessions
SELECT s.session_id, s.user_id, s.created_at, s.expires_at, s.is_active
FROM sessions s
JOIN users u ON s.user_id = u.user_id
WHERE u.email = 'user@example.com'
  AND s.is_active = TRUE;

-- Check refresh tokens
SELECT token_id, user_id, created_at, expires_at, revoked, last_used_at
FROM refresh_tokens
WHERE user_id = '550e8400-e29b-41d4-a716-446655440000'
  AND revoked = FALSE;

-- Check recent login attempts
SELECT email, success, failure_reason, ip_address, attempted_at
FROM login_attempts
WHERE email = 'user@example.com'
ORDER BY attempted_at DESC
LIMIT 10;
```

### Redis Debugging

```bash
# Connect to Redis
redis-cli

# Check session cache
GET session:550e8400-e29b-41d4-a716-446655440000

# Check rate limits
KEYS rate_limit:*

# Check specific rate limit
GET rate_limit:minute:192.168.1.1:1704067200
```

## Security Best Practices

1. **Always use HTTPS in production** - Never send tokens over HTTP
2. **Rotate SECRET_KEY periodically** - Update and redeploy
3. **Monitor failed login attempts** - Set up alerts for suspicious activity
4. **Use strong passwords** - Enforce password strength requirements
5. **Implement IP whitelisting** - For admin endpoints
6. **Regular security audits** - Review code and dependencies
7. **Keep dependencies updated** - Patch security vulnerabilities
8. **Use environment variables** - Never commit secrets to version control
9. **Implement CSRF protection** - For web applications
10. **Enable audit logging** - Track all authentication events

## Support

For issues or questions:
- Check this documentation
- Review the [Migration Guide](../../migrations/README.md)
- Check application logs
- Contact the development team

---

**Version:** 1.0.0
**Last Updated:** January 2025
**Maintainer:** Development Team
