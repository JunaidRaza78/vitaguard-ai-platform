# Logging System Documentation

Comprehensive logging system with file rotation, performance monitoring, and error tracking.

---

## 📋 Features

✅ **Centralized Logging**
- Single logging configuration for entire application
- Multiple log handlers (console, debug, error, database, performance)
- Automatic log file rotation

✅ **Log Levels**
- DEBUG: Detailed diagnostic information
- INFO: General informational messages
- WARNING: Warning messages (e.g., slow queries, rate limits)
- ERROR: Error messages with stack traces

✅ **Log Files**
- `logs/debug.log` - All debug messages (10MB rotation, 5 backups)
- `logs/database.log` - Database operations only (10MB rotation, 5 backups)
- `logs/error.log` - Errors and exceptions (daily rotation, 30 days)
- `logs/performance.log` - Performance metrics (5MB rotation, 3 backups)

✅ **Performance Monitoring**
- Automatic timing for database operations
- Warnings for slow operations (>1s for functions, >2s for DB queries)
- Performance metrics logged separately

---

## 🚀 Quick Start

### Basic Usage

```python
from backend.shared.logging import get_logger

# Get a logger for your module
logger = get_logger('my_module')

# Log messages
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

### Database Operations

```python
from backend.shared.logging import get_logger, log_database_operation

logger = get_logger('postgres')

@log_database_operation('CREATE', logger=logger)
def create_user(user_id: str, email: str):
    logger.info(f"Creating user: {user_id}")
    # ... database operation ...
    return user
```

### Function Timing

```python
from backend.shared.logging import get_logger, log_function_call

logger = get_logger('api')

@log_function_call(logger=logger, log_args=True)
def process_request(data: dict):
    # ... function logic ...
    return result
```

---

## 📊 Log Format

### Console Output
```
2025-12-29 20:47:42 | INFO     | family_health_manager.postgres | PostgreSQL health check: PASSED
```

### File Output
```
2025-12-29 20:47:42 | INFO     | family_health_manager.postgres | health_check:274 | PostgreSQL health check: PASSED
```

**Format:** `timestamp | level | logger_name | function:line | message`

---

## 🎯 Module-Specific Loggers

### PostgreSQL Logger
```python
from backend.shared.logging import get_logger
logger = get_logger('postgres')

logger.info("PostgreSQL operation completed")
# Logged to: console + debug.log + database.log
```

### Redis Logger
```python
from backend.shared.logging import get_logger
logger = get_logger('redis')

logger.info("Cache operation completed")
# Logged to: console + debug.log + database.log
```

### Neo4j Logger
```python
from backend.shared.logging import get_logger
logger = get_logger('neo4j')

logger.info("Graph query executed")
# Logged to: console + debug.log + database.log
```

---

## 🔧 Configuration

### Log Levels

Default levels:
- Console: INFO and above
- Debug file: DEBUG and above
- Error file: ERROR and above
- Database file: DEBUG and above (filtered to database loggers)
- Performance file: INFO and above (filtered to performance messages)

### File Rotation

**Size-based rotation:**
- Debug log: 10MB, 5 backups
- Database log: 10MB, 5 backups
- Performance log: 5MB, 3 backups

**Time-based rotation:**
- Error log: Daily, 30 days retention

### Customization

Edit `backend/shared/logging/logger.py` to customize:
- Log levels
- File sizes
- Rotation policies
- Log format

---

## 📝 Examples

### Example 1: Basic Database Operation

```python
from backend.shared.logging import get_logger, log_database_operation
from backend.shared.database.postgres import SimpleConversationClient

logger = get_logger('postgres')

@log_database_operation('CREATE', logger=logger)
def create_conversation(conversation_id: str, user_id: str):
    logger.info(f"Creating conversation: {conversation_id} for user: {user_id}")

    with SimpleConversationClient() as client:
        conversation = client.create_conversation(
            conversation_id=conversation_id,
            user_id=user_id
        )

    logger.info(f"Conversation created successfully: {conversation_id}")
    return conversation
```

**Output:**
```
2025-12-29 20:47:42 | INFO     | postgres | Creating conversation: conv_123 for user: user_abc
2025-12-29 20:47:42 | INFO     | postgres | DB CREATE: create_conversation completed in 0.045s
2025-12-29 20:47:42 | INFO     | postgres | Conversation created successfully: conv_123
```

### Example 2: Error Handling

```python
from backend.shared.logging import get_logger, log_database_operation

logger = get_logger('postgres')

@log_database_operation('QUERY', logger=logger)
def get_user_conversations(user_id: str):
    try:
        logger.info(f"Fetching conversations for user: {user_id}")
        # ... database query ...
        return conversations
    except Exception as e:
        logger.error(f"Failed to fetch conversations: {type(e).__name__}: {str(e)}", exc_info=True)
        raise
```

**Error Output:**
```
2025-12-29 20:47:42 | ERROR    | postgres | wrapper:260 | DB QUERY: get_user_conversations failed after 0.023s - DatabaseError: Connection timeout
Traceback (most recent call last):
  File "client.py", line 224, in get_user_conversations
    ...
