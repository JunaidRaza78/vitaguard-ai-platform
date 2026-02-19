"""
PostgreSQL unified client for all database operations.
Provides comprehensive interface for User, Session, Conversation, Message, and other operations.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text, desc
from .config import db_config
from .models import (
    Base, User, UserSession, Notification, AuditLog,
    DocumentJob, ApiRateLimit, ChatFeedback, ChatMetric,
    ChatMessage, Conversation, HealthEvent
)

# Logging - use basic logging for now
import logging
logger = logging.getLogger('postgres')

def get_logger(name):
    return logging.getLogger(name)

def log_database_operation(operation_type, logger=None):
    """Decorator factory for logging database operations"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


class PostgresClient:
    """Unified PostgreSQL client for all database operations."""

    def __init__(self):
        self.config = db_config
        self.session: Optional[Session] = None
        logger.debug("PostgreSQL client initialized")

    def __enter__(self):
        """Context manager entry."""
        logger.debug("Opening PostgreSQL session")
        self.session = self.config.get_session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with auto-commit/rollback."""
        if self.session:
            if exc_type:
                logger.error(f"Session rollback due to exception: {exc_type.__name__}: {exc_val}")
                self.session.rollback()
            else:
                logger.debug("Committing PostgreSQL session")
                self.session.commit()
            self.session.close()
            logger.debug("PostgreSQL session closed")

    def get_session(self) -> Session:
        """Get a database session."""
        if not self.session:
            self.session = self.config.get_session()
        return self.session

    def close(self):
        """Close the current session."""
        if self.session:
            logger.debug("Closing PostgreSQL session")
            self.session.close()
            self.session = None

    def commit(self):
        """Commit the current transaction."""
        if self.session:
            logger.debug("Committing transaction")
            self.session.commit()

    def rollback(self):
        """Rollback the current transaction."""
        if self.session:
            logger.warning("Rolling back transaction")
            self.session.rollback()

    # ==================== User Operations ====================

    @log_database_operation('CREATE', logger=logger)
    def create_user(self, email: str, password_hash: str, **kwargs) -> User:
        """Create a new user."""
        logger.info(f"Creating user with email: {email}")
        user = User(
            email=email,
            password_hash=password_hash,
            **kwargs
        )
        self.get_session().add(user)
        self.get_session().commit()
        logger.info(f"User created successfully: {user.user_id}")
        return user

    @log_database_operation('READ', logger=logger)
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        logger.debug(f"Fetching user by email: {email}")
        user = self.get_session().query(User).filter(User.email == email).first()
        if user:
            logger.debug(f"User found: {user.user_id}")
        else:
            logger.debug(f"User not found with email: {email}")
        return user

    @log_database_operation('READ', logger=logger)
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        logger.debug(f"Fetching user by ID: {user_id}")
        user = self.get_session().query(User).filter(User.user_id == user_id).first()
        if user:
            logger.debug(f"User found: {user.user_id}")
        else:
            logger.debug(f"User not found with ID: {user_id}")
        return user

    @log_database_operation('DELETE', logger=logger)
    def delete_user(self, user_id: str) -> bool:
        """Delete user by ID. Related records will be cascade deleted."""
        logger.info(f"Deleting user: {user_id}")
        user = self.get_user_by_id(user_id)
        if not user:
            logger.warning(f"User not found: {user_id}")
            return False

        self.get_session().delete(user)
        self.get_session().commit()
        logger.info(f"User deleted: {user_id}")
        return True

    # ==================== Session Operations ====================

    @log_database_operation('CREATE', logger=logger)
    def create_session(self, user_id: str, token: str, expires_at, **kwargs) -> UserSession:
        """Create a new user session."""
        logger.info(f"Creating session for user: {user_id}")
        session = UserSession(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            **kwargs
        )
        self.get_session().add(session)
        self.get_session().commit()
        logger.info(f"Session created successfully: {session.session_id}")
        return session

    @log_database_operation('READ', logger=logger)
    def get_session_by_token(self, token: str) -> Optional[UserSession]:
        """Get session by token."""
        logger.debug(f"Fetching session by token")
        session = self.get_session().query(UserSession).filter(UserSession.token == token).first()
        if session:
            logger.debug(f"Session found: {session.session_id}")
        else:
            logger.debug("Session not found with provided token")
        return session

    # ==================== Notification Operations ====================

    @log_database_operation('CREATE', logger=logger)
    def create_notification(self, user_id: str, type: str, message: str, **kwargs) -> Notification:
        """Create a new notification."""
        logger.info(f"Creating notification for user: {user_id} (type: {type})")
        notification = Notification(
            user_id=user_id,
            type=type,
            message=message,
            **kwargs
        )
        self.get_session().add(notification)
        self.get_session().commit()
        logger.info(f"Notification created successfully: {notification.notification_id}")
        return notification

    # ==================== Audit Log Operations ====================

    @log_database_operation('CREATE', logger=logger)
    def create_audit_log(self, action: str, **kwargs) -> AuditLog:
        """Create an audit log entry."""
        logger.info(f"Creating audit log entry: {action}")
        audit_log = AuditLog(
            action=action,
            **kwargs
        )
        self.get_session().add(audit_log)
        self.get_session().commit()
        logger.debug(f"Audit log created: {audit_log.log_id}")
        return audit_log

    # ==================== Document Job Operations ====================

    @log_database_operation('CREATE', logger=logger)
    def create_document_job(
        self,
        user_id: str,
        file_path: str,
        job_type: str,
        file_type: Optional[str] = None,
        **kwargs
    ) -> DocumentJob:
        """Create a document processing job."""
        logger.info(f"Creating document job: user={user_id}, type={job_type}, file={file_path}")
        job = DocumentJob(
            user_id=user_id,
            file_path=file_path,
            job_type=job_type,
            file_type=file_type,
            status='pending',
            **kwargs
        )
        self.get_session().add(job)
        self.get_session().commit()
        logger.info(f"Document job created: {job.job_id}")
        return job

    @log_database_operation('READ', logger=logger)
    def get_document_job(self, job_id: str) -> Optional[DocumentJob]:
        """Get document job by ID."""
        logger.debug(f"Fetching document job: {job_id}")
        return self.get_session().query(DocumentJob).filter(
            DocumentJob.job_id == job_id
        ).first()

    @log_database_operation('QUERY', logger=logger)
    def get_user_document_jobs(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[DocumentJob]:
        """Get all document jobs for a user."""
        logger.info(f"Fetching document jobs for user: {user_id} (status={status})")
        query = self.get_session().query(DocumentJob).filter(
            DocumentJob.user_id == user_id
        )

        if status:
            query = query.filter(DocumentJob.status == status)

        jobs = query.order_by(DocumentJob.created_at.desc()).limit(limit).all()
        logger.debug(f"Found {len(jobs)} document jobs")
        return jobs

    @log_database_operation('UPDATE', logger=logger)
    def update_document_job_status(
        self,
        job_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> Optional[DocumentJob]:
        """Update document job status and result."""
        from datetime import datetime, timezone

        logger.info(f"Updating document job {job_id}: status={status}")
        job = self.get_document_job(job_id)

        if not job:
            logger.warning(f"Document job not found: {job_id}")
            return None

        job.status = status

        if status == 'processing' and not job.started_at:
            job.started_at = datetime.now(timezone.utc)

        if status in ['completed', 'failed']:
            job.completed_at = datetime.now(timezone.utc)
            if job.started_at:
                delta = (job.completed_at - job.started_at).total_seconds() * 1000
                job.processing_time_ms = int(delta)

        if result:
            job.result = result

        if error_message:
            job.error_message = error_message

        self.get_session().commit()
        logger.debug(f"Document job updated: {job_id}")
        return job

    # ==================== User Documents Operations ====================

    @log_database_operation('CREATE', logger=logger)
    def create_user_document(
        self,
        user_id: str,
        filename: str,
        file_path: str,
        file_size_bytes: Optional[int] = None,
        document_type: Optional[str] = None,
        **kwargs
    ):
        """Create a user document record."""
        from shared.database.postgres.models import UserDocument

        logger.info(f"Creating document record: user={user_id}, file={filename}")
        doc = UserDocument(
            user_id=user_id,
            filename=filename,
            file_path=file_path,
            file_size_bytes=file_size_bytes,
            document_type=document_type,
            **kwargs
        )
        self.get_session().add(doc)
        self.get_session().commit()
        logger.info(f"Document created: {doc.document_id}")
        return doc

    @log_database_operation('READ', logger=logger)
    def get_user_documents(
        self,
        user_id: str,
        document_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ):
        """Get all documents for a user."""
        from shared.database.postgres.models import UserDocument

        query = self.get_session().query(UserDocument).filter(
            UserDocument.user_id == user_id
        )

        if document_type:
            query = query.filter(UserDocument.document_type == document_type)

        if status:
            query = query.filter(UserDocument.processing_status == status)

        return query.order_by(UserDocument.upload_date.desc()).limit(limit).all()

    @log_database_operation('READ', logger=logger)
    def get_user_document(self, document_id: str):
        """Get a single document by ID."""
        from shared.database.postgres.models import UserDocument

        return self.get_session().query(UserDocument).filter(
            UserDocument.document_id == document_id
        ).first()

    @log_database_operation('UPDATE', logger=logger)
    def update_user_document(
        self,
        document_id: str,
        chroma_ids: Optional[str] = None,
        processing_status: Optional[str] = None,
        specialty: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """Update document processing status and metadata."""
        from datetime import datetime, timezone

        doc = self.get_user_document(document_id)
        if not doc:
            return None

        if chroma_ids is not None:
            doc.chroma_ids = chroma_ids
        if processing_status:
            doc.processing_status = processing_status
            if processing_status == 'completed':
                doc.processed_at = datetime.now(timezone.utc)
        if specialty:
            doc.specialty = specialty
        if metadata:
            doc.doc_metadata = {**doc.doc_metadata, **metadata}

        doc.updated_at = datetime.now(timezone.utc)
        self.get_session().commit()
        return doc

    @log_database_operation('DELETE', logger=logger)
    def delete_user_document(self, document_id: str) -> bool:
        """Delete a document record."""
        doc = self.get_user_document(document_id)
        if doc:
            self.get_session().delete(doc)
            self.get_session().commit()
            return True
        return False

    # ==================== API Rate Limit Operations ====================

    @log_database_operation('CHECK', logger=logger)
    def check_rate_limit(
        self,
        user_id: str,
        endpoint: str,
        max_requests: int = 100,
        window_minutes: int = 1
    ) -> bool:
        """
        Check if user has exceeded rate limit.

        Args:
            user_id: User ID
            endpoint: API endpoint (e.g., '/api/chat')
            max_requests: Maximum requests allowed in window
            window_minutes: Time window in minutes

        Returns:
            True if allowed, False if rate limit exceeded
        """
        from datetime import datetime, timedelta, timezone

        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=window_minutes)

        logger.debug(f"Checking rate limit: user={user_id}, endpoint={endpoint}, max={max_requests}")

        # Find active rate limit record
        rate_limit = self.get_session().query(ApiRateLimit).filter(
            ApiRateLimit.user_id == user_id,
            ApiRateLimit.endpoint == endpoint,
            ApiRateLimit.window_end > now
        ).first()

        if not rate_limit:
            # Create new window
            logger.debug(f"Creating new rate limit window for user {user_id}")
            rate_limit = ApiRateLimit(
                user_id=user_id,
                endpoint=endpoint,
                request_count=1,
                window_start=now,
                window_end=now + timedelta(minutes=window_minutes)
            )
            self.get_session().add(rate_limit)
            self.get_session().commit()
            return True

        # Check if limit exceeded
        if rate_limit.request_count >= max_requests:
            logger.warning(
                f"Rate limit exceeded: user={user_id}, endpoint={endpoint}, "
                f"count={rate_limit.request_count}/{max_requests}"
            )
            return False

        # Increment counter
        rate_limit.request_count += 1
        self.get_session().commit()
        logger.debug(
            f"Rate limit check passed: user={user_id}, "
            f"count={rate_limit.request_count}/{max_requests}"
        )
        return True

    @log_database_operation('QUERY', logger=logger)
    def get_rate_limit_status(self, user_id: str, endpoint: str) -> Optional[Dict[str, Any]]:
        """Get current rate limit status for user and endpoint."""
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)

        rate_limit = self.get_session().query(ApiRateLimit).filter(
            ApiRateLimit.user_id == user_id,
            ApiRateLimit.endpoint == endpoint,
            ApiRateLimit.window_end > now
        ).first()

        if not rate_limit:
            return None

        return {
            "user_id": rate_limit.user_id,
            "endpoint": rate_limit.endpoint,
            "request_count": rate_limit.request_count,
            "window_start": rate_limit.window_start.isoformat(),
            "window_end": rate_limit.window_end.isoformat(),
            "remaining_time_seconds": (rate_limit.window_end - now).total_seconds()
        }

    @log_database_operation('DELETE', logger=logger)
    def cleanup_expired_rate_limits(self) -> int:
        """Delete expired rate limit records."""
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)

        count = self.get_session().query(ApiRateLimit).filter(
            ApiRateLimit.window_end <= now
        ).delete()

        self.get_session().commit()
        logger.info(f"Cleaned up {count} expired rate limit records")
        return count

    # ==================== ChatConversation Operations ====================

    @log_database_operation('CREATE', logger=logger)
    def create_chat_conversation(
        self,
        user_id: str,
        title: Optional[str] = None,
        status: str = "active",
        **kwargs
    ) -> Conversation:
        """
        Create a new chat conversation.

        This is a convenience wrapper around create_conversation()
        that auto-generates a conversation_id.
        """
        import uuid
        conversation_id = str(uuid.uuid4())
        logger.info(f"Creating chat conversation for user: {user_id}")
        return self.create_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            title=title,
            status=status,
            **kwargs
        )

    @log_database_operation('QUERY', logger=logger)
    def get_user_chat_conversations(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Conversation]:
        """Get all chat conversations for a user, ordered by last_message_at DESC."""
        logger.info(f"Fetching chat conversations for user: {user_id} (status={status}, limit={limit})")
        query = self.get_session().query(Conversation).filter(
            Conversation.user_id == user_id
        )

        if status:
            query = query.filter(Conversation.status == status)

        conversations = query.order_by(
            Conversation.last_message_at.desc().nullslast(),
            Conversation.created_at.desc()
        ).limit(limit).offset(offset).all()
        logger.debug(f"Found {len(conversations)} chat conversations")
        return conversations

    @log_database_operation('READ', logger=logger)
    def get_chat_conversation_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """Get chat conversation by ID (wrapper around get_conversation)."""
        return self.get_conversation(conversation_id)

    @log_database_operation('UPDATE', logger=logger)
    def update_chat_conversation(
        self,
        conversation_id: str,
        title: Optional[str] = None,
        status: Optional[str] = None,
        **kwargs
    ) -> Optional[Conversation]:
        """Update chat conversation (wrapper around update_conversation)."""
        logger.info(f"Updating chat conversation: {conversation_id}")

        updates = {}
        if title is not None:
            updates['title'] = title
        if status is not None:
            updates['status'] = status
        updates.update(kwargs)

        return self.update_conversation(conversation_id, **updates)

    @log_database_operation('DELETE', logger=logger)
    def delete_chat_conversation(self, conversation_id: str) -> bool:
        """Delete a chat conversation and all its messages."""
        logger.info(f"Deleting chat conversation: {conversation_id}")
        conversation = self.get_chat_conversation_by_id(conversation_id)
        if not conversation:
            logger.warning(f"Chat conversation not found for deletion: {conversation_id}")
            return False
        self.get_session().delete(conversation)
        self.get_session().commit()
        logger.info(f"Chat conversation deleted: {conversation_id}")
        return True

    # ==================== ChatMessage Operations ====================

    @log_database_operation('CREATE', logger=logger)
    def create_chat_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        entities: Optional[Dict[str, Any]] = None,
        message_metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> ChatMessage:
        """Create a new chat message."""
        logger.info(f"Creating chat message in conversation: {conversation_id} (role: {role})")
        message = ChatMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            entities=entities,
            message_metadata=message_metadata,
            **kwargs
        )
        self.get_session().add(message)
        self.get_session().commit()

        # Conversation will be auto-updated by trigger, but refresh to get latest
        conversation = self.get_chat_conversation_by_id(conversation_id)
        if conversation:
            self.get_session().refresh(conversation)

        logger.info(f"Chat message created: {message.message_id}")
        return message

    @log_database_operation('QUERY', logger=logger)
    def get_conversation_chat_messages(
        self,
        conversation_id: str,
        limit: int = 100,
        offset: int = 0,
        role: Optional[str] = None
    ) -> List[ChatMessage]:
        """Get all chat messages in a conversation, ordered by timestamp ASC."""
        logger.debug(f"Fetching chat messages for conversation: {conversation_id} (limit={limit})")
        query = self.get_session().query(ChatMessage).filter(
            ChatMessage.conversation_id == conversation_id
        )

        if role:
            query = query.filter(ChatMessage.role == role)

        messages = query.order_by(ChatMessage.timestamp.asc()).limit(limit).offset(offset).all()
        logger.debug(f"Found {len(messages)} chat messages")
        return messages

    @log_database_operation('QUERY', logger=logger)
    def get_user_all_chat_messages(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[ChatMessage]:
        """Get all chat messages for a user across all conversations."""
        logger.debug(f"Fetching all chat messages for user: {user_id} (limit={limit})")
        messages = self.get_session().query(ChatMessage).filter(
            ChatMessage.user_id == user_id
        ).order_by(ChatMessage.timestamp.desc()).limit(limit).offset(offset).all()
        logger.debug(f"Found {len(messages)} chat messages")
        return messages

    @log_database_operation('READ', logger=logger)
    def get_chat_message_by_id(self, message_id: str) -> Optional[ChatMessage]:
        """Get chat message by ID."""
        logger.debug(f"Fetching chat message: {message_id}")
        message = self.get_session().query(ChatMessage).filter(
            ChatMessage.message_id == message_id
        ).first()
        if message:
            logger.debug(f"Chat message found: {message_id}")
        else:
            logger.debug(f"Chat message not found: {message_id}")
        return message

    @log_database_operation('UPDATE', logger=logger)
    def update_chat_message_feedback(
        self,
        message_id: str,
        feedback_rating: str
    ) -> Optional[ChatMessage]:
        """Update feedback rating for a chat message."""
        logger.info(f"Updating feedback for chat message: {message_id}")
        message = self.get_chat_message_by_id(message_id)
        if not message:
            logger.warning(f"Chat message not found for feedback update: {message_id}")
            return None
        message.feedback_rating = feedback_rating
        self.get_session().commit()
        logger.info(f"Feedback updated for chat message: {message_id}")
        return message

    @log_database_operation('DELETE', logger=logger)
    def delete_chat_message(self, message_id: str) -> bool:
        """Delete a chat message."""
        logger.info(f"Deleting chat message: {message_id}")
        message = self.get_chat_message_by_id(message_id)
        if not message:
            logger.warning(f"Chat message not found for deletion: {message_id}")
            return False
        self.get_session().delete(message)
        self.get_session().commit()

        # Update conversation message count
        conversation = self.get_chat_conversation_by_id(str(message.conversation_id))
        if conversation:
            conversation.message_count = max(0, conversation.message_count - 1)
            self.get_session().commit()

        logger.info(f"Chat message deleted: {message_id}")
        return True

    # ==================== Chat Feedback Operations ====================

    @log_database_operation('CREATE', logger=logger)
    def create_chat_feedback(
        self,
        conversation_id: str,
        message_id: str,
        rating: str,
        comment: Optional[str] = None,
        **kwargs
    ) -> ChatFeedback:
        """Create chat feedback."""
        logger.info(f"Creating chat feedback for message: {message_id} (rating: {rating})")
        feedback = ChatFeedback(
            conversation_id=conversation_id,
            message_id=message_id,
            rating=rating,
            comment=comment,
            **kwargs
        )
        self.get_session().add(feedback)
        self.get_session().commit()
        logger.info(f"Chat feedback created: {feedback.feedback_id}")
        return feedback

    # ==================== Chat Metrics Operations ====================

    @log_database_operation('CREATE', logger=logger)
    def create_chat_metric(
        self,
        conversation_id: str,
        response_time_ms: Optional[int] = None,
        token_count: Optional[int] = None,
        retrieval_time_ms: Optional[int] = None,
        generation_time_ms: Optional[int] = None,
        sources_used: Optional[int] = None,
        user_satisfaction: Optional[int] = None,
        **kwargs
    ) -> ChatMetric:
        """Create chat metric."""
        logger.info(f"Creating chat metric for conversation: {conversation_id}")
        metric = ChatMetric(
            conversation_id=conversation_id,
            response_time_ms=response_time_ms,
            token_count=token_count,
            retrieval_time_ms=retrieval_time_ms,
            generation_time_ms=generation_time_ms,
            sources_used=sources_used,
            user_satisfaction=user_satisfaction,
            **kwargs
        )
        self.get_session().add(metric)
        self.get_session().commit()
        logger.info(f"Chat metric created: {metric.metric_id}")
        return metric

    # ==================== Conversation Operations (API-style) ====================

    @log_database_operation('PROCESS', logger=logger)
    def process_api_request(self, request_data: Dict[str, Any]) -> Conversation:
        """
        Process API request and update conversation.

        Handles API request format:
        {
          "auth_key": "test",
          "user_id": "user_340DlA9nYN4BilkhEt31PWs5Z1i",
          "message_id": "9465606bc2486de1241e3a38d303535f...",
          "conversation_id": "47b244ee9484f5ae3288282a26f929181...",
          "context": {"prompts": [...], "replies": [...]},
          "payload": {"prompt": "...", "attached_files": [...]},
          "resources": ["conversation"]
        }

        Args:
            request_data: Full API request data

        Returns:
            Updated Conversation object
        """
        conversation_id = request_data["conversation_id"]
        user_id = request_data["user_id"]
        message_id = request_data["message_id"]
        auth_key = request_data.get("auth_key")
        context = request_data.get("context", {"prompts": [], "replies": []})
        payload = request_data.get("payload")
        resources = request_data.get("resources", [])

        logger.info(f"Processing API request for conversation: {conversation_id}")

        # Get or create conversation
        conversation = self.get_or_create_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            auth_key=auth_key
        )

        # Update with latest data
        conversation.current_message_id = message_id
        conversation.current_payload = payload
        conversation.resources = resources
        conversation.context = context
        conversation.updated_at = datetime.utcnow()
        conversation.last_message_at = datetime.utcnow()

        # Add current prompt to context if in payload
        if payload and "prompt" in payload:
            conversation.add_prompt(
                content=payload["prompt"],
                timestamp=datetime.utcnow().isoformat() + "Z",
                agents=[],
                attached_files=payload.get("attached_files", [])
            )

        self.get_session().commit()
        logger.info(f"API request processed for conversation: {conversation_id}")
        return conversation

    @log_database_operation('CREATE', logger=logger)
    def create_conversation(
        self,
        conversation_id: str,
        user_id: str,
        title: Optional[str] = None,
        auth_key: Optional[str] = None,
        **kwargs
    ) -> Conversation:
        """
        Create a new conversation.

        Can be used for both:
        - Chat conversations (with title)
        - API conversations (with auth_key)
        """
        logger.info(f"Creating conversation: {conversation_id} for user: {user_id}")
        conversation = Conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            title=title,
            auth_key=auth_key,
            status=kwargs.get('status', 'active'),
            message_count=kwargs.get('message_count', 0),
            context=kwargs.get('context', {"prompts": [], "replies": []}),
            resources=kwargs.get('resources', []),
            messages=kwargs.get('messages', [])
        )

        self.get_session().add(conversation)
        self.get_session().commit()
        logger.info(f"Conversation created: {conversation_id}")
        return conversation

    @log_database_operation('READ', logger=logger)
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID."""
        logger.debug(f"Fetching conversation: {conversation_id}")
        result = self.get_session().query(Conversation).filter(
            Conversation.conversation_id == conversation_id
        ).first()
        if result:
            logger.debug(f"Found conversation: {conversation_id}")
        else:
            logger.debug(f"Conversation not found: {conversation_id}")
        return result

    def get_or_create_conversation(
        self,
        conversation_id: str,
        user_id: str,
        **kwargs
    ) -> Conversation:
        """Get existing conversation or create new one."""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            logger.debug(f"Conversation not found, creating new: {conversation_id}")
            conversation = self.create_conversation(
                conversation_id=conversation_id,
                user_id=user_id,
                **kwargs
            )
        return conversation

    @log_database_operation('UPDATE', logger=logger)
    def update_conversation(
        self,
        conversation_id: str,
        **updates
    ) -> Optional[Conversation]:
        """Update conversation fields."""
        logger.info(f"Updating conversation: {conversation_id} with {len(updates)} fields")
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            logger.warning(f"Conversation not found for update: {conversation_id}")
            return None

        for key, value in updates.items():
            if hasattr(conversation, key):
                setattr(conversation, key, value)

        conversation.updated_at = datetime.utcnow()
        self.get_session().commit()
        logger.info(f"Conversation updated: {conversation_id}")
        return conversation

    @log_database_operation('QUERY', logger=logger)
    def get_user_conversations(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Conversation]:
        """Get user's conversations."""
        logger.info(f"Fetching conversations for user: {user_id} (status={status}, limit={limit})")
        query = self.get_session().query(Conversation).filter(
            Conversation.user_id == user_id
        )

        if status:
            query = query.filter(Conversation.status == status)

        conversations = query.order_by(
            desc(Conversation.last_message_at)
        ).limit(limit).offset(offset).all()
        logger.debug(f"Found {len(conversations)} conversations")
        return conversations

    @log_database_operation('DELETE', logger=logger)
    def delete_conversation(self, conversation_id: str) -> bool:
        """Soft delete conversation."""
        logger.info(f"Deleting conversation: {conversation_id}")
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            logger.warning(f"Conversation not found for deletion: {conversation_id}")
            return False

        conversation.status = "deleted"
        conversation.updated_at = datetime.utcnow()
        self.get_session().commit()
        logger.info(f"Conversation deleted: {conversation_id}")
        return True

    def archive_conversation(self, conversation_id: str) -> bool:
        """Archive conversation."""
        logger.debug(f"Archiving conversation: {conversation_id}")
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            logger.warning(f"Conversation not found for archiving: {conversation_id}")
            return False

        conversation.status = "archived"
        conversation.updated_at = datetime.utcnow()
        self.get_session().commit()
        logger.info(f"Conversation archived: {conversation_id}")
        return True

    # ==================== Message Operations (Conversation) ====================

    def add_prompt(
        self,
        conversation_id: str,
        content: str,
        timestamp: Optional[str] = None,
        agents: Optional[List] = None,
        attached_files: Optional[List] = None
    ) -> Optional[Conversation]:
        """Add a prompt to conversation."""
        logger.debug(f"Adding prompt to conversation: {conversation_id}")
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            logger.warning(f"Conversation not found for adding prompt: {conversation_id}")
            return None

        conversation.add_prompt(content, timestamp, agents, attached_files)
        self.get_session().commit()
        logger.debug(f"Prompt added to conversation: {conversation_id}")
        return conversation

    def add_reply(
        self,
        conversation_id: str,
        content: str,
        timestamp: Optional[str] = None,
        agents: Optional[List] = None,
        attached_files: Optional[List] = None
    ) -> Optional[Conversation]:
        """Add a reply to conversation."""
        logger.debug(f"Adding reply to conversation: {conversation_id}")
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            logger.warning(f"Conversation not found for adding reply: {conversation_id}")
            return None

        conversation.add_reply(content, timestamp, agents, attached_files)
        self.get_session().commit()
        logger.debug(f"Reply added to conversation: {conversation_id}")
        return conversation

    # ==================== Raw Query Execution ====================

    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Any]:
        """Execute a raw SQL query."""
        logger.debug(f"Executing raw SQL query: {query[:100]}...")
        try:
            result = self.get_session().execute(text(query), params or {})
            records = result.fetchall()
            logger.debug(f"Query returned {len(records)} records")
            return records
        except Exception as e:
            logger.error(f"Query execution failed: {type(e).__name__}: {str(e)}")
            raise

    # ==================== Health Check ====================

    def health_check(self) -> bool:
        """Check database connection health."""
        try:
            self.get_session().execute(text("SELECT 1"))
            logger.info("PostgreSQL health check: PASSED")
            return True
        except Exception as e:
            logger.error(f"PostgreSQL health check: FAILED - {type(e).__name__}: {str(e)}")
            return False


# Convenience function for quick access
def get_postgres_client() -> PostgresClient:
    """Get a PostgreSQL client instance."""
    return PostgresClient()
