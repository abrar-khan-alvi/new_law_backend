import os

from django.core.exceptions import ValidationError

# Upload limits (bytes)
MAX_IMAGE_SIZE = 10 * 1024 * 1024        # 10 MB
MAX_VIDEO_SIZE = 500 * 1024 * 1024       # 500 MB
MAX_DOCUMENT_SIZE = 25 * 1024 * 1024     # 25 MB

ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'}
ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.webm', '.mov', '.avi', '.wmv'}
ALLOWED_DOCUMENT_EXTENSIONS = {'.pdf', '.doc', '.docx', '.txt'}


def validate_file_size(file_obj, max_size: int):
    if file_obj.size > max_size:
        mb = max_size / (1024 * 1024)
        raise ValidationError(f'File too large. Maximum size is {mb:.0f} MB.')


def validate_file_extension(file_obj, allowed: set):
    ext = os.path.splitext(file_obj.name)[1].lower()
    if ext not in allowed:
        raise ValidationError(
            f'Unsupported file type "{ext}". Allowed: {", ".join(sorted(allowed))}.'
        )
    return ext
