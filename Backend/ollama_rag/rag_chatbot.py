"""
Medical RAG Chatbot Pipeline
ChromaDB + Ollama + PostgreSQL (production safe)
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Generator
from dataclasses import dataclass, field
import uuid
import time
from web_search import duckduckgo_medical_search


# ------------------------------------------------------------------
# PATH SETUP
# ------------------------------------------------------------------
BACKEND_DIR = Path(__file__).parent.parent
CHROMA_DIR = BACKEND_DIR / "shared" / "database" / "chroma"
sys.path.insert(0, str(CHROMA_DIR))
sys.path.insert(0, str(Path(__file__).parent))

from ollama_client import OllamaClient, get_ollama_client
from query_by_agent import query_medical_documents
from postgres_rag import RAGPostgresClient, get_rag_postgres_client

# ------------------------------------------------------------------
# LOGGING
# ------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# CONSTANTS
# ------------------------------------------------------------------
MAX_HISTORY_MESSAGES = 6
MAX_CONTEXT_TOKENS = 2000
MIN_RELEVANCE_SCORE = 0.1  # 10%

# ------------------------------------------------------------------
# SYSTEM PROMPT
# ------------------------------------------------------------------
MEDICAL_SYSTEM_PROMPT = """
You are a caring medical information assistant who behaves like a real doctor during a consultation.

Your workflow:
1. If the user describes symptoms but information is incomplete,
   ASK 2–4 short, relevant follow-up questions first.
2. Do NOT give explanations until enough information is collected.
3. Once sufficient details are available, explain possible common causes
   in simple language (NOT diagnosis).
4. Clearly point out warning signs that need urgent care.
5. Suggest what to do next (rest, monitor, doctor visit, emergency).

Rules:
- Do NOT diagnose or prescribe medicines.
- Ask questions naturally, like a doctor talking to a patient.
- Keep language simple, calm, and friendly.
- If symptoms sound serious, clearly say it is urgent.
- Never say “based on documents” or “knowledge base”.

Tone:
- Human
- Supportive
- Doctor-like
- Conversational

