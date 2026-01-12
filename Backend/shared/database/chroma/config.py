"""
Chroma DB Configuration
Handles vector database configuration for medical knowledge embeddings
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class ChromaConfig(BaseSettings):
    """Chroma database configuration"""

    # Connection settings
    CHROMA_HOST: str = Field(default="localhost", env="CHROMA_HOST")
    CHROMA_PORT: int = Field(default=8000, env="CHROMA_PORT")
    CHROMA_PERSIST_DIRECTORY: str = Field(
        default="./chroma_data",
        env="CHROMA_PERSIST_DIRECTORY"
    )

    # Client settings
    CHROMA_CLIENT_TYPE: str = Field(
        default="persistent",  # "persistent" or "http"
        env="CHROMA_CLIENT_TYPE"
    )

    # Collection settings
    CHROMA_COLLECTION_NAME: str = Field(
        default="medical_knowledge",
        env="CHROMA_COLLECTION_NAME"
    )

    # Embedding settings
    EMBEDDING_PROVIDER: str = Field(
        default="sentence-transformers",  # "sentence-transformers", "huggingface", or "openai"
        env="EMBEDDING_PROVIDER"
    )

    # Open-source models (Sentence Transformers / HuggingFace)
    EMBEDDING_MODEL: str = Field(
        default="all-MiniLM-L6-v2",  # Popular open-source model
        env="EMBEDDING_MODEL"
    )
    EMBEDDING_DIMENSION: int = Field(default=384, env="EMBEDDING_DIMENSION")  # for all-MiniLM-L6-v2

    # Alternative models:
    # - "all-MiniLM-L6-v2": 384 dimensions, fast and efficient
    # - "all-mpnet-base-v2": 768 dimensions, higher quality
    # - "multi-qa-MiniLM-L6-cos-v1": 384 dimensions, optimized for Q&A
    # - "paraphrase-multilingual-MiniLM-L12-v2": 384 dimensions, multilingual
    # - "msmarco-MiniLM-L-6-v3": 384 dimensions, optimized for search

    # OpenAI settings (optional, only if EMBEDDING_PROVIDER="openai")
    OPENAI_API_KEY: str = Field(default="", env="OPENAI_API_KEY")

    # Model device
    DEVICE: str = Field(default="cpu", env="DEVICE")  # "cpu" or "cuda"

    # Chunking settings
    CHUNK_SIZE: int = Field(default=1000, env="CHUNK_SIZE")
    CHUNK_OVERLAP: int = Field(default=100, env="CHUNK_OVERLAP")

    # Retrieval settings
    DEFAULT_TOP_K: int = Field(default=5, env="DEFAULT_TOP_K")
    MIN_RELEVANCE_SCORE: float = Field(default=0.7, env="MIN_RELEVANCE_SCORE")

    # Performance settings
    BATCH_SIZE: int = Field(default=32, env="BATCH_SIZE")
    MAX_RETRIES: int = Field(default=3, env="MAX_RETRIES")
    TIMEOUT: int = Field(default=30, env="TIMEOUT")

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def connection_string(self) -> str:
        """Get Chroma connection string"""
        if self.CHROMA_CLIENT_TYPE == "http":
            return f"http://{self.CHROMA_HOST}:{self.CHROMA_PORT}"
        return self.CHROMA_PERSIST_DIRECTORY

    def get_collection_metadata(self) -> dict:
        """Get collection metadata"""
        return {
            "embedding_provider": self.EMBEDDING_PROVIDER,
            "embedding_model": self.EMBEDDING_MODEL,
            "embedding_dimension": self.EMBEDDING_DIMENSION,
            "chunk_size": self.CHUNK_SIZE,
            "chunk_overlap": self.CHUNK_OVERLAP,
            "description": "Medical knowledge base for RAG-based chatbot"
        }

    def get_model_config(self) -> dict:
        """Get model configuration"""
        config = {
            "provider": self.EMBEDDING_PROVIDER,
            "model": self.EMBEDDING_MODEL,
            "dimension": self.EMBEDDING_DIMENSION,
            "device": self.DEVICE,
            "batch_size": self.BATCH_SIZE
        }

        if self.EMBEDDING_PROVIDER == "openai":
            config["api_key"] = self.OPENAI_API_KEY

        return config


# Global configuration instance
chroma_config = ChromaConfig()
