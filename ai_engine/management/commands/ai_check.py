"""
Verify the configured AI model end-to-end.

    python manage.py ai_check

Prints the active AI_MODE / model, checks connectivity (for ollama: that the
server is reachable and the configured model is pulled), then runs one short
generation through the same ModelClient the app uses.
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from ai_engine.model_client import ModelClient

PROMPT = (
    "In two sentences, write a professional, objective opening line for a police "
    "incident report about a reported larceny. Use neutral, formal language."
)


class Command(BaseCommand):
    help = 'Check AI model configuration and run a short test generation.'

    def handle(self, *args, **options):
        mode = getattr(settings, 'AI_MODE', 'mock')
        self.stdout.write(self.style.MIGRATE_HEADING('AI configuration'))
        self.stdout.write(f'  AI_MODE          : {mode}')
        if mode == 'ollama':
            self.stdout.write(f'  LOCAL_MODEL_URL  : {settings.LOCAL_MODEL_URL}')
            self.stdout.write(f'  LOCAL_MODEL_NAME : {settings.LOCAL_MODEL_NAME}')
            self._check_ollama()
        elif mode == 'bedrock':
            self.stdout.write(f'  BEDROCK_REGION   : {settings.BEDROCK_REGION}')
            self.stdout.write(f'  BEDROCK_MODEL_ID : {settings.BEDROCK_MODEL_ID}')
        else:
            self.stdout.write(self.style.WARNING(
                '  Running in MOCK mode — output is a placeholder, not a real model.'))

        self.stdout.write(self.style.MIGRATE_HEADING('\nTest generation'))
        try:
            client = ModelClient()
            text = client.generate(PROMPT, max_tokens=200, temperature=0.2)
        except Exception as exc:  # noqa: BLE001
            self.stdout.write(self.style.ERROR(f'  Generation FAILED: {exc}'))
            return

        self.stdout.write(f'  model_used: {client.model_name}')
        self.stdout.write('  ----- output -----')
        for line in text.strip().splitlines() or ['(empty)']:
            self.stdout.write(f'  {line}')
        self.stdout.write(self.style.SUCCESS('\n✅ AI check complete.'))

    def _check_ollama(self):
        import requests
        try:
            resp = requests.get(f'{settings.LOCAL_MODEL_URL}/api/tags', timeout=5)
            resp.raise_for_status()
            models = [m.get('name', '') for m in resp.json().get('models', [])]
        except Exception as exc:  # noqa: BLE001
            self.stdout.write(self.style.ERROR(
                f'  Ollama not reachable at {settings.LOCAL_MODEL_URL}: {exc}'))
            self.stdout.write(self.style.WARNING(
                '  Start it with `ollama serve` on the host, then re-run.'))
            return
        self.stdout.write(f'  Ollama models available: {", ".join(models) or "(none)"}')
        want = settings.LOCAL_MODEL_NAME
        if not any(m == want or m.startswith(want.split(":")[0]) for m in models):
            self.stdout.write(self.style.WARNING(
                f'  Model "{want}" not found. Pull it with: ollama pull {want}'))
