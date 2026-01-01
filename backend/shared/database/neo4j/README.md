# Neo4j Database Module - Modular Structure

## 📋 Table of Contents
- [Quick Setup](#-quick-setup)
- [Overview](#overview)
- [Usage](#usage)
- [Module Breakdown](#module-breakdown)
- [Adding New Features](#adding-new-operation-modules)

---

## 🚀 Quick Setup

### Step 1: Install Neo4j

#### Option A: Neo4j Desktop (Recommended for Development)
1. Download Neo4j Desktop: https://neo4j.com/download/
2. Install and open Neo4j Desktop
3. Create a new project
4. Add a local DBMS:
   - Name: `family-health-db`
   - Password: `your_secure_password` (choose a strong password)
   - Version: Latest (5.x)
5. Start the database
6. Open Neo4j Browser (click "Open" button)

#### Option B: Docker
```bash
docker run \
  --name neo4j-family-health \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_secure_password \
  -v $HOME/neo4j/data:/data \
  -v $HOME/neo4j/logs:/logs \
  neo4j:latest
```

#### Option C: Linux/Mac System Install
```bash
# Ubuntu/Debian
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list
sudo apt-get update
sudo apt-get install neo4j

# Mac with Homebrew
brew install neo4j
neo4j start
```

### Step 2: Configure Environment

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Update Neo4j settings in `.env`:
```bash
# Neo4j Connection Settings
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_secure_password  # Use the password you set in Step 1
NEO4J_DATABASE=neo4j
```

### Step 3: Install Python Dependencies

```bash
# Install required packages
pip install neo4j python-dotenv
```

### Step 4: Initialize Database Schema

```bash
# Run schema initialization
cd backend/shared/database/neo4j
python3 init_schema.py
```

Expected output:
```
============================================================
Initializing Neo4j Schema...
============================================================

[1/50] Executing: CREATE CONSTRAINT userId_unique IF NOT EXISTS...
✅ Success

[2/50] Executing: CREATE CONSTRAINT user_email_unique IF NOT EXISTS...
✅ Success

...

============================================================
Schema Initialization Complete!
✅ Successful: 48
⚠️  Skipped/Errors: 2
============================================================
```

### Step 5: Test Connection

```bash
# Run quick test
python3 quick_test.py
```

Expected output:
```
============================================================
Neo4j Quick Test - Modular Client
============================================================

✅ Successfully imported Neo4jClient
✅ Created Neo4jClient instance

📡 Testing Neo4j connection...
   URI: bolt://localhost:7687
   Database: neo4j
✅ Neo4j connection: HEALTHY

...

✅ All tests passed! Your Neo4j client is ready to use!
```

### Step 6: Verify in Neo4j Browser

1. Open Neo4j Browser: **http://localhost:7474**
2. Login:
   - Username: `neo4j`
   - Password: `your_secure_password` (the one you set)
3. Run this query:
```cypher
MATCH (n) RETURN n LIMIT 25
```

---

## Overview

The Neo4j database module has been refactored from a single **3200+ line file** into a **clean, modular architecture** with small, focused files that are easy to maintain and extend.

## Before & After

### Before (Monolithic)
```
neo4j/
├── __init__.py
├── config.py
└── neo4j_client.py (3200+ lines!) ❌
```

### After (Modular)
```
neo4j/
├── __init__.py
├── config.py                    # Configuration
├── base_client.py               # Core connection (~100 lines)
├── client.py                    # Unified client (~60 lines)
├── operations/
│   ├── __init__.py
│   ├── graph_ops.py            # Generic operations (~350 lines)
│   ├── user_ops.py             # User operations (~200 lines)
│   └── family_ops.py           # Family operations (~300 lines)
└── neo4j_client_legacy.py      # Old file (backup)
```

## Usage

### Basic Usage (Recommended)

```python
from backend.shared.database.neo4j import Neo4jClient

# Create client instance
client = Neo4jClient()

# User operations
user = client.create_user(
    userId="user-123",
    email="john@example.com",
    name="John Doe",
    dateOfBirth="1990-01-01",
    gender="M",
    bloodType="O+",
    phoneNumber="+1234567890"
)

# Get user
user = client.get_user_by_id("user-123")
user_by_email = client.get_user_by_email("john@example.com")

# Update user
client.update_user("user-123", {"phoneNumber": "+9876543210"})

# Family operations
family = client.create_family(
    familyId="family-456",
    name="Doe Family",
    createdBy="user-123"
)

# Add user to family
client.add_user_to_family(
    userId="user-123",
    familyId="family-456",
    role="parent"
)

# Get family members
members = client.get_family_members("family-456")

# Create family relationships
client.create_family_relationship(
    user1_id="parent-id",
    relationship_type="PARENT_OF",
    user2_id="child-id"
)

# Generic graph operations (inherited from GraphOperations)
node = client.get_node("User", "userId", "user-123")
client.create_relationship(
    from_label="User",
    from_property="userId",
    from_value="user-123",
    relationship_type="HAS_CONDITION",
    to_label="Condition",
    to_property="conditionId",
    to_value="condition-789"
)

# Health check
if client.health_check():
    print("Neo4j connection is healthy")
```

### Advanced Usage (Individual Operation Classes)

```python
from backend.shared.database.neo4j.operations import UserOperations, FamilyOperations

# Use specific operation classes
user_ops = UserOperations()
user = user_ops.create_user(...)

family_ops = FamilyOperations()
family = family_ops.create_family(...)
```

## Module Breakdown

### 1. `config.py`
- Configuration management
- Connection pooling
- Environment variable loading
- Health checks

### 2. `base_client.py`
- Core Neo4j connection
- Session management
- Query execution with proper error handling
- Context manager support

### 3. `operations/graph_ops.py`
- Generic node operations (create, get, update, delete)
- Generic relationship operations
- Path finding
- Base class for all specific operation classes

### 4. `operations/user_ops.py`
- User CRUD operations
- User search (by ID, by email)
- User management

### 5. `operations/family_ops.py`
- Family CRUD operations
- User-family relationships (add/remove members)
- Family tree operations
- Family relationship types (PARENT_OF, CHILD_OF, etc.)

### 6. `client.py`
- Unified client combining all operations
- Single interface for all functionality
- **Recommended for all applications**

## Benefits of Modular Structure

### ✅ Maintainability
- Small, focused files (200-350 lines each)
- Easy to find and fix issues
- Clear separation of concerns

### ✅ Extensibility
- Easy to add new operation modules
- Simple inheritance model
- No need to modify existing code

### ✅ Testability
- Test individual modules independently
- Mock specific operations easily
- Clearer test organization

### ✅ Code Organization
- Domain-driven design
- Logical grouping of operations
- Better code navigation

### ✅ Reusability
- Use specific operation classes when needed
- Share base functionality across modules
- Compose clients with only needed operations

## Adding New Operation Modules

To add a new domain (e.g., HealthRecord operations):

### 1. Create new operation file

```python
# operations/health_record_ops.py
from backend.shared.database.neo4j.operations.graph_ops import GraphOperations
from backend.shared.logging import get_logger

logger = get_logger('neo4j.health_record_ops')

class HealthRecordOperations(GraphOperations):
    """Health record specific operations."""

    def create_health_record(self, ...):
        # Implementation
        pass

    def get_user_health_records(self, userId: str):
        # Implementation
        pass
```

### 2. Update `operations/__init__.py`

```python
from backend.shared.database.neo4j.operations.health_record_ops import HealthRecordOperations

__all__ = [
    ...
    "HealthRecordOperations",
]
```

### 3. Add to unified client

```python
# client.py
class Neo4jClient(UserOperations, FamilyOperations, HealthRecordOperations):
    """Unified client with all operations."""
    pass
```

### 4. Export from main `__init__.py`

```python
# __init__.py
from backend.shared.database.neo4j.operations import HealthRecordOperations

__all__ = [
    ...
    "HealthRecordOperations",
]
```

## Migration from Old Code

The new modular client is **100% backward compatible**:

```python
# Old code (still works!)
from backend.shared.database.neo4j import Neo4jClient

client = Neo4jClient()
user = client.create_user(...)  # Works exactly the same!
```

The old `neo4j_client.py` has been renamed to `neo4j_client_legacy.py` for reference.

## Testing

Run the test script to verify everything works:

```bash
cd backend/shared/database/neo4j
python3 test_modular_client.py
```

Expected output:
```
✅ Config imports successful
✅ Unified client imports successful
✅ Individual operation class imports successful
✅ Neo4jClient instance created
✅ All expected methods are available
✅ Neo4j connection: HEALTHY
✅ Modular structure is working correctly!
```

## Performance

- **No performance impact**: Same underlying code, just better organized
- **Better logging**: All operations now have comprehensive logging
- **Proper session management**: Sessions are properly closed, preventing connection leaks

## File Sizes Comparison

| File | Old Size | New Size |
|------|----------|----------|
| neo4j_client.py | 3200+ lines | N/A (split) |
| base_client.py | - | ~100 lines |
| graph_ops.py | - | ~350 lines |
| user_ops.py | - | ~200 lines |
| family_ops.py | - | ~300 lines |
| client.py | - | ~60 lines |

**Total**: Same functionality, better organized!

## Logging

All operations now have comprehensive logging:

```python
# Logs are categorized by module
logger = get_logger('neo4j.user_ops')      # User operations
logger = get_logger('neo4j.family_ops')    # Family operations
logger = get_logger('neo4j.graph_ops')     # Graph operations
logger = get_logger('neo4j.base_client')   # Core client
```

Log levels:
- `DEBUG`: Query details, session creation
- `INFO`: Successful operations
- `WARNING`: Not found, empty results
- `ERROR`: Exceptions with full context

## Future Additions

The structure makes it easy to add:
- `operations/health_record_ops.py` - Health record operations
- `operations/medical_ops.py` - Medication, Condition, Symptom operations
- `operations/provider_ops.py` - Doctor, Hospital, Appointment operations
- `operations/conversation_ops.py` - Chat and conversation operations

Each module can be developed and tested independently!

## Troubleshooting

### Connection Issues

**Problem:** `Neo4j connection: FAILED`

**Solutions:**
```bash
# 1. Check if Neo4j is running
# Neo4j Desktop: Check if database is started
# Docker: docker ps | grep neo4j
# Linux: systemctl status neo4j

# 2. Verify connection settings in .env
NEO4J_URI=bolt://localhost:7687      # Correct port?
NEO4J_PASSWORD=your_secure_password  # Correct password?

# 3. Test connection manually
neo4j://localhost:7687
# Or visit: http://localhost:7474
```

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'backend'`

**Solution:**
```bash
# Make sure you're running from project root
cd /path/to/agentic-ai-family-health-manager
python3 backend/shared/database/neo4j/quick_test.py
```

### Schema Initialization Errors

**Problem:** Schema initialization fails

**Solutions:**
```bash
# 1. Delete all existing data (CAUTION: Deletes everything!)
# In Neo4j Browser:
MATCH (n) DETACH DELETE n

# 2. Re-run schema initialization
python3 init_schema.py
```

### Port Already in Use

**Problem:** `Port 7687 already in use`

**Solution:**
```bash
# Find what's using the port
lsof -i :7687

# Kill the process
kill -9 <PID>

# Or change Neo4j port in .env
NEO4J_URI=bolt://localhost:7688
```

### Authentication Failed

**Problem:** `Authentication failed`

**Solutions:**
```bash
# 1. Reset Neo4j password
# Neo4j Desktop: Stop DB → Click gear → Reset password

# 2. Or change initial password in Neo4j Browser
# First login: neo4j/neo4j
# You'll be prompted to change password

# 3. Update .env with new password
NEO4J_PASSWORD=your_new_password
```

---

## Summary

✅ **Easier to maintain** - Small, focused files
✅ **Better organized** - Domain-driven structure
✅ **Fully tested** - All imports and operations work
✅ **Backward compatible** - No breaking changes
✅ **Ready to extend** - Easy to add new features
✅ **Production ready** - Comprehensive logging and error handling

---

## Support

- **Neo4j Browser:** http://localhost:7474
- **Neo4j Documentation:** https://neo4j.com/docs/
- **Cypher Query Language:** https://neo4j.com/docs/cypher-manual/current/
