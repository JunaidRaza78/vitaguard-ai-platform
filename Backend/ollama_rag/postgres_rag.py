"""
PostgreSQL client for RAG Chatbot
Safe, transactional, production-ready
"""

import os
import logging
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import uuid
import json

# Load .env
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_USER_ID = "28f09c09-6b69-4179-b6bf-21b56c746de6"
MAX_MESSAGES_LIMIT = 200
MAX_CONVERSATIONS_LIMIT = 100


# ------------------------------------------------------------------
# Config
# ------------------------------------------------------------------
class RAGPostgresConfig:
    def __init__(self):
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = int(os.getenv("DB_PORT", "5432"))
        self.database = os.getenv("DB_NAME", "family_health_db")
        self.user = os.getenv("DB_USER", "postgres")
        self.password = os.getenv("DB_PASSWORD", "")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )

    def create_engine(self):
        return create_engine(
            self.database_url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 10},
        )


# ------------------------------------------------------------------
# Client
# ------------------------------------------------------------------
class RAGPostgresClient:
    def __init__(self):
        self.config = RAGPostgresConfig()
        self.engine = self.config.create_engine()
        self.SessionLocal = sessionmaker(bind=self.engine)

    @contextmanager
    def session_scope(self) -> Session:
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------
    def health_check(self) -> bool:
        try:
            with self.session_scope() as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"DB health check failed: {e}")
            return False

    # ------------------------------------------------------------------
    # Conversations
    # ------------------------------------------------------------------
    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        with self.session_scope() as session:
            row = session.execute(
                text("""
                    SELECT conversation_id, user_id, title, status,
                           created_at, updated_at, last_message_at, message_count
                    FROM conversations
                    WHERE conversation_id = :id
                """),
                {"id": conversation_id},
            ).fetchone()

            if not row:
                return None

            return dict(row._mapping)

    def create_conversation(
        self,
        conversation_id: str,
        user_id: str,
        title: Optional[str] = None,
        status: str = "active",
    ) -> Dict:
        now = datetime.utcnow()

        try:
            user_uuid = uuid.UUID(user_id)
        except Exception:
            user_uuid = uuid.UUID(DEFAULT_SYSTEM_USER_ID)

        with self.session_scope() as session:
            session.execute(
                text("""
                    INSERT INTO conversations
                    (conversation_id, user_id, title, status,
                     created_at, updated_at, last_message_at, message_count)
                    VALUES (:id, :user_id, :title, :status,
                            :now, :now, :now, 0)
                """),
                {
                    "id": conversation_id,
                    "user_id": str(user_uuid),
                    "title": title or f"Chat {now:%Y-%m-%d %H:%M}",
                    "status": status,
                    "now": now,
                },
            )

        return self.get_conversation(conversation_id)

    def get_user_conversations(self, user_id: str, limit: int = 50) -> List[Dict]:
        limit = min(limit, MAX_CONVERSATIONS_LIMIT)

        with self.session_scope() as session:
            rows = session.execute(
                text("""
                    SELECT conversation_id, title, status,
                           created_at, last_message_at, message_count
                    FROM conversations
                    WHERE user_id = :uid
                    ORDER BY last_message_at DESC
                    LIMIT :limit
                """),
                {"uid": user_id, "limit": limit},
            ).fetchall()

            return [dict(r._mapping) for r in rows]

    # ------------------------------------------------------------------
    # Messages
    # ------------------------------------------------------------------
    def create_chat_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        message_metadata: Optional[Dict] = None,
    ) -> Dict:
        now = datetime.utcnow()
        message_id = str(uuid.uuid4())

        with self.session_scope() as session:
            session.execute(
                text("""
                    INSERT INTO chat_messages
                    (message_id, conversation_id, role, content, timestamp, metadata)
                    VALUES (:mid, :cid, :role, :content, :ts, :meta)
                """),
                {
                    "mid": message_id,
                    "cid": conversation_id,
                    "role": role,
                    "content": content,
                    "ts": now,
                    "meta": json.dumps(message_metadata) if message_metadata else None,
                },
            )

            # 🔥 Update conversation stats
            session.execute(
                text("""
                    UPDATE conversations
                    SET last_message_at = :ts,
                        updated_at = :ts,
                        message_count = message_count + 1
                    WHERE conversation_id = :cid
                """),
                {"ts": now, "cid": conversation_id},
            )

        return {
            "message_id": message_id,
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "timestamp": now,
        }

    def get_conversation_messages(
        self,
        conversation_id: str,
        limit: int = 100,
    ) -> List[Dict]:
        limit = min(limit, MAX_MESSAGES_LIMIT)

        with self.session_scope() as session:
            rows = session.execute(
                text("""
                    SELECT message_id, role, content, timestamp, metadata
                    FROM chat_messages
                    WHERE conversation_id = :cid
                    ORDER BY timestamp ASC
                    LIMIT :limit
                """),
                {"cid": conversation_id, "limit": limit},
            ).fetchall()

            return [dict(r._mapping) for r in rows]

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------
    def create_chat_metric(
        self,
        conversation_id: str,
        response_time_ms: Optional[int] = None,
        sources_used: Optional[int] = None,
        retrieval_time_ms: Optional[int] = None,
        generation_time_ms: Optional[int] = None,
    ):
        with self.session_scope() as session:
            session.execute(
                text("""
                    INSERT INTO chat_metrics
                    (conversation_id, response_time_ms, sources_used,
                     retrieval_time_ms, generation_time_ms, created_at)
                    VALUES (:cid, :rt, :src, :retr, :gen, :now)
                """),
                {
                    "cid": conversation_id,
                    "rt": response_time_ms,
                    "src": sources_used,
                    "retr": retrieval_time_ms,
                    "gen": generation_time_ms,
                    "now": datetime.utcnow(),
                },
            )


# ------------------------------------------------------------------
# Singleton
# ------------------------------------------------------------------
_rag_client: Optional[RAGPostgresClient] = None


def get_rag_postgres_client() -> RAGPostgresClient:
    global _rag_client
    if _rag_client is None:
        _rag_client = RAGPostgresClient()
    return _rag_client