End with a short safety reminder only when appropriate.
"""


# ------------------------------------------------------------------
# IN-MEMORY FALLBACK
# ------------------------------------------------------------------
@dataclass
class Message:
    role: str
    content: str


@dataclass
class Conversation:
    conversation_id: str
    messages: list[Message] = field(default_factory=list)

    def add(self, role: str, content: str):
        self.messages.append(Message(role, content))
        self.messages = self.messages[-(MAX_HISTORY_MESSAGES * 2):]


# ------------------------------------------------------------------
# CHATBOT
# ------------------------------------------------------------------
class MedicalRAGChatbot:

    def __init__(self):
        self.llm: OllamaClient = get_ollama_client()
        self.db: RAGPostgresClient = get_rag_postgres_client()
        self.conversations: dict[str, Conversation] = {}

    # --------------------------------------------------
    # GREETING DETECTOR
    # --------------------------------------------------
    def _is_greeting(self, text: str) -> bool:
        greetings = {
            "hi", "hello", "hey", "hii",
            "assalam", "assalamualaikum", "salam",
            "good morning", "good evening", "good afternoon"
        }
        t = text.lower().strip()
        return t in greetings or len(t.split()) <= 2

    # --------------------------------------------------
    # TOKEN ESTIMATION
    # --------------------------------------------------
    def _estimate_tokens(self, text: str) -> int:
        return len(text) // 4

    # --------------------------------------------------
    # CONTEXT RETRIEVAL
    # --------------------------------------------------
    def _retrieve_context(self, question: str, specialty: Optional[str], top_k: int):
        results = query_medical_documents(
            query_text=question,
            agent_specialty=specialty,
            n_results=top_k,
            alpha=0.7
        )

        docs = [
            r for r in results.get("results", [])
            if r.get("score", 0) >= MIN_RELEVANCE_SCORE * 100
        ]

        context_parts = []
        tokens = 0

        for i, doc in enumerate(docs, 1):
            block = (
                f"{doc.get('text')}"
            )
            block_tokens = self._estimate_tokens(block)
            if tokens + block_tokens > MAX_CONTEXT_TOKENS:
                break
            context_parts.append(block)
            tokens += block_tokens

        return "\n\n".join(context_parts), docs[:len(context_parts)]

    # --------------------------------------------------
    # CHAT
    # --------------------------------------------------
    def chat(
        self,
        question: str,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        specialty: Optional[str] = None,
        top_k: int = 5,
        temperature: float = 0.3,
        stream: bool = False
    ) -> dict | Generator:

        start = time.time()
        conv_id = conversation_id or str(uuid.uuid4())

        # ---------------- GREETING ----------------
        if self._is_greeting(question):
            return {
                "answer": (
                    "Hi! 👋 I can help explain medical and health-related topics in a simple, "
                    "doctor-like way.\n\n"
                    "Tell me what you’re feeling or what’s worrying you, and I’ll ask a few "
                    "questions to understand better."
                ),
                "conversation_id": conv_id,
                "context_used": False,
                "sources": [],
                "storage": "none"
            }

        # ---------------- LOAD HISTORY ----------------
        history = []
        if self.db:
            conversation = self.db.get_conversation(conv_id)
            if not conversation:
                self.db.create_conversation(conv_id, user_id or "system")
            messages = self.db.get_conversation_messages(
                conv_id, limit=MAX_HISTORY_MESSAGES
            )
            history = [{"role": m["role"], "content": m["content"]} for m in messages]

        # ---------------- STEP 1: ASK FOLLOW-UP IF NEEDED ----------------
        if len(question.split()) < 7:
            followup_prompt = [
                {"role": "system", "content": MEDICAL_SYSTEM_PROMPT},
                *history,
                {
                    "role": "user",
                    "content": (
                        f"The patient said: '{question}'.\n\n"
                        "If information is missing, ask 2–4 short follow-up questions "
                        "like a real doctor. Do NOT explain yet."
                    )
                }
            ]

            response = self.llm.chat(
                messages=followup_prompt,
                temperature=0.2,
                stream=False
            )

            return {
                "answer": response,
                "conversation_id": conv_id,
                "context_used": False,
                "sources": [],
                "storage": "llm-followup"
            }

        # ---------------- STEP 2: RAG SEARCH ----------------
        context, sources = self._retrieve_context(question, specialty, top_k)

        # ---------------- STEP 3: WEB FALLBACK ----------------
        if not context:
            web_context = duckduckgo_medical_search(question)

            messages = [
                {
                    "role": "system",
                    "content": MEDICAL_SYSTEM_PROMPT +
                    "\n\nGeneral medical information:\n" + web_context
                },
                *history,
                {"role": "user", "content": question}
            ]

            response = self.llm.chat(
                messages=messages,
                temperature=temperature,
                stream=False
            )

            return {
                "answer": response + (
                    "\n\n⚠️ Medical Safety Reminder: "
                    "This is general medical information. Please consult a licensed doctor."
                ),
                "conversation_id": conv_id,
                "context_used": False,
                "sources": [{"type": "duckduckgo"}],
                "storage": "web"
            }

        # ---------------- STEP 4: FINAL ANSWER (RAG) ----------------
        messages = [
            {
                "role": "system",
                "content": MEDICAL_SYSTEM_PROMPT + "\n\n" + context
            },
            *history,
            {"role": "user", "content": question}
        ]

        temperature = max(0.1, min(temperature, 0.5))

        response = self.llm.chat(
            messages=messages,
            temperature=temperature,
            stream=False
        )

        response_time = int((time.time() - start) * 1000)

        if self.db:
            self.db.create_chat_message(conv_id, "user", question)
            self.db.create_chat_message(conv_id, "assistant", response)
            self.db.create_chat_metric(
                conversation_id=conv_id,
                response_time_ms=response_time,
                sources_used=len(sources)
            )

        return {
            "answer": response + (
                "\n\n⚠️ Medical Safety Reminder: "
                "This information is not a diagnosis. Please consult a healthcare professional."
            ),
            "conversation_id": conv_id,
            "context_used": True,
            "sources": [
                {"file": s.get("source_file"), "relevance": s.get("score")}
                for s in sources
            ],
            "storage": "postgresql"
        }

    # --------------------------------------------------
    # HEALTH
    # --------------------------------------------------
    def health_check(self):
        return {
            "ollama": "healthy" if self.llm.health_check() else "unhealthy",
            "postgresql": "healthy" if self.db.health_check() else "unhealthy"
        }


# ------------------------------------------------------------------
# SINGLETON
# ------------------------------------------------------------------
_chatbot: Optional[MedicalRAGChatbot] = None


def get_chatbot() -> MedicalRAGChatbot:
    global _chatbot
    if not _chatbot:
        _chatbot = MedicalRAGChatbot()
    return _chatbot
