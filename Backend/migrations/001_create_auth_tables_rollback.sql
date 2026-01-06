-- ==========================================
-- Authentication System Database Migration Rollback
-- Version: 001
-- Description: Rollback authentication tables
-- ==========================================

-- WARNING: This will delete all authentication data!
-- Only run this in development or if you're absolutely sure.

-- Drop triggers
DROP TRIGGER IF EXISTS update_users_updated_at ON users;

-- Drop functions
DROP FUNCTION IF EXISTS update_updated_at_column();
DROP FUNCTION IF EXISTS cleanup_expired_tokens();

-- Drop tables (in reverse order of creation to respect foreign keys)
DROP TABLE IF EXISTS password_reset_tokens CASCADE;
DROP TABLE IF EXISTS email_verification_tokens CASCADE;
DROP TABLE IF EXISTS sessions CASCADE;
DROP TABLE IF EXISTS login_attempts CASCADE;
DROP TABLE IF EXISTS refresh_tokens CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Note: We don't drop the uuid-ossp extension as it might be used by other tables
