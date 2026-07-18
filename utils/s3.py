"""
S3 helpers. boto3 client is created lazily so the app runs fine without AWS
configured (e.g. during local dev). Callers should handle the case where
AWS_S3_BUCKET is empty.
"""
import io
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

_client = None


def _s3():
    global _client
    if _client is None:
        import boto3
        _client = boto3.client(
            's3',
            region_name=settings.AWS_S3_BUCKET_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
        )
    return _client


def s3_configured() -> bool:
    return bool(settings.AWS_S3_BUCKET)


def upload_file_to_s3(file_obj, s3_key: str,
                      content_type: str = 'application/octet-stream') -> str:
    _s3().upload_fileobj(
        file_obj, settings.AWS_S3_BUCKET, s3_key,
        ExtraArgs={
            'ContentType': content_type,
            'ServerSideEncryption': 'AES256',  # CJIS: encrypt at rest
        },
    )
    logger.info('Uploaded to S3: %s', s3_key)
    return s3_key


def upload_bytes_to_s3(data: bytes, s3_key: str,
                       content_type: str = 'application/octet-stream') -> str:
    return upload_file_to_s3(io.BytesIO(data), s3_key, content_type)


def generate_presigned_url(s3_key: str, expires_in: int = 3600) -> str:
    return _s3().generate_presigned_url(
        'get_object',
        Params={'Bucket': settings.AWS_S3_BUCKET, 'Key': s3_key},
        ExpiresIn=expires_in,
    )


def download_bytes_from_s3(s3_key: str) -> bytes:
    buf = io.BytesIO()
    _s3().download_fileobj(settings.AWS_S3_BUCKET, s3_key, buf)
    return buf.getvalue()


def delete_file_from_s3(s3_key: str) -> bool:
    try:
        _s3().delete_object(Bucket=settings.AWS_S3_BUCKET, Key=s3_key)
        return True
    except Exception as e:
        logger.error('S3 delete failed for %s: %s', s3_key, e)
        return False
