from django.urls import re_path
from .consumers import MonitorConsumer

websocket_urlpatterns = [
	re_path(r'ws/monitors/(?P<monitor_id>\d+)/$', MonitorConsumer.as_asgi()),
]