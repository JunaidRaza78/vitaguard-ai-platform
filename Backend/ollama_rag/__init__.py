"""
Ollama RAG Module
Agentic RAG Pipeline with Ollama LLM (DeepSeek-R1:8B) Integration
"""

from .ollama_client import OllamaClient, OllamaConfig, get_ollama_client
from .rag_chatbot import MedicalRAGChatbot, get_chatbot

__all__ = [
    "OllamaClient",
    "OllamaConfig",
    "get_ollama_client",
    "MedicalRAGChatbot",
    "get_chatbot"
]
