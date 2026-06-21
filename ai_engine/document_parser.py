"""Text extraction + chunking for training-document ingestion."""
from django.conf import settings


def extract_text(file_bytes: bytes, filename: str) -> str:
    """Extract plain text from PDF / DOCX / TXT bytes."""
    ext = filename.lower().rsplit('.', 1)[-1] if '.' in filename else ''

    if ext == 'pdf':
        import fitz  # PyMuPDF
        doc = fitz.open(stream=file_bytes, filetype='pdf')
        try:
            return '\n'.join(page.get_text() for page in doc)
        finally:
            doc.close()

    if ext in ('docx', 'doc'):
        import io
        from docx import Document
        document = Document(io.BytesIO(file_bytes))
        return '\n'.join(p.text for p in document.paragraphs)

    if ext == 'txt':
        return file_bytes.decode('utf-8', errors='ignore')

    raise ValueError(f'Unsupported file type: .{ext}')


def chunk_text(text: str, size: int = None, overlap: int = None) -> list[str]:
    """Sliding-window chunking by characters with overlap, on whitespace boundaries."""
    size = size or settings.RAG_CHUNK_SIZE
    overlap = overlap or settings.RAG_CHUNK_OVERLAP
    text = ' '.join(text.split())  # normalise whitespace
    if not text:
        return []

    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + size, n)
        # try to break on a space near the end for cleaner chunks
        if end < n:
            space = text.rfind(' ', start, end)
            if space > start:
                end = space
        chunks.append(text[start:end].strip())
        if end >= n:
            break
        start = max(end - overlap, start + 1)
    return [c for c in chunks if c]
