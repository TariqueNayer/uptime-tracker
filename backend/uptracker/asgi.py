"""
ASGI config for uptracker project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'uptracker.settings')
django.setup()

from monitors.routing import websocket_urlpatterns
from monitors.middleware import JWTAuthMiddleware

application = ProtocolTypeRouter({
	'http': get_asgi_application(),
	'websocket': JWTAuthMiddleware(
		URLRouter(websocket_urlpatterns)
	),
})