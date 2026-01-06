-- ==========================================
-- Authentication System Database Migration
-- Version: 001
-- Description: Create authentication tables
-- ==========================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==========================================
-- USERS TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Authentication
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,

    -- Profile
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone_number VARCHAR(20),
    date_of_birth DATE,

    -- Status
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE NOT NULL,
    is_superuser BOOLEAN DEFAULT FALSE NOT NULL,

    -- Security
    failed_login_attempts INTEGER DEFAULT 0 NOT NULL,
    account_locked_until TIMESTAMP,
    password_changed_at TIMESTAMP,
    last_login_at TIMESTAMP,
    last_login_ip VARCHAR(45),

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP,

    -- Constraints
    CONSTRAINT email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT username_length CHECK (LENGTH(username) >= 3 AND LENGTH(username) <= 50),
    CONSTRAINT phone_format CHECK (phone_number IS NULL OR phone_number ~* '^\+?[1-9]\d{1,14}$')
);

-- Indexes for users table
CREATE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_username ON users(username) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_active ON users(is_active) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_verified ON users(is_verified) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_created_at ON users(created_at DESC);

-- ==========================================
-- REFRESH TOKENS TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS refresh_tokens (
    token_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- Token data
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    device_info JSONB,

    -- Status
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    revoked BOOLEAN DEFAULT FALSE NOT NULL,
    revoked_at TIMESTAMP,
    revoked_reason VARCHAR(255),

    -- Security
    ip_address VARCHAR(45),
    user_agent TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    last_used_at TIMESTAMP,

    -- Constraints
    CONSTRAINT valid_expiry CHECK (expires_at > created_at)
);

-- Indexes for refresh_tokens table
CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_token_hash ON refresh_tokens(token_hash) WHERE revoked = FALSE;
CREATE INDEX idx_refresh_tokens_active ON refresh_tokens(is_active) WHERE revoked = FALSE;
CREATE INDEX idx_refresh_tokens_expires_at ON refresh_tokens(expires_at);

-- ==========================================
-- LOGIN ATTEMPTS TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS login_attempts (
    attempt_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- User reference (nullable for failed attempts with non-existent emails)
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    email VARCHAR(255) NOT NULL,

    -- Attempt details
    success BOOLEAN NOT NULL,
    failure_reason VARCHAR(255),

    -- Security
    ip_address VARCHAR(45),
    user_agent TEXT,
    location JSONB,

    -- Timestamp
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indexes for login_attempts table
CREATE INDEX idx_login_attempts_user_id ON login_attempts(user_id);
CREATE INDEX idx_login_attempts_email ON login_attempts(email);
CREATE INDEX idx_login_attempts_ip_address ON login_attempts(ip_address);
CREATE INDEX idx_login_attempts_attempted_at ON login_attempts(attempted_at DESC);
CREATE INDEX idx_login_attempts_success ON login_attempts(success);

-- ==========================================
-- SESSIONS TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- Session data
    access_token TEXT NOT NULL,
    refresh_token_id UUID REFERENCES refresh_tokens(token_id) ON DELETE CASCADE,

    -- Device info
    device_info JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,

    -- Status
    is_active BOOLEAN DEFAULT TRUE NOT NULL,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    -- Constraints
    CONSTRAINT valid_session_expiry CHECK (expires_at > created_at)
);

-- Indexes for sessions table
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_access_token ON sessions(access_token) WHERE is_active = TRUE;
CREATE INDEX idx_sessions_active ON sessions(is_active);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);
CREATE INDEX idx_sessions_last_activity ON sessions(last_activity_at DESC);

-- ==========================================
-- EMAIL VERIFICATION TOKENS TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS email_verification_tokens (
    token_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- Token data
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,

    -- Status
    used BOOLEAN DEFAULT FALSE NOT NULL,
    used_at TIMESTAMP,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,

    -- Constraints
    CONSTRAINT valid_token_expiry CHECK (expires_at > created_at)
);

