import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')

app = Celery('law_enforcement')
# Read CELERY_* settings from Django settings.
app.config_from_object('django.conf:settings', namespace='CELERY')
# Discover tasks.py in each installed app.
app.autodiscover_tasks()
