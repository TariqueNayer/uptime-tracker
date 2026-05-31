from rest_framework import viewsets, permissions, mixins
from rest_framework.decorators import action
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, OpenApiParameter

from django.core.cache import cache

from .models import Monitor, CheckResult, Incident
from .serializers import MonitorSerializer, CheckResultSerializer, IncidentSerializer

@extend_schema(parameters=[
	OpenApiParameter('id', int, OpenApiParameter.PATH)
])
class MonitorViewSet(viewsets.ModelViewSet):
	serializer_class = MonitorSerializer
	permission_classes = [permissions.IsAuthenticated]

	def get_queryset(self):
		# users only see their own monitors — never someone else's
		return Monitor.objects.filter(owner=self.request.user)

	def list(self, request, *args, **kwargs):
		# unique cache key per user — user A never sees user B's monitors
		cache_key = f'monitors_list_{request.user.id}'
		cached = cache.get(cache_key)

		if cached is not None:
			return Response(cached, headers={'X-Cache': 'HIT'})

		response = super().list(request, *args, **kwargs)
		cache.set(cache_key, response.data, timeout=None)  # no expiry
		response['X-Cache'] = 'MISS'
		return response

	def retrieve(self, request, *args, **kwargs):
		# unique cache key per monitor
		cache_key = f'monitor_detail_{kwargs["pk"]}_{request.user.id}'
		cached = cache.get(cache_key)

		if cached is not None:
			return Response(cached)

		response = super().retrieve(request, *args, **kwargs)
		cache.set(cache_key, response.data, timeout=None)
		return response

	def perform_create(self, serializer):
		# automatically attach the logged-in user as owner
		serializer.save(owner=self.request.user)

	@action(detail=True, methods=['get'])
	def results(self, request, pk=None):
		# GET /monitors/{id}/results/ → all check results for this monitor
		monitor = self.get_object()
		results = CheckResult.objects.filter(monitor=monitor).order_by('-checked_at')[:50]
		serializer = CheckResultSerializer(results, many=True)
		return Response(serializer.data)

	@action(detail=True, methods=['get'])
	def incidents(self, request, pk=None):
		# GET /monitors/{id}/incidents/ → all incidents for this monitor
		monitor = self.get_object()
		incidents = Incident.objects.filter(monitor=monitor).order_by('-started_at')
		serializer = IncidentSerializer(incidents, many=True)
		return Response(serializer.data)