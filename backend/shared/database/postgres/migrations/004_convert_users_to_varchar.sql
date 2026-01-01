-- Migration 004: Convert users.user_id from UUID to VARCHAR
-- This allows foreign keys from conversations (which use VARCHAR)
-- Date: 2025-12-29

-- ==================== IMPORTANT ====================
-- This migration changes users.user_id from UUID to VARCHAR
-- All related foreign keys will be updated automatically
-- Make sure to backup your data first!

-- ==================== Step 1: Drop existing FK constraints temporarily ====================

-- Drop FKs that reference users.user_id
ALTER TABLE user_sessions DROP CONSTRAINT IF EXISTS fk_user_sessions_user_id;
ALTER TABLE notifications DROP CONSTRAINT IF EXISTS fk_notifications_user_id;
ALTER TABLE document_jobs DROP CONSTRAINT IF EXISTS fk_document_jobs_user_id;
ALTER TABLE api_rate_limit DROP CONSTRAINT IF EXISTS fk_api_rate_limit_user_id;
ALTER TABLE audit_log DROP CONSTRAINT IF EXISTS fk_audit_log_user_id;
ALTER TABLE chat_conversations DROP CONSTRAINT IF EXISTS chat_conversations_user_id_fkey;
ALTER TABLE chat_messages DROP CONSTRAINT IF EXISTS chat_messages_user_id_fkey;
ALTER TABLE chat_feedback DROP CONSTRAINT IF EXISTS chat_feedback_user_id_fkey;

-- ==================== Step 2: Convert users.user_id to VARCHAR ====================

-- Convert UUID to VARCHAR (preserves data as string representation)
ALTER TABLE users
ALTER COLUMN user_id TYPE VARCHAR(255)
USING user_id::TEXT;

-- ==================== Step 3: Convert related tables to VARCHAR ====================

-- Convert user_sessions.user_id
ALTER TABLE user_sessions
ALTER COLUMN user_id TYPE VARCHAR(255)
USING user_id::TEXT;

-- Convert notifications.user_id
ALTER TABLE notifications
ALTER COLUMN user_id TYPE VARCHAR(255)
USING user_id::TEXT;

-- Convert document_jobs.user_id
ALTER TABLE document_jobs
ALTER COLUMN user_id TYPE VARCHAR(255)
USING user_id::TEXT;

-- Convert api_rate_limit.user_id
ALTER TABLE api_rate_limit
ALTER COLUMN user_id TYPE VARCHAR(255)
USING user_id::TEXT;

-- Convert audit_log.user_id
ALTER TABLE audit_log
ALTER COLUMN user_id TYPE VARCHAR(255)
USING user_id::TEXT;

-- Old chat tables (if still exist)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'chat_conversations') THEN
        ALTER TABLE chat_conversations ALTER COLUMN user_id TYPE VARCHAR(255) USING user_id::TEXT;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'chat_messages') THEN
        ALTER TABLE chat_messages ALTER COLUMN user_id TYPE VARCHAR(255) USING user_id::TEXT;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'chat_feedback') THEN
        ALTER TABLE chat_feedback ALTER COLUMN user_id TYPE VARCHAR(255) USING user_id::TEXT;
    END IF;
END $$;

-- ==================== Step 4: Re-add FK constraints ====================

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

-- Add FK: api_rate_limit → users
ALTER TABLE api_rate_limit
ADD CONSTRAINT fk_api_rate_limit_user_id
FOREIGN KEY (user_id) REFERENCES users(user_id)
ON DELETE CASCADE ON UPDATE CASCADE;

-- Add FK: audit_log → users (SET NULL on delete)
ALTER TABLE audit_log
ADD CONSTRAINT fk_audit_log_user_id
FOREIGN KEY (user_id) REFERENCES users(user_id)
ON DELETE SET NULL ON UPDATE CASCADE;

-- ==================== Step 5: Add FK for conversations → users ====================

-- NOW we can add the FK for conversations!
ALTER TABLE conversations
ADD CONSTRAINT fk_conversations_user_id
FOREIGN KEY (user_id) REFERENCES users(user_id)
ON DELETE CASCADE ON UPDATE CASCADE;

-- ==================== Verify ====================

-- Check all user_id columns are now VARCHAR
SELECT
    table_name,
    column_name,
    data_type,
    character_maximum_length
FROM information_schema.columns
WHERE column_name = 'user_id'
    AND table_schema = 'public'
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
ORDER BY tc.table_name;

-- ==================== Done! ====================
-- All user_id columns are now VARCHAR(255)
-- All foreign keys are properly linked
-- conversations → users FK is now working!
