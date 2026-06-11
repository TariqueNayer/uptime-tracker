from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from unittest.mock import patch, MagicMock
from monitors.tasks import ping_monitor

from .models import Monitor, CheckResult, Incident

# Create your tests here.

User_model = get_user_model()
def make_user(username : str ,is_staff : bool = False ):
	return User_model.objects.create_user(username=username, is_staff=is_staff)

def make_monitor(user, name):
	return Monitor.objects.create(
		name=name, 
		owner=user, 
		url="https://testurl.com", 
		method='GET', 
		expected_status_code=200,
	)

class MonitorViewSetTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.user = make_user("simple-user")

	def test_unauthenticated_cannot_list_monitors(self):
		response = self.client.get(reverse("monitor-list"))
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


	def test_create_monitor_with_signed_in_user_as_user(self):
		self.client.force_authenticate(self.user)
		response = self.client.post(reverse("monitor-list"), {
			"name": "test_monitor",
			"url": "https://testurl.com",
			"method": "GET",
			"expected_status_code": 200,
		})

		self.assertEqual(response.status_code, 201)
		self.assertEqual(response.data["owner"], self.user.id)


	def test_user_only_sees_their_own_monitors(self):
		self.user_a = make_user("user_a")
		self.user_b = make_user("user_b")
		make_monitor(user=self.user_a, name="monitor-a")
		make_monitor(user=self.user_b, name="monitor-b")

		# User A 
		self.client.force_authenticate(self.user_a)
		response = self.client.get(reverse("monitor-list"))
		self.assertTrue(len(response.data) > 0)
		for monitor in response.data:
			retrieved = Monitor.objects.get(id=monitor["id"])
			self.assertEqual(retrieved.owner, self.user_a)

		# User B
		self.client.force_authenticate(self.user_b)
		response = self.client.get(reverse("monitor-list"))
		self.assertTrue(len(response.data) > 0)
		for monitor in response.data:
			retrieved = Monitor.objects.get(id=monitor["id"])
			self.assertEqual(retrieved.owner, self.user_b)

	@patch("monitors.tasks.httpx.Client")
	def test_ping_task_creates_result_on_success(self, mock_client_class):
		# mock the response
		mock_response = MagicMock()
		mock_response.status_code = 200

		
		mock_client_class.return_value.__enter__.return_value.request.return_value = mock_response

		monitor = Monitor.objects.create(
			owner=self.user,
			name="test_monitor",
			url="https://example.com",
			method="GET",
			expected_status_code=200,
		)

		ping_monitor(str(monitor.id))  # pass as string since it's a UUID

		result = CheckResult.objects.get(monitor=monitor)
		self.assertTrue(result.is_up)
		self.assertEqual(result.status_code, 200)

	@patch("monitors.tasks.httpx.Client")
	def test_ping_task_creates_incident_when_monitor_is_down(self, mock_client_class):
		mock_response = MagicMock()
		mock_response.status_code = 500  # unexpected → is_up = False
		mock_client_class.return_value.__enter__.return_value.request.return_value = mock_response

		monitor = Monitor.objects.create(
			owner=self.user,
			name="test_monitor",
			url="https://example.com",
			method="GET",
			expected_status_code=200,  # 500 != 200, so is_up = False
		)

		ping_monitor(str(monitor.id))

		self.assertEqual(Incident.objects.filter(monitor=monitor, is_resolved=False).count(), 1)

	@patch("monitors.tasks.httpx.Client")
	def test_ping_task_resolves_incident_when_monitor_is_back_up(self, mock_client_class):
		mock_response = MagicMock()
		mock_response.status_code = 200
		mock_client_class.return_value.__enter__.return_value.request.return_value = mock_response

		monitor = Monitor.objects.create(
			owner=self.user,
			name="test_monitor",
			url="https://example.com",
			method="GET",
			expected_status_code=200,
		)
		# pre-existing open incident (monitor was already down)
		Incident.objects.create(monitor=monitor, is_resolved=False)

		ping_monitor(str(monitor.id))

		incident = Incident.objects.get(monitor=monitor)
		self.assertTrue(incident.is_resolved)
		self.assertIsNotNone(incident.resolved_at)