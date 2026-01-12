"""
Vector Store Operations
CRUD operations for medical knowledge embeddings in Chroma DB
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
import uuid
from datetime import datetime

from ..client import get_client
from ..embeddings import get_embedding_service
from ..config import chroma_config

logger = logging.getLogger(__name__)


class VectorStoreOperations:
    """Operations for managing medical knowledge vectors"""

    def __init__(self):
        """Initialize vector store operations"""
        self.client = get_client()
        self.embedding_service = get_embedding_service()
        self.collection = self.client.get_or_create_collection()

    def add_document(
        self,
        text: str,
        metadata: Dict[str, Any],
        document_id: Optional[str] = None
    ) -> str:
        """
        Add a single document to the vector store

        Args:
            text: Document text content
            metadata: Document metadata (source, type, etc.)
            document_id: Optional document ID (generated if not provided)

        Returns:
            Document ID
        """
        try:
            if document_id is None:
                document_id = str(uuid.uuid4())

            # Generate embedding
            embedding = self.embedding_service.generate_embedding(text)

            # Add timestamp to metadata
            metadata["indexed_at"] = datetime.utcnow().isoformat()

            # Add to collection
            self.collection.add(
                ids=[document_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata]
            )

            logger.info(f"Added document {document_id} to collection")
            return document_id

        except Exception as e:
            logger.error(f"Error adding document: {str(e)}")
            raise

    def add_documents_batch(
        self,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        document_ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Add multiple documents in batch

        Args:
            texts: List of document texts
            metadatas: List of document metadata
            document_ids: Optional list of document IDs

        Returns:
            List of document IDs
        """
        try:
            if len(texts) != len(metadatas):
                raise ValueError("Texts and metadatas must have same length")

            # Generate IDs if not provided
            if document_ids is None:
                document_ids = [str(uuid.uuid4()) for _ in range(len(texts))]

            # Generate embeddings in batch
            embeddings = self.embedding_service.generate_embeddings_batch(texts)

            # Add timestamp to all metadata
            timestamp = datetime.utcnow().isoformat()
            for metadata in metadatas:
                metadata["indexed_at"] = timestamp

            # Add to collection in batch
            self.collection.add(
                ids=document_ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )

            logger.info(f"Added {len(document_ids)} documents to collection")
            return document_ids

        except Exception as e:
            logger.error(f"Error adding documents batch: {str(e)}")
            raise

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        min_score: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents

        Args:
            query: Search query text
            top_k: Number of results to return
            filters: Metadata filters
            min_score: Minimum relevance score

        Returns:
            List of search results with documents and metadata
        """
        try:
            if top_k is None:
                top_k = chroma_config.DEFAULT_TOP_K

            if min_score is None:
                min_score = chroma_config.MIN_RELEVANCE_SCORE

            # Generate query embedding
            query_embedding = self.embedding_service.generate_embedding(query)

            # Search collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filters
            )

            # Format results
            formatted_results = []
            if results['ids'] and len(results['ids']) > 0:
                for i in range(len(results['ids'][0])):
                    score = 1 - results['distances'][0][i] if results['distances'] else 1.0

                    # Filter by minimum score
                    if score < min_score:
                        continue

                    result = {
                        "id": results['ids'][0][i],
                        "document": results['documents'][0][i] if results['documents'] else None,
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                        "score": score,
                        "distance": results['distances'][0][i] if results['distances'] else 0.0
                    }
                    formatted_results.append(result)

            logger.info(f"Search returned {len(formatted_results)} results above threshold")
            return formatted_results

        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            raise

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific document by ID

        Args:
            document_id: Document ID

        Returns:
            Document data or None if not found
        """
        try:
            result = self.collection.get(
                ids=[document_id],
                include=["documents", "metadatas", "embeddings"]
            )

            if result['ids'] and len(result['ids']) > 0:
                return {
                    "id": result['ids'][0],
                    "document": result['documents'][0] if result['documents'] else None,
                    "metadata": result['metadatas'][0] if result['metadatas'] else {},
                    "embedding": result['embeddings'][0] if result.get('embeddings') else None
                }

            return None

        except Exception as e:
            logger.error(f"Error getting document: {str(e)}")
            raise

    def update_document(
        self,
        document_id: str,
        text: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update a document

        Args:
            document_id: Document ID
            text: New text content (optional)
            metadata: New metadata (optional)

        Returns:
            Success status
        """
        try:
            update_data = {"ids": [document_id]}

            if text is not None:
                # Generate new embedding for updated text
                embedding = self.embedding_service.generate_embedding(text)
                update_data["embeddings"] = [embedding]
                update_data["documents"] = [text]

            if metadata is not None:
                metadata["updated_at"] = datetime.utcnow().isoformat()
                update_data["metadatas"] = [metadata]

            self.collection.update(**update_data)
            logger.info(f"Updated document {document_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating document: {str(e)}")
            raise

    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document

        Args:
            document_id: Document ID

        Returns:
            Success status
        """
        try:
            self.collection.delete(ids=[document_id])
            logger.info(f"Deleted document {document_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            raise

    def delete_documents_batch(self, document_ids: List[str]) -> bool:
        """
        Delete multiple documents

        Args:
            document_ids: List of document IDs

        Returns:
            Success status
        """
        try:
            self.collection.delete(ids=document_ids)
            logger.info(f"Deleted {len(document_ids)} documents")
            return True

        except Exception as e:
            logger.error(f"Error deleting documents batch: {str(e)}")
            raise

    def count_documents(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count documents in collection

        Args:
            filters: Optional metadata filters

        Returns:
            Number of documents
        """
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"Error counting documents: {str(e)}")
            raise

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get collection statistics

        Returns:
            Collection statistics
        """
        try:
            count = self.collection.count()
            metadata = self.collection.metadata

            return {
                "count": count,
                "metadata": metadata,
                "collection_name": self.collection.name
            }

        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            raise

    def clear_collection(self) -> bool:
        """
        Clear all documents from collection (use with caution!)

        Returns:
            Success status
        """
        try:
            # Get all document IDs
            results = self.collection.get()
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                logger.warning(f"Cleared {len(results['ids'])} documents from collection")
            return True

        except Exception as e:
            logger.error(f"Error clearing collection: {str(e)}")
            raise

    def hybrid_search(
        self,
        query: str,
        top_k: Optional[int] = None,
        keyword_filter: Optional[str] = None,
        metadata_filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search (vector + keyword)

        Args:
            query: Search query
            top_k: Number of results
            keyword_filter: Keyword to filter by
            metadata_filters: Metadata filters

        Returns:
            Search results
        """
        try:
            # For now, implement basic vector search
            # Can be enhanced with keyword matching later
            results = self.search(query, top_k, metadata_filters)

            # Apply keyword filter if provided
            if keyword_filter:
                results = [
                    r for r in results
                    if keyword_filter.lower() in r['document'].lower()
                ]

            return results

        except Exception as e:
            logger.error(f"Error in hybrid search: {str(e)}")
            raise


# Global operations instance
vector_operations = VectorStoreOperations()


def get_vector_operations() -> VectorStoreOperations:
    """Get global vector operations instance"""
    return vector_operations
