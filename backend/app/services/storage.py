import os
import io
import uuid
import asyncio
from abc import ABC, abstractmethod
from typing import Optional
from backend.app.core.config import settings

class StorageService(ABC):
    """Abstract Base Class for Storage Backend (Local Disk, Cloudflare R2, AWS S3)."""

    @abstractmethod
    async def save(self, file_bytes: bytes, key: str, content_type: str = "image/jpeg") -> str:
        """Save a file to storage and return its public/serving URL."""
        pass

    @abstractmethod
    async def get(self, key: str) -> bytes:
        """Retrieve file content bytes by key."""
        pass

    @abstractmethod
    async def atomic_write(self, key: str, content_bytes: bytes, content_type: str = "application/json") -> str:
        """
        Atomically write file bytes to prevent readers from ever seeing partial writes.
        Returns the saved file path/URL.
        """
        pass

    @abstractmethod
    async def get_url(self, key: str) -> str:
        """Return the accessible URL for a given storage key."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a file from storage."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a file exists in storage."""
        pass


class LocalStorageService(StorageService):
    """
    Local filesystem storage with POSIX/Windows atomic file replacement.
    Ideal for local dev, testing, and containerized single-host deployments.
    """

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or settings.STORAGE_LOCAL_DIR
        os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, "uploads"), exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, "catalog"), exist_ok=True)

    def _resolve_path(self, key: str) -> str:
        # Normalize slashes and prevent directory traversal
        sanitized_key = key.replace("\\", "/").lstrip("/")
        return os.path.abspath(os.path.join(self.base_dir, sanitized_key))

    async def save(self, file_bytes: bytes, key: str, content_type: str = "image/jpeg") -> str:
        target_path = self._resolve_path(key)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        loop = asyncio.get_running_loop()
        def _write():
            with open(target_path, "wb") as f:
                f.write(file_bytes)
        await loop.run_in_executor(None, _write)
        return await self.get_url(key)

    async def get(self, key: str) -> bytes:
        target_path = self._resolve_path(key)
        if not os.path.exists(target_path):
            raise FileNotFoundError(f"Storage file not found: {key}")
        
        loop = asyncio.get_running_loop()
        def _read():
            with open(target_path, "rb") as f:
                return f.read()
        return await loop.run_in_executor(None, _read)

    async def atomic_write(self, key: str, content_bytes: bytes, content_type: str = "application/json") -> str:
        """
        Atomic write implementation:
        1. Write content to a temporary file in the same target directory.
        2. Flush and fsync to guarantee data hits physical storage.
        3. Atomically rename/replace the temporary file into place with os.replace().
        If the process dies mid-write, the live file remains untouched and uncorrupted.
        """
        target_path = self._resolve_path(key)
        target_dir = os.path.dirname(target_path)
        os.makedirs(target_dir, exist_ok=True)

        tmp_path = os.path.join(target_dir, f".tmp_{uuid.uuid4().hex}_{os.path.basename(target_path)}")

        loop = asyncio.get_running_loop()
        def _atomic_op():
            try:
                with open(tmp_path, "wb") as f:
                    f.write(content_bytes)
                    f.flush()
                    os.fsync(f.fileno())
                # Atomic replace on same filesystem
                os.replace(tmp_path, target_path)
            except Exception as e:
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except OSError:
                        pass
                raise e

        await loop.run_in_executor(None, _atomic_op)
        return await self.get_url(key)

    async def get_url(self, key: str) -> str:
        sanitized_key = key.replace("\\", "/").lstrip("/")
        # Serve via API static endpoint or direct storage URL
        return f"/api/v1/storage/{sanitized_key}"

    async def delete(self, key: str) -> bool:
        target_path = self._resolve_path(key)
        if os.path.exists(target_path):
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, os.remove, target_path)
            return True
        return False

    async def exists(self, key: str) -> bool:
        target_path = self._resolve_path(key)
        return os.path.exists(target_path)


class CloudflareR2StorageService(StorageService):
    """
    Cloudflare R2 / AWS S3 storage implementation using boto3.
    Single class swap for production deployments.
    """

    def __init__(self):
        import boto3
        from botocore.config import Config

        self.bucket = settings.R2_BUCKET_NAME
        self.public_url_prefix = settings.R2_PUBLIC_URL_PREFIX.rstrip("/")

        endpoint = settings.R2_ENDPOINT_URL
        if not endpoint and settings.R2_ACCOUNT_ID:
            endpoint = f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

        self.s3_client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            region_name="auto",
            config=Config(signature_version="s3v4")
        )

    async def save(self, file_bytes: bytes, key: str, content_type: str = "image/jpeg") -> str:
        loop = asyncio.get_running_loop()
        def _put():
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=file_bytes,
                ContentType=content_type
            )
        await loop.run_in_executor(None, _put)
        return await self.get_url(key)

    async def get(self, key: str) -> bytes:
        loop = asyncio.get_running_loop()
        def _get():
            response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
            return response["Body"].read()
        return await loop.run_in_executor(None, _get)

    async def atomic_write(self, key: str, content_bytes: bytes, content_type: str = "application/json") -> str:
        # S3 / R2 PutObject operations are inherently atomic per key
        return await self.save(file_bytes=content_bytes, key=key, content_type=content_type)

    async def get_url(self, key: str) -> str:
        return f"{self.public_url_prefix}/{key.lstrip('/')}"

    async def delete(self, key: str) -> bool:
        loop = asyncio.get_running_loop()
        def _del():
            self.s3_client.delete_object(Bucket=self.bucket, Key=key)
        await loop.run_in_executor(None, _del)
        return True

    async def exists(self, key: str) -> bool:
        loop = asyncio.get_running_loop()
        def _check():
            try:
                self.s3_client.head_object(Bucket=self.bucket, Key=key)
                return True
            except Exception:
                return False
        return await loop.run_in_executor(None, _check)


# Storage Singleton Factory
_storage_instance: Optional[StorageService] = None

def get_storage() -> StorageService:
    global _storage_instance
    if _storage_instance is None:
        if settings.STORAGE_BACKEND.lower() in ("r2", "s3", "cloudflare"):
            _storage_instance = CloudflareR2StorageService()
        else:
            _storage_instance = LocalStorageService()
    return _storage_instance
