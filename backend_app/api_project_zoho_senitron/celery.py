import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api_project_zoho_senitron.settings')

app = Celery('api_project_zoho_senitron')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.beat_scheduler = 'celery.beat.PersistentScheduler' 

app.autodiscover_tasks()
