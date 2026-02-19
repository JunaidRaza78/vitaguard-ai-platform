"""
AI Health Assistant Chat API
Provides AI-powered health guidance and information
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
import logging

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


@router.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(
    request: ChatRequest,
    current_user: dict = Depends(get_current_active_user),
):
    """
    Chat with AI health assistant.
    Provides general health information and guidance based on user queries.
    """
    try:
        # Generate response based on specialty and message
        response_text = _generate_response(request.message, request.specialty)

        return ChatResponse(
            response=response_text,
            sources=_get_relevant_sources(request.message),
        )
    except Exception as e:
        logger.error(f"Error in chat assistant: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat request",
        )


def _generate_response(message: str, specialty: Optional[str] = None) -> str:
    """
    Generate AI response based on message and specialty.
    This is a simplified implementation - in production, integrate with OpenAI/Claude API.
    """
    message_lower = message.lower()

    # Emergency keywords
    emergency_keywords = ['chest pain', 'difficulty breathing', 'stroke', 'seizure',
                         'unconscious', 'severe bleeding', 'heart attack']
    if any(kw in message_lower for kw in emergency_keywords):
        return (
            "⚠️ **EMERGENCY ALERT** ⚠️\n\n"
            "Based on your message, this may be a medical emergency. "
            "**Please call emergency services (911) immediately** or go to the nearest emergency room.\n\n"
            "Do not wait for online advice in emergency situations."
        )

    # General health queries
    if any(word in message_lower for word in ['glucose', 'blood sugar', 'diabetes']):
        return (
            "**Blood Glucose & Diabetes Information:**\n\n"
            "Normal fasting glucose levels are 70-100 mg/dL. Levels between 100-125 mg/dL may indicate prediabetes, "
            "while levels above 126 mg/dL on two separate tests may indicate diabetes.\n\n"
            "**Tips for managing blood sugar:**\n"
            "- Eat a balanced diet with whole grains, lean proteins, and vegetables\n"
            "- Exercise regularly (30 minutes most days)\n"
            "- Monitor your blood sugar if recommended by your doctor\n"
            "- Stay hydrated\n"
            "- Manage stress\n\n"
            "If you have concerns about your glucose levels, please consult with your healthcare provider for personalized advice and testing."
        )

    if any(word in message_lower for word in ['cholesterol', 'lipid', 'hdl', 'ldl']):
        return (
            "**Cholesterol & Heart Health:**\n\n"
            "Cholesterol is a waxy substance in your blood. Your body needs it, but too much can increase heart disease risk.\n\n"
            "**Target levels:**\n"
            "- Total cholesterol: <200 mg/dL\n"
            "- LDL (bad): <100 mg/dL\n"
            "- HDL (good): >40 mg/dL (men), >50 mg/dL (women)\n"
            "- Triglycerides: <150 mg/dL\n\n"
            "**Ways to improve cholesterol:**\n"
            "- Eat heart-healthy foods (oats, fatty fish, nuts, olive oil)\n"
            "- Reduce saturated and trans fats\n"
            "- Exercise regularly\n"
            "- Maintain healthy weight\n"
            "- Don't smoke\n\n"
            "Your doctor may recommend medication if lifestyle changes aren't enough."
        )

    if any(word in message_lower for word in ['blood pressure', 'hypertension', 'bp']):
        return (
            "**Blood Pressure Information:**\n\n"
            "Blood pressure is measured as systolic/diastolic (e.g., 120/80 mmHg).\n\n"
            "**Categories:**\n"
            "- Normal: <120/<80\n"
            "- Elevated: 120-129/<80\n"
            "- Hypertension Stage 1: 130-139/80-89\n"
            "- Hypertension Stage 2: ≥140/≥90\n"
            "- Crisis: >180/>120 (seek immediate care)\n\n"
            "**Managing blood pressure:**\n"
            "- Reduce sodium intake (<2,300 mg/day)\n"
            "- Exercise regularly\n"
            "- Maintain healthy weight\n"
            "- Limit alcohol\n"
            "- Manage stress\n"
            "- Take prescribed medications as directed\n\n"
            "Regular monitoring and doctor visits are important for managing hypertension."
        )

    if any(word in message_lower for word in ['vitamin d', 'vitamins', 'supplements']):
        return (
            "**Vitamins & Supplements:**\n\n"
            "**Vitamin D:**\n"
            "- Important for bone health, immune function, and mood\n"
            "- Normal range: 30-100 ng/mL\n"
            "- Sources: Sunlight, fatty fish, fortified foods\n"
            "- Many people need supplements, especially in winter\n\n"
            "**General supplement advice:**\n"
            "- Get nutrients from food first when possible\n"
            "- Talk to your doctor before starting supplements\n"
            "- Some vitamins can interact with medications\n"
            "- More isn't always better - avoid mega-doses\n\n"
            "Your doctor can test your vitamin levels and recommend appropriate supplementation."
        )

    if any(word in message_lower for word in ['weight', 'bmi', 'obesity', 'diet']):
        return (
            "**Weight Management & Nutrition:**\n\n"
            "**Healthy eating principles:**\n"
            "- Eat plenty of vegetables and fruits\n"
            "- Choose whole grains over refined grains\n"
            "- Include lean proteins (fish, poultry, beans, nuts)\n"
            "- Limit added sugars and saturated fats\n"
            "- Watch portion sizes\n"
            "- Stay hydrated\n\n"
            "**For sustainable weight loss:**\n"
            "- Aim for 1-2 pounds per week\n"
            "- Combine diet changes with physical activity\n"
            "- Keep a food diary\n"
            "- Get adequate sleep (7-9 hours)\n"
            "- Manage stress\n\n"
            "Consider consulting a registered dietitian for personalized meal planning."
        )

    # Specialty-specific responses
    if specialty == 'cardiology':
        return (
            "**Cardiology - Heart Health:**\n\n"
            "I can help answer questions about heart health, cholesterol, blood pressure, "
            "and cardiovascular disease prevention.\n\n"
            "Common topics include:\n"
            "- Understanding cholesterol and lipid panels\n"
            "- Blood pressure management\n"
            "- Heart-healthy lifestyle changes\n"
            "- Recognizing warning signs of heart problems\n\n"
            "What specific heart health question do you have?"
        )

    if specialty == 'nutrition':
        return (
            "**Nutrition Guidance:**\n\n"
            "I can provide information about healthy eating, dietary recommendations, "
            "and nutrition for managing health conditions.\n\n"
            "Topics I can help with:\n"
            "- Balanced meal planning\n"
            "- Nutrition for diabetes, heart disease, etc.\n"
            "- Reading nutrition labels\n"
            "- Healthy snacking\n"
            "- Vitamin and mineral needs\n\n"
            "What nutrition question can I help you with?"
        )

    # Default response
    return (
        "I'm your AI health assistant. I can provide general health information on topics like:\n\n"
        "- Blood test results (glucose, cholesterol, vitamins)\n"
        "- Chronic condition management (diabetes, hypertension)\n"
        "- Healthy lifestyle tips (diet, exercise, sleep)\n"
        "- Preventive care recommendations\n\n"
        "**Important:** I provide educational information only and cannot diagnose conditions or prescribe treatment. "
        "Always consult your healthcare provider for medical advice.\n\n"
        "What health topic would you like to learn about?"
    )


def _get_relevant_sources(message: str) -> List[str]:
    """Get relevant health information sources based on message content."""
    sources = []

    message_lower = message.lower()

    if any(word in message_lower for word in ['diabetes', 'glucose', 'blood sugar']):
        sources.extend([
            "American Diabetes Association",
            "CDC Diabetes Prevention Program",
        ])

    if any(word in message_lower for word in ['heart', 'cholesterol', 'blood pressure']):
        sources.extend([
            "American Heart Association",
            "National Heart, Lung, and Blood Institute",
        ])

    if any(word in message_lower for word in ['vitamin', 'nutrition', 'diet']):
        sources.extend([
            "Academy of Nutrition and Dietetics",
            "NIH Office of Dietary Supplements",
        ])

    # Default sources
    if not sources:
        sources = [
            "Mayo Clinic",
            "Cleveland Clinic",
            "National Institutes of Health (NIH)",
        ]

    return sources[:3]  # Limit to top 3 sources


# Export router
__all__ = ["router"]