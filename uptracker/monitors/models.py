from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

from http import HTTPStatus


User = get_user_model()
STATUS_CHOICES = [(s.value, f"{s.value} {s.phrase}") for s in HTTPStatus]

class Monitor(models.Model):
	owner = models.ForeignKey(User, on_delete=models.CASCADE)
	name = models.CharField(max_length=200)
	url = models.URLField()

	class RequestMethod(models.TextChoices):
		GET = 'GET', 'GET'
		POST = 'POST', 'POST'
	
	method = models.CharField(max_length=4, choices= RequestMethod.choices)


	expected_status_code = models.PositiveSmallIntegerField(
		choices=STATUS_CHOICES,
		default=HTTPStatus.OK,
	)
	check_interval_seconds = models.PositiveSmallIntegerField(default=60)
	timeout_seconds = models.PositiveSmallIntegerField(default=30)
	is_active = models.BooleanField()
	created_at = models.DateTimeField(auto_now_add=True)

class Check_results(models.Model):
	monitor = models.ForeignKey(Monitor, on_delete=models.CASCADE)
	checked_at = models.DateTimeField(default=timezone.now)
	is_up = models.BooleanField()
	status_code = models.PositiveSmallIntegerField(
		choices=STATUS_CHOICES,
	)
	response_time_ms = models.PositiveSmallIntegerField()
	error_message = models.CharField(max_length=200)

class Incident(models.Model):
	monitor = models.ForeignKey(Monitor, on_delete=models.CASCADE)
	started_at = models.DateTimeField()
	resolved_at = models.DateTimeField()
	is_resolved = models.BooleanField()