"""
Embedding Service
Handles text embedding generation for vector storage
Supports open-source models (Sentence Transformers) and OpenAI
"""

from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
import time
import numpy as np

from .config import chroma_config

logger = logging.getLogger(__name__)


class BaseEmbeddingService(ABC):
    """Abstract base class for embedding services"""

    @abstractmethod
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        pass

    @abstractmethod
    def generate_embeddings_batch(self, texts: List[str], batch_size: Optional[int] = None) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        pass

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity score (0-1)
        """
        try:
            v1 = np.array(vec1)
            v2 = np.array(vec2)

            dot_product = np.dot(v1, v2)
            norm_v1 = np.linalg.norm(v1)
            norm_v2 = np.linalg.norm(v2)

            if norm_v1 == 0 or norm_v2 == 0:
                return 0.0

            similarity = dot_product / (norm_v1 * norm_v2)
            return float(similarity)

        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {str(e)}")
            return 0.0


class SentenceTransformerEmbedding(BaseEmbeddingService):
    """Open-source embedding service using Sentence Transformers"""

    def __init__(self, model_name: Optional[str] = None, device: Optional[str] = None):
        """Initialize Sentence Transformer model"""
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers is not installed. "
                "Install it with: pip install sentence-transformers"
            )

        self.model_name = model_name or chroma_config.EMBEDDING_MODEL
        self.device = device or chroma_config.DEVICE
        self.dimension = chroma_config.EMBEDDING_DIMENSION

        logger.info(f"Loading Sentence Transformer model: {self.model_name} on {self.device}")

        try:
            self.model = SentenceTransformer(self.model_name, device=self.device)
            # Verify dimension
            test_embedding = self.model.encode("test", show_progress_bar=False)
            actual_dimension = len(test_embedding)

            if actual_dimension != self.dimension:
                logger.warning(
                    f"Model dimension mismatch: expected {self.dimension}, "
                    f"got {actual_dimension}. Updating config."
                )
                self.dimension = actual_dimension

            logger.info(f"✓ Model loaded successfully (dimension: {self.dimension})")

        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            raise

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Input text to embed

        Returns:
            List of floats representing the embedding vector
        """
        try:
            if not text or not text.strip():
                logger.warning("Empty text provided for embedding")
                return [0.0] * self.dimension

            # Sentence transformers handle long text automatically
            embedding = self.model.encode(
                text,
                convert_to_numpy=True,
                show_progress_bar=False
            )

            logger.debug(f"Generated embedding of dimension {len(embedding)}")
            return embedding.tolist()

        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise

    def generate_embeddings_batch(
        self,
        texts: List[str],
        batch_size: Optional[int] = None
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches

        Args:
            texts: List of texts to embed
            batch_size: Size of each batch (default from config)

        Returns:
            List of embedding vectors
        """
        if batch_size is None:
            batch_size = chroma_config.BATCH_SIZE

        try:
            logger.info(f"Generating embeddings for {len(texts)} texts")

            # Filter out empty texts
            valid_texts = [t if t and t.strip() else " " for t in texts]

            # Generate embeddings (sentence-transformers handles batching internally)
            embeddings = self.model.encode(
                valid_texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=True
            )

            logger.info(f"Successfully generated {len(embeddings)} embeddings")
            return embeddings.tolist()

        except Exception as e:
            logger.error(f"Error generating batch embeddings: {str(e)}")
            raise

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the embedding model"""
        return {
            "provider": "sentence-transformers",
            "model": self.model_name,
            "dimension": self.dimension,
            "device": self.device,
            "max_seq_length": self.model.max_seq_length if hasattr(self.model, 'max_seq_length') else "auto"
        }


class OpenAIEmbedding(BaseEmbeddingService):
    """OpenAI embedding service"""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        """Initialize OpenAI embedding service"""
        try:
            import openai
        except ImportError:
            raise ImportError(
                "openai is not installed. "
                "Install it with: pip install openai"
            )

        self.api_key = api_key or chroma_config.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key is required")

        openai.api_key = self.api_key
        self.model = model_name or chroma_config.EMBEDDING_MODEL
        self.dimension = chroma_config.EMBEDDING_DIMENSION

        logger.info(f"Initialized OpenAI embedding service with model: {self.model}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Input text to embed

        Returns:
            List of floats representing the embedding vector
        """
        try:
            import openai

            if not text or not text.strip():
                logger.warning("Empty text provided for embedding")
                return [0.0] * self.dimension

            # Truncate text if too long (OpenAI limit: ~8191 tokens)
            max_chars = 30000  # Approximate character limit
            if len(text) > max_chars:
                logger.warning(f"Text too long ({len(text)} chars), truncating to {max_chars}")
                text = text[:max_chars]

            response = openai.embeddings.create(
                input=text,
                model=self.model
            )

            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding of dimension {len(embedding)}")

            return embedding

        except Exception as e:
            logger.error(f"Error generating OpenAI embedding: {str(e)}")
            raise

    def generate_embeddings_batch(
        self,
        texts: List[str],
        batch_size: Optional[int] = None
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches

        Args:
            texts: List of texts to embed
            batch_size: Size of each batch (default from config)

        Returns:
            List of embedding vectors
        """
        import openai

        if batch_size is None:
            batch_size = chroma_config.BATCH_SIZE

        embeddings = []
        total_batches = (len(texts) + batch_size - 1) // batch_size

        logger.info(f"Generating embeddings for {len(texts)} texts in {total_batches} batches")

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_num = i // batch_size + 1

            try:
                logger.debug(f"Processing batch {batch_num}/{total_batches}")

                # Filter out empty texts
                valid_texts = [t if t and t.strip() else " " for t in batch]

                response = openai.embeddings.create(
                    input=valid_texts,
                    model=self.model
                )

                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)

                # Rate limiting: sleep between batches
                if i + batch_size < len(texts):
                    time.sleep(0.5)

            except Exception as e:
                logger.error(f"Error processing batch {batch_num}: {str(e)}")
                # Add zero embeddings for failed batch
                embeddings.extend([[0.0] * self.dimension] * len(batch))

        logger.info(f"Successfully generated {len(embeddings)} embeddings")
        return embeddings

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the embedding model"""
        return {
            "provider": "openai",
            "model": self.model,
            "dimension": self.dimension,
            "max_tokens": 8191
        }


def create_embedding_service(
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
    **kwargs
) -> BaseEmbeddingService:
    """
    Factory function to create embedding service based on provider

    Args:
        provider: "sentence-transformers", "huggingface", or "openai"
        model_name: Model name to use
        **kwargs: Additional arguments for the service

    Returns:
        Embedding service instance
    """
    provider = provider or chroma_config.EMBEDDING_PROVIDER

    logger.info(f"Creating embedding service: {provider}")

    if provider == "sentence-transformers" or provider == "huggingface":
        return SentenceTransformerEmbedding(
            model_name=model_name,
            device=kwargs.get('device')
        )
    elif provider == "openai":
        return OpenAIEmbedding(
            api_key=kwargs.get('api_key'),
            model_name=model_name
        )
    else:
        raise ValueError(
            f"Unknown embedding provider: {provider}. "
            f"Supported: sentence-transformers, huggingface, openai"
        )


# Global embedding service instance
_embedding_service: Optional[BaseEmbeddingService] = None


def get_embedding_service() -> BaseEmbeddingService:
    """Get global embedding service instance (singleton)"""
    global _embedding_service

    if _embedding_service is None:
        _embedding_service = create_embedding_service()

    return _embedding_service


def reset_embedding_service():
    """Reset global embedding service (useful for testing)"""
    global _embedding_service
    _embedding_service = None
