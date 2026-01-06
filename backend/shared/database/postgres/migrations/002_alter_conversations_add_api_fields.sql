-- Migration: Alter existing conversations table to support API requirements
-- Description: Adds JSONB fields for context, payload, and other API-specific fields
-- Author: Claude Code
-- Date: 2025-12-29

-- This migration modifies the EXISTING conversations table
-- It preserves your current structure and adds new fields

-- ==================== Add New Columns to Existing Table ====================

-- Add auth_key column (if not exists)
ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS auth_key VARCHAR(255);

-- Add message_id column for current message tracking
ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS current_message_id VARCHAR(255);

-- Add context JSONB column for storing prompts and replies
ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS context JSONB DEFAULT '{"prompts": [], "replies": []}'::jsonb;

-- Add current_payload JSONB column for current request data
ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS current_payload JSONB;

-- Add resources JSONB array column
ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS resources JSONB DEFAULT '[]'::jsonb;

-- ==================== Update Existing Columns (if needed) ====================

-- Ensure conversation_id can handle string IDs (if it's currently UUID)
-- Skip if already VARCHAR
-- ALTER TABLE conversations ALTER COLUMN conversation_id TYPE VARCHAR(255);

-- Ensure user_id can handle string IDs (if it's currently UUID)
-- Skip if already VARCHAR
-- ALTER TABLE conversations ALTER COLUMN user_id TYPE VARCHAR(255);

-- ==================== Create New Indexes ====================

-- GIN index on context JSONB for efficient querying
CREATE INDEX IF NOT EXISTS idx_conversations_context_gin
ON conversations USING GIN(context);

-- GIN index on current_payload JSONB
CREATE INDEX IF NOT EXISTS idx_conversations_payload_gin
ON conversations USING GIN(current_payload);

-- Index on auth_key for API authentication lookups
CREATE INDEX IF NOT EXISTS idx_conversations_auth_key
ON conversations(auth_key);

-- Index on current_message_id
CREATE INDEX IF NOT EXISTS idx_conversations_current_message_id
ON conversations(current_message_id);

-- ==================== Add Comments ====================

COMMENT ON COLUMN conversations.auth_key IS 'Authentication key for API access';
COMMENT ON COLUMN conversations.current_message_id IS 'Current message ID being processed';
COMMENT ON COLUMN conversations.context IS 'JSONB containing prompts and replies arrays with full message history';
COMMENT ON COLUMN conversations.current_payload IS 'JSONB containing current request payload with prompt and attached files';
COMMENT ON COLUMN conversations.resources IS 'JSONB array of resources requested in conversation';

-- ==================== Update Trigger (if not exists) ====================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_conversations_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop old trigger if exists
DROP TRIGGER IF EXISTS trigger_conversations_updated_at ON conversations;

-- Create trigger to automatically update updated_at
CREATE TRIGGER trigger_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_conversations_timestamp();

-- ==================== Helper Functions ====================

-- Function to add prompt to conversation context
CREATE OR REPLACE FUNCTION add_prompt_to_conversation(
    p_conversation_id VARCHAR,
    p_content TEXT,
    p_timestamp VARCHAR DEFAULT NULL,
    p_agents JSONB DEFAULT '[]'::jsonb,
    p_attached_files JSONB DEFAULT '[]'::jsonb
)
RETURNS VOID AS $$
DECLARE
    v_timestamp VARCHAR;
    v_prompt JSONB;
BEGIN
    -- Use provided timestamp or generate new one
    v_timestamp := COALESCE(p_timestamp, to_char(NOW() AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'));

    -- Build prompt object
    v_prompt := jsonb_build_object(
        'content', p_content,
        'timestamp', v_timestamp,
        'agents', p_agents,
        'attached_files', p_attached_files
    );

    -- Update conversation
    UPDATE conversations
    SET
        context = jsonb_set(
            COALESCE(context, '{"prompts": [], "replies": []}'::jsonb),
            '{prompts}',
            COALESCE(context->'prompts', '[]'::jsonb) || v_prompt
        ),
        message_count = message_count + 1,
        last_message_at = NOW(),
        updated_at = NOW()
    WHERE conversation_id = p_conversation_id;
END;
$$ LANGUAGE plpgsql;

-- Function to add reply to conversation context
CREATE OR REPLACE FUNCTION add_reply_to_conversation(
    p_conversation_id VARCHAR,
    p_content TEXT,
    p_timestamp VARCHAR DEFAULT NULL,
    p_agents JSONB DEFAULT '[]'::jsonb,
    p_attached_files JSONB DEFAULT '[]'::jsonb
)
RETURNS VOID AS $$
DECLARE
    v_timestamp VARCHAR;
    v_reply JSONB;
BEGIN
    -- Use provided timestamp or generate new one
    v_timestamp := COALESCE(p_timestamp, to_char(NOW() AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'));

    -- Build reply object
    v_reply := jsonb_build_object(
        'content', p_content,
        'timestamp', v_timestamp,
        'agents', p_agents,
        'attached_files', p_attached_files
    );

    -- Update conversation
    UPDATE conversations
    SET
        context = jsonb_set(
            COALESCE(context, '{"prompts": [], "replies": []}'::jsonb),
            '{replies}',
            COALESCE(context->'replies', '[]'::jsonb) || v_reply
        ),
        message_count = message_count + 1,
        last_message_at = NOW(),
        updated_at = NOW()
    WHERE conversation_id = p_conversation_id;
END;
$$ LANGUAGE plpgsql;

-- Function to get conversation statistics
CREATE OR REPLACE FUNCTION get_conversation_stats(p_conversation_id VARCHAR)
RETURNS TABLE(
    total_prompts BIGINT,
    total_replies BIGINT,
    total_messages BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COALESCE(jsonb_array_length(c.context->'prompts'), 0)::BIGINT as total_prompts,
        COALESCE(jsonb_array_length(c.context->'replies'), 0)::BIGINT as total_replies,
        c.message_count::BIGINT as total_messages
    FROM conversations c
    WHERE c.conversation_id = p_conversation_id;
END;
$$ LANGUAGE plpgsql;

-- ==================== Example Usage ====================

-- Example: Add a prompt to conversation
-- SELECT add_prompt_to_conversation(
--     '47b244ee9484f5ae3288282a26f929181e8599d21a2cd7366da79a82b7eeb4e9',
--     'What are the symptoms of diabetes?',
--     NULL,
--     '["medical_agent"]'::jsonb,
--     '[]'::jsonb
-- );

-- Example: Add a reply to conversation
-- SELECT add_reply_to_conversation(
--     '47b244ee9484f5ae3288282a26f929181e8599d21a2cd7366da79a82b7eeb4e9',
--     'Common symptoms include increased thirst and frequent urination.',
--     NULL,
--     '["medical_agent", "response_generator"]'::jsonb,
--     '[]'::jsonb
-- );

-- Example: Get conversation stats
-- SELECT * FROM get_conversation_stats('47b244ee9484f5ae3288282a26f929181e8599d21a2cd7366da79a82b7eeb4e9');

-- Example: Query conversations with specific content
-- SELECT conversation_id, title, context->'prompts' as prompts
-- FROM conversations
-- WHERE context @> '{"prompts": [{"content": "diabetes"}]}';

-- ==================== Verification ====================

-- Check new columns added
-- \d conversations

-- Check indexes created
-- \di conversations*

-- Check functions created
-- \df add_prompt_to_conversation
-- \df add_reply_to_conversation
-- \df get_conversation_stats

-- Migration complete!
-- Run with: psql -U postgres -d family_health_db -f migrations/002_alter_conversations_add_api_fields.sql
