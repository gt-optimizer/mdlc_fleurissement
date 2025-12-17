import os

from celery.schedules import crontab

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ton_projet.settings')

app = Celery('ton_projet')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'cleanup-old-images-every-day': {
        'task': 'control.tasks.cleanup_old_images',
        'schedule': crontab(hour=0, minute=0),  # Exécute tous les jours à minuit
    },
}