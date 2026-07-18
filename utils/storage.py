"""
Unified upload storage. Uses S3 when AWS_S3_BUCKET is configured, otherwise
falls back to Django's local FileSystemStorage (MEDIA_ROOT) so media works
in development without AWS.
"""
from django.core.files.storage import default_storage

from .s3 import (
    delete_file_from_s3,
    download_bytes_from_s3,
    generate_presigned_url,
    s3_configured,
    upload_file_to_s3,
)


def store_upload(file_obj, key: str, content_type='application/octet-stream') -> str:
    """Persist an uploaded file. Returns the storage key actually used."""
    if s3_configured():
        upload_file_to_s3(file_obj, key, content_type)
        return key
    return default_storage.save(key, file_obj)


def media_url(key: str):
    if not key:
        return None
    if s3_configured():
        return generate_presigned_url(key)
    return default_storage.url(key)


def get_upload_bytes(key: str) -> bytes | None:
    """Fetch raw bytes for a stored upload, regardless of backend. Returns None
    if the key is missing or unreadable — callers should treat this as optional."""
    if not key:
        return None
    try:
        if s3_configured():
            return download_bytes_from_s3(key)
        if default_storage.exists(key):
            with default_storage.open(key, 'rb') as f:
                return f.read()
    except Exception:  # noqa: BLE001 — best-effort fetch, never raise
        pass
    return None


def delete_upload(key: str) -> bool:
    if not key:
        return False
    if s3_configured():
        return delete_file_from_s3(key)
    if default_storage.exists(key):
        default_storage.delete(key)
        return True
    return False
