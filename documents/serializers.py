from rest_framework import serializers

from .models import GeneratedDocument


class GeneratedDocumentSerializer(serializers.ModelSerializer):
    supervisor_reviewed_by_email = serializers.CharField(
        source='supervisor_reviewed_by.email', read_only=True, default=None,
    )

    class Meta:
        model = GeneratedDocument
        fields = [
            'id', 'doc_type', 'case_number', 'form_data', 'ai_narrative', 'narrative_body',
            'narrative_style', 'status', 'error_message',
            'model_used', 'tokens_used', 'generation_time_ms',
            'leak_flags', 'quality_flags',
            'review_status', 'supervisor_reviewed_by_email', 'supervisor_reviewed_at',
            'supervisor_notes', 'prosecutor_reviewed_name', 'prosecutor_reviewed_at',
            'prosecutor_approved', 'prosecutor_notes',
            'signature_name', 'signed_at',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields


class GeneratedDocumentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedDocument
        fields = [
            'id', 'doc_type', 'case_number', 'status',
            'narrative_style', 'created_at',
        ]


class GenerateRequestSerializer(serializers.Serializer):
    doc_type = serializers.ChoiceField(choices=GeneratedDocument.DocType.choices)
    narrative_style = serializers.ChoiceField(
        choices=GeneratedDocument.NarrativeStyle.choices,
        default=GeneratedDocument.NarrativeStyle.FIRST_PERSON,
    )
    form_data = serializers.JSONField()

    # Minimal per-doc_type required-field checks (see docs/FORM_DATA_SCHEMAS.md).
    REQUIRED = {
        'incident_report': lambda d: bool(d.get('facts', {}).get('what')),
        'search_warrant': lambda d: bool(d.get('offenses')) and bool(d.get('place_to_search')),
        'arrest_warrant': lambda d: bool(d.get('defendant', {}).get('full_name')),
    }

    def validate_form_data(self, value):
        if not isinstance(value, dict) or not value:
            raise serializers.ValidationError('form_data must be a non-empty object.')
        return value

    def validate(self, attrs):
        check = self.REQUIRED.get(attrs['doc_type'])
        if check and not check(attrs['form_data']):
            raise serializers.ValidationError(
                {'form_data': f"Missing required fields for {attrs['doc_type']}."}
            )
        return attrs
