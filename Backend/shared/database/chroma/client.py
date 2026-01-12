"""
Chroma DB Client
Manages connection to Chroma vector database
"""

import chromadb
from chromadb.config import Settings
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection
from typing import Optional, List, Dict, Any
import logging
from contextlib import contextmanager

from .config import chroma_config

logger = logging.getLogger(__name__)


class ChromaClient:
    """Singleton Chroma database client"""

    _instance: Optional['ChromaClient'] = None
    _client: Optional[ClientAPI] = None
    _collection: Optional[Collection] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ChromaClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize Chroma client"""
        if self._client is None:
            self.connect()

    def connect(self) -> None:
        """Establish connection to Chroma database"""
        try:
            if chroma_config.CHROMA_CLIENT_TYPE == "http":
                # HTTP client for remote Chroma server
                logger.info(f"Connecting to Chroma server at {chroma_config.CHROMA_HOST}:{chroma_config.CHROMA_PORT}")
                self._client = chromadb.HttpClient(
                    host=chroma_config.CHROMA_HOST,
                    port=chroma_config.CHROMA_PORT,
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
            else:
                # Persistent client for local storage
                logger.info(f"Using persistent Chroma client at {chroma_config.CHROMA_PERSIST_DIRECTORY}")
                self._client = chromadb.PersistentClient(
                    path=chroma_config.CHROMA_PERSIST_DIRECTORY,
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )

            logger.info("Successfully connected to Chroma DB")

        except Exception as e:
            logger.error(f"Failed to connect to Chroma DB: {str(e)}")
            raise

    def get_or_create_collection(
        self,
        collection_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Collection:
        """Get or create a collection"""
        try:
            if collection_name is None:
                collection_name = chroma_config.CHROMA_COLLECTION_NAME

            if metadata is None:
                metadata = chroma_config.get_collection_metadata()

            logger.info(f"Getting or creating collection: {collection_name}")
            self._collection = self._client.get_or_create_collection(
                name=collection_name,
                metadata=metadata
            )

            return self._collection

        except Exception as e:
            logger.error(f"Failed to get or create collection: {str(e)}")
            raise

    def get_collection(self, collection_name: Optional[str] = None) -> Collection:
        """Get existing collection"""
        try:
            if collection_name is None:
                collection_name = chroma_config.CHROMA_COLLECTION_NAME

            logger.info(f"Getting collection: {collection_name}")
            return self._client.get_collection(name=collection_name)

        except Exception as e:
            logger.error(f"Failed to get collection: {str(e)}")
            raise

    def list_collections(self) -> List[Collection]:
        """List all collections"""
        try:
            return self._client.list_collections()
        except Exception as e:
            logger.error(f"Failed to list collections: {str(e)}")
            raise

    def delete_collection(self, collection_name: str) -> None:
        """Delete a collection"""
        try:
            logger.warning(f"Deleting collection: {collection_name}")
            self._client.delete_collection(name=collection_name)
            logger.info(f"Successfully deleted collection: {collection_name}")
        except Exception as e:
            logger.error(f"Failed to delete collection: {str(e)}")
            raise

    def reset(self) -> None:
        """Reset the database (delete all data)"""
        try:
            logger.warning("Resetting Chroma database - ALL DATA WILL BE DELETED")
            self._client.reset()
            logger.info("Successfully reset Chroma database")
        except Exception as e:
            logger.error(f"Failed to reset database: {str(e)}")
            raise

    def get_version(self) -> str:
        """Get Chroma version"""
        try:
            return self._client.get_version()
        except Exception as e:
            logger.error(f"Failed to get version: {str(e)}")
            raise

    def heartbeat(self) -> int:
        """Check if connection is alive"""
        try:
            return self._client.heartbeat()
        except Exception as e:
            logger.error(f"Heartbeat failed: {str(e)}")
            raise

    def disconnect(self) -> None:
        """Close connection to Chroma database"""
        try:
            if self._client is not None:
                # Chroma client doesn't have explicit close method
                self._client = None
                self._collection = None
                logger.info("Disconnected from Chroma DB")
        except Exception as e:
            logger.error(f"Error during disconnect: {str(e)}")
            raise

    @property
    def client(self) -> ClientAPI:
        """Get the Chroma client instance"""
        if self._client is None:
            self.connect()
        return self._client

    @property
    def collection(self) -> Collection:
        """Get the default collection"""
        if self._collection is None:
            self._collection = self.get_or_create_collection()
        return self._collection


# Global client instance
chroma_client = ChromaClient()


@contextmanager
def get_chroma_client():
    """Context manager for Chroma client"""
    client = None
    try:
        client = ChromaClient()
        yield client
    except Exception as e:
        logger.error(f"Error in Chroma client context: {str(e)}")
        raise
    finally:
        if client:
            # Cleanup if needed
            pass


def get_client() -> ChromaClient:
    """Get global Chroma client instance"""
    return chroma_client
