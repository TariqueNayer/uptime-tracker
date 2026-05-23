import httpx
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import CheckResult, Incident, Monitor

@shared_task
def ping_monitor(monitor_id):

	# ─── 1. fetch the monitor ────────────────────────────────────────
	try:
		monitor = Monitor.objects.get(id=monitor_id, is_active=True)
	except Monitor.DoesNotExist:
		return

	# ─── 2. make the HTTP request ────────────────────────────────────
	start_time = timezone.now()
	status_code = None
	error_message = None
	is_up = False
	response_time_ms = None

	try:
		timeout = httpx.Timeout(
			connect=5.0,
			read=monitor.timeout_seconds,
			write=5.0, 
			pool=5.0,
		)
		with httpx.Client() as client:
			response = client.request(
				method=monitor.method,
				url=monitor.url,
				timeout=timeout,
			)
		status_code = response.status_code
		response_time_ms = int(
			(timezone.now() - start_time).total_seconds() * 1000
		)
		is_up = (status_code == monitor.expected_status_code)

	except httpx.TimeoutException:
		error_message = "Request timed out"

	except httpx.ConnectError:
		error_message = "Connection failed"

	except httpx.RequestError as e:
		error_message = f"Request error: {str(e)}"

	# ─── 3. save the CheckResult ─────────────────────────────────────
	check_result = CheckResult.objects.create(
		monitor=monitor,
		checked_at=start_time,
		is_up=is_up,
		status_code=status_code,
		response_time_ms=response_time_ms,
		error_message=error_message,
	)

	# ─── 4. state machine ────────────────────────────────────────────
	open_incident = Incident.objects.filter(
		monitor=monitor,
		is_resolved=False
	).first()

	if not is_up and open_incident is None:
		# was UP, now DOWN → open a new incident
		Incident.objects.create(
			monitor=monitor,
			is_resolved=False,
		)

	elif is_up and open_incident is not None:
		# was DOWN, now UP → close the incident
		open_incident.resolved_at = timezone.now()
		open_incident.is_resolved = True
		open_incident.save()

# ─── 5. push to WebSocket ────────────────────────────────────────────
	channel_layer = get_channel_layer()
	async_to_sync(channel_layer.group_send)(
		f'monitor_{monitor_id}',
		{
			'type': 'check_result',
			'data': {
				'monitor_id': monitor_id,
				'checked_at': check_result.checked_at.isoformat(),
				'is_up': check_result.is_up,
				'status_code': check_result.status_code,
				'response_time_ms': check_result.response_time_ms,
				'error_message': check_result.error_message,
			}
		}
	)

# cleanup old task results.
@shared_task
def cleanup_old_check_results():
	cutoff = timezone.now() - timedelta(days=30)
	deleted_count, _ = CheckResult.objects.filter(
		checked_at__lt=cutoff
	).delete()
	return f"Deleted {deleted_count} old CheckResult rows"