"""
AI Health Assistant Chat API
Provides AI-powered health guidance using Ollama LLM
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
import logging
import os

from app.middleware.auth import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1",
    tags=["Chat"],
)


class ChatRequest(BaseModel):
    """Chat request with user message and optional specialty."""
    message: str = Field(..., min_length=1, max_length=2000)
    specialty: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response from AI assistant."""
    response: str
    sources: List[str] = []
    disclaimer: str = "This is general health information only. Always consult a healthcare professional for medical advice."


# Emergency keywords - always handled locally (no LLM needed)
EMERGENCY_KEYWORDS = [
    'chest pain', 'difficulty breathing', 'stroke', 'seizure',
    'unconscious', 'severe bleeding', 'heart attack', 'can\'t breathe',
    'not breathing', 'overdose', 'poisoning', 'suicide'
]


def _get_ollama_client():
    """Get Ollama client instance."""
    try:
        from ollama_rag.ollama_client import get_ollama_client
        return get_ollama_client()
    except Exception as e:
        logger.warning(f"Ollama client not available: {e}")
        return None


def _build_health_prompt(message: str, specialty: Optional[str] = None) -> str:
    """Build a health-focused system prompt for Ollama."""
    specialty_context = f" Focus on {specialty} topics." if specialty else ""
    return (
        f"You are a knowledgeable AI health assistant.{specialty_context} "
        "Provide clear, accurate, and helpful health information. "
        "Always recommend consulting a healthcare provider for personal medical advice. "
        "Keep responses concise, well-structured with bullet points where appropriate, "
        "and use markdown formatting. "
        "If asked about an emergency, always advise calling emergency services immediately.\n\n"
        f"User question: {message}"
    )


def _fallback_response(message: str) -> str:
    """Simple fallback when Ollama is unavailable."""
    return (
        "I'm your AI health assistant. I can provide general health information on topics like:\n\n"
        "- Blood test results (glucose, cholesterol, vitamins)\n"
        "- Chronic condition management (diabetes, hypertension)\n"
        "- Healthy lifestyle tips (diet, exercise, sleep)\n"
        "- Preventive care recommendations\n\n"
        "**Note:** The AI model is currently loading. Please try again in a moment.\n\n"
        "**Important:** I provide educational information only. "
        "Always consult your healthcare provider for medical advice."
    )


def _get_relevant_sources(message: str) -> List[str]:
    """Get relevant health information sources based on message content."""
    message_lower = message.lower()

    if any(word in message_lower for word in ['diabetes', 'glucose', 'blood sugar', 'hba1c']):
        return ["American Diabetes Association", "CDC Diabetes Prevention Program"]

    if any(word in message_lower for word in ['heart', 'cholesterol', 'blood pressure', 'cardio']):
        return ["American Heart Association", "National Heart, Lung, and Blood Institute"]

    if any(word in message_lower for word in ['vitamin', 'nutrition', 'diet', 'supplement']):
        return ["Academy of Nutrition and Dietetics", "NIH Office of Dietary Supplements"]

    if any(word in message_lower for word in ['cancer', 'tumor', 'oncology']):
        return ["American Cancer Society", "National Cancer Institute"]

    if any(word in message_lower for word in ['mental', 'anxiety', 'depression', 'stress']):
        return ["National Alliance on Mental Illness", "American Psychological Association"]

    return ["Mayo Clinic", "Cleveland Clinic", "National Institutes of Health (NIH)"]


@router.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(
    request: ChatRequest,
    current_user: dict = Depends(get_current_active_user),
):
    """
    Chat with AI health assistant powered by Ollama LLM.
    """
    message = request.message.strip()
    message_lower = message.lower()

    # Emergency detection - always handle locally
    if any(kw in message_lower for kw in EMERGENCY_KEYWORDS):
        return ChatResponse(
            response=(
                "⚠️ **EMERGENCY ALERT** ⚠️\n\n"
                "Based on your message, this may be a medical emergency. "
                "**Please call emergency services (115/1122) immediately** or go to the nearest emergency room.\n\n"
                "Do not wait for online advice in emergency situations."
            ),
            sources=["Emergency Services - 115", "Rescue - 1122"],
            disclaimer=""
        )

    # Try Ollama
    ollama = _get_ollama_client()
    if ollama:
        try:
            prompt = _build_health_prompt(message, request.specialty)
            model = os.getenv("OLLAMA_MODEL", "deepseek-r1:8b")

            logger.info(f"Sending to Ollama model={model}: {message[:60]}...")
            result = ollama.generate(prompt=prompt)

            if result and isinstance(result, str) and result.strip():
                response_text = result.strip()
                logger.info(f"Ollama responded: {len(response_text)} chars")
                return ChatResponse(
                    response=response_text,
                    sources=_get_relevant_sources(message),
                )
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            # Fall through to fallback

    # Fallback when Ollama is unavailable
    logger.warning("Using fallback response - Ollama unavailable")
    return ChatResponse(
        response=_fallback_response(message),
        sources=_get_relevant_sources(message),
    )


__all__ = ["router"]
