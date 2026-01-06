-- Migration 003: Add Foreign Keys for Monolithic Architecture
-- Description: Links tables with foreign keys for data integrity
-- Date: 2025-12-29

-- ==================== Foreign Keys ====================

-- 1. Link conversations to users
ALTER TABLE conversations
ADD CONSTRAINT fk_conversations_user_id
FOREIGN KEY (user_id)
REFERENCES users(user_id)
ON DELETE CASCADE
ON UPDATE CASCADE;

-- 2. Link conversation_metrics to conversations
ALTER TABLE conversation_metrics
ADD CONSTRAINT fk_conversation_metrics_conversation_id
FOREIGN KEY (conversation_id)
REFERENCES conversations(conversation_id)
ON DELETE CASCADE
ON UPDATE CASCADE;

-- 3. Link user_sessions to users
ALTER TABLE user_sessions
ADD CONSTRAINT fk_user_sessions_user_id
FOREIGN KEY (user_id)
REFERENCES users(user_id)
ON DELETE CASCADE
ON UPDATE CASCADE;

-- 4. Link notifications to users
ALTER TABLE notifications
ADD CONSTRAINT fk_notifications_user_id
FOREIGN KEY (user_id)
REFERENCES users(user_id)
ON DELETE CASCADE
ON UPDATE CASCADE;

-- 5. Link document_jobs to users
ALTER TABLE document_jobs
ADD CONSTRAINT fk_document_jobs_user_id
FOREIGN KEY (user_id)
REFERENCES users(user_id)
ON DELETE CASCADE
ON UPDATE CASCADE;

-- 6. Link audit_logs to users
ALTER TABLE audit_log
ADD CONSTRAINT fk_audit_log_user_id
FOREIGN KEY (user_id)
REFERENCES users(user_id)
ON DELETE SET NULL
ON UPDATE CASCADE;

-- 7. Link api_rate_limits to users
ALTER TABLE api_rate_limit
ADD CONSTRAINT fk_api_rate_limit_user_id
FOREIGN KEY (user_id)
REFERENCES users(user_id)
ON DELETE CASCADE
ON UPDATE CASCADE;

-- ==================== Indexes for Foreign Keys ====================

-- These likely already exist, but adding for completeness
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversation_metrics_conversation_id ON conversation_metrics(conversation_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_document_jobs_user_id ON document_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_api_rate_limit_user_id ON api_rate_limit(user_id);

-- ==================== Verify Foreign Keys ====================

SELECT
    tc.table_name AS "Table",
    kcu.column_name AS "Column",
    ccu.table_name AS "References Table",
    ccu.column_name AS "References Column",
    rc.delete_rule AS "On Delete",
    rc.update_rule AS "On Update"
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
JOIN information_schema.referential_constraints AS rc
    ON tc.constraint_name = rc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
ORDER BY tc.table_name;

-- ==================== Comments ====================

COMMENT ON CONSTRAINT fk_conversations_user_id ON conversations IS 'Links conversation to user (CASCADE delete)';
COMMENT ON CONSTRAINT fk_conversation_metrics_conversation_id ON conversation_metrics IS 'Links metrics to conversation (CASCADE delete)';
COMMENT ON CONSTRAINT fk_user_sessions_user_id ON user_sessions IS 'Links session to user (CASCADE delete)';
COMMENT ON CONSTRAINT fk_notifications_user_id ON notifications IS 'Links notification to user (CASCADE delete)';

-- ==================== Migration Complete ====================
-- Foreign keys added for monolithic architecture
-- Database will now enforce referential integrity
