"""
Ollama Client for DeepSeek-R1:8B Model Integration
Production-ready for Medical RAG systems
"""

import httpx
import json
import logging
import os
import time
import uuid
from typing import Generator, Optional
from dataclasses import dataclass, field

# -------------------------------------------------------------------
# Logging
# -------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# Constants
# -------------------------------------------------------------------
MAX_PROMPT_CHARS = 8000
MAX_CHAT_MESSAGES = 10

DEFAULT_MEDICAL_SYSTEM_PROMPT = """
You are a medical information assistant.
Do NOT provide diagnosis, prescriptions, or treatment plans.
Information is for educational purposes only.
Always advise consulting a licensed healthcare professional.
"""

# -------------------------------------------------------------------
# Config
# -------------------------------------------------------------------
@dataclass
class OllamaConfig:
    base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model: str = "deepseek-r1:8b"

    timeout: httpx.Timeout = field(default_factory=lambda: httpx.Timeout(
        connect=5.0,
        read=120.0,
        write=120.0,
        pool=5.0,
    ))

    default_temperature: float = 0.3
    default_max_tokens: int = 1000

    max_retries: int = 3
    retry_base_delay: float = 1.0
    retry_max_delay: float = 10.0


# -------------------------------------------------------------------
# Client
# -------------------------------------------------------------------
class OllamaClient:
    def __init__(self, config: Optional[OllamaConfig] = None):
        self.config = config or OllamaConfig()
        self.client = httpx.Client(timeout=self.config.timeout)
        self.async_client: Optional[httpx.AsyncClient] = None

        logger.info(f"OllamaClient initialized | model={self.config.model}")

    # -------------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------------
    def _truncate_prompt(self, prompt: str) -> str:
        return prompt[-MAX_PROMPT_CHARS:] if len(prompt) > MAX_PROMPT_CHARS else prompt

    def _truncate_messages(self, messages: list[dict]) -> list[dict]:
        return messages[-MAX_CHAT_MESSAGES:]

    def _retry_with_backoff(self, func, *args, **kwargs):
        last_exception = None

        for attempt in range(self.config.max_retries):
            try:
                return func(*args, **kwargs)
            except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError) as e:
                last_exception = e
                delay = min(
                    self.config.retry_base_delay * (2 ** attempt),
                    self.config.retry_max_delay
                )
                logger.warning(
                    f"Retry {attempt + 1}/{self.config.max_retries} failed. Retrying in {delay}s"
                )
                time.sleep(delay)

        raise last_exception

    async def _get_async_client(self) -> httpx.AsyncClient:
        if self.async_client is None:
            self.async_client = httpx.AsyncClient(timeout=self.config.timeout)
        return self.async_client

    # -------------------------------------------------------------------
    # Generate
    # -------------------------------------------------------------------
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ):
        prompt = self._truncate_prompt(prompt)

        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature or self.config.default_temperature,
                "num_predict": max_tokens or self.config.default_max_tokens,
                "stop": ["###", "</s>"],
            },
            "system": system_prompt or DEFAULT_MEDICAL_SYSTEM_PROMPT,
        }

        url = f"{self.config.base_url}/api/generate"

        if stream:
            return self._retry_with_backoff(self._stream_response, url, payload)

        return self._retry_with_backoff(self._sync_response, url, payload)

    def _sync_response(self, url: str, payload: dict) -> str:
        request_id = str(uuid.uuid4())
        logger.info(f"[{request_id}] Sending generate request")

        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response.json().get("response", "")

    def _stream_response(self, url: str, payload: dict) -> Generator[str, None, None]:
        request_id = str(uuid.uuid4())
        logger.info(f"[{request_id}] Streaming generate request")

        with self.client.stream("POST", url, json=payload) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line or not line.startswith(b"{"):
                    continue
                data = json.loads(line)
                if token := data.get("response"):
                    yield token
                if data.get("done"):
                    break

    # -------------------------------------------------------------------
    # Chat
    # -------------------------------------------------------------------
    def chat(
        self,
        messages: list[dict],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ):
        messages = self._truncate_messages(messages)

        payload = {
            "model": self.config.model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature or self.config.default_temperature,
                "num_predict": max_tokens or self.config.default_max_tokens,
                "stop": ["###", "</s>"],
            },
        }

        url = f"{self.config.base_url}/api/chat"

        if stream:
            return self._retry_with_backoff(self._stream_chat_response, url, payload)

        return self._retry_with_backoff(self._sync_chat_response, url, payload)

    def _sync_chat_response(self, url: str, payload: dict) -> str:
        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return response.json().get("message", {}).get("content", "")

    def _stream_chat_response(self, url: str, payload: dict) -> Generator[str, None, None]:
        with self.client.stream("POST", url, json=payload) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line or not line.startswith(b"{"):
                    continue
                data = json.loads(line)
                token = data.get("message", {}).get("content")
                if token:
                    yield token
                if data.get("done"):
                    break

    # -------------------------------------------------------------------
    # Async Generate
    # -------------------------------------------------------------------
    async def agenerate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        prompt = self._truncate_prompt(prompt)

        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature or self.config.default_temperature,
                "num_predict": max_tokens or self.config.default_max_tokens,
            },
            "system": system_prompt or DEFAULT_MEDICAL_SYSTEM_PROMPT,
        }

        client = await self._get_async_client()
        response = await client.post(f"{self.config.base_url}/api/generate", json=payload)
        response.raise_for_status()
        return response.json().get("response", "")

    # -------------------------------------------------------------------
    # Health / Cleanup
    # -------------------------------------------------------------------
    def health_check(self) -> bool:
        try:
            return self.client.get(f"{self.config.base_url}/api/tags").status_code == 200
        except Exception:
            return False

    def close(self):
        self.client.close()

    async def aclose(self):
        if self.async_client:
            await self.async_client.aclose()


# -------------------------------------------------------------------
# Singleton
# -------------------------------------------------------------------
_ollama_client: Optional[OllamaClient] = None


def get_ollama_client() -> OllamaClient:
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client
