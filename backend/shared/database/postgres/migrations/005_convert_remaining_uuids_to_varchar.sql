-- Migration 005: Convert Remaining UUID user_id to VARCHAR
-- This completes the conversion started in 004
-- Date: 2025-12-29

-- ==================== Step 1: Drop FK constraints (if any remain) ====================

ALTER TABLE user_sessions DROP CONSTRAINT IF EXISTS fk_user_sessions_user_id;
ALTER TABLE user_sessions DROP CONSTRAINT IF EXISTS user_sessions_user_id_fkey;

ALTER TABLE notifications DROP CONSTRAINT IF EXISTS fk_notifications_user_id;
ALTER TABLE notifications DROP CONSTRAINT IF EXISTS notifications_user_id_fkey;

ALTER TABLE document_jobs DROP CONSTRAINT IF EXISTS fk_document_jobs_user_id;
ALTER TABLE document_jobs DROP CONSTRAINT IF EXISTS document_jobs_user_id_fkey;

ALTER TABLE api_rate_limits DROP CONSTRAINT IF EXISTS fk_api_rate_limit_user_id;
ALTER TABLE api_rate_limits DROP CONSTRAINT IF EXISTS api_rate_limits_user_id_fkey;

ALTER TABLE audit_logs DROP CONSTRAINT IF EXISTS fk_audit_log_user_id;
ALTER TABLE audit_logs DROP CONSTRAINT IF EXISTS audit_logs_user_id_fkey;

-- ==================== Step 2: Convert users.user_id to VARCHAR ====================

-- This is the PRIMARY KEY, must convert it first
ALTER TABLE users
ALTER COLUMN user_id TYPE VARCHAR(255)
USING user_id::TEXT;

-- ==================== Step 3: Convert child tables ====================

-- Convert user_sessions.user_id
ALTER TABLE user_sessions
ALTER COLUMN user_id TYPE VARCHAR(255)
USING user_id::TEXT;

-- Convert notifications.user_id (parent partitioned table)
ALTER TABLE notifications
ALTER COLUMN user_id TYPE VARCHAR(255)
USING user_id::TEXT;

-- Convert document_jobs.user_id
ALTER TABLE document_jobs
ALTER COLUMN user_id TYPE VARCHAR(255)
USING user_id::TEXT;

-- Convert api_rate_limits.user_id
ALTER TABLE api_rate_limits
ALTER COLUMN user_id TYPE VARCHAR(255)
USING user_id::TEXT;

-- Convert audit_logs.user_id (parent partitioned table)
ALTER TABLE audit_logs
ALTER COLUMN user_id TYPE VARCHAR(255)
USING user_id::TEXT;

-- ==================== Step 4: Re-add Foreign Key Constraints ====================

-- Add FK: user_sessions → users
ALTER TABLE user_sessions
ADD CONSTRAINT fk_user_sessions_user_id
FOREIGN KEY (user_id) REFERENCES users(user_id)
ON DELETE CASCADE ON UPDATE CASCADE;

-- Add FK: notifications → users
ALTER TABLE notifications
ADD CONSTRAINT fk_notifications_user_id
FOREIGN KEY (user_id) REFERENCES users(user_id)
ON DELETE CASCADE ON UPDATE CASCADE;

-- Add FK: document_jobs → users
ALTER TABLE document_jobs
ADD CONSTRAINT fk_document_jobs_user_id
FOREIGN KEY (user_id) REFERENCES users(user_id)
ON DELETE CASCADE ON UPDATE CASCADE;

-- Add FK: api_rate_limits → users
ALTER TABLE api_rate_limits
ADD CONSTRAINT fk_api_rate_limits_user_id
FOREIGN KEY (user_id) REFERENCES users(user_id)
ON DELETE CASCADE ON UPDATE CASCADE;

-- Add FK: audit_logs → users (SET NULL on delete)
ALTER TABLE audit_logs
ADD CONSTRAINT fk_audit_logs_user_id
FOREIGN KEY (user_id) REFERENCES users(user_id)
ON DELETE SET NULL ON UPDATE CASCADE;

-- ==================== Step 5: Add FK for conversations → users ====================

-- Drop old constraint if exists
ALTER TABLE conversations DROP CONSTRAINT IF EXISTS fk_conversations_user_id;

-- Add the constraint
ALTER TABLE conversations
ADD CONSTRAINT fk_conversations_user_id
FOREIGN KEY (user_id) REFERENCES users(user_id)
ON DELETE CASCADE ON UPDATE CASCADE;

-- ==================== Step 6: Verify Conversion ====================

-- Check all user_id columns are now VARCHAR
SELECT
    table_name,
    column_name,
    data_type,
    character_maximum_length
FROM information_schema.columns
WHERE column_name = 'user_id'
    AND table_schema = 'public'
    AND table_name NOT LIKE '%_default'
    AND table_name NOT LIKE '%_202%'
ORDER BY table_name;

-- Check all foreign keys
SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS references_table,
    rc.delete_rule
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
JOIN information_schema.referential_constraints AS rc
    ON tc.constraint_name = rc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND kcu.column_name = 'user_id'
    AND tc.table_name NOT LIKE '%_default'
    AND tc.table_name NOT LIKE '%_202%'
ORDER BY tc.table_name;

-- ==================== Done! ====================
-- All main user_id columns are now VARCHAR(255)
-- All foreign keys properly linked
-- Monolithic architecture complete!
