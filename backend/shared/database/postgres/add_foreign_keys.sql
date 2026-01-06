-- Add foreign keys to existing tables
-- Run this to add foreign key constraints for api_rate_limits, chat_metrics, and chat_feedback

-- 1. Add foreign key to api_rate_limits.user_id
ALTER TABLE api_rate_limits 
DROP CONSTRAINT IF EXISTS api_rate_limits_user_id_fkey;

ALTER TABLE api_rate_limits
ADD CONSTRAINT api_rate_limits_user_id_fkey 
FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE;

-- 2. Add foreign key to chat_feedback.conversation_id
ALTER TABLE chat_feedback
DROP CONSTRAINT IF EXISTS chat_feedback_conversation_id_fkey;

ALTER TABLE chat_feedback
ADD CONSTRAINT chat_feedback_conversation_id_fkey
FOREIGN KEY (conversation_id) REFERENCES chat_conversations(conversation_id) ON DELETE CASCADE;

-- 3. Add foreign key to chat_feedback.message_id
ALTER TABLE chat_feedback
DROP CONSTRAINT IF EXISTS chat_feedback_message_id_fkey;

ALTER TABLE chat_feedback
ADD CONSTRAINT chat_feedback_message_id_fkey
FOREIGN KEY (message_id) REFERENCES chat_messages(message_id) ON DELETE CASCADE;

-- 4. Add foreign key to chat_metrics.conversation_id
-- Note: For partitioned tables, we need to drop and recreate
-- The foreign key is already in the CREATE TABLE statement in schema.sql
-- So we'll just document that running schema.sql fresh will add it

-- Verify foreign keys were added
SELECT 
    tc.table_name, 
    kcu.column_name, 
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    tc.constraint_name
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
  AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' 
  AND tc.table_name IN ('api_rate_limits', 'chat_feedback', 'chat_metrics')
ORDER BY tc.table_name, kcu.column_name;
