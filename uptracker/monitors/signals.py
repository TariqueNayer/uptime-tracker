from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

from django_celery_beat.models import PeriodicTask, IntervalSchedule
from .models import Monitor
import json


@receiver(post_save, sender=Monitor)
def sync_periodic_task(sender, instance, created, **kwargs):
	if created and instance.is_active:
		# new monitor → create a periodic task
		schedule, _ = IntervalSchedule.objects.get_or_create(
			every=instance.check_interval_seconds,
			period=IntervalSchedule.SECONDS,
		)
		PeriodicTask.objects.create(
			interval=schedule,
			name=f'monitor-{instance.id}',
			task='monitors.tasks.ping_monitor',
			args=json.dumps([instance.id]),
		)

	elif not created:
		# existing monitor updated → sync the periodic task
		try:
			pt = PeriodicTask.objects.get(name=f'monitor-{instance.id}')
			if instance.is_active:
				# update interval in case user changed check_interval_seconds
				schedule, _ = IntervalSchedule.objects.get_or_create(
					every=instance.check_interval_seconds,
					period=IntervalSchedule.SECONDS,
				)
				pt.interval = schedule
				pt.enabled = True
				pt.save()
			else:
				# monitor paused → disable without deleting
				pt.enabled = False
				pt.save()
		except PeriodicTask.DoesNotExist:
			pass


@receiver(post_delete, sender=Monitor)
def delete_periodic_task(sender, instance, **kwargs):
	PeriodicTask.objects.filter(name=f'monitor-{instance.id}').delete()

@receiver(post_save, sender=Monitor)
def invalidate_monitor_cache(sender, instance, **kwargs):
	# clear this monitor's detail cache
	cache.delete(f'monitor_detail_{instance.id}_{instance.owner.id}')
	# clear this user's list cache
	cache.delete(f'monitors_list_{instance.owner.id}')

@receiver(post_delete, sender=Monitor)
def invalidate_monitor_cache_on_delete(sender, instance, **kwargs):
	cache.delete(f'monitor_detail_{instance.id}_{instance.owner.id}')
	cache.delete(f'monitors_list_{instance.owner.id}')