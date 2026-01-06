# Monolithic PostgreSQL Database - Setup Guide

Complete step-by-step guide to setup monolithic PostgreSQL database with foreign keys.

---

## 📋 Prerequisites

1. PostgreSQL installed and running
2. Database created: `family_health_db`
3. Python 3.8+ installed

---

---

## 📝 Manual Setup (Step by Step)

### Step 1: Verify Database Connection

```bash
psql -U postgres -d family_health_db -c "SELECT version();"
```

Expected: PostgreSQL version information displayed

---

### Step 2: Run Migration 002 - Add JSONB Fields

```bash
psql -U postgres -d family_health_db -f migrations/002_alter_conversations_add_api_fields.sql
```

**What it does:**
- Adds `context` JSONB field (for prompts and replies)
- Adds `current_payload` JSONB field
- Adds `resources` JSONB field
- Adds `messages` JSONB array field
- Adds `auth_key` and `current_message_id` fields
- Creates GIN indexes for fast JSONB queries

**Verify:**
```bash
psql -U postgres -d family_health_db -c "\d conversations"
```

You should see new columns: `context`, `current_payload`, `resources`, `messages`

---

### Step 3: Run Migration 003 - Add Foreign Keys

```bash
psql -U postgres -d family_health_db -f migrations/003_add_foreign_keys_monolithic.sql
```

**What it does:**
- Links `conversations` → `users` (CASCADE)
- Links `conversation_metrics` → `conversations` (CASCADE)
- Links `user_sessions` → `users` (CASCADE)
- Links `notifications` → `users` (CASCADE)
- Links `document_jobs` → `users` (CASCADE)
- Links `api_rate_limit` → `users` (CASCADE)
- Links `audit_log` → `users` (SET NULL)

**Verify:**
```bash
psql -U postgres -d family_health_db -c "
SELECT tc.table_name, kcu.column_name, ccu.table_name AS references
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
ORDER BY tc.table_name;
"
```

---

### Step 4: Run Migration 004 - Convert UUID to VARCHAR

```bash
psql -U postgres -d family_health_db -f migrations/004_convert_users_to_varchar.sql
```

**What it does:**
- Converts `users.user_id` from UUID → VARCHAR(255)
- Converts `conversations.user_id` from UUID → VARCHAR(255)
- Converts all foreign key columns to VARCHAR(255)
- Re-adds foreign key constraints

**Why?**
- Your API uses string-based IDs: `user_340DlA9nYN4BilkhEt31PWs5Z1i`
- VARCHAR is more flexible than UUID
- Matches your API format exactly

**Verify:**
```bash
psql -U postgres -d family_health_db -c "
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE column_name = 'user_id' AND table_schema = 'public'
ORDER BY table_name;
"
```

All should show: `character varying`

---

### Step 5: Run Migration 005 - Complete VARCHAR Conversion

```bash
psql -U postgres -d family_health_db -f migrations/005_convert_remaining_uuids_to_varchar.sql
```

**What it does:**
- Converts remaining UUID columns to VARCHAR
- Handles partitioned tables (audit_logs, notifications)
- Re-adds all foreign key constraints
- Finalizes monolithic architecture

**Verify:**
```bash
psql -U postgres -d family_health_db -c "
SELECT table_name, data_type
FROM information_schema.columns
WHERE column_name = 'user_id'
  AND table_name IN ('users', 'conversations', 'user_sessions')
ORDER BY table_name;
"
```

---

### Step 6: Run Migration 006 - Add Messages Array

```bash
psql -U postgres -d family_health_db -f migrations/006_merge_messages_into_conversations.sql
```

**What it does:**
- Adds `messages` JSONB array to conversations table
- Creates GIN index for efficient queries
- Messages stored directly in conversation (no separate table needed)

**Message Structure:**
```json
{
  "message_id": "msg_001",
  "role": "user",
  "content": "Hello!",
  "timestamp": "2025-12-29T14:30:00Z",
  "metadata": {}
}
```

**Verify:**
```bash
psql -U postgres -d family_health_db -c "
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'conversations' AND column_name = 'messages';
"
```

---

### Step 7: Run Migration 007 - Link chat_messages

```bash
psql -U postgres -d family_health_db -f migrations/007_link_chat_messages_to_conversations.sql
```

**What it does:**
- Converts `chat_messages.conversation_id` to VARCHAR
- Links `chat_messages` → `conversations` with FK

**Verify:**
```bash
psql -U postgres -d family_health_db -c "
SELECT tc.table_name, ccu.table_name AS references
FROM information_schema.table_constraints AS tc
JOIN information_schema.constraint_column_usage AS ccu ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = 'chat_messages';
"
```

---

### Step 8: Clean Up Orphaned Messages

```bash
psql -U postgres -d family_health_db -c "
DELETE FROM chat_messages
WHERE conversation_id NOT IN (SELECT conversation_id FROM conversations);
"
```

**What it does:**
- Removes messages that reference non-existent conversations
- Required before adding FK constraint

---

### Step 9: Add chat_messages Foreign Key

```bash
psql -U postgres -d family_health_db -c "
ALTER TABLE chat_messages
ADD CONSTRAINT fk_chat_messages_conversation_id
FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
ON DELETE CASCADE ON UPDATE CASCADE;
"
```

**Verify:**
```bash
psql -U postgres -d family_health_db -c "\d chat_messages"
```

Should show FK constraint to conversations

---

### Step 10: Remove Old Tables

```bash
psql -U postgres -d family_health_db -c "
DROP TABLE IF EXISTS chat_feedback CASCADE;
DROP TABLE IF EXISTS chat_conversations CASCADE;
DROP TABLE IF EXISTS chat_metrics CASCADE;
"
```

