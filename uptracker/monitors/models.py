from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
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
	check_interval_seconds = models.PositiveSmallIntegerField(default=600, validators=[MinValueValidator(settings.MIN_CHECK_INTERVAL_SECONDS)])
	timeout_seconds = models.PositiveSmallIntegerField(default=10, validators=[MinValueValidator(5), MaxValueValidator(30)])
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)

class CheckResult(models.Model):
	monitor = models.ForeignKey(Monitor, on_delete=models.CASCADE)
	checked_at = models.DateTimeField(default=timezone.now)
	is_up = models.BooleanField()
	status_code = models.PositiveSmallIntegerField(
		choices=STATUS_CHOICES,
		null=True, blank=True,
	)
	response_time_ms = models.PositiveSmallIntegerField(null=True, blank=True)
	error_message = models.CharField(max_length=200, null=True, blank=True)

class Incident(models.Model):
	monitor = models.ForeignKey(Monitor, on_delete=models.CASCADE)
	started_at = models.DateTimeField(auto_now_add=True)
	resolved_at = models.DateTimeField(null=True, blank=True)
	is_resolved = models.BooleanField(default=False)