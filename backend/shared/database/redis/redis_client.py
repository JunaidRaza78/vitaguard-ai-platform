"""
Redis client for cache and session operations.
Provides utilities for session storage, caching, rate limiting, and pub/sub.
"""
import json
import uuid
from typing import Optional, Any, Dict, List, Callable
from datetime import timedelta
import redis
from redis import Redis
from .config import redis_config
import logging

# Initialize logger for Redis operations
logger = logging.getLogger('redis')

# Simple decorator replacement
def log_database_operation(operation_type, logger=None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


class RedisClient:
    """Redis client for cache and session operations."""

    def __init__(self):
        self.config = redis_config
        self.client: Optional[Redis] = None
        logger.debug("Redis client initialized")

    def __enter__(self):
        """Context manager entry."""
        logger.debug("Opening Redis connection")
        self.client = self.config.get_client()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.client:
            if exc_type:
                logger.error(f"Redis operation failed: {exc_type.__name__}: {exc_val}")
            self.client.close()
            logger.debug("Redis connection closed")
    
    def get_client(self) -> Redis:
        """Get Redis client instance."""
        if not self.client:
            self.client = self.config.get_client()
        return self.client
    
    def close(self):
        """Close Redis connection."""
        if self.client:
            self.client.close()
            self.client = None
    
    # ==================== Session Storage ====================

    @log_database_operation('SET', logger=logger)
    def set_session(self, session_id: str, user_id: str, data: Dict[str, Any], ttl: int = 3600) -> bool:
        """
        Store session data.

        Args:
            session_id: Session identifier
            user_id: User identifier
            data: Session data dictionary
            ttl: Time to live in seconds (default: 1 hour)
        """
        logger.info(f"Setting session for user: {user_id}, TTL: {ttl}s")
        key = f"session:{session_id}"
        session_data = {
            "user_id": user_id,
            **data
        }
        return self.get_client().setex(
            key,
            ttl,
            json.dumps(session_data)
        )
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data."""
        key = f"session:{session_id}"
        data = self.get_client().get(key)
        if data:
            logger.debug(f"Session retrieved: {session_id}")
            return json.loads(data)
        logger.debug(f"Session not found: {session_id}")
        return None
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session."""
        logger.info(f"Deleting session: {session_id}")
        key = f"session:{session_id}"
        return bool(self.get_client().delete(key))
    
    def extend_session(self, session_id: str, ttl: int = 3600) -> bool:
        """Extend session TTL."""
        logger.debug(f"Extending session: {session_id}, new TTL: {ttl}s")
        key = f"session:{session_id}"
        return bool(self.get_client().expire(key, ttl))
    
    # ==================== Query Result Caching ====================

    @log_database_operation('CACHE_SET', logger=logger)
    def cache_set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """
        Cache a value.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (default: 5 minutes)
        """
        logger.debug(f"Caching key: {key}, TTL: {ttl}s")
        serialized = json.dumps(value) if not isinstance(value, str) else value
        return self.get_client().setex(key, ttl, serialized)
    
    def cache_get(self, key: str) -> Optional[Any]:
        """Get cached value."""
        data = self.get_client().get(key)
        if data:
            logger.debug(f"Cache hit: {key}")
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return data
        logger.debug(f"Cache miss: {key}")
        return None
    
    def cache_delete(self, key: str) -> bool:
        """Delete cached value."""
        logger.debug(f"Deleting cache key: {key}")
        return bool(self.get_client().delete(key))

    def cache_delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        keys = self.get_client().keys(pattern)
        if keys:
            logger.info(f"Deleting {len(keys)} keys matching pattern: {pattern}")
            return self.get_client().delete(*keys)
        logger.debug(f"No keys found matching pattern: {pattern}")
        return 0
    
    # ==================== Rate Limiting ====================

    @log_database_operation('RATE_LIMIT', logger=logger)
    def rate_limit_check(self, key: str, limit: int, window: int) -> tuple[bool, int]:
        """
        Check rate limit.

        Args:
            key: Rate limit key (e.g., "ratelimit:user:123:api")
            limit: Maximum requests allowed
            window: Time window in seconds

        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        current = self.get_client().incr(key)
        if current == 1:
            self.get_client().expire(key, window)

        remaining = max(0, limit - current)
        is_allowed = current <= limit

        if not is_allowed:
            logger.warning(f"Rate limit exceeded for key: {key} (limit: {limit}, current: {current})")
        else:
            logger.debug(f"Rate limit check passed for key: {key} (remaining: {remaining})")

        return is_allowed, remaining
    
    def rate_limit_reset(self, key: str) -> bool:
        """Reset rate limit counter."""
        logger.info(f"Resetting rate limit for key: {key}")
        return bool(self.get_client().delete(key))
    
    # ==================== Conversation Memory ====================
    
    def store_conversation_message(self, conversation_id: str, message: Dict[str, Any], max_messages: int = 100) -> bool:
        """
        Store conversation message in a list.

        Args:
            conversation_id: Conversation identifier
            message: Message data dictionary
            max_messages: Maximum messages to keep (FIFO)
        """
        logger.debug(f"Storing conversation message: {conversation_id}")
        key = f"conversation:{conversation_id}:messages"
        self.get_client().lpush(key, json.dumps(message))
        self.get_client().ltrim(key, 0, max_messages - 1)
        return True
    
    def get_conversation_messages(self, conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversation messages."""
        key = f"conversation:{conversation_id}:messages"
        messages = self.get_client().lrange(key, 0, limit - 1)
        logger.debug(f"Retrieved {len(messages)} messages for conversation: {conversation_id}")
        return [json.loads(msg) for msg in messages]

    def clear_conversation(self, conversation_id: str) -> bool:
        """Clear conversation messages."""
        logger.info(f"Clearing conversation: {conversation_id}")
        key = f"conversation:{conversation_id}:messages"
        return bool(self.get_client().delete(key))
    
    # ==================== Chat Response Caching ====================
    
    def cache_chat_response(self, cache_key: str, response: Dict[str, Any], ttl: int = 3600) -> bool:
        """Cache chat response."""
        return self.cache_set(f"chat:response:{cache_key}", response, ttl)
    
    def get_cached_chat_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached chat response."""
        return self.cache_get(f"chat:response:{cache_key}")
    
    # ==================== Pub/Sub ====================
    
    def publish(self, channel: str, message: Dict[str, Any]) -> int:
        """
        Publish message to channel.

        Args:
            channel: Pub/Sub channel name
            message: Message data dictionary

        Returns:
            Number of subscribers that received the message
        """
        logger.debug(f"Publishing to channel: {channel}")
        subscriber_count = self.get_client().publish(channel, json.dumps(message))
        logger.debug(f"Message delivered to {subscriber_count} subscribers")
        return subscriber_count
    
    def subscribe(self, channels: List[str], handler: Callable[[str, Dict[str, Any]], None]):
        """
        Subscribe to channels and handle messages.

        Args:
            channels: List of channel names to subscribe to
            handler: Callback function(channel, message_dict)
        """
        logger.info(f"Subscribing to channels: {', '.join(channels)}")
        pubsub = self.get_client().pubsub()
        pubsub.subscribe(*channels)

        try:
            for message in pubsub.listen():
                if message['type'] == 'message':
                    channel = message['channel'].decode() if isinstance(message['channel'], bytes) else message['channel']
                    data = json.loads(message['data']) if isinstance(message['data'], bytes) else json.loads(message['data'])
                    logger.debug(f"Received message on channel: {channel}")
                    handler(channel, data)
        except Exception as e:
            logger.error(f"Error in subscription handler: {type(e).__name__}: {str(e)}")
            raise
        finally:
            logger.info("Closing subscription")
            pubsub.close()
    
    # ==================== Health Updates Pub/Sub ====================
    
    def publish_health_update(self, user_id: str, health_data: Dict[str, Any]) -> int:
        """Publish health update to user's channel."""
        channel = f"health_updates:{user_id}"
        return self.publish(channel, health_data)
    
    # ==================== Notifications Pub/Sub ====================
    
    def publish_notification(self, user_id: str, notification: Dict[str, Any]) -> int:
        """Publish notification to user's channel."""
        channel = f"notifications:{user_id}"
        return self.publish(channel, notification)
    
    # ==================== Appointment Reminders Pub/Sub ====================
    
    def publish_appointment_reminder(self, reminder_data: Dict[str, Any]) -> int:
        """Publish appointment reminder to broadcast channel."""
        channel = "appointment_reminders"
        return self.publish(channel, reminder_data)
    
    # ==================== Chat Pub/Sub ====================
    
    def publish_typing_indicator(self, conversation_id: str, typing_data: Dict[str, Any]) -> int:
        """Publish typing indicator."""
        channel = f"chat:typing:{conversation_id}"
        return self.publish(channel, typing_data)
    
    def publish_chat_response(self, conversation_id: str, response_data: Dict[str, Any]) -> int:
        """Publish streaming chat response."""
        channel = f"chat:response:{conversation_id}"
        return self.publish(channel, response_data)
    
    # ==================== Health Check ====================
    
    def health_check(self) -> bool:
        """Check Redis connection health."""
        try:
            logger.debug("Performing Redis client health check")
            self.get_client().ping()
            logger.info("Redis client health check passed")
            return True
        except Exception as e:
            logger.error(f"Redis client health check failed: {type(e).__name__}: {str(e)}")
            return False
    
    # ==================== Utility Methods ====================
    
    def set_with_ttl(self, key: str, value: Any, ttl: int) -> bool:
        """Set key with TTL."""
        serialized = json.dumps(value) if not isinstance(value, str) else value
        return self.get_client().setex(key, ttl, serialized)
    
    def get_ttl(self, key: str) -> int:
        """Get remaining TTL for a key."""
        return self.get_client().ttl(key)
    
    def exists(self, key: str) -> bool:
        """Check if key exists."""
        return bool(self.get_client().exists(key))
    
    def delete(self, *keys: str) -> int:
        """Delete one or more keys."""
        return self.get_client().delete(*keys)


# Convenience function
def get_redis_client() -> RedisClient:
    """Get a Redis client instance."""
    return RedisClient()