**What it removes:**
- `chat_feedback` (old feedback table)
- `chat_conversations` (old UUID-based conversations)
- `chat_metrics` (old metrics table)

**Verify:**
```bash
psql -U postgres -d family_health_db -c "
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public' AND table_name LIKE '%chat%'
ORDER BY table_name;
"
```

Should only show: `chat_messages`

---

## ✅ Verification

### Check All Foreign Keys

```bash
psql -U postgres -d family_health_db -c "
SELECT
    tc.table_name AS \"Table\",
    kcu.column_name AS \"Column\",
    ccu.table_name AS \"References\",
    rc.delete_rule AS \"On Delete\"
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu ON ccu.constraint_name = tc.constraint_name
JOIN information_schema.referential_constraints AS rc ON tc.constraint_name = rc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND ccu.table_name IN ('users', 'conversations')
ORDER BY ccu.table_name, tc.table_name;
"
```

**Expected Output:**
```
Table                | Column          | References    | On Delete
---------------------|-----------------|---------------|----------
api_rate_limits      | user_id         | users         | CASCADE
audit_logs           | user_id         | users         | SET NULL
conversations        | user_id         | users         | CASCADE
document_jobs        | user_id         | users         | CASCADE
notifications        | user_id         | users         | CASCADE
user_sessions        | user_id         | users         | CASCADE
chat_messages        | conversation_id | conversations | CASCADE
conversation_metrics | conversation_id | conversations | CASCADE
```

---

### Check VARCHAR Conversion

```bash
psql -U postgres -d family_health_db -c "
SELECT table_name, column_name, data_type, character_maximum_length
FROM information_schema.columns
WHERE column_name = 'user_id' AND table_schema = 'public'
  AND table_name IN ('users', 'conversations', 'user_sessions')
ORDER BY table_name;
"
```

**Expected Output:**
All should show `character varying` with length `255`

---

### Test Python Import

```bash
python3 -c "
from backend.shared.database.postgres.client import SimpleConversationClient
from backend.shared.database.postgres.models import User, Conversation
print('✅ All imports working!')
"
```

---

## 🎯 Final Database Structure

```
users (VARCHAR user_id)
 ├── conversations (CASCADE)
 │    ├── chat_messages (CASCADE)
 │    └── conversation_metrics (CASCADE)
 ├── user_sessions (CASCADE)
 ├── notifications (CASCADE)
 ├── document_jobs (CASCADE)
 ├── api_rate_limits (CASCADE)
 └── audit_logs (SET NULL)
```

**Key Features:**
- ✅ All tables linked with foreign keys
- ✅ CASCADE delete rules (except audit_logs)
- ✅ VARCHAR(255) for all user_id columns
- ✅ JSONB fields for flexible data storage
- ✅ GIN indexes for fast JSONB queries
- ✅ Monolithic architecture (NOT microservices)

---

## 📊 View ERD in DBeaver

1. Open DBeaver
2. Connect to `family_health_db`
3. Right-click database → **Refresh**
4. Right-click database → **View Diagram**
5. You'll see all foreign key relationships with arrows

---

## 💻 Usage Example

```python
from backend.shared.database.postgres.client import SimpleConversationClient
from backend.shared.database.postgres.models import Conversation

with SimpleConversationClient() as client:
    # Create conversation (user must exist!)
    conv = Conversation(
        conversation_id="conv_123",
        user_id="user_abc",  # Must exist in users table
        status="active",
        context={"prompts": [], "replies": []},
        messages=[]
    )

    session = client.get_session()
    session.add(conv)

    # Add message
    conv.add_message(
        message_id="msg_001",
        role="user",
        content="Hello!",
        metadata={"source": "web"}
    )

    session.commit()
    print(f"✅ Created conversation with {len(conv.messages)} messages")
```

---

## 🔧 Troubleshooting

### Error: "foreign key constraint ... cannot be implemented"

**Cause:** Type mismatch (UUID vs VARCHAR)

**Solution:** Run migrations 004 and 005 to convert all UUIDs to VARCHAR

---

### Error: "violates foreign key constraint"

**Cause:** Orphaned records (data referencing non-existent parent)

**Solution:**
```bash
# Find orphaned conversations
psql -U postgres -d family_health_db -c "
SELECT c.conversation_id, c.user_id
FROM conversations c
LEFT JOIN users u ON c.user_id = u.user_id
WHERE u.user_id IS NULL;
"

# Delete orphaned conversations
psql -U postgres -d family_health_db -c "
DELETE FROM conversations
WHERE user_id NOT IN (SELECT user_id FROM users);
"
```

---

### Error: "relation does not exist"

**Cause:** Migrations not run in order

**Solution:** Run migrations in sequence (002 → 003 → 004 → 005 → 006 → 007)

---

## 📚 Related Files

- [models.py](models.py) - SQLAlchemy models (User, Conversation)
- [client.py](client.py) - Database client with helper methods
- [config.py](config.py) - Database configuration
- [migrations/](migrations/) - All 6 migration SQL files

---

## ✨ Summary

You've successfully set up a monolithic PostgreSQL database with:

1. ✅ MongoDB removed completely
2. ✅ All tables linked with foreign keys
3. ✅ CASCADE delete rules for automatic cleanup
4. ✅ VARCHAR user_id (matches your API format)
5. ✅ JSONB fields for flexible data storage
6. ✅ Messages embedded in conversations
7. ✅ Clean, maintainable structure

**Your database is production-ready!** 🚀

---

## 🎉 Next Steps

1. Test the API with your frontend
2. Monitor foreign key performance
3. Add indexes as needed for your queries
4. Consider adding database triggers for complex business logic
5. Set up regular backups

---

**Need help?** Check the troubleshooting section above.
