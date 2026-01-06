# Database Clients Documentation

Comprehensive guide to the database clients for the Agentic AI Family Health Manager.

## Overview

The database layer provides async clients for all four databases used in the system:

- **PostgreSQL**: Transactional data, user authentication, audit logs
- **Neo4j**: Knowledge graph for health relationships and entity connections
- **MongoDB**: Document storage for conversations, medical documents, unstructured data
- **Redis**: Caching, session management, conversation memory

All clients implement:
- ✅ **Singleton pattern** - Single connection pool per application
- ✅ **Async/await** - Non-blocking I/O for high performance
- ✅ **Connection pooling** - Efficient resource management
- ✅ **Type hints** - Full type annotations
- ✅ **Error handling** - Comprehensive exception handling
- ✅ **Health checks** - Connection monitoring

---

## Table of Contents

1. [Installation](#installation)
2. [Configuration](#configuration)
3. [PostgreSQL Client](#postgresql-client)
4. [Neo4j Client](#neo4j-client)
5. [MongoDB Client](#mongodb-client)
6. [Redis Client](#redis-client)
7. [Usage Examples](#usage-examples)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Installation

### Required Dependencies

```bash
# PostgreSQL
pip install asyncpg==0.29.0

# Neo4j
pip install neo4j==5.15.0

# MongoDB
pip install motor==3.3.2
pip install pymongo==4.6.1

# Redis
pip install redis==5.0.1
```

### Install All Dependencies

```bash
pip install -r requirements.txt
```

Add to `requirements.txt`:
```txt
asyncpg==0.29.0
neo4j==5.15.0
motor==3.3.2
pymongo==4.6.1
redis==5.0.1
```

---

## Configuration

### Environment Variables

Create a `.env` file with database configurations:

```env
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=health_manager
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j

# MongoDB
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=health_manager

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
```

### Application Startup

```python
from shared.database import init_all_databases, close_all_databases
from fastapi import FastAPI
import os

app = FastAPI()

@app.on_event("startup")
async def startup():
    """Initialize all database connections on startup."""
    config = {
        "postgres": {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": int(os.getenv("POSTGRES_PORT", 5432)),
            "database": os.getenv("POSTGRES_DB", "health_manager"),
            "user": os.getenv("POSTGRES_USER", "postgres"),
            "password": os.getenv("POSTGRES_PASSWORD", ""),
        },
        "neo4j": {
            "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            "user": os.getenv("NEO4J_USER", "neo4j"),
            "password": os.getenv("NEO4J_PASSWORD", ""),
            "database": os.getenv("NEO4J_DATABASE", "neo4j"),
        },
        "mongodb": {
            "uri": os.getenv("MONGODB_URI", "mongodb://localhost:27017"),
            "database": os.getenv("MONGODB_DB", "health_manager"),
        },
        "redis": {
            "host": os.getenv("REDIS_HOST", "localhost"),
            "port": int(os.getenv("REDIS_PORT", 6379)),
            "password": os.getenv("REDIS_PASSWORD") or None,
            "db": int(os.getenv("REDIS_DB", 0)),
        }
    }

    await init_all_databases(config)

@app.on_event("shutdown")
async def shutdown():
    """Close all database connections on shutdown."""
    await close_all_databases()

@app.get("/health/databases")
async def check_databases():
    """Health check endpoint for databases."""
    from shared.database import check_all_connections
    return await check_all_connections()
```

---

## PostgreSQL Client

### Overview

Async PostgreSQL client using `asyncpg` for transactional data operations.

### Basic Usage

```python
from shared.database import postgres_client

# Query data
users = await postgres_client.fetch(
    "SELECT * FROM users WHERE active = $1",
    True
)

# Get single row
user = await postgres_client.fetchrow(
    "SELECT * FROM users WHERE user_id = $1",
    "user-123"
)

# Get single value
count = await postgres_client.fetchval(
    "SELECT COUNT(*) FROM users"
)

# Insert/Update/Delete
result = await postgres_client.execute(
    "INSERT INTO users (user_id, email, name) VALUES ($1, $2, $3)",
    "user-123", "user@example.com", "John Doe"
)

# Batch insert
users_data = [
    ("user-1", "user1@example.com", "User 1"),
    ("user-2", "user2@example.com", "User 2"),
]
await postgres_client.executemany(
    "INSERT INTO users (user_id, email, name) VALUES ($1, $2, $3)",
    users_data
)
```

### Transactions

```python
# Method 1: Using acquire() with transaction context
async with postgres_client.acquire() as conn:
    async with conn.transaction():
        await conn.execute(
            "INSERT INTO users (user_id, name) VALUES ($1, $2)",
            "user-123", "John Doe"
        )
        await conn.execute(
            "INSERT INTO profiles (user_id, bio) VALUES ($1, $2)",
            "user-123", "Software Engineer"
        )
        # Transaction commits automatically if no exception
        # Rolls back automatically on exception
```

### Advanced Queries

```python
# Using context manager for connection
async with postgres_client.acquire() as conn:
    # Prepared statement (executed multiple times efficiently)
    stmt = await conn.prepare("SELECT * FROM users WHERE age > $1")

    young_users = await stmt.fetch(18)
    older_users = await stmt.fetch(65)

# Execute SQL script
migration_script = """
CREATE TABLE IF NOT EXISTS health_records (
    record_id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    record_type VARCHAR(50),
    data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_health_records_user
    ON health_records(user_id);
"""
await postgres_client.execute_script(migration_script)
```

### Repository Pattern Example

```python
class UserRepository:
    """Repository for user operations."""

    async def create_user(self, user_id: str, email: str, name: str) -> dict:
        """Create a new user."""
        query = """
        INSERT INTO users (user_id, email, name, created_at)
        VALUES ($1, $2, $3, NOW())
        RETURNING *
        """
        return await postgres_client.fetchrow(query, user_id, email, name)

    async def get_user(self, user_id: str) -> Optional[dict]:
        """Get user by ID."""
        query = "SELECT * FROM users WHERE user_id = $1"
        return await postgres_client.fetchrow(query, user_id)

    async def update_user(self, user_id: str, **kwargs) -> dict:
        """Update user fields."""
        set_clause = ", ".join([f"{k} = ${i+2}" for i, k in enumerate(kwargs.keys())])
        query = f"""
        UPDATE users
        SET {set_clause}, updated_at = NOW()
        WHERE user_id = $1
        RETURNING *
        """
        return await postgres_client.fetchrow(query, user_id, *kwargs.values())

    async def delete_user(self, user_id: str) -> bool:
        """Delete user."""
        query = "DELETE FROM users WHERE user_id = $1"
        result = await postgres_client.execute(query, user_id)
        return result == "DELETE 1"
```

---

## Neo4j Client

### Overview

Async Neo4j client for knowledge graph operations and relationship queries.

### Basic Node Operations

```python
from shared.database import neo4j_client

# Create a node
user = await neo4j_client.create_node(
    "User",
    {
        "userId": "user-123",
        "name": "John Doe",
        "email": "john@example.com",
        "dateOfBirth": "1990-01-01"
    }
)

# Update a node
updated_user = await neo4j_client.update_node(
    "User",
    "userId",
    "user-123",
    {"email": "newemail@example.com"}
)

# Find nodes
users = await neo4j_client.find_nodes(
    "User",
    filters={"name": "John Doe"},
    limit=10
)

# Delete a node (with relationships)
deleted = await neo4j_client.delete_node(
    "User",
    "userId",
    "user-123",
    detach=True  # Also delete relationships
)
```

### Relationship Operations

```python
# Create a relationship
relationship = await neo4j_client.create_relationship(
    from_label="User",
    from_id_key="userId",
    from_id_value="user-123",
    to_label="Condition",
    to_id_key="conditionId",
    to_id_value="cond-456",
    relationship_type="HAS_CONDITION",
    properties={
        "diagnosedAt": "2024-01-15",
        "severity": "moderate"
    }
)
```

### Custom Cypher Queries

```python
# Read query
query = """
MATCH (u:User {userId: $userId})-[:HAS_CONDITION]->(c:Condition)
RETURN u, c
"""
results = await neo4j_client.execute_read(
    query,
    {"userId": "user-123"}
)

# Write query
query = """
MATCH (u:User {userId: $userId})
CREATE (u)-[:HAS_RECORD {date: $date}]->(r:HealthRecord {recordId: $recordId, type: $type})
RETURN r
"""
result = await neo4j_client.execute_write(
    query,
    {
        "userId": "user-123",
        "recordId": "rec-789",
        "type": "lab_result",
        "date": "2024-01-20"
    }
)
```

### Complex Graph Queries

```python
# Find family health patterns
query = """
MATCH (u:User)-[:MEMBER_OF]->(f:Family)
MATCH (u)-[:HAS_CONDITION]->(c:Condition)
WITH f, c, COUNT(u) as patientCount
WHERE patientCount >= 2
RETURN f.familyId, f.name, c.name, patientCount
ORDER BY patientCount DESC
"""
patterns = await neo4j_client.execute_read(query)

# Get user's complete health graph
query = """
MATCH (u:User {userId: $userId})
OPTIONAL MATCH (u)-[:HAS_CONDITION]->(c:Condition)
OPTIONAL MATCH (u)-[:TAKES]->(m:Medication)
OPTIONAL MATCH (u)-[:HAS_RECORD]->(r:HealthRecord)
RETURN u,
       COLLECT(DISTINCT c) as conditions,
       COLLECT(DISTINCT m) as medications,
       COLLECT(DISTINCT r) as records
"""
health_graph = await neo4j_client.execute_read(
    query,
    {"userId": "user-123"}
)
```

### Using Session Context Manager

```python
# For multiple operations in one session
async with neo4j_client.session() as session:
    # Create user
    result1 = await session.run(
        "CREATE (u:User {userId: $userId, name: $name}) RETURN u",
        userId="user-123",
        name="John Doe"
    )
    user = await result1.single()

    # Create family
    result2 = await session.run(
        "CREATE (f:Family {familyId: $familyId, name: $name}) RETURN f",
        familyId="fam-456",
        name="Doe Family"
    )
    family = await result2.single()

    # Link user to family
    result3 = await session.run(
        """
        MATCH (u:User {userId: $userId})
        MATCH (f:Family {familyId: $familyId})
        CREATE (u)-[:MEMBER_OF {role: $role}]->(f)
        """,
        userId="user-123",
        familyId="fam-456",
        role="parent"
    )
```

---

## MongoDB Client

### Overview

Async MongoDB client using Motor for document storage and chat conversations.

### Basic CRUD Operations

```python
from shared.database import mongo_client

# Insert a document
conversation_id = await mongo_client.insert_one(
    "conversations",
    {
        "conversationId": "conv-123",
        "userId": "user-123",
        "startTime": "2024-01-20T10:00:00Z",
        "status": "active",
        "language": "en"
    }
)

# Insert multiple documents
message_ids = await mongo_client.insert_many(
    "messages",
    [
        {"conversationId": "conv-123", "role": "user", "content": "Hello"},
        {"conversationId": "conv-123", "role": "assistant", "content": "Hi!"}
    ]
)

# Find one document
conversation = await mongo_client.find_one(
    "conversations",
    {"conversationId": "conv-123"}
)

# Find many documents
messages = await mongo_client.find_many(
    "messages",
    filter={"conversationId": "conv-123"},
    sort=[("createdAt", 1)],  # Sort ascending
    limit=50
)

# Update document
modified = await mongo_client.update_one(
    "conversations",
    filter={"conversationId": "conv-123"},
    update={"$set": {"status": "completed"}}
)

# Delete document
deleted = await mongo_client.delete_one(
    "conversations",
    {"conversationId": "conv-123"}
)
```

### Pagination

```python
# Get page 2 of conversations (10 per page)
page = 2
page_size = 10
skip = (page - 1) * page_size

conversations = await mongo_client.find_many(
    "conversations",
    filter={"userId": "user-123"},
    sort=[("startTime", -1)],  # Most recent first
    skip=skip,
    limit=page_size
)

# Get total count
total = await mongo_client.count_documents(
    "conversations",
    {"userId": "user-123"}
)

total_pages = (total + page_size - 1) // page_size
```

### Aggregation Pipeline

```python
# Get conversation statistics by user
pipeline = [
    {
        "$match": {
            "status": "completed"
        }
    },
    {
        "$group": {
            "_id": "$userId",
            "totalConversations": {"$sum": 1},
            "avgMessageCount": {"$avg": "$messageCount"},
            "lastConversation": {"$max": "$startTime"}
        }
    },
    {
        "$sort": {"totalConversations": -1}
    },
    {
        "$limit": 10
    }
]

stats = await mongo_client.aggregate("conversations", pipeline)
```

### Working with Medical Documents

```python
# Store uploaded medical document
doc_id = await mongo_client.insert_one(
    "medical_documents",
    {
        "userId": "user-123",
        "documentType": "lab_report",
        "fileName": "blood_test_2024.pdf",
        "s3Key": "documents/user-123/blood_test_2024.pdf",
        "extractedText": "...",
        "metadata": {
            "testDate": "2024-01-15",
            "labName": "City Lab",
            "testType": "Complete Blood Count"
        },
        "processed": True
    }
)

# Search documents by metadata
lab_reports = await mongo_client.find_many(
    "medical_documents",
    filter={
        "userId": "user-123",
        "documentType": "lab_report",
        "metadata.testDate": {"$gte": "2024-01-01"}
    },
    sort=[("metadata.testDate", -1)]
)
```

### Indexes

```python
# Create indexes for performance
await mongo_client.create_index(
    "conversations",
    [("userId", 1), ("startTime", -1)]
)

await mongo_client.create_index(
    "messages",
    [("conversationId", 1), ("createdAt", 1)]
)

await mongo_client.create_index(
    "medical_documents",
    [("userId", 1), ("documentType", 1)]
)

# Create unique index
await mongo_client.create_index(
    "conversations",
    "conversationId",
    unique=True
)
```

---

## Redis Client

### Overview

Async Redis client for caching, session management, and conversation memory.

### String Operations

```python
from shared.database import redis_client

# Set and get
await redis_client.set("user:123:name", "John Doe")
name = await redis_client.get("user:123:name")

# Set with expiration (TTL)
await redis_client.set("session:abc123", "user-123", ex=3600)  # 1 hour

# Check if key exists
exists = await redis_client.exists("user:123:name")

# Delete keys
await redis_client.delete("user:123:name", "user:123:email")

# Get TTL
ttl = await redis_client.ttl("session:abc123")  # Seconds remaining
```

### JSON Caching

```python
# Cache complex objects
user_data = {
    "userId": "user-123",
    "name": "John Doe",
    "preferences": {"theme": "dark", "language": "en"}
}

# Set with 1 hour TTL
await redis_client.set_json("user:123:profile", user_data, ex=3600)

# Get cached object
cached_user = await redis_client.get_json("user:123:profile")

# Using cache helpers
await redis_client.cache_set("api:response:123", {"status": "ok"}, ttl=300)
response = await redis_client.cache_get("api:response:123")
```

### Hash Operations

```python
# Store user session data
await redis_client.hset(
    "session:abc123",
    mapping={
        "userId": "user-123",
        "loginTime": "2024-01-20T10:00:00Z",
        "ipAddress": "192.168.1.1"
    }
)

# Get single field
user_id = await redis_client.hget("session:abc123", "userId")

# Get all fields
session = await redis_client.hgetall("session:abc123")

# Delete field
await redis_client.hdel("session:abc123", "ipAddress")
```

### List Operations (Conversation History)

```python
# Add messages to conversation history
await redis_client.rpush(
    "conversation:conv-123",
    '{"role": "user", "content": "Hello"}',
    '{"role": "assistant", "content": "Hi!"}'
)

# Get recent messages
messages = await redis_client.lrange("conversation:conv-123", -10, -1)

# Keep only last 50 messages
await redis_client.ltrim("conversation:conv-123", -50, -1)

# Pop oldest message
oldest = await redis_client.lpop("conversation:conv-123")
```

### Conversation Memory Helpers

```python
import json

# Save conversation history
messages = [
    {"role": "user", "content": "What's my blood pressure?"},
    {"role": "assistant", "content": "Your last reading was 120/80..."}
]

await redis_client.save_conversation_history(
    "conv-123",
    messages,
    max_messages=50,
    ttl=86400  # 24 hours
)

# Retrieve conversation history
history = await redis_client.get_conversation_history(
    "conv-123",
    limit=10  # Last 10 messages
)
```

### Set Operations (User Permissions)

```python
# Add permissions
await redis_client.sadd(
    "user:123:permissions",
    "read:health_records",
    "write:appointments",
    "read:family_data"
)

# Check permission
has_perm = await redis_client.sismember(
    "user:123:permissions",
    "read:health_records"
)

# Get all permissions
permissions = await redis_client.smembers("user:123:permissions")

# Remove permission
await redis_client.srem("user:123:permissions", "write:appointments")
```

### Sorted Sets (Leaderboards, Rankings)

```python
# Track API usage by endpoint
await redis_client.zadd(
    "api:usage:2024-01",
    {
        "/api/chat": 1500,
        "/api/users": 800,
        "/api/health-records": 600
    }
)

# Get top 5 endpoints
top_endpoints = await redis_client.zrange(
    "api:usage:2024-01",
    0, 4,
    desc=True,
    withscores=True
)
# Returns: [('/api/chat', 1500.0), ('/api/users', 800.0), ...]
```

### Rate Limiting Example

```python
async def check_rate_limit(user_id: str, limit: int = 100, window: int = 3600) -> bool:
    """
    Check if user is within rate limit.

    Args:
        user_id: User identifier
        limit: Max requests per window
        window: Time window in seconds

    Returns:
        True if within limit, False otherwise
    """
    key = f"rate_limit:{user_id}"

    # Get current count
    current = await redis_client.get(key)

    if current is None:
        # First request in window
        await redis_client.set(key, 1, ex=window)
        return True

    current_count = int(current)
    if current_count >= limit:
        return False

    # Increment counter
    await redis_client.execute("INCR", key)
    return True
```

---

## Usage Examples

### Example 1: User Registration Flow

```python
from shared.database import postgres_client, neo4j_client, redis_client
import uuid
from datetime import datetime

async def register_user(email: str, name: str, password_hash: str):
    """Complete user registration across all databases."""

    user_id = str(uuid.uuid4())

    # 1. Create user in PostgreSQL (transactional data)
    user = await postgres_client.fetchrow(
        """
        INSERT INTO users (user_id, email, name, password_hash, created_at)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING *
        """,
        user_id, email, name, password_hash, datetime.utcnow()
    )

    # 2. Create user node in Neo4j (knowledge graph)
    await neo4j_client.create_node(
        "User",
        {
            "userId": user_id,
            "email": email,
            "name": name,
            "createdAt": datetime.utcnow().isoformat()
        }
    )

    # 3. Cache user profile in Redis (1 hour)
    await redis_client.cache_set(
        f"user:{user_id}:profile",
        {"userId": user_id, "email": email, "name": name},
        ttl=3600
    )

    return user
```

### Example 2: Chat Message Storage

```python
from shared.database import mongo_client, neo4j_client, redis_client

async def save_chat_message(
    conversation_id: str,
    user_id: str,
    role: str,
    content: str,
    intent: str
):
    """Save chat message across MongoDB, Neo4j, and Redis."""

    message_id = str(uuid.uuid4())

    # 1. Store message in MongoDB (persistent storage)
    await mongo_client.insert_one(
        "messages",
        {
            "messageId": message_id,
            "conversationId": conversation_id,
            "role": role,
            "content": content,
            "intent": intent,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

    # 2. Create message node in Neo4j (for relationship queries)
    await neo4j_client.create_node(
        "ChatMessage",
        {
            "messageId": message_id,
            "conversationId": conversation_id,
            "role": role,
            "intent": intent,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

    # Link message to conversation
    await neo4j_client.create_relationship(
        from_label="Conversation",
        from_id_key="conversationId",
        from_id_value=conversation_id,
        to_label="ChatMessage",
        to_id_key="messageId",
        to_id_value=message_id,
        relationship_type="HAS_MESSAGE"
    )

    # 3. Add to Redis conversation memory (last 50 messages)
    await redis_client.rpush(
        f"conversation:{conversation_id}",
        json.dumps({"role": role, "content": content})
    )
    await redis_client.ltrim(f"conversation:{conversation_id}", -50, -1)

    return message_id
```

### Example 3: Health Record Retrieval with Caching

```python
async def get_user_health_records(user_id: str) -> dict:
    """Get user health records with Redis caching."""

    cache_key = f"health_records:{user_id}"

    # Try cache first
    cached = await redis_client.cache_get(cache_key)
    if cached:
        return cached

    # Query Neo4j for health graph
    query = """
    MATCH (u:User {userId: $userId})
    OPTIONAL MATCH (u)-[:HAS_CONDITION]->(c:Condition)
    OPTIONAL MATCH (u)-[:TAKES]->(m:Medication)
    OPTIONAL MATCH (u)-[:HAS_RECORD]->(r:HealthRecord)
    RETURN u,
           COLLECT(DISTINCT c) as conditions,
           COLLECT(DISTINCT m) as medications,
           COLLECT(DISTINCT r) as records
    """

    result = await neo4j_client.execute_read(query, {"userId": user_id})

    # Cache for 5 minutes
    await redis_client.cache_set(cache_key, result[0], ttl=300)

    return result[0]
```

---

## Best Practices

### 1. Connection Management

```python
# ✅ DO: Initialize once at startup
@app.on_event("startup")
async def startup():
    await init_all_databases(config)

# ❌ DON'T: Create new clients for each request
async def bad_handler():
    client = PostgresClient()
    await client.connect(...)  # DON'T DO THIS
```

### 2. Use Context Managers

```python
# ✅ DO: Use context managers for sessions
async with neo4j_client.session() as session:
    result = await session.run(query)

# ✅ DO: Use context managers for transactions
async with postgres_client.acquire() as conn:
    async with conn.transaction():
        await conn.execute(query1)
        await conn.execute(query2)
```

### 3. Error Handling

```python
from asyncpg import PostgresError
from neo4j.exceptions import ServiceUnavailable
from pymongo.errors import PyMongoError

async def safe_database_operation():
    try:
        result = await postgres_client.fetch("SELECT * FROM users")
        return result
    except PostgresError as e:
        logger.error(f"PostgreSQL error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
```

### 4. Use Prepared Statements

```python
# ✅ DO: Use parameterized queries (prevents SQL injection)
await postgres_client.fetch(
    "SELECT * FROM users WHERE email = $1",
    email
)

# ❌ DON'T: Use string formatting
await postgres_client.fetch(
    f"SELECT * FROM users WHERE email = '{email}'"  # DANGEROUS!
)
```

### 5. Implement Caching Strategy

```python
async def get_user_with_cache(user_id: str):
    # 1. Check Redis cache (fastest)
    cached = await redis_client.cache_get(f"user:{user_id}")
    if cached:
        return cached

    # 2. Query PostgreSQL (source of truth)
    user = await postgres_client.fetchrow(
        "SELECT * FROM users WHERE user_id = $1",
        user_id
    )

    # 3. Cache result (15 minutes)
    if user:
        await redis_client.cache_set(f"user:{user_id}", dict(user), ttl=900)

    return user
```

### 6. Health Checks

```python
@app.get("/health")
async def health_check():
    """Application health check with database status."""
    from shared.database import check_all_connections

    db_status = await check_all_connections()

    all_healthy = all(db_status.values())
    status_code = 200 if all_healthy else 503

    return {
        "status": "healthy" if all_healthy else "unhealthy",
        "databases": db_status
    }
```

---

## Troubleshooting

### PostgreSQL Connection Issues

```python
# Problem: "too many clients already"
# Solution: Reduce pool size or increase PostgreSQL max_connections

await init_postgres(
    host="localhost",
    port=5432,
    database="health_manager",
    user="postgres",
    password="password",
    min_size=5,   # Reduce from 10
    max_size=20   # Reduce from 50
)
```

### Neo4j Memory Issues

```python
# Problem: "OutOfMemoryError"
# Solution: Add database parameter and reduce pool size

await init_neo4j(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password",
    database="neo4j",
    max_connection_pool_size=20  # Reduce from 50
)
```

### MongoDB Timeout Issues

```python
# Problem: "ServerSelectionTimeoutError"
# Solution: Increase timeout and check connection string

await init_mongo(
    uri="mongodb://localhost:27017",
    database="health_manager",
    server_selection_timeout_ms=10000  # Increase to 10 seconds
)
```

### Redis Connection Drops

```python
# Problem: Connection drops under load
# Solution: Configure connection pooling and timeouts

await init_redis(
    host="localhost",
    port=6379,
    max_connections=100,  # Increase pool
    socket_timeout=10,     # Increase timeout
    socket_connect_timeout=10
)
```

### Debug Logging

```python
import logging

# Enable debug logging for database clients
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("shared.database").setLevel(logging.DEBUG)
```

---

## Performance Tips

### 1. Use Batch Operations

```python
# ✅ Batch insert (faster)
await postgres_client.executemany(query, data_list)

# ❌ Individual inserts (slower)
for data in data_list:
    await postgres_client.execute(query, *data)
```

### 2. Index Your Queries

```python
# Create indexes for frequently queried fields
await mongo_client.create_index(
    "conversations",
    [("userId", 1), ("startTime", -1)]
)
```

### 3. Use Connection Pooling

All clients implement connection pooling by default. Configure based on your load:

- **Low traffic** (<100 req/s): min=5, max=20
- **Medium traffic** (100-500 req/s): min=10, max=50
- **High traffic** (>500 req/s): min=20, max=100

### 4. Cache Frequently Accessed Data

```python
# Cache user profiles, configuration, static data
await redis_client.cache_set(key, value, ttl=3600)  # 1 hour
```

---

## Additional Resources

- [AsyncPG Documentation](https://magicstack.github.io/asyncpg/)
- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)
- [Motor Documentation](https://motor.readthedocs.io/)
- [Redis Python Documentation](https://redis-py.readthedocs.io/)

---

## Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review database-specific documentation
3. Check application logs for error details
4. Open an issue on the project repository
