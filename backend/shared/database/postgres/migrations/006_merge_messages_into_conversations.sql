-- Migration 006: Merge chat_messages into conversations table
-- Add messages as JSONB array to conversations
-- Date: 2025-12-29

-- ==================== Step 1: Add messages field to conversations ====================

-- Add messages array to store all messages for a conversation
ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS messages JSONB DEFAULT '[]'::jsonb;

-- Create GIN index for efficient message queries
CREATE INDEX IF NOT EXISTS idx_conversations_messages_gin ON conversations USING GIN(messages);

-- ==================== Step 2: Migrate existing chat_messages data (if any) ====================

-- This will move data from chat_messages to conversations.messages array
DO $$
BEGIN
    -- Check if chat_messages table exists
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'chat_messages') THEN
        -- Update conversations with messages from chat_messages
        UPDATE conversations c
        SET messages = COALESCE(
            (
                SELECT jsonb_agg(
                    jsonb_build_object(
                        'message_id', cm.message_id,
                        'role', cm.role,
                        'content', cm.content,
                        'timestamp', cm.timestamp,
                        'metadata', COALESCE(cm.metadata, '{}'::jsonb)
                    ) ORDER BY cm.timestamp
                )
                FROM chat_messages cm
                WHERE cm.conversation_id = c.conversation_id
            ),
            '[]'::jsonb
        )
        WHERE EXISTS (
            SELECT 1 FROM chat_messages cm2
            WHERE cm2.conversation_id = c.conversation_id
        );

        RAISE NOTICE 'Migrated messages from chat_messages to conversations.messages';
    ELSE
        RAISE NOTICE 'chat_messages table does not exist, skipping migration';
    END IF;
END $$;

-- ==================== Step 3: Update conversation model comment ====================

COMMENT ON COLUMN conversations.messages IS 'Array of messages with structure: [{message_id, role, content, timestamp, metadata}]';

-- ==================== Step 4: Verify migration ====================

-- Show sample of messages structure
SELECT
    conversation_id,
    user_id,
    jsonb_array_length(messages) as message_count,
    messages -> 0 as first_message_sample
FROM conversations
WHERE jsonb_array_length(messages) > 0
LIMIT 3;

-- ==================== Done! ====================
-- Messages are now stored in conversations.messages as JSONB array
-- Each message has: message_id, role, content, timestamp, metadata
-- Old chat_messages table can now be dropped (use cleanup script)