```

### Example 3: Performance Monitoring

```python
from backend.shared.logging import get_logger, log_database_operation

logger = get_logger('postgres')

@log_database_operation('QUERY', logger=logger)
def complex_analytics_query(user_id: str):
    logger.info(f"Running analytics for user: {user_id}")
    # ... slow query taking 3 seconds ...
    return results
```

**Performance Warning Output:**
```
2025-12-29 20:47:42 | INFO     | postgres | DB QUERY: complex_analytics_query completed in 3.124s
2025-12-29 20:47:42 | WARNING  | postgres | PERFORMANCE: Slow DB QUERY in complex_analytics_query took 3.124s
```

### Example 4: Rate Limiting

```python
from backend.shared.logging import get_logger, log_database_operation
from backend.shared.database.redis import RedisClient

logger = get_logger('redis')

@log_database_operation('RATE_LIMIT', logger=logger)
def check_api_rate_limit(user_id: str):
    with RedisClient() as client:
        key = f"ratelimit:api:{user_id}"
        is_allowed, remaining = client.rate_limit_check(key, limit=100, window=3600)

        if not is_allowed:
            logger.warning(f"Rate limit exceeded for user: {user_id}")
        else:
            logger.debug(f"Rate limit check passed. Remaining: {remaining}")

        return is_allowed, remaining
```

**Rate Limit Warning Output:**
```
2025-12-29 20:47:42 | WARNING  | redis | Rate limit exceeded for key: ratelimit:api:user_abc (limit: 100, current: 101)
```

---

## 🛠️ Testing

Run the logging test suite:

```bash
python3 backend/test_logging.py
```

**Expected Output:**
```
╔════════════════════════════════════════════════════════════════════╗
║               Database Logging System Test                         ║
╚════════════════════════════════════════════════════════════════════╝

Testing PostgreSQL Logging
✅ PostgreSQL logging working correctly!

Testing Redis Logging
✅ Redis logging working correctly!

Testing Neo4j Logging
✅ Neo4j logging working correctly!

Check the following log files:
  - logs/debug.log       (All debug messages)
  - logs/database.log    (Database operations)
  - logs/error.log       (Errors and exceptions)
  - logs/performance.log (Performance metrics)
```

---

## 📂 File Structure

```
backend/
├── shared/
│   ├── logging/
│   │   ├── __init__.py          # Exports: get_logger, decorators
│   │   ├── logger.py            # Core logging configuration
│   │   └── README.md            # This file
│   └── exceptions/
│       └── __init__.py          # Custom exceptions
└── test_logging.py              # Test script

logs/
├── .gitignore                   # Ignore log files
├── debug.log                    # All debug messages
├── database.log                 # Database operations
├── error.log                    # Errors and exceptions
└── performance.log              # Performance metrics
```

---

## 🎯 Best Practices

1. **Use module-specific loggers:**
   ```python
   logger = get_logger('my_module')
   ```

2. **Log at appropriate levels:**
   - DEBUG: Detailed flow information
   - INFO: Important events (create, update, delete)
   - WARNING: Performance issues, rate limits
   - ERROR: Exceptions and failures

3. **Use decorators for database operations:**
   ```python
   @log_database_operation('CREATE', logger=logger)
   def create_entity(...):
       ...
   ```

4. **Always log exceptions with stack traces:**
   ```python
   try:
       ...
   except Exception as e:
       logger.error(f"Operation failed: {e}", exc_info=True)
       raise
   ```

5. **Monitor performance:**
   - Operations >1s: Automatically logged as warnings
   - Check `logs/performance.log` regularly

6. **Review logs periodically:**
   - `logs/error.log`: Fix errors
   - `logs/performance.log`: Optimize slow operations
   - `logs/database.log`: Monitor query patterns

---

## 🔍 Troubleshooting

### Logs not appearing

**Cause:** Logger not initialized properly

**Solution:**
```python
from backend.shared.logging import get_logger
logger = get_logger('your_module')
```

### Performance warnings for fast operations

**Cause:** Threshold too low (default: 1s for functions, 2s for DB)

**Solution:** Adjust threshold in decorator:
```python
@log_database_operation('QUERY', logger=logger, threshold=5.0)
def slow_analytics_query():
    ...
```

### Log files too large

**Cause:** Rotation not working

**Solution:** Check rotation settings in `logger.py`:
```python
debug_handler = RotatingFileHandler(
    debug_log,
    maxBytes=10*1024*1024,  # Adjust size
    backupCount=5            # Adjust backup count
)
```

---

## ✨ Summary

You've successfully implemented a production-ready logging system with:

1. ✅ Centralized logging configuration
2. ✅ Multiple log handlers with rotation
3. ✅ Database operation logging
4. ✅ Performance monitoring
5. ✅ Error tracking with stack traces
6. ✅ Custom decorators for easy integration
7. ✅ Module-specific loggers
8. ✅ Comprehensive test suite

**Your logging system is production-ready!** 🚀

---

**Need help?** Check the examples above or review the code in `backend/shared/logging/logger.py`.
