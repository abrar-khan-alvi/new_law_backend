"""
Regression tests for admin_panel (previously zero coverage in this app):
- Agency management is admin-only (the permission gap fix: this used to be
  any-authenticated-user under /api/auth/agencies/).
- UserDetailView.patch actually validates input before saving (the "broken
  PATCH" finding was retracted as a false positive on re-inspection — this
  locks that behavior in so a future change can't silently reintroduce it).
- JurisdictionProfileDetailView.delete() blocks deletion when custom warrant
  templates are attached (Phase 1 fix).
- AgencySealUploadView returns clean error text, not a Python list repr.
- The admin document list surfaces review_status and can filter down to a
  review queue (previously review_status wasn't returned or filterable here
  at all — an admin had no way to find documents awaiting supervisor/
  prosecutor review without opening each one individually).
"""
import io

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import Agency, JurisdictionProfile
from documents.models import GeneratedDocument, WarrantTemplate

User = get_user_model()


def _png_bytes():
    # Minimal valid 1x1 PNG (magic bytes only matter to validate_file_signature).
    return (b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0'
            b'\x00\x00\x03\x01\x01\x00\x18\xdd\x8d\xb0\x00\x00\x00\x00IEND\xaeB`\x82')


class AgencyPermissionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create(email='admin@example.com', role='admin', email_verified=True)
        self.officer = User.objects.create(email='officer@example.com', role='officer', email_verified=True)

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_non_admin_cannot_create_agency(self):
        self._auth(self.officer)
        resp = self.client.post('/api/admin-panel/agencies/', {
            'name': 'Rogue PD', 'jurisdiction_type': 'state', 'state': 'GA', 'ori': 'GA0000001',
        }, format='json')
        self.assertEqual(resp.status_code, 403)
        self.assertFalse(Agency.objects.filter(name='Rogue PD').exists())

    def test_admin_can_create_agency(self):
        self._auth(self.admin)
        resp = self.client.post('/api/admin-panel/agencies/', {
            'name': 'Real PD', 'jurisdiction_type': 'state', 'state': 'GA', 'ori': 'GA0000002',
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(Agency.objects.filter(name='Real PD').exists())


class UserDetailPatchTests(TestCase):
    """Re-inspection confirmed this was never actually broken (see the QA
    audit's 'Retracted' entry) — this test exists so a future refactor that
    removes the is_valid(raise_exception=True) call gets caught immediately."""

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create(email='admin2@example.com', role='admin', email_verified=True)
        self.target = User.objects.create(email='target@example.com', role='officer', email_verified=True)
        self.client.force_authenticate(user=self.admin)

    def test_valid_patch_applies(self):
        resp = self.client.patch(f'/api/admin-panel/users/{self.target.id}/', {
            'is_supervisor': True,
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.target.refresh_from_db()
        self.assertTrue(self.target.is_supervisor)

    def test_invalid_field_value_is_rejected_not_silently_saved(self):
        # AdminUserUpdateSerializer doesn't expose 'role' as a free-text
        # field with arbitrary choices — sending garbage for a real
        # constrained field must 400, not silently persist.
        resp = self.client.patch(f'/api/admin-panel/users/{self.target.id}/', {
            'agency': 'not-a-valid-agency-pk',
        }, format='json')
        self.assertEqual(resp.status_code, 400)


class JurisdictionProfileDeleteGuardTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create(email='admin3@example.com', role='admin', email_verified=True)
        self.client.force_authenticate(user=self.admin)
        self.profile = JurisdictionProfile.objects.create(
            name='Georgia — State', jurisdiction_type='state', state='Georgia',
        )

    def test_delete_blocked_when_templates_attached(self):
        WarrantTemplate.objects.create(
            jurisdiction_profile=self.profile, doc_type='search_warrant',
            section_key='affidavit_intro', template_text='Custom text {affiant_name}',
        )
        resp = self.client.delete(f'/api/admin-panel/jurisdiction-profiles/{self.profile.id}/')
        self.assertEqual(resp.status_code, 400)
        self.assertTrue(JurisdictionProfile.objects.filter(pk=self.profile.pk).exists())

    def test_delete_allowed_when_no_templates_or_agencies(self):
        resp = self.client.delete(f'/api/admin-panel/jurisdiction-profiles/{self.profile.id}/')
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(JurisdictionProfile.objects.filter(pk=self.profile.pk).exists())


class AgencySealUploadErrorMessageTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create(email='admin4@example.com', role='admin', email_verified=True)
        self.client.force_authenticate(user=self.admin)
        self.agency = Agency.objects.create(name='Seal PD', jurisdiction_type='state', state='GA')

    def test_oversized_file_returns_clean_message_not_list_repr(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        # 11 MB of junk, over the 10 MB image cap — content doesn't need to be
        # a real image since the size check runs before signature validation.
        big = SimpleUploadedFile('seal.png', b'0' * (11 * 1024 * 1024), content_type='image/png')
        resp = self.client.post(f'/api/admin-panel/agencies/{self.agency.id}/seal/', {'seal': big})
        self.assertEqual(resp.status_code, 400)
        detail = resp.data['error']['detail']
        self.assertNotIn('[', detail)
        self.assertNotIn("'", detail)

    def test_valid_png_uploads_successfully(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        png = SimpleUploadedFile('seal.png', _png_bytes(), content_type='image/png')
        resp = self.client.post(f'/api/admin-panel/agencies/{self.agency.id}/seal/', {'seal': png})
        self.assertEqual(resp.status_code, 200)
        self.agency.refresh_from_db()
        self.assertTrue(self.agency.seal_image_key)


class DocumentReviewQueueTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create(email='admin5@example.com', role='admin', email_verified=True)
        self.client.force_authenticate(user=self.admin)
        self.agency = Agency.objects.create(name='Queue PD', jurisdiction_type='state', state='GA')
        self.officer = User.objects.create(
            email='queue-officer@example.com', role='officer', agency=self.agency,
        )
        self.pending = GeneratedDocument.objects.create(
            user=self.officer, doc_type='search_warrant', case_number='LE-Q1',
            form_data={}, status=GeneratedDocument.Status.COMPLETED,
            review_status=GeneratedDocument.ReviewStatus.PENDING_SUPERVISOR,
        )
        self.approved = GeneratedDocument.objects.create(
            user=self.officer, doc_type='search_warrant', case_number='LE-Q2',
            form_data={}, status=GeneratedDocument.Status.COMPLETED,
            review_status=GeneratedDocument.ReviewStatus.APPROVED,
        )

    def test_list_surfaces_review_status(self):
        resp = self.client.get('/api/admin-panel/documents/')
        self.assertEqual(resp.status_code, 200)
        by_case = {row['case_number']: row for row in resp.data['results']}
        self.assertEqual(by_case['LE-Q1']['review_status'], 'pending_supervisor')
        self.assertEqual(by_case['LE-Q1']['agency_name'], 'Queue PD')

    def test_pending_review_filter_excludes_approved(self):
        resp = self.client.get('/api/admin-panel/documents/?pending_review=true')
        case_numbers = {row['case_number'] for row in resp.data['results']}
        self.assertIn('LE-Q1', case_numbers)
        self.assertNotIn('LE-Q2', case_numbers)

    def test_review_status_filter(self):
        resp = self.client.get('/api/admin-panel/documents/?review_status=approved')
        case_numbers = {row['case_number'] for row in resp.data['results']}
        self.assertEqual(case_numbers, {'LE-Q2'})

    def test_admin_can_approve_from_the_documents_endpoint(self):
        # The action itself already worked for admins (IsSupervisorOfAgency
        # bypasses the same-agency check for role=admin) — this just confirms
        # that still holds now that the queue is visible.
        resp = self.client.post(f'/api/documents/{self.pending.id}/supervisor-review/', {
            'approved': True,
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.pending.refresh_from_db()
        self.assertEqual(self.pending.review_status, GeneratedDocument.ReviewStatus.APPROVED)


class UserDirectoryFilterTests(TestCase):
    """
    Users & Permissions must show officers only, not admins — and Platform
    Stats needs the breakdown (active/suspended/supervisors/admins) the
    redesigned pages' stat cards read from.
    """

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create(email='dir-admin@example.com', role='admin', email_verified=True)
        self.client.force_authenticate(user=self.admin)
        self.officer_active = User.objects.create(
            email='dir-officer-active@example.com', role='officer', is_active=True,
        )
        self.officer_suspended = User.objects.create(
            email='dir-officer-suspended@example.com', role='officer', is_active=False,
        )
        self.supervisor = User.objects.create(
            email='dir-supervisor@example.com', role='officer', is_supervisor=True,
        )
        self.other_admin = User.objects.create(email='dir-admin2@example.com', role='admin')

    def test_exclude_role_admin_hides_admins(self):
        resp = self.client.get('/api/admin-panel/users/?exclude_role=admin')
        emails = {row['email'] for row in resp.data['results']}
        self.assertIn('dir-officer-active@example.com', emails)
        self.assertNotIn('dir-admin@example.com', emails)
        self.assertNotIn('dir-admin2@example.com', emails)

    def test_role_admin_shows_only_admins(self):
        resp = self.client.get('/api/admin-panel/users/?role=admin')
        emails = {row['email'] for row in resp.data['results']}
        self.assertEqual(emails, {'dir-admin@example.com', 'dir-admin2@example.com'})

    def test_is_active_filter(self):
        resp = self.client.get('/api/admin-panel/users/?exclude_role=admin&is_active=false')
        emails = {row['email'] for row in resp.data['results']}
        self.assertIn('dir-officer-suspended@example.com', emails)
        self.assertNotIn('dir-officer-active@example.com', emails)

    def test_is_supervisor_filter(self):
        resp = self.client.get('/api/admin-panel/users/?is_supervisor=true')
        emails = {row['email'] for row in resp.data['results']}
        self.assertEqual(emails, {'dir-supervisor@example.com'})

    def test_platform_stats_breakdown(self):
        resp = self.client.get('/api/admin-panel/stats/')
        users_stats = resp.data['users']
        self.assertEqual(users_stats['admins'], 2)
        self.assertEqual(users_stats['active_officers'], 2)  # officer_active + supervisor
        self.assertEqual(users_stats['suspended_officers'], 1)
        self.assertEqual(users_stats['supervisors'], 1)
