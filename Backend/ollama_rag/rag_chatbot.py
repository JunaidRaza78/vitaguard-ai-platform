"""
Medical RAG Chatbot Pipeline - FULLY OPTIMIZED VERSION
✅ No repeated questions
✅ Better context tracking
✅ Proper conversation flow
✅ Empty response handling
✅ External prompts from prompts.py
✅ Short answers (3-5 sentences)
✅ Fixed greeting detection
✅ Fixed follow-up logic
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Generator
from dataclasses import dataclass, field
import uuid
import time

from .web_search import duckduckgo_medical_search

# Import prompts from external file
from .prompts import (
    MEDICAL_SYSTEM_PROMPT,
    FOLLOWUP_INSTRUCTION,
    ADVICE_INSTRUCTION,
    GREETING_RESPONSE,
    ERROR_MESSAGES,
    RAG_SAFETY_DISCLAIMER,
    WEB_SAFETY_DISCLAIMER
)

# ------------------------------------------------------------------
# PATH SETUP
# ------------------------------------------------------------------
BACKEND_DIR = Path(__file__).parent.parent
CHROMA_DIR = BACKEND_DIR / "shared" / "database" / "chroma"
sys.path.insert(0, str(CHROMA_DIR))
sys.path.insert(0, str(Path(__file__).parent))

from .ollama_client import get_ollama_client
from .postgres_rag import get_rag_postgres_client

# Try importing chroma-based query, fallback to None if not available
try:
    from shared.database.chroma.query_by_agent import query_medical_documents
except ImportError:
    query_medical_documents = None

# ------------------------------------------------------------------
# LOGGING
# ------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# CONSTANTS
# ------------------------------------------------------------------
MAX_HISTORY_MESSAGES = 10
MAX_CONTEXT_TOKENS = 2000
MIN_RELEVANCE_SCORE = 0.1

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


# ------------------------------------------------------------------
# CHATBOT
# ------------------------------------------------------------------
class MedicalRAGChatbot:

    def __init__(self):
        self.llm = get_ollama_client()
        self.db = get_rag_postgres_client()
        logger.info("MedicalRAGChatbot initialized with optimized prompts")

    # --------------------------------------------------
    # GREETING DETECTOR - IMPROVED
    # --------------------------------------------------
    def _is_greeting(self, text: str) -> bool:
        """
        Detect if message is just a greeting.
        Medical complaints are NOT greetings.
        """
        greetings = {
            "hi", "hello", "hey", "hii", "helo",
            "assalam", "assalamualaikum", "salam",
            "good morning", "good evening", "good afternoon",
            "sup", "wassup", "yo"
        }
        t = text.lower().strip()
        
        # DON'T treat medical complaints as greetings
        medical_keywords = [
            "feeling", "pain", "hurt", "sick", "ill", "headache", 
            "fever", "stomach", "not well", "unwell", "ache",
            "problem", "issue", "dizzy", "tired", "weak"
        ]
        
        # If contains medical keyword, it's NOT a greeting
        if any(keyword in t for keyword in medical_keywords):
            logger.info(f"❌ NOT a greeting (contains medical keywords): {text}")
            return False
        
        # Must be ONLY greeting (not part of larger sentence)
        if t in greetings:
            logger.info(f"✅ Detected pure greeting: {text}")
            return True
        
        # Check if it's very short and contains greeting
        words = t.split()
        if len(words) <= 3 and any(g in t for g in greetings):
            logger.info(f"✅ Detected short greeting: {text}")
            return True
        
        return False

    # --------------------------------------------------
    # TOKEN ESTIMATION
    # --------------------------------------------------
    def _estimate_tokens(self, text: str) -> int:
        return len(text) // 4

    # --------------------------------------------------
    # IMPROVED: SUMMARIZE KNOWN INFO
    # --------------------------------------------------
    def _summarize_known_info(self, history: list, current_msg: str) -> str:
        """
        Extract key medical info already mentioned in conversation.
        IMPROVED VERSION - Better tracking to avoid repeated questions.
        """
        # Combine ALL history including current message
        all_messages = []
        for msg in history:
            role = msg.get("role", "")
            content = msg.get("content", "")
            all_messages.append(f"{role}: {content}")
        
        all_messages.append(f"user: {current_msg}")
        
        full_conversation = "\n".join(all_messages)
        all_text_lower = full_conversation.lower()
        
        known = []
        missing = []
        questions_asked = []
        
        # Track what questions were already asked by the assistant
        question_indicators = {
            "how long": ["how long", "when did", "since when"],
            "where": ["where", "what part", "which area", "location"],
            "severity": ["how severe", "how bad", "how painful", "intensity"],
            "other symptoms": ["any other", "do you have", "have you had", "experiencing"]
        }
        
        for category, indicators in question_indicators.items():
            for indicator in indicators:
                if indicator in all_text_lower:
                    questions_asked.append(category)
                    break
        
        # Check for symptom mentions
        symptoms = [
            "headache", "pain", "fever", "nausea", "dizziness", "cough",
            "fatigue", "tired", "vomiting", "stomach", "chest", "cold",
            "flu", "sore throat", "body ache", "weakness", "dizzy",
            "ache", "hurt", "sore", "bp", "blood pressure", "diabetes",
            "sugar"
        ]
        found_symptoms = []
        for symptom in symptoms:
            if symptom in all_text_lower:
                found_symptoms.append(symptom)
        
        if found_symptoms:
            known.append(f"✓ Symptoms: {', '.join(set(found_symptoms))}")
        else:
            if len(history) == 0:
                missing.append("what symptoms")
        
        # Check for location mentions
        location_patterns = [
            "middle of", "middle", "center", "front", "back",
            "left side", "right side", "left", "right",
            "upper", "lower", "top", "bottom",
            "stomach", "head", "chest", "neck", "throat",
            "arm", "leg", "shoulder", "back"
        ]
        found_locations = []
        for pattern in location_patterns:
            if pattern in all_text_lower:
                found_locations.append(pattern)
        
        if found_locations:
            known.append(f"✓ Location: {', '.join(set(found_locations))}")
        else:
            if "where" not in questions_asked and len(found_symptoms) > 0:
                missing.append("location")
        
        # Check for duration mentions
        duration_patterns = [
            r"\d+\s*(hour|hours|hr|hrs)",
            r"\d+\s*(day|days)",
            r"\d+\s*(week|weeks)",
            "since morning", "since yesterday", "since last night",
            "this morning", "today", "yesterday", "last night",
            "started", "began", "for the past", "about", "approximately"
        ]
        
        found_duration = False
        for pattern in duration_patterns:
            if pattern.replace("\\", "") in all_text_lower or any(p in all_text_lower for p in pattern.split()):
                found_duration = True
                break
        
        # Check for explicit time mentions
        time_words = ["hour", "day", "week", "month", "morning", "yesterday", "today", "night"]
        if any(word in all_text_lower for word in time_words):
            found_duration = True
        
        if found_duration:
            known.append(f"✓ Duration: mentioned (check conversation for details)")
        else:
            if "how long" not in questions_asked and len(history) > 0:
                missing.append("how long")
        
        # Check for severity mentions
        severity_words = [
            "severe", "mild", "moderate", "bad", "terrible", "awful",
            "worse", "better", "intense", "sharp", "dull", 
            "throbbing", "constant", "stabbing", "burning"
        ]
        found_severity = [sev for sev in severity_words if sev in all_text_lower]
        if found_severity:
            known.append(f"✓ Severity: {', '.join(set(found_severity))}")
        
        # Check if patient is on medication
        medication_keywords = [
            "taking", "medication", "medicine", "pills", "tablet",
            "prescribed", "doctor gave", "tenormin", "metformin",
            "insulin", "treatment"
        ]
        on_medication = any(keyword in all_text_lower for keyword in medication_keywords)
        if on_medication:
            known.append("✓ Patient is currently on medication")
        
        # Check if asking about medicine/treatment
        medicine_keywords = [
            "what medicine", "can i take", "should i take",
            "recommend", "suggest", "prescribe", "treatment",
            "what should i do", "how to treat", "medicine for"
        ]
        asking_medicine = any(word in all_text_lower for word in medicine_keywords)
        if asking_medicine:
            known.append("✓ Patient is asking for medicine/treatment recommendation")
        
        # Build summary
        result = ""
        if known:
            result += "INFORMATION ALREADY PROVIDED BY PATIENT:\n" + "\n".join(known)
        
        if missing and len(history) < 6 and not asking_medicine:
            result += "\n\nNEXT TO ASK (choose ONE): " + " OR ".join(missing)
        
        # Critical: Add what questions were already asked
        if questions_asked:
            unique_questions = list(set(questions_asked))
            result += f"\n\n⚠️ QUESTIONS ALREADY ASKED: {', '.join(unique_questions)}"
            result += "\n⚠️ DO NOT REPEAT ANY OF THESE QUESTIONS"
        
        # Check if we have enough info to give advice
        has_symptom = len(found_symptoms) > 0
        has_location = len(found_locations) > 0
        has_duration = found_duration
        
        enough_info = (has_symptom and (has_location or has_duration)) or asking_medicine or len(history) >= 6
        
        if enough_info:
            result += "\n\n✅ ENOUGH INFORMATION COLLECTED - READY TO GIVE ADVICE"
        
        summary = result if result else "No specific details collected yet. Start by understanding the main symptom."
        
        # Log for debugging
        logger.info(f"\n{'='*60}")
        logger.info(f"CONTEXT SUMMARY:")
        logger.info(f"{summary}")
        logger.info(f"{'='*60}\n")
        
        return summary

    # --------------------------------------------------
    # CONTEXT RETRIEVAL (RAG)
    # --------------------------------------------------
    def _retrieve_context(self, question: str, user_id: str, specialty: Optional[str], top_k: int):
        """
        Retrieve context with user isolation.

        Args:
            question: User query
            user_id: REQUIRED - Filter by this user's documents
            specialty: Optional specialty filter
            top_k: Number of results
        """
        logger.info(f"Retrieving RAG context for user {user_id}: {question[:50]}...")

        try:
            results = query_medical_documents(
                query_text=question,
                user_id=user_id,  # NEW: Pass user_id for filtering
                agent_specialty=specialty,
                n_results=top_k,
                alpha=0.7
            )

            # Check if query is generic (about documents themselves vs. specific medical content)
            generic_keywords = ["document", "upload", "summarize", "report", "file"]
            is_generic_query = any(kw in question.lower() for kw in generic_keywords)

            # Use lower threshold for generic queries, or accept top results if none meet threshold
            relevance_threshold = MIN_RELEVANCE_SCORE * 50 if is_generic_query else MIN_RELEVANCE_SCORE * 100  # 5% vs 10%

            docs = [
                r for r in results.get("results", [])
                if r.get("score", 0) >= relevance_threshold
            ]

            # If generic query and still no results, take top 3 anyway
            if is_generic_query and len(docs) == 0 and len(results.get("results", [])) > 0:
                docs = results.get("results", [])[:3]
                logger.info(f"Generic query with low scores - using top {len(docs)} results anyway")

            logger.info(f"Found {len(docs)} relevant documents (threshold: {relevance_threshold}%)")

            context_parts = []
            tokens = 0

            for doc in docs:
                block = doc.get("text", "")
                block_tokens = self._estimate_tokens(block)
                if tokens + block_tokens > MAX_CONTEXT_TOKENS:
                    break
                context_parts.append(block)
                tokens += block_tokens

            context = "\n\n".join(context_parts)
            logger.info(f"Context length: {len(context)} chars, ~{tokens} tokens")
            
            return context, docs[:len(context_parts)]
        
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return "", []

    # --------------------------------------------------
    # CHAT
    # --------------------------------------------------
    def chat(
        self,
        question: str,
        user_id: str,  # NEW: REQUIRED parameter for user isolation
        conversation_id: Optional[str] = None,
        specialty: Optional[str] = None,
        top_k: int = 5,
        temperature: float = 0.3,
        stream: bool = False
    ) -> dict | Generator:

        logger.info(f"\n{'='*60}")
        logger.info(f"NEW CHAT REQUEST")
        logger.info(f"Question: {question}")
        logger.info(f"Conversation ID: {conversation_id}")
        logger.info(f"{'='*60}\n")

        start = time.time()
        conv_id = conversation_id or str(uuid.uuid4())

        # ---------------- GREETING ----------------
        if self._is_greeting(question):
            logger.info(f"Returning greeting response")
            return {
                "answer": GREETING_RESPONSE,
                "conversation_id": conv_id,
                "context_used": False,
                "sources": [],
                "storage": "none"
            }

        # ---------------- LOAD HISTORY ----------------
        history = []
        if self.db:
            try:
                conversation = self.db.get_conversation(conv_id)
                if not conversation:
                    logger.info(f"Creating new conversation: {conv_id}")
                    self.db.create_conversation(conv_id, user_id or "system")

                messages = self.db.get_conversation_messages(
                    conv_id, limit=MAX_HISTORY_MESSAGES
                )
                history = [{"role": m["role"], "content": m["content"]} for m in messages]
                logger.info(f"Loaded {len(history)} messages from history")
            except Exception as e:
                logger.error(f"Error loading conversation history: {e}")

        # ---------------- CONVERSATION MODE ----------------
        # Build context summary of what we already know
        known_info = self._summarize_known_info(history, question)

        # Determine if we should ask follow-up or give advice
        has_enough_info = (
            "READY TO GIVE ADVICE" in known_info or
            "asking for medicine" in known_info.lower() or
            len(history) >= 8
        )
        
        # Check if message is very short (likely a simple answer to previous question)
        is_short_response = len(question.split()) < 10
        
        # Don't treat everything as short - check context
        is_new_topic = len(history) == 0
        is_complex_question = len(question.split()) > 15 or "?" in question

        logger.info(f"has_enough_info: {has_enough_info}")
        logger.info(f"is_short_response: {is_short_response}")
        logger.info(f"is_new_topic: {is_new_topic}")
        logger.info(f"history_length: {len(history)}")

        # Check if question is about documents (force RAG mode)
        document_keywords = ["document", "upload", "report", "summarize", "pdf", "file", "lab result", "test result", "prescription"]
        is_document_question = any(keyword in question.lower() for keyword in document_keywords)
        logger.info(f"is_document_question: {is_document_question}")

        # ---------------- FOLLOW-UP QUESTION MODE (FIXED) ----------------
        # Should ask follow-up if:
        # 1. It's a NEW vague complaint (like "not feeling well")
        # 2. OR it's a short response to previous question
        # BUT NOT if it's a document-related question
        should_ask_followup = (
            not is_document_question and  # NEW: Skip follow-up for document questions
            ((is_new_topic and is_short_response and not has_enough_info) or  # NEW vague complaint
            (not is_new_topic and is_short_response and not has_enough_info and not is_complex_question))  # Short answer
        )

        if should_ask_followup:
            logger.info("Mode: FOLLOW-UP QUESTION")
            
            followup_prompt = [
                {"role": "system", "content": MEDICAL_SYSTEM_PROMPT},
                *history,
                {"role": "user", "content": question},
                {
                    "role": "system",
                    "content": FOLLOWUP_INSTRUCTION.format(known_info=known_info)
                }
            ]

            try:
                response = self.llm.chat(
                    messages=followup_prompt,
                    temperature=0.2,
                    stream=False
                )
                
                logger.info(f"Follow-up response length: {len(response)} chars")

                # Check for empty response
                if not response or len(response.strip()) == 0:
                    logger.error("EMPTY RESPONSE FROM LLM!")
                    response = ERROR_MESSAGES["empty_response"]

                # Save to history
                if self.db:
                    try:
                        self.db.create_chat_message(conv_id, "user", question)
                        self.db.create_chat_message(conv_id, "assistant", response)
                        logger.info("Messages saved successfully")
                    except Exception as e:
                        logger.error(f"Error saving messages: {e}")

                return {
                    "answer": response,
                    "conversation_id": conv_id,
                    "context_used": False,
                    "sources": [],
                    "storage": "llm-followup"
                }
            
            except Exception as e:
                logger.error(f"Error in follow-up mode: {e}", exc_info=True)
                return {
                    "answer": ERROR_MESSAGES["processing_error"],
                    "conversation_id": conv_id,
                    "context_used": False,
                    "sources": [],
                    "error": str(e)
                }

        # ---------------- ADVICE MODE ----------------
        # Skip advice mode for document questions - go straight to RAG
        if has_enough_info and not is_document_question:
            logger.info("Mode: GIVING ADVICE")
            
            advice_prompt = [
                {"role": "system", "content": MEDICAL_SYSTEM_PROMPT},
                *history,
                {"role": "user", "content": question},
                {
                    "role": "system",
                    "content": ADVICE_INSTRUCTION.format(known_info=known_info)
                }
            ]

            try:
                response = self.llm.chat(
                    messages=advice_prompt,
                    temperature=0.3,
                    stream=False
                )

                logger.info(f"Advice response length: {len(response)} chars")

                # Check for empty response
                if not response or len(response.strip()) == 0:
                    logger.error("EMPTY ADVICE RESPONSE!")
                    response = ERROR_MESSAGES["empty_advice"]

                # Save to history
                if self.db:
                    try:
                        self.db.create_chat_message(conv_id, "user", question)
                        self.db.create_chat_message(conv_id, "assistant", response)
                    except Exception as e:
                        logger.error(f"Error saving advice: {e}")

                return {
                    "answer": response,
                    "conversation_id": conv_id,
                    "context_used": False,
                    "sources": [],
                    "storage": "llm-advice"
                }
            
            except Exception as e:
                logger.error(f"Error in advice mode: {e}", exc_info=True)
                return {
                    "answer": ERROR_MESSAGES["general_error"],
                    "conversation_id": conv_id,
                    "context_used": False,
                    "sources": [],
                    "error": str(e)
                }

        # ---------------- RAG SEARCH ----------------
        logger.info("Mode: RAG SEARCH (complex medical question)")

        try:
            context, sources = self._retrieve_context(question, user_id, specialty, top_k)  # NEW: Pass user_id
        except Exception as e:
            logger.error(f"Error retrieving context: {e}", exc_info=True)
            context, sources = "", []

        # ---------------- WEB FALLBACK ----------------
        if not context:
            logger.info("No RAG context - using web search")
            
            try:
                web_context = duckduckgo_medical_search(question)

                messages = [
                    {"role": "system", "content": MEDICAL_SYSTEM_PROMPT + "\n\n" + web_context},
                    *history,
                    {"role": "user", "content": question}
                ]

                response = self.llm.chat(messages=messages, temperature=temperature, stream=False)
                logger.info(f"Web fallback response: {len(response)} chars")

                if not response or len(response.strip()) == 0:
                    response = ERROR_MESSAGES["web_fallback_empty"]

                # Save to history
                if self.db:
                    try:
                        self.db.create_chat_message(conv_id, "user", question)
                        self.db.create_chat_message(conv_id, "assistant", response)
                    except Exception as e:
                        logger.error(f"Error saving web response: {e}")

                return {
                    "answer": response,  # NO DISCLAIMER
                    "conversation_id": conv_id,
                    "context_used": False,
                    "sources": [{"type": "web"}],
                    "storage": "web"
                }
            
            except Exception as e:
                logger.error(f"Error in web fallback: {e}", exc_info=True)
                return {
                    "answer": ERROR_MESSAGES["no_info"],
                    "conversation_id": conv_id,
                    "context_used": False,
                    "sources": [],
                    "error": str(e)
                }

        # ---------------- FINAL ANSWER (RAG) ----------------
        logger.info("Generating RAG-based response")
        
        messages = [
            {"role": "system", "content": MEDICAL_SYSTEM_PROMPT + "\n\nMEDICAL CONTEXT:\n" + context},
            *history,
            {"role": "user", "content": question}
        ]

        temperature = max(0.1, min(temperature, 0.5))

        try:
            response = self.llm.chat(messages=messages, temperature=temperature, stream=False)
            logger.info(f"RAG response: {len(response)} chars")

            if not response or len(response.strip()) == 0:
                response = ERROR_MESSAGES["rag_empty"]

            response_time = int((time.time() - start) * 1000)

            # Save to database
            if self.db:
                try:
                    self.db.create_chat_message(conv_id, "user", question)
                    self.db.create_chat_message(conv_id, "assistant", response)
                    self.db.create_chat_metric(
                        conversation_id=conv_id,
                        response_time_ms=response_time,
                        sources_used=len(sources)
                    )
                    logger.info("RAG messages saved successfully")
                except Exception as e:
                    logger.error(f"Error saving RAG messages: {e}")

            return {
                "answer": response,  # NO DISCLAIMER
                "conversation_id": conv_id,
                "context_used": True,
                "sources": [
                    {"file": s.get("source_file"), "relevance": s.get("score")}
                    for s in sources
                ],
                "storage": "postgresql",
                "response_time_ms": response_time
            }
        
        except Exception as e:
            logger.error(f"Error generating RAG response: {e}", exc_info=True)
            return {
                "answer": ERROR_MESSAGES["general_error"],
                "conversation_id": conv_id,
                "context_used": False,
                "sources": [],
                "error": str(e)
            }

    # --------------------------------------------------
    # HEALTH CHECK
    # --------------------------------------------------
    def health_check(self):
        ollama_status = "healthy" if self.llm.health_check() else "unhealthy"
        postgres_status = "healthy" if self.db and self.db.health_check() else "unhealthy"
        
        logger.info(f"Health - Ollama: {ollama_status}, PostgreSQL: {postgres_status}")
        
        return {
            "ollama": ollama_status,
            "postgresql": postgres_status
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
