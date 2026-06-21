"""
End-to-end smoke test for the core backend.

Run inside the running stack:
    docker compose exec backend python manage.py smoke_test

It provisions a verified test officer on the Pro plan, then drives the public
API (login → generate all 3 doc types → export PDF+DOCX → list → blog → plans →
confirm payments are dormant) and prints a PASS/FAIL banner.
"""
import requests
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from subscriptions.models import Plan, Subscription

User = get_user_model()

EMAIL = 'smoke_officer@example.com'
PASSWORD = 'SmokeTest123!'

GREEN = '\033[92m'
RED = '\033[91m'
BOLD = '\033[1m'
RESET = '\033[0m'


class Command(BaseCommand):
    help = 'Run an end-to-end smoke test against the running server.'

    def add_arguments(self, parser):
        parser.add_argument('--base-url', default='http://localhost:8000')

    def handle(self, *args, **opts):
        base = opts['base_url'].rstrip('/')
        self.results = []
        self._provision_user()
        token = self._login(base)
        headers = {'Authorization': f'Bearer {token}'} if token else {}

        self._check_health(base)
        self._check_profile(base, headers)
        ids = self._check_generate(base, headers)
        self._check_list(base, headers)
        self._check_export(base, headers, ids)
        self._check_blog_and_plans(base)
        self._check_payments_dormant(base)

        self._summary()

    # ── helpers ──────────────────────────────────────────────────────
    def _ok(self, name, condition, detail=''):
        self.results.append((name, bool(condition)))
        mark = f'{GREEN}PASS{RESET}' if condition else f'{RED}FAIL{RESET}'
        self.stdout.write(f'  [{mark}] {name}{(" — " + detail) if detail else ""}')

    def _provision_user(self):
        pro = Plan.objects.filter(name='pro').first() or Plan.objects.first()
        user, _ = User.objects.get_or_create(
            email=EMAIL, defaults={'role': 'officer', 'first_name': 'Smoke', 'last_name': 'Officer'})
        user.role = 'officer'
        user.email_verified = True
        user.is_verified = True
        user.department_name = 'Test PD'
        user.rank = 'Sergeant'
        user.badge_number = 'T-001'
        user.set_password(PASSWORD)
        user.save()
        sub, _ = Subscription.objects.get_or_create(user=user, defaults={'plan': pro})
        sub.plan = pro
        sub.status = 'active'
        sub.documents_generated_this_month = 0
        sub.save()
        self.stdout.write(f'{BOLD}Provisioned test officer {EMAIL} on plan "{pro.name}".{RESET}\n')

    def _login(self, base):
        try:
            r = requests.post(f'{base}/api/auth/login/',
                              json={'email': EMAIL, 'password': PASSWORD}, timeout=30)
            token = r.json().get('access') if r.ok else None
            self._ok('Login (JWT)', r.ok and token, f'HTTP {r.status_code}')
            return token
        except Exception as e:  # noqa: BLE001
            self._ok('Login (JWT)', False, str(e))
            return None

    def _check_health(self, base):
        try:
            r = requests.get(f'{base}/health/', timeout=10)
            self._ok('Health endpoint', r.ok and r.json().get('status') == 'ok')
        except Exception as e:  # noqa: BLE001
            self._ok('Health endpoint', False, str(e))

    def _check_profile(self, base, headers):
        r = requests.get(f'{base}/api/auth/profile/', headers=headers, timeout=30)
        plan = (r.json().get('subscription') or {}).get('plan') if r.ok else None
        self._ok('Profile + subscription', r.ok and plan == 'pro', f'plan={plan}')

    def _check_generate(self, base, headers):
        payloads = {
            'incident_report': {'facts': {'what': 'Test theft report', 'who': 'John Doe',
                                          'officer_actions': 'Took report'}},
            'search_warrant': {'offenses': [{'code_section': '18 U.S.C. 1030', 'description': 'fraud'}],
                               'place_to_search': {'description': 'a server', 'address': 'LA'},
                               'probable_cause': {'affiant_background': 'x', 'investigation_summary': 'y',
                                                  'nexus_to_place': 'z'}},
            'arrest_warrant': {'defendant': {'full_name': 'Jane Roe'},
                               'offense': {'brief_description': 'theft'},
                               'charging_document': 'complaint'},
        }
        ids = {}
        for dt, fd in payloads.items():
            r = requests.post(f'{base}/api/documents/generate/', headers=headers,
                              json={'doc_type': dt, 'narrative_style': 'third_person', 'form_data': fd},
                              timeout=300)  # live model (ollama) is slower than mock
            ok = r.status_code == 201 and r.json().get('status') == 'completed'
            self._ok(f'Generate {dt}', ok, f'HTTP {r.status_code}')
            if ok:
                ids[dt] = r.json()['id']
        return ids

    def _check_list(self, base, headers):
        r = requests.get(f'{base}/api/documents/', headers=headers, timeout=30)
        count = r.json().get('count') if r.ok else 0
        self._ok('Document history list', r.ok and count >= 1, f'count={count}')

    def _check_export(self, base, headers, ids):
        doc_id = next(iter(ids.values()), None)
        if not doc_id:
            self._ok('Export PDF', False, 'no document to export')
            self._ok('Export DOCX', False, 'no document to export')
            return
        rp = requests.post(f'{base}/api/documents/{doc_id}/export/', headers=headers,
                           json={'format': 'pdf'}, timeout=60)
        self._ok('Export PDF', rp.ok and rp.content[:4] == b'%PDF', f'{len(rp.content)} bytes')
        rd = requests.post(f'{base}/api/documents/{doc_id}/export/', headers=headers,
                           json={'format': 'docx'}, timeout=60)
        self._ok('Export DOCX', rd.ok and rd.content[:2] == b'PK', f'{len(rd.content)} bytes')

    def _check_blog_and_plans(self, base):
        rp = requests.get(f'{base}/api/subscriptions/plans/', timeout=30)
        self._ok('Plans (public)', rp.ok and len(rp.json()) >= 1, f'{len(rp.json())} plans')
        rb = requests.get(f'{base}/api/blog/posts/', timeout=30)
        self._ok('Blog list (public)', rb.ok)

    def _check_payments_dormant(self, base):
        r = requests.post(f'{base}/api/payments/webhook/', json={}, timeout=30)
        self._ok('Payments dormant (503)', r.status_code == 503, f'HTTP {r.status_code}')

    def _summary(self):
        passed = sum(1 for _, ok in self.results if ok)
        total = len(self.results)
        self.stdout.write('')
        if passed == total:
            self.stdout.write(f'{GREEN}{BOLD}🎉 ALL {total} CHECKS PASSED — backend is working.{RESET}')
        else:
            self.stdout.write(
                f'{RED}{BOLD}❌ {total - passed}/{total} checks FAILED.{RESET} '
                f'({passed} passed)')