-- Indexes for email_verification_tokens table
CREATE INDEX idx_email_verification_user_id ON email_verification_tokens(user_id);
CREATE INDEX idx_email_verification_token_hash ON email_verification_tokens(token_hash) WHERE used = FALSE;
CREATE INDEX idx_email_verification_expires_at ON email_verification_tokens(expires_at);

-- ==========================================
-- PASSWORD RESET TOKENS TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    token_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- Token data
    token_hash VARCHAR(255) UNIQUE NOT NULL,

    -- Status
    used BOOLEAN DEFAULT FALSE NOT NULL,
    used_at TIMESTAMP,

    -- Security
    ip_address VARCHAR(45),

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,

    -- Constraints
    CONSTRAINT valid_reset_token_expiry CHECK (expires_at > created_at)
);

-- Indexes for password_reset_tokens table
CREATE INDEX idx_password_reset_user_id ON password_reset_tokens(user_id);
CREATE INDEX idx_password_reset_token_hash ON password_reset_tokens(token_hash) WHERE used = FALSE;
CREATE INDEX idx_password_reset_expires_at ON password_reset_tokens(expires_at);

-- ==========================================
-- TRIGGERS
-- ==========================================

-- Update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==========================================
-- FUNCTIONS
-- ==========================================

-- Clean up expired tokens (to be run periodically)
CREATE OR REPLACE FUNCTION cleanup_expired_tokens()
RETURNS void AS $$
BEGIN
    -- Mark expired refresh tokens as revoked
    UPDATE refresh_tokens
    SET revoked = TRUE, revoked_at = CURRENT_TIMESTAMP, revoked_reason = 'Expired'
    WHERE expires_at < CURRENT_TIMESTAMP AND revoked = FALSE;

    -- Delete expired email verification tokens (older than 7 days)
    DELETE FROM email_verification_tokens
    WHERE expires_at < CURRENT_TIMESTAMP - INTERVAL '7 days';

    -- Delete expired password reset tokens (older than 7 days)
    DELETE FROM password_reset_tokens
    WHERE expires_at < CURRENT_TIMESTAMP - INTERVAL '7 days';

    -- Delete old login attempts (older than 90 days)
    DELETE FROM login_attempts
    WHERE attempted_at < CURRENT_TIMESTAMP - INTERVAL '90 days';

    -- Deactivate expired sessions
    UPDATE sessions
    SET is_active = FALSE
    WHERE expires_at < CURRENT_TIMESTAMP AND is_active = TRUE;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- INITIAL DATA
-- ==========================================

-- Create default admin user (password: AdminPass123!)
-- WARNING: Change this password immediately in production
INSERT INTO users (
    email,
    username,
    password_hash,
    first_name,
    last_name,
    is_active,
    is_verified,
    is_superuser
) VALUES (
    'admin@example.com',
    'admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLaEiizu', -- AdminPass123!
    'System',
    'Administrator',
    TRUE,
    TRUE,
    TRUE
) ON CONFLICT (email) DO NOTHING;

-- ==========================================
-- COMMENTS
-- ==========================================

COMMENT ON TABLE users IS 'User accounts and profiles';
COMMENT ON TABLE refresh_tokens IS 'JWT refresh tokens for authentication';
COMMENT ON TABLE login_attempts IS 'Login attempt tracking for security monitoring';
COMMENT ON TABLE sessions IS 'Active user sessions';
COMMENT ON TABLE email_verification_tokens IS 'Email verification tokens';
COMMENT ON TABLE password_reset_tokens IS 'Password reset tokens';

COMMENT ON COLUMN users.password_hash IS 'bcrypt hashed password (12 rounds)';
COMMENT ON COLUMN users.failed_login_attempts IS 'Counter for failed login attempts (resets on successful login)';
COMMENT ON COLUMN users.account_locked_until IS 'Account lockout timestamp (NULL if not locked)';
COMMENT ON COLUMN refresh_tokens.token_hash IS 'SHA-256 hash of refresh token';
COMMENT ON COLUMN sessions.access_token IS 'JWT access token (stored for session validation)';

-- ==========================================
-- GRANT PERMISSIONS
-- ==========================================

-- Grant permissions to application user (adjust username as needed)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;
