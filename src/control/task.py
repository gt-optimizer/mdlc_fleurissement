import os

from celery import shared_task
from django.utils import timezone

from control.models import PredictionHistory


@shared_task
def cleanup_old_images():
    today = timezone.now().date()
    # filtre uniquement les images existantes et anciennes
    old_analyses = PredictionHistory.objects.filter(
        image__isnull=False,
        datetime__lte=timezone.now() - timezone.timedelta(days=31)
    )

    deleted_count = 0
    for a in old_analyses:
        if a.image and os.path.isfile(a.image.path):
            os.remove(a.image.path)
            deleted_count += 1
        a.image = None
        a.save()

    return f"Supprimé {deleted_count} images anciennes."