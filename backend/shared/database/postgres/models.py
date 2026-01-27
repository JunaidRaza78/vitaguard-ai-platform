"""
Updated models for monolithic architecture with foreign key relationships.
Works with your existing structure + new JSONB fields + FK constraints.
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, DateTime, Index, Integer, ForeignKey, Boolean
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref

Base = declarative_base()


class User(Base):
    """User model - references existing users table"""
    __tablename__ = "users"

    user_id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(255), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)

    # Profile fields
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    phone_number = Column(String(50), nullable=True)
    date_of_birth = Column(String(20), nullable=True)
    gender = Column(String(20), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    timezone = Column(String(100), default="UTC", nullable=False)
    language = Column(String(10), default="en", nullable=False)

    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)

    # Security fields
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    account_locked_until = Column(DateTime(timezone=True), nullable=True)
    password_changed_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime(timezone=True))

    # Relationships to all child tables
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    document_jobs = relationship("DocumentJob", back_populates="user", cascade="all, delete-orphan")
    api_rate_limits = relationship("ApiRateLimit", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    login_attempts = relationship("LoginAttempt", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.user_id}, email={self.email})>"


class RefreshToken(Base):
    """Refresh tokens for JWT authentication"""
    __tablename__ = "refresh_tokens"

    token_id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String(255),
        ForeignKey('users.user_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    token = Column(String, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    device_info = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)

    # Relationship to User
    user = relationship("User", back_populates="refresh_tokens")

    def __repr__(self) -> str:
        return f"<RefreshToken(id={self.token_id}, user={self.user_id}, revoked={self.revoked})>"


class LoginAttempt(Base):
    """Login attempts for security tracking"""
    __tablename__ = "login_attempts"

    attempt_id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String(255),
        ForeignKey('users.user_id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    email = Column(String(255), nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String, nullable=True)
    success = Column(Boolean, default=False, nullable=False)
    failure_reason = Column(String(255), nullable=True)
    attempted_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationship to User (optional - may not exist if email doesn't match)
    user = relationship("User", back_populates="login_attempts")

    def __repr__(self) -> str:
        return f"<LoginAttempt(id={self.attempt_id}, email={self.email}, success={self.success})>"


class Conversation(Base):
    """
    Unified conversation model - supports both chat and API integrations.

    Core fields:
    - conversation_id (VARCHAR)
    - user_id
    - title
    - status
    - created_at
    - updated_at
    - last_message_at
    - message_count

    Optional fields for API integration:
    - auth_key
    - current_message_id
    - context (JSONB)
    - current_payload (JSONB)
    - resources (JSONB)
    - messages (JSONB) - for storing messages as JSON array
    """
    __tablename__ = "conversations"

    # Core fields
    conversation_id = Column(
        String(255),
        primary_key=True,
        nullable=False
    )

    user_id = Column(
        String(255),
        ForeignKey('users.user_id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False,
        index=True
    )

    title = Column(String(500))

    status = Column(
        String(50),
        nullable=False,
        default="active",
        index=True
    )

    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    last_message_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )

    message_count = Column(
        Integer,
        default=0,
        nullable=False
    )

    # New fields (added by migration)
    auth_key = Column(
        String(255),
        nullable=True
    )

    current_message_id = Column(
        String(255),
        nullable=True
    )

    # JSONB fields for flexible API data
    context = Column(
        JSONB,
        nullable=True,
        default={"prompts": [], "replies": []}
    )

    current_payload = Column(
        JSONB,
        nullable=True
    )

    resources = Column(
        JSONB,
        nullable=True,
        default=[]
    )

    # Messages array - stores all messages for this conversation
    # Structure: [{message_id, role, content, timestamp, metadata}]
    messages = Column(
        JSONB,
        nullable=True,
        default=[]
    )

    # Relationship to User
    user = relationship("User", back_populates="conversations")

    def __repr__(self) -> str:
        return f"<Conversation(id={self.conversation_id}, user={self.user_id}, messages={self.message_count})>"

    def add_prompt(self, content: str, timestamp: str = None, agents: list = None, attached_files: list = None):
        """Add a prompt to the conversation context."""
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat() + "Z"

        prompt = {
            "content": content,
            "timestamp": timestamp,
            "agents": agents or [],
            "attached_files": attached_files or []
        }

        if self.context is None:
            self.context = {"prompts": [], "replies": []}

        if "prompts" not in self.context:
            self.context["prompts"] = []

        self.context["prompts"].append(prompt)
        self.message_count += 1
        self.last_message_at = datetime.utcnow()

    def add_reply(self, content: str, timestamp: str = None, agents: list = None, attached_files: list = None):
        """Add a reply to the conversation context."""
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat() + "Z"

        reply = {
            "content": content,
            "timestamp": timestamp,
            "agents": agents or [],
            "attached_files": attached_files or []
        }

        if self.context is None:
            self.context = {"prompts": [], "replies": []}

        if "replies" not in self.context:
            self.context["replies"] = []

        self.context["replies"].append(reply)
        self.message_count += 1
        self.last_message_at = datetime.utcnow()

    def get_prompts(self) -> list:
        """Get all prompts from context."""
        if self.context and "prompts" in self.context:
            return self.context["prompts"]
        return []

    def get_replies(self) -> list:
        """Get all replies from context."""
        if self.context and "replies" in self.context:
            return self.context["replies"]
        return []

    def add_message(self, message_id: str, role: str, content: str, timestamp: str = None, metadata: dict = None):
        """
        Add a message to the conversation.

        Args:
            message_id: Unique message identifier
            role: Message role (user, assistant, system)
            content: Message content
            timestamp: ISO format timestamp
            metadata: Additional metadata (optional)
        """
        from datetime import datetime, UTC

        if timestamp is None:
            timestamp = datetime.now(UTC).isoformat()

        message = {
            "message_id": message_id,
            "role": role,
            "content": content,
            "timestamp": timestamp,
            "metadata": metadata or {}
        }

        if self.messages is None:
            self.messages = []

        self.messages.append(message)
        self.message_count = len(self.messages)
        self.last_message_at = datetime.now(UTC)

    def get_messages(self) -> list:
        """Get all messages in the conversation."""
        return self.messages if self.messages else []

    def get_message_by_id(self, message_id: str) -> dict:
        """Get a specific message by ID."""
        if self.messages:
            for msg in self.messages:
                if msg.get("message_id") == message_id:
                    return msg
        return None

    def to_dict(self) -> dict:
        """Convert conversation to dictionary matching API format."""
        return {
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "message_id": self.current_message_id,
            "auth_key": self.auth_key,
            "status": self.status,
            "context": self.context,
            "payload": self.current_payload,
            "resources": self.resources,
            "messages": self.messages or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_message_at": self.last_message_at.isoformat() if self.last_message_at else None,
            "message_count": self.message_count
        }


class UserSession(Base):
    """User sessions table for authentication and session management."""
    __tablename__ = "user_sessions"

    session_id = Column(String(255), primary_key=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String(255),
        ForeignKey('users.user_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    token = Column(String, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    ip_address = Column(String(45))  # INET stored as string
    user_agent = Column(String)
    device_info = Column(JSONB)

    # Relationship to User
    user = relationship("User", back_populates="sessions")

    def __repr__(self) -> str:
        return f"<UserSession(id={self.session_id}, user={self.user_id})>"


class Notification(Base):
    """Notifications table (partitioned by scheduled_at)."""
    __tablename__ = "notifications"

    notification_id = Column(String(255), primary_key=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String(255),
        ForeignKey('users.user_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    type = Column(String(50), nullable=False)
    title = Column(String(255))
    message = Column(String, nullable=False)
    status = Column(String(50), nullable=False, index=True)
    priority = Column(String(50))
    scheduled_at = Column(DateTime(timezone=True), index=True)
    sent_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    notification_metadata = Column('metadata', JSONB)  # Renamed to avoid SQLAlchemy conflict
    retry_count = Column(Integer, default=0, nullable=False)

    # Relationship to User
    user = relationship("User", back_populates="notifications")

    def __repr__(self) -> str:
        return f"<Notification(id={self.notification_id}, type={self.type}, status={self.status})>"


class AuditLog(Base):
    """Audit logs table (partitioned by created_at)."""
    __tablename__ = "audit_logs"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        String(255),
        ForeignKey('users.user_id', ondelete='SET NULL'),
        index=True
    )
    action = Column(String(255), nullable=False, index=True)
    resource_type = Column(String(255))
    resource_id = Column(String(255))
    ip_address = Column(String(45))  # INET stored as string
    user_agent = Column(String)
    request_data = Column(JSONB)
    response_status = Column(Integer)
    details = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)

    # Relationship to User
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.log_id}, action={self.action})>"


class DocumentJob(Base):
    """Document processing jobs table."""
    __tablename__ = "document_jobs"

    job_id = Column(String(255), primary_key=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String(255),
        ForeignKey('users.user_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    file_path = Column(String, nullable=False)
    file_type = Column(String(255))
    status = Column(String(50), nullable=False, index=True)
    job_type = Column(String(50), nullable=False)
    result = Column(JSONB)
    error_message = Column(String)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    processing_time_ms = Column(Integer)

    # Relationship to User
    user = relationship("User", back_populates="document_jobs")

    def __repr__(self) -> str:
        return f"<DocumentJob(id={self.job_id}, status={self.status}, type={self.job_type})>"


class ApiRateLimit(Base):
    """API rate limiting table."""
    __tablename__ = "api_rate_limits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        String(255),
        ForeignKey('users.user_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    endpoint = Column(String(255), nullable=False, index=True)
    request_count = Column(Integer, default=0, nullable=False)
    window_start = Column(DateTime(timezone=True), nullable=False, index=True)
    window_end = Column(DateTime(timezone=True), nullable=False)

    # Relationship to User
    user = relationship("User", back_populates="api_rate_limits")

    def __repr__(self) -> str:
        return f"<ApiRateLimit(user={self.user_id}, endpoint={self.endpoint}, count={self.request_count})>"


class ChatFeedback(Base):
    """Chat feedback table."""
    __tablename__ = "chat_feedback"

    feedback_id = Column(String(255), primary_key=True, nullable=False, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(
        String(255),
        ForeignKey('conversations.conversation_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    message_id = Column(
        String(255),
        ForeignKey('chat_messages.message_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    rating = Column(String(50), nullable=False)
    comment = Column(String)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    conversation = relationship("Conversation", backref=backref("feedback_list", passive_deletes=True))
    message = relationship("ChatMessage", backref=backref("feedback", passive_deletes=True))

    def __repr__(self) -> str:
        return f"<ChatFeedback(id={self.feedback_id}, rating={self.rating})>"


class ChatMetric(Base):
    """Chat metrics table (partitioned by created_at)."""
    __tablename__ = "chat_metrics"

    metric_id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String(255), nullable=False, index=True)
    response_time_ms = Column(Integer)
    token_count = Column(Integer)
    retrieval_time_ms = Column(Integer)
    generation_time_ms = Column(Integer)
    sources_used = Column(Integer)
    user_satisfaction = Column(Integer)  # Float stored as Integer for partitioning
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)

    # Note: Foreign key is defined in schema.sql but not in model due to partitioning
    # Relationship cannot be defined here because partitioned tables have issues with FK relationships in SQLAlchemy

    def __repr__(self) -> str:
        return f"<ChatMetric(id={self.metric_id}, conversation={self.conversation_id})>"


# ChatConversation class removed - now using unified Conversation model


class ChatMessage(Base):
    """Chat messages table."""
    __tablename__ = "chat_messages"

    message_id = Column(String(255), primary_key=True, nullable=False, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(
        String(255),
        ForeignKey('conversations.conversation_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    role = Column(String(50), nullable=False, index=True)
    content = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    entities = Column(JSONB)
    message_metadata = Column('metadata', JSONB)

    # Relationships
    conversation = relationship("Conversation", backref=backref("chat_messages_list", passive_deletes=True))

    def __repr__(self) -> str:
        return f"<ChatMessage(id={self.message_id}, role={self.role})>"
