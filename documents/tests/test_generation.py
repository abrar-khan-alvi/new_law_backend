"""
Regression tests for the requirements-driven changes to document generation:
- WarrantTemplate resolution order (agency override -> jurisdiction profile ->
  seeded global default -> built-in Python fallback).
- Jurisdiction-aware PDF export dispatch (federal -> official AO forms,
  state/municipal -> the custom agency-aware builder).
- _officer_profile() actually carrying the full Agency field set through.
- Incomplete officer profiles block incident-report export instead of
  silently rendering another department's identity.
"""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import Agency, JurisdictionProfile
from documents.exporters.pdf import render_pdf
from documents.templates_engine import get_template_text, render_template
from documents.models import GeneratedDocument, WarrantTemplate
from documents.views import ExportDocumentView, _officer_profile

User = get_user_model()


class WarrantTemplateResolutionTests(TestCase):
    def setUp(self):
        self.profile = JurisdictionProfile.objects.create(
            name='Georgia — State', jurisdiction_type='state', state='Georgia',
        )
        self.agency = Agency.objects.create(
            name='Test PD', jurisdiction_type='state', jurisdiction_profile=self.profile,
        )

    def test_falls_back_to_seeded_global_default(self):
        text = get_template_text(self.agency, 'search_warrant', 'affidavit_intro')
        self.assertIn('{affiant_name}', text)
        self.assertTrue(len(text) > 0)

    def test_falls_back_to_python_default_with_zero_db_rows(self):
        WarrantTemplate.objects.all().delete()
        text = get_template_text(self.agency, 'search_warrant', 'nexus_closing')
        self.assertIn('{nexus_to_place}', text)

    def test_jurisdiction_profile_override_takes_precedence_over_global(self):
        WarrantTemplate.objects.create(
            jurisdiction_profile=self.profile, doc_type='search_warrant',
            section_key='affidavit_intro', template_text='PROFILE TEXT {affiant_name}',
        )
        text = get_template_text(self.agency, 'search_warrant', 'affidavit_intro')
        self.assertEqual(text, 'PROFILE TEXT {affiant_name}')

    def test_agency_override_takes_precedence_over_profile(self):
        WarrantTemplate.objects.create(
            jurisdiction_profile=self.profile, doc_type='search_warrant',
            section_key='affidavit_intro', template_text='PROFILE TEXT',
        )
        WarrantTemplate.objects.create(
            agency=self.agency, doc_type='search_warrant',
            section_key='affidavit_intro', template_text='AGENCY TEXT',
        )
        text = get_template_text(self.agency, 'search_warrant', 'affidavit_intro')
        self.assertEqual(text, 'AGENCY TEXT')

    def test_render_template_never_raises_on_malformed_placeholder(self):
        # An admin's typo in a custom template must not break generation.
        out = render_template('Hello {missing_key} and {unclosed', {'affiant_name': 'X'})
        self.assertIsInstance(out, str)


class OfficerProfileAgencyMergeTests(TestCase):
    def test_full_agency_field_set_flows_through(self):
        agency = Agency.objects.create(
            name='Full PD', jurisdiction_type='federal', state='CA', county='LA',
            city='Los Angeles', court_name='US District Court', judicial_district='Central',
            division='Criminal', court_caption='CENTRAL DISTRICT OF CALIFORNIA',
            judge_title='Magistrate Judge', prosecuting_authority='US Attorney',
            case_number_format='{year}-CR-{seq}', ori='CA1234500',
            default_legal_citations='18 U.S.C. 1030',
        )
        user = User.objects.create(email='o@example.com', agency=agency, rank='Detective')

        profile = _officer_profile(user)

        self.assertEqual(profile['agency_jurisdiction_type'], 'federal')
        self.assertEqual(profile['agency_judicial_district'], 'Central')
        self.assertEqual(profile['agency_division'], 'Criminal')
        self.assertEqual(profile['agency_judge_title'], 'Magistrate Judge')
        self.assertEqual(profile['agency_prosecuting_authority'], 'US Attorney')
        self.assertEqual(profile['agency_case_number_format'], '{year}-CR-{seq}')
        self.assertEqual(profile['agency_default_legal_citations'], '18 U.S.C. 1030')

    def test_agency_citations_fall_back_to_jurisdiction_profile(self):
        profile = JurisdictionProfile.objects.create(
            name='CA State', jurisdiction_type='state', state='CA',
            default_legal_citations='CA Penal Code 187',
        )
        agency = Agency.objects.create(
            name='No Citations PD', jurisdiction_type='state', jurisdiction_profile=profile,
        )
        user = User.objects.create(email='o2@example.com', agency=agency)

        prof = _officer_profile(user)
        self.assertEqual(prof['agency_default_legal_citations'], 'CA Penal Code 187')


