import uuid

from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdmin
from utils.storage import store_upload

from .document_parser import extract_text
from .models import TrainingDocument
from .serializers import TrainingDocumentSerializer
from .tasks import index_training_document

VALID_DOC_TYPES = {'incident_report', 'search_warrant', 'arrest_warrant'}


class TrainingDocumentListView(APIView):
    """GET /api/ai/training-docs/ — admin list of training documents."""
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = TrainingDocument.objects.all()
        doc_type = request.GET.get('doc_type')
        if doc_type:
            qs = qs.filter(doc_type=doc_type)
        return Response(TrainingDocumentSerializer(qs, many=True).data)


class UploadTrainingDocumentView(APIView):
    """
    POST /api/ai/training-docs/upload/  (multipart)
    Fields: file (pdf/docx/txt), doc_type, title (optional)
    Parses text, stores the doc, and queues async embedding/indexing.
    """
    permission_classes = [IsAdmin]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        doc_type = request.data.get('doc_type')
        if doc_type not in VALID_DOC_TYPES:
            return Response(
                {'error': {'detail': f'doc_type must be one of {sorted(VALID_DOC_TYPES)}.'}},
                status=400,
            )
        file = request.FILES.get('file')
        if not file:
            return Response({'error': {'detail': 'No file provided.'}}, status=400)

        file_bytes = file.read()
        try:
            raw_text = extract_text(file_bytes, file.name)
        except ValueError as e:
            return Response({'error': {'detail': str(e)}}, status=400)

        ext = file.name.rsplit('.', 1)[-1].lower() if '.' in file.name else 'bin'
        key = f'training/{doc_type}/{uuid.uuid4()}.{ext}'
        import io
        stored_key = store_upload(io.BytesIO(file_bytes), key, content_type=file.content_type or '')

        td = TrainingDocument.objects.create(
            doc_type=doc_type,
            title=request.data.get('title', '') or file.name,
            original_filename=file.name,
            s3_key=stored_key,
            raw_text=raw_text,
            uploaded_by=request.user,
        )
        index_training_document.delay(td.id)
        return Response(
            {'message': 'Uploaded. Indexing queued.',
             'training_document': TrainingDocumentSerializer(td).data},
            status=201,
        )
