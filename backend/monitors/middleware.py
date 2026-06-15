from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError

User = get_user_model()


@database_sync_to_async
def get_user_from_token(token):
	try:
		validated = AccessToken(token)
		return User.objects.get(id=validated['user_id'])
	except (TokenError, User.DoesNotExist):
		return AnonymousUser()


class JWTAuthMiddleware:

	def __init__(self, inner):
		self.inner = inner

	async def __call__(self, scope, receive, send):
		# parse cookies from WebSocket handshake headers
		cookies = {}
		for header_name, header_value in scope.get('headers', []):
			if header_name == b'cookie':
				for chunk in header_value.decode().split(';'):
					parts = chunk.strip().split('=', 1)
					if len(parts) == 2:
						cookies[parts[0].strip()] = parts[1].strip()

		token = cookies.get('access_token')

		if token:
			scope['user'] = await get_user_from_token(token)
		else:
			scope['user'] = AnonymousUser()

		return await self.inner(scope, receive, send)