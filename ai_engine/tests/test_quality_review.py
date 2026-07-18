"""
Regression tests for the Constitutional Quality Review completion:
- fails CLOSED (never silently "no issues found") on any model/parse error.
- deterministic structural pre-flight catches blank required fields even if
  the LLM call never runs.
- deterministic consistency check catches a name that doesn't survive into
  the final document text.
"""
from unittest.mock import patch

from django.test import SimpleTestCase

from ai_engine.quality_review import (
    check_constitutional_quality,
    consistency_review,
    structural_review,
)


class FailClosedTests(SimpleTestCase):
    @patch('ai_engine.quality_review.ModelClient')
    def test_model_exception_fails_closed(self, MockClient):
        MockClient.return_value.generate.side_effect = RuntimeError('boom')
        flags = check_constitutional_quality('search_warrant', 'some narrative')
        self.assertTrue(flags)
        self.assertEqual(flags[0]['source'], 'system')
        self.assertIn('incomplete', flags[0]['issue'].lower())

    @patch('ai_engine.quality_review.ModelClient')
    def test_unparseable_response_fails_closed(self, MockClient):
        MockClient.return_value.generate.return_value = '[MOCK NARRATIVE] not json at all'
        flags = check_constitutional_quality('search_warrant', 'some narrative')
        self.assertTrue(flags)
        self.assertEqual(flags[0]['source'], 'system')

    @patch('ai_engine.quality_review.ModelClient')
    def test_clean_response_passes_with_no_flags(self, MockClient):
        MockClient.return_value.generate.return_value = '[]'
        flags = check_constitutional_quality('search_warrant', 'some narrative')
        self.assertEqual(flags, [])

    @patch('ai_engine.quality_review.ModelClient')
    def test_llm_flags_are_tagged_with_source(self, MockClient):
        MockClient.return_value.generate.return_value = (
            '[{"issue": "Missing nexus language", "detail": "..."}]'
        )
        flags = check_constitutional_quality('search_warrant', 'some narrative')
        self.assertEqual(flags[0]['source'], 'llm')

    def test_incident_report_is_not_reviewed(self):
        # Quality review only applies to warrants.
        self.assertEqual(check_constitutional_quality('incident_report', 'narrative'), [])


class StructuralPreflightTests(SimpleTestCase):
    def test_flags_blank_required_field(self):
        form_data = {
            'offenses': [{'code_section': '18 U.S.C. 1030'}],
            'place_to_search': {'description': 'a house'},
            'probable_cause': {'affiant_background': 'x', 'investigation_summary': 'y'},
            # nexus_to_place intentionally missing
        }
        flags = structural_review('search_warrant', form_data)
        issues = [f['issue'] for f in flags]
        self.assertTrue(any('Nexus' in i or 'nexus' in i for i in issues))
        self.assertTrue(all(f['source'] == 'structural' for f in flags))

    def test_passes_with_all_required_fields(self):
        form_data = {
            'offenses': [{'code_section': '18 U.S.C. 1030'}],
            'place_to_search': {'description': 'a house'},
            'probable_cause': {
                'affiant_background': 'x', 'investigation_summary': 'y', 'nexus_to_place': 'z',
            },
        }
        self.assertEqual(structural_review('search_warrant', form_data), [])


class ConsistencyReviewTests(SimpleTestCase):
    def test_flags_defendant_name_missing_from_assembled_text(self):
        form_data = {'defendant': {'full_name': 'Jane Roe'}}
        flags = consistency_review('arrest_warrant', 'This text never names anyone.', form_data)
        self.assertTrue(flags)
        self.assertEqual(flags[0]['source'], 'structural')

    def test_passes_when_name_present(self):
        form_data = {'defendant': {'full_name': 'Jane Roe'}}
        flags = consistency_review('arrest_warrant', 'Jane Roe was arrested today.', form_data)
        self.assertEqual(flags, [])
