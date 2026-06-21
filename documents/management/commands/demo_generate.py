"""
End-to-end demo of a REAL generation through the HTTP API (live model + RAG).

    docker compose exec backend python manage.py demo_generate

Provisions a realistic officer, logs in, POSTs the larceny incident sample to
/api/documents/generate/ (which runs the prompt builder → RAG retrieval →
Ollama), prints the AI narrative + metadata, then exports a PDF to docs/.
"""
import time

import requests
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from subscriptions.models import Plan, Subscription

User = get_user_model()

EMAIL = 'demo_officer@example.com'
PASSWORD = 'DemoOfficer123!'
OUT_PATH = 'docs/sample_incident_live.pdf'

PAYLOAD = {
    'doc_type': 'incident_report',
    'narrative_style': 'third_person',
    'form_data': {
        'case_number': None,
        'incident': {
            'categories': ['Larceny', 'General Information'],
            'urgency': 'normal',
            'date': '2026-01-06',
            'time': '19:30',
            'location': 'University Commons Room #1240-B',
            'reported_date': '2026-01-06',
            'reported_time': '19:45',
        },
        'involved_parties': [
            {'role': 'complainant', 'full_name': 'Justin Kim', 'id_number': '0281984',
             'dob': '2003-02-05', 'email': 'justin.kim@student.life.edu', 'phone': '267-752-0534'},
            {'role': 'alleged', 'full_name': 'Martrece Smith', 'id_number': '0271959',
             'dob': '2001-07-21', 'phone': '224-566-3916'},
        ],
        'property_items': [{'type': 'currency', 'value': 400, 'status': 'missing'}],
        'notifications': {
            'outside_agency': 'N/A', 'ems_notified': False, 'fire_dept_notified': False,
            'weapon_involved': False, 'alcohol_drugs': False, 'is_hazing': False,
        },
        'facts': {
            'who': 'Complainant Justin Kim; alleged party Martrece Smith (roommate)',
            'what': 'Report of $400 in U.S. currency missing from a wallet',
            'when': 'Loss occurred between 1930 hours on 01/04/2026 and 1930 hours on 01/06/2026',
            'where': 'Dormitory room NC1 1240B, University Commons',
            'why': 'Complainant suspects roommate; ongoing roommate dispute',
            'how': 'Wallet was located under the bed with the cash missing; no other contents taken',
            'officer_actions': (
                'Took the report at 1945 hours; telephoned Martrece Smith at 2001 hours and '
                'left a voicemail; Smith returned the call at 2010 hours and denied knowledge '
                'of the missing funds; documented the timeline and noted discrepancies.'),
            'additional_notes': "Complainant's written statement later listed $500 missing.",
        },
        'attachments': [],
    },
}


class Command(BaseCommand):
    help = 'Run a real end-to-end document generation and export a PDF.'

    def add_arguments(self, parser):
        parser.add_argument('--base-url', default='http://localhost:8000')

    def handle(self, *args, **opts):
        base = opts['base_url'].rstrip('/')
        self._provision()
        token = self._login(base)
        headers = {'Authorization': f'Bearer {token}'}

        self.stdout.write(self.style.MIGRATE_HEADING(
            '\nGenerating incident report (live model + RAG)…'))
        self.stdout.write('  (first call may take 10-60s while Ollama loads the model)')
        start = time.time()
        r = requests.post(f'{base}/api/documents/generate/', headers=headers,
                          json=PAYLOAD, timeout=300)
        elapsed = time.time() - start
        if r.status_code != 201:
            self.stdout.write(self.style.ERROR(f'  Generation failed: HTTP {r.status_code} {r.text}'))
            return

        doc = r.json()
        self.stdout.write(self.style.SUCCESS(f'  HTTP 201 in {elapsed:.1f}s'))
        self.stdout.write(f"  doc id        : {doc['id']}")
        self.stdout.write(f"  case number   : {doc['case_number']}")
        self.stdout.write(f"  model_used    : {doc.get('model_used')}")
        self.stdout.write(f"  gen time (ms) : {doc.get('generation_time_ms')}")
        self.stdout.write(self.style.MIGRATE_HEADING('\n----- AI NARRATIVE -----'))
        self.stdout.write(doc.get('ai_narrative', '(none)'))

        flags = doc.get('leak_flags') or []
        self.stdout.write(self.style.MIGRATE_HEADING('\n----- LEAK CHECK -----'))
        if not flags:
            self.stdout.write(self.style.SUCCESS('  ✅ No ungrounded details detected.'))
        else:
            self.stdout.write(self.style.WARNING(
                f'  ⚠️  {len(flags)} ungrounded detail(s) flagged for officer review:'))
            for f in flags:
                self.stdout.write(f"     - {f['type']}: {f['value']}")

        # Export PDF through the API and save it.
        self.stdout.write(self.style.MIGRATE_HEADING('\nExporting PDF…'))
        rp = requests.post(f"{base}/api/documents/{doc['id']}/export/", headers=headers,
                           json={'format': 'pdf'}, timeout=120)
        if rp.ok and rp.content[:4] == b'%PDF':
            with open(OUT_PATH, 'wb') as fh:
                fh.write(rp.content)
            self.stdout.write(self.style.SUCCESS(
                f'  Saved {len(rp.content)} bytes → {OUT_PATH}'))
        else:
            self.stdout.write(self.style.ERROR(
                f'  PDF export failed: HTTP {rp.status_code}'))

        self.stdout.write(self.style.SUCCESS('\n✅ End-to-end demo complete.'))

    def _provision(self):
        pro = Plan.objects.filter(name='pro').first() or Plan.objects.first()
        user, _ = User.objects.get_or_create(
            email=EMAIL, defaults={'role': 'officer', 'first_name': 'Edward', 'last_name': 'Brown'})
        user.role = 'officer'
        user.email_verified = True
        user.is_verified = True
        user.first_name = 'Edward'
        user.last_name = 'Brown'
        user.rank = 'Police Officer'
        user.badge_number = '2911'
        user.department_name = 'Life University Police Department'
        user.department_address = '1269 Barclay Cir SE, Marietta, GA 30060'
        user.department_state = 'GA'
        user.ori = 'GA0331100'
        user.phone_number = '770-426-2911'
        user.set_password(PASSWORD)
        user.save()
        sub, _ = Subscription.objects.get_or_create(user=user, defaults={'plan': pro})
        sub.plan = pro
        sub.status = 'active'
        sub.documents_generated_this_month = 0
        sub.save()
        self.stdout.write(f'Provisioned demo officer {EMAIL} on plan "{pro.name}".')

    def _login(self, base):
        r = requests.post(f'{base}/api/auth/login/',
                          json={'email': EMAIL, 'password': PASSWORD}, timeout=30)
        r.raise_for_status()
        return r.json()['access']
