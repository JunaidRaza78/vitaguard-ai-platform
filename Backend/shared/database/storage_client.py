"""
Azure Storage Client for Blob Storage (Buckets)
Provides async blob storage operations for documents, conversations, and file uploads
"""

from azure.storage.blob.aio import BlobServiceClient, ContainerClient, BlobClient
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from typing import Optional, List, Dict, Any, Union, AsyncIterator
import json
import logging
from datetime import datetime, timedelta
from io import BytesIO

logger = logging.getLogger(__name__)


class StorageClient:
    """
    Async Azure Storage client for blob/bucket operations.
    Implements singleton pattern for shared client across application.
    """

    _instance: Optional['StorageClient'] = None
    _service_client: Optional[BlobServiceClient] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def connect(
        self,
        connection_string: str,
        **kwargs
    ) -> None:
        """
        Initialize Azure Storage Blob Service Client.

        Args:
            connection_string: Azure Storage connection string
        """
        if self._service_client is not None:
            logger.warning("Storage client already exists. Skipping connection.")
            return

        try:
            self._service_client = BlobServiceClient.from_connection_string(
                connection_string,
                **kwargs
            )
            logger.info("Azure Storage client created successfully")
        except Exception as e:
            logger.error(f"Failed to create Storage client: {e}")
            raise

    async def disconnect(self) -> None:
        """Close Azure Storage client."""
        if self._service_client is not None:
            await self._service_client.close()
            self._service_client = None
            logger.info("Azure Storage client closed")

    def _ensure_connected(self) -> None:
        """Ensure Storage client is connected."""
        if self._service_client is None:
            raise RuntimeError("Storage client not initialized. Call connect() first.")

    def get_container_client(self, container_name: str) -> ContainerClient:
        """
        Get container client for a specific bucket.

        Args:
            container_name: Name of the container/bucket

        Returns:
            ContainerClient instance
        """
        self._ensure_connected()
        return self._service_client.get_container_client(container_name)

    def get_blob_client(self, container_name: str, blob_name: str) -> BlobClient:
        """
        Get blob client for a specific file.

        Args:
            container_name: Name of the container/bucket
            blob_name: Name of the blob/file

        Returns:
            BlobClient instance
        """
        self._ensure_connected()
        return self._service_client.get_blob_client(
            container=container_name,
            blob=blob_name
        )

    # ==========================================
    # BLOB OPERATIONS
    # ==========================================

    async def upload_blob(
        self,
        container_name: str,
        blob_name: str,
        data: Union[bytes, str, BytesIO],
        metadata: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None,
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        Upload a blob to storage.

        Args:
            container_name: Container name
            blob_name: Blob name (path/filename)
            data: Data to upload (bytes, string, or file-like object)
            metadata: Custom metadata key-value pairs
            content_type: Content type (e.g., "application/json")
            overwrite: Overwrite if exists

        Returns:
            Blob properties
        """
        blob_client = self.get_blob_client(container_name, blob_name)

        # Add timestamp to metadata
        if metadata is None:
            metadata = {}
        metadata["uploaded_at"] = datetime.utcnow().isoformat()

        try:
            await blob_client.upload_blob(
                data,
                metadata=metadata,
                content_settings={"content_type": content_type} if content_type else None,
                overwrite=overwrite
            )

            properties = await blob_client.get_blob_properties()

            return {
                "name": blob_name,
                "container": container_name,
                "size": properties.size,
                "content_type": properties.content_settings.content_type,
                "created_on": properties.creation_time,
                "last_modified": properties.last_modified,
                "etag": properties.etag,
                "metadata": properties.metadata
            }
        except ResourceExistsError:
            if not overwrite:
                logger.error(f"Blob {blob_name} already exists in {container_name}")
                raise
        except Exception as e:
            logger.error(f"Failed to upload blob {blob_name}: {e}")
            raise

    async def upload_json(
        self,
        container_name: str,
        blob_name: str,
        data: Any,
        metadata: Optional[Dict[str, str]] = None,
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        Upload JSON data to storage.

        Args:
            container_name: Container name
            blob_name: Blob name
            data: Data to serialize as JSON
            metadata: Custom metadata
            overwrite: Overwrite if exists

        Returns:
            Blob properties
        """
        try:
            json_data = json.dumps(data, indent=2)
            return await self.upload_blob(
                container_name,
                blob_name,
                json_data.encode('utf-8'),
                metadata=metadata,
                content_type="application/json",
                overwrite=overwrite
            )
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize JSON for {blob_name}: {e}")
            raise

    async def download_blob(
        self,
        container_name: str,
        blob_name: str
    ) -> bytes:
        """
        Download blob as bytes.

        Args:
            container_name: Container name
            blob_name: Blob name

        Returns:
            Blob data as bytes
        """
        blob_client = self.get_blob_client(container_name, blob_name)

        try:
            downloader = await blob_client.download_blob()
            return await downloader.readall()
        except ResourceNotFoundError:
            logger.error(f"Blob {blob_name} not found in {container_name}")
            return None
        except Exception as e:
            logger.error(f"Failed to download blob {blob_name}: {e}")
            raise

    async def download_json(
        self,
        container_name: str,
        blob_name: str
    ) -> Optional[Any]:
        """
        Download and parse JSON blob.

        Args:
            container_name: Container name
            blob_name: Blob name

        Returns:
            Parsed JSON data or None
        """
        data = await self.download_blob(container_name, blob_name)
        if data is None:
            return None

        try:
            return json.loads(data.decode('utf-8'))
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from {blob_name}: {e}")
            return None

    async def download_to_stream(
        self,
        container_name: str,
        blob_name: str,
        stream: BytesIO
    ) -> int:
        """
        Download blob to a stream.

        Args:
            container_name: Container name
            blob_name: Blob name
            stream: Stream to write to

        Returns:
            Number of bytes downloaded
        """
        blob_client = self.get_blob_client(container_name, blob_name)

        try:
            downloader = await blob_client.download_blob()
            return await downloader.readinto(stream)
        except Exception as e:
            logger.error(f"Failed to download blob {blob_name} to stream: {e}")
            raise

    async def delete_blob(
        self,
        container_name: str,
        blob_name: str
    ) -> bool:
        """
        Delete a blob.

        Args:
            container_name: Container name
            blob_name: Blob name

        Returns:
            True if deleted, False if not found
        """
        blob_client = self.get_blob_client(container_name, blob_name)

        try:
            await blob_client.delete_blob()
            return True
        except ResourceNotFoundError:
            logger.warning(f"Blob {blob_name} not found in {container_name}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete blob {blob_name}: {e}")
            raise

    async def blob_exists(
        self,
        container_name: str,
        blob_name: str
    ) -> bool:
        """
        Check if blob exists.

        Args:
            container_name: Container name
            blob_name: Blob name

        Returns:
            True if exists
        """
        blob_client = self.get_blob_client(container_name, blob_name)

        try:
            await blob_client.get_blob_properties()
            return True
        except ResourceNotFoundError:
            return False

    async def get_blob_properties(
        self,
        container_name: str,
        blob_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get blob properties and metadata.

        Args:
            container_name: Container name
            blob_name: Blob name

        Returns:
            Blob properties or None
        """
        blob_client = self.get_blob_client(container_name, blob_name)

        try:
            properties = await blob_client.get_blob_properties()
            return {
                "name": blob_name,
                "container": container_name,
                "size": properties.size,
                "content_type": properties.content_settings.content_type,
                "created_on": properties.creation_time,
                "last_modified": properties.last_modified,
                "etag": properties.etag,
                "metadata": properties.metadata
            }
        except ResourceNotFoundError:
            return None

    async def list_blobs(
        self,
        container_name: str,
        prefix: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        List blobs in a container.

        Args:
            container_name: Container name
            prefix: Filter by prefix (e.g., "folder/")
            limit: Maximum number of blobs to return

        Returns:
            List of blob properties
        """
        container_client = self.get_container_client(container_name)

        blobs = []
        count = 0

        try:
            async for blob in container_client.list_blobs(name_starts_with=prefix):
                blobs.append({
                    "name": blob.name,
                    "size": blob.size,
                    "content_type": blob.content_settings.content_type,
                    "created_on": blob.creation_time,
                    "last_modified": blob.last_modified,
                    "metadata": blob.metadata
                })

                count += 1
                if limit and count >= limit:
                    break

            return blobs
        except Exception as e:
            logger.error(f"Failed to list blobs in {container_name}: {e}")
            raise

    async def generate_sas_url(
        self,
        container_name: str,
        blob_name: str,
        expiry_hours: int = 1,
        permissions: str = "r"
    ) -> str:
        """
        Generate a SAS URL for temporary blob access.

        Args:
            container_name: Container name
            blob_name: Blob name
            expiry_hours: Hours until expiration
            permissions: Permissions (r=read, w=write, d=delete)

        Returns:
            SAS URL
        """
        from azure.storage.blob import generate_blob_sas, BlobSasPermissions

        blob_client = self.get_blob_client(container_name, blob_name)

        sas_token = generate_blob_sas(
            account_name=blob_client.account_name,
            container_name=container_name,
            blob_name=blob_name,
            account_key=self._service_client.credential.account_key,
            permission=BlobSasPermissions(read="r" in permissions),
            expiry=datetime.utcnow() + timedelta(hours=expiry_hours)
        )

        return f"{blob_client.url}?{sas_token}"

    # ==========================================
    # HELPER METHODS FOR COMMON USE CASES
    # ==========================================

    async def save_conversation(
        self,
        conversation_id: str,
        conversation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Save conversation to storage.

        Args:
            conversation_id: Conversation ID
            conversation_data: Conversation data

        Returns:
            Blob properties
        """
        blob_name = f"{conversation_id}/conversation.json"
        return await self.upload_json(
            "conversations",
            blob_name,
            conversation_data,
            metadata={"conversation_id": conversation_id},
            overwrite=True
        )

    async def get_conversation(
        self,
        conversation_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get conversation from storage.

        Args:
            conversation_id: Conversation ID

        Returns:
            Conversation data or None
        """
        blob_name = f"{conversation_id}/conversation.json"
        return await self.download_json("conversations", blob_name)

    async def save_chat_message(
        self,
        conversation_id: str,
        message_id: str,
        message_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Save chat message to storage.

        Args:
            conversation_id: Conversation ID
            message_id: Message ID
            message_data: Message data

        Returns:
            Blob properties
        """
        blob_name = f"{conversation_id}/{message_id}.json"
        return await self.upload_json(
            "chat-messages",
            blob_name,
            message_data,
            metadata={
                "conversation_id": conversation_id,
                "message_id": message_id
            },
            overwrite=False
        )

    async def get_conversation_messages(
        self,
        conversation_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all messages for a conversation.

        Args:
            conversation_id: Conversation ID
            limit: Maximum messages to return

        Returns:
            List of messages
        """
        blobs = await self.list_blobs(
            "chat-messages",
            prefix=f"{conversation_id}/",
            limit=limit
        )

        messages = []
        for blob in blobs:
            message_data = await self.download_json("chat-messages", blob["name"])
            if message_data:
                messages.append(message_data)

        return messages

    async def check_connection(self) -> bool:
        """
        Check if storage connection is healthy.

        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            if self._service_client is None:
                return False

            # Try to list containers (lightweight operation)
            async for _ in self._service_client.list_containers(max_results=1):
                break

            return True
        except Exception as e:
            logger.error(f"Storage health check failed: {e}")
            return False

    def is_connected(self) -> bool:
        """Check if client is initialized."""
        return self._service_client is not None


# Global instance
storage_client = StorageClient()


# Helper functions for common operations
async def init_storage(
    connection_string: str,
    **kwargs
) -> StorageClient:
    """
    Initialize Storage client with environment configuration.

    Args:
        connection_string: Azure Storage connection string
        **kwargs: Additional client configuration

    Returns:
        StorageClient instance
    """
    await storage_client.connect(
        connection_string=connection_string,
        **kwargs
    )
    return storage_client


async def close_storage() -> None:
    """Close Storage client."""
    await storage_client.disconnect()