class JurisdictionExportDispatchTests(TestCase):
    def _officer(self, jurisdiction_type):
        return {
            'full_name': 'Jane Doe', 'rank': 'Officer', 'badge_number': '123',
            'agency_name': 'Test Agency', 'agency_jurisdiction_type': jurisdiction_type,
            'agency_state': 'GA', 'agency_county': 'Cobb',
            'agency_court_caption': 'SUPERIOR COURT OF COBB COUNTY',
        }

    @patch('documents.exporters.ao_forms.fill_search_warrant')
    def test_federal_search_warrant_uses_ao_forms(self, mock_fill):
        mock_fill.return_value = b'%PDF-FAKE'
        form_data = {'court': {}, 'place_to_search': {'description': 'a house'}, 'offenses': []}
        render_pdf('search_warrant', form_data, 'narrative', self._officer('federal'))
        mock_fill.assert_called_once()

    @patch('documents.exporters.ao_forms.fill_search_warrant')
    def test_state_search_warrant_skips_ao_forms(self, mock_fill):
        form_data = {'court': {}, 'place_to_search': {'description': 'a house'}, 'offenses': []}
        content = render_pdf('search_warrant', form_data, 'narrative', self._officer('state'))
        mock_fill.assert_not_called()
        self.assertTrue(content[:4] == b'%PDF')

    @patch('documents.exporters.ao_forms.fill_search_warrant')
    def test_jurisdiction_override_beats_agency_default(self, mock_fill):
        mock_fill.return_value = b'%PDF-FAKE'
        form_data = {
            'court': {'jurisdiction_type_override': 'federal'},
            'place_to_search': {'description': 'a house'}, 'offenses': [],
        }
        render_pdf('search_warrant', form_data, 'narrative', self._officer('state'))
        mock_fill.assert_called_once()


class IncidentReportExportValidationTests(TestCase):
    """
    Client-facing fix: exporting an incident report with a blank department
    name / ORI / badge number used to silently render a real, unrelated
    department's identity onto the document. It must now be blocked instead.
    """

    def setUp(self):
        # manage.py test forces settings.DEBUG=False, so the (unrelated)
        # plan-based export gate is NOT bypassed here — give the user a real
        # plan with export enabled so these tests exercise the profile check
        # specifically, not that gate.
        from subscriptions.models import Plan, Subscription
        plan = Plan.objects.create(
            name='t-export', display_name='Export Test',
            can_incident_report=True, can_search_warrant=True,
            can_export_pdf=True, can_export_docx=True,
        )
        self.factory = APIRequestFactory()
        self.user = User.objects.create(
            email='incomplete@example.com', role='officer',
        )
        Subscription.objects.filter(user=self.user).delete()
        Subscription.objects.create(user=self.user, plan=plan, status='active')
        self.doc = GeneratedDocument.objects.create(
            user=self.user, doc_type='incident_report',
            case_number='LE-TEST1', form_data={'facts': {'what': 'test'}},
            ai_narrative='A test narrative.', status=GeneratedDocument.Status.COMPLETED,
        )

    def _export(self):
        req = self.factory.post(f'/api/documents/{self.doc.id}/export/', {'format': 'pdf'}, format='json')
        force_authenticate(req, user=self.user)
        return ExportDocumentView.as_view()(req, pk=self.doc.id)

    def test_blocks_export_with_incomplete_profile(self):
        # No department_name / ori / badge_number set at all.
        resp = self._export()
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.data['error']['code'], 'incomplete_officer_profile')

    def test_allows_export_once_profile_is_complete(self):
        self.user.department_name = 'Test PD'
        self.user.ori = 'TE0000000'
        self.user.badge_number = 'T-001'
        self.user.save()
        resp = self._export()
        self.assertEqual(resp.status_code, 200)

    def test_only_incident_reports_are_gated(self):
        # A warrant with the same blank profile must not be blocked by this check.
        warrant = GeneratedDocument.objects.create(
            user=self.user, doc_type='search_warrant',
            case_number='LE-TEST2',
            form_data={'offenses': [], 'place_to_search': {'description': 'x'}},
            ai_narrative='A test affidavit.', status=GeneratedDocument.Status.COMPLETED,
        )
        req = self.factory.post(f'/api/documents/{warrant.id}/export/', {'format': 'pdf'}, format='json')
        force_authenticate(req, user=self.user)
        resp = ExportDocumentView.as_view()(req, pk=warrant.id)
        self.assertEqual(resp.status_code, 200)
