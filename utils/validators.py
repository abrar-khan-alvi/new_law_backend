import os

from django.core.exceptions import ValidationError

# Upload limits (bytes)
MAX_IMAGE_SIZE = 10 * 1024 * 1024        # 10 MB
MAX_VIDEO_SIZE = 500 * 1024 * 1024       # 500 MB
MAX_DOCUMENT_SIZE = 25 * 1024 * 1024     # 25 MB

# SVG deliberately excluded: it's XML, not a fixed binary format, so a magic-byte
# check can't validate it, and it can carry an embedded <script> that runs if the
# stored file is ever opened directly (a real stored-XSS vector via file upload).
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.webm', '.mov', '.avi', '.wmv'}
ALLOWED_DOCUMENT_EXTENSIONS = {'.pdf', '.doc', '.docx', '.txt'}

# Magic-byte signatures for the image/video types this app accepts. Extensions
# and browser-supplied Content-Type headers are both attacker-controlled — a
# file named "x.png" can contain anything — so the actual bytes are what get
# checked before anything is stored or served back to other users.
_SIGNATURES = {
    'image/jpeg': [b'\xff\xd8\xff'],
    'image/png': [b'\x89PNG\r\n\x1a\n'],
    'image/gif': [b'GIF87a', b'GIF89a'],
    'image/webp': [b'RIFF'],  # followed by size (4 bytes) then b'WEBP' — checked below
    'video/mp4': [b'ftyp'],  # appears at offset 4 in the ISO-BMFF header — checked below
    'video/quicktime': [b'ftyp', b'moov', b'mdat', b'wide'],
    'video/webm': [b'\x1a\x45\xdf\xa3'],
    'video/x-msvideo': [b'RIFF'],  # followed by b'AVI ' — checked below
}


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


def _sniff(header: bytes, mime: str) -> bool:
    if mime in ('image/webp', 'video/x-msvideo'):
        if not header.startswith(b'RIFF') or len(header) < 12:
            return False
        return header[8:12] == (b'WEBP' if mime == 'image/webp' else b'AVI ')
    if mime in ('video/mp4', 'video/quicktime'):
        return len(header) >= 12 and header[4:8] in (b'ftyp', b'moov', b'mdat', b'wide', b'free', b'skip')
    return any(header.startswith(sig) for sig in _SIGNATURES.get(mime, []))


EXT_TO_MIME = {
    '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.webp': 'image/webp',
    '.mp4': 'video/mp4',
    '.webm': 'video/webm',
    '.mov': 'video/quicktime',
    '.avi': 'video/x-msvideo',
}


def validate_file_signature(file_obj, declared_mime: str):
    """
    Read the file's actual leading bytes and confirm they match a real,
    known signature for `declared_mime` — the declared Content-Type and the
    filename extension are both supplied by the client and can't be trusted
    on their own. Raises ValidationError if the bytes don't match anything
    this app recognizes as that type.
    """
    header = file_obj.read(16)
    file_obj.seek(0)
    if declared_mime not in _SIGNATURES or not _sniff(header, declared_mime):
        raise ValidationError(
            f'File content does not match a valid {declared_mime} file.'
        )
