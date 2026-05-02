from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import CheckResult

@shared_task
def cleanup_old_check_results():
    cutoff = timezone.now() - timedelta(days=30)
    deleted_count, _ = CheckResult.objects.filter(
        checked_at__lt=cutoff
    ).delete()
    return f"Deleted {deleted_count} old CheckResult rows"