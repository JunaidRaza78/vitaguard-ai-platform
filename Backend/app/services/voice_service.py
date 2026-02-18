"""
Voice Service
Speech-to-text and text-to-speech functionality for hands-free
health management. Uses browser Web Speech API on the frontend
and provides TTS via gTTS/pyttsx3 on the backend.
"""

import logging
import os
import tempfile
import uuid
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class VoiceService:
    """Service for voice interaction — TTS and STT processing."""

    def __init__(self):
        self._tts_engine = None

    def text_to_speech(self, text: str, language: str = "en") -> Optional[str]:
        """
        Convert text to speech audio file.
        Returns path to generated audio file.
        """
        try:
            from gtts import gTTS

            filename = f"tts_{uuid.uuid4().hex[:8]}.mp3"
            filepath = os.path.join(tempfile.gettempdir(), filename)

            tts = gTTS(text=text, lang=language, slow=False)
            tts.save(filepath)

            logger.info(f"Generated TTS audio: {filepath}")
            return filepath

        except ImportError:
            logger.warning("gTTS not installed (pip install gTTS). Trying pyttsx3...")
            try:
                import pyttsx3

                if not self._tts_engine:
                    self._tts_engine = pyttsx3.init()

                filename = f"tts_{uuid.uuid4().hex[:8]}.mp3"
                filepath = os.path.join(tempfile.gettempdir(), filename)

                self._tts_engine.save_to_file(text, filepath)
                self._tts_engine.runAndWait()

                return filepath

            except ImportError:
                logger.error("Neither gTTS nor pyttsx3 is installed.")
                return None

        except Exception as e:
            logger.error(f"TTS error: {e}")
            return None

    def process_stt_result(self, transcript: str) -> Dict[str, Any]:
        """
        Process a speech-to-text transcript.
        Cleans up the text and detects possible commands.
        """
        cleaned = transcript.strip()
        if not cleaned:
            return {"text": "", "type": "empty", "command": None}

        # Detect voice commands
        commands = {
            "record vitals": "navigate_vitals",
            "check emergency": "emergency_check",
            "show dashboard": "navigate_dashboard",
            "medication reminder": "navigate_medications",
            "lab report": "navigate_labs",
        }

        lower = cleaned.lower()
        for trigger, cmd in commands.items():
            if trigger in lower:
                return {
                    "text": cleaned,
                    "type": "command",
                    "command": cmd,
                    "trigger": trigger,
                }

        return {"text": cleaned, "type": "message", "command": None}

    def get_tts_for_response(self, response: str, max_length: int = 500) -> Optional[str]:
        """
        Generate TTS for an AI response.
        Truncates long responses for reasonable audio length.
        """
        text = response[:max_length]
        if len(response) > max_length:
            text += "... For the full response, please read the text on screen."
        return self.text_to_speech(text)


# Singleton
voice_service = VoiceService()
