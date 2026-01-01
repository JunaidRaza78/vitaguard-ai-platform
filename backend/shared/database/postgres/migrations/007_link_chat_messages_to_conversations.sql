-- Migration 007: Link chat_messages to conversations table
-- Date: 2025-12-29

-- ==================== Step 1: Drop old FK constraint ====================

ALTER TABLE chat_messages DROP CONSTRAINT IF EXISTS chat_messages_conversation_id_fkey;

-- ==================== Step 2: Convert conversation_id to VARCHAR ====================

-- Convert chat_messages.conversation_id from UUID to VARCHAR
ALTER TABLE chat_messages
ALTER COLUMN conversation_id TYPE VARCHAR(255)
USING conversation_id::TEXT;

-- ==================== Step 3: Add FK to conversations table ====================

-- Add foreign key constraint: chat_messages → conversations
ALTER TABLE chat_messages
ADD CONSTRAINT fk_chat_messages_conversation_id
FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
ON DELETE CASCADE ON UPDATE CASCADE;

-- ==================== Step 4: Verify ====================

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
    AND tc.table_name = 'chat_messages'
    AND kcu.column_name = 'conversation_id';

-- ==================== Done! ====================
-- chat_messages is now linked to conversations table with CASCADE delete
