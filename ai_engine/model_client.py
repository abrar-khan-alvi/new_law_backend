"""
Unified AI model client.

AI_MODE (settings / .env):
    mock     → returns a deterministic stub narrative (default; no infra needed)
    ollama   → local Ollama server (dev)
    bedrock  → AWS Bedrock custom/foundation model (prod)
"""
import json
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


class ModelClient:
    def __init__(self):
        self.mode = getattr(settings, 'AI_MODE', 'mock')
        if self.mode == 'ollama':
            self.model_name = settings.LOCAL_MODEL_NAME
        elif self.mode == 'bedrock':
            self.model_name = settings.BEDROCK_MODEL_ID
        else:
            self.model_name = 'mock'

    def generate(self, prompt: str, max_tokens: int = 3000,
                 temperature: float = 0.2) -> str:
        if self.mode == 'ollama':
            return self._call_ollama(prompt, max_tokens, temperature)
        if self.mode == 'bedrock':
            return self._call_bedrock(prompt, max_tokens, temperature)
        return self._mock(prompt)

    # ── Mock ─────────────────────────────────────────────────────────
    def _mock(self, prompt: str) -> str:
        logger.info('ModelClient mock generation (%d char prompt)', len(prompt))
        return (
            "[MOCK NARRATIVE]\n\n"
            "This is a placeholder narrative generated in AI_MODE=mock. "
            "It lets the full generate/edit/export pipeline be exercised without "
            "a running model. Switch AI_MODE to 'ollama' or 'bedrock' for real output.\n\n"
            "--- Prompt preview ---\n"
            f"{prompt[:600]}"
        )

    # ── Ollama (dev) ─────────────────────────────────────────────────
    def _call_ollama(self, prompt, max_tokens, temperature) -> str:
        import requests
        try:
            response = requests.post(
                f"{settings.LOCAL_MODEL_URL}/api/generate",
                json={
                    'model': settings.LOCAL_MODEL_NAME,
                    'prompt': prompt,
                    'stream': False,
                    'options': {
                        'temperature': temperature,
                        'num_predict': max_tokens,
                    },
                },
                timeout=180,
            )
            response.raise_for_status()
            return response.json()['response'].strip()
        except requests.ConnectionError as exc:
            raise RuntimeError(
                'Ollama is not reachable. Start it (ollama serve) or set AI_MODE=mock.'
            ) from exc

    # ── Bedrock (prod) ───────────────────────────────────────────────
    def _call_bedrock(self, prompt, max_tokens, temperature) -> str:
        import boto3
        client = boto3.client(
            'bedrock-runtime',
            region_name=settings.BEDROCK_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
        )
        response = client.converse(
            modelId=settings.BEDROCK_MODEL_ID,
            messages=[{'role': 'user', 'content': [{'text': prompt}]}],
            inferenceConfig={
                'maxTokens': max_tokens,
                'temperature': temperature,
                'topP': 0.9
            }
        )
        return response['output']['message']['content'][0]['text'].strip()
