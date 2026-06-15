import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Monitor


class MonitorConsumer(AsyncWebsocketConsumer):

	async def connect(self):
		self.monitor_id = self.scope['url_route']['kwargs']['monitor_id']
		self.group_name = f'monitor_{self.monitor_id}'

		# reject anonymous users immediately
		if not self.scope['user'].is_authenticated:
			await self.close()
			return

		# verify monitor exists and belongs to this user
		monitor = await self.get_monitor()
		if monitor is None:
			await self.close()
			return

		# join the channel group for this monitor
		await self.channel_layer.group_add(
			self.group_name,
			self.channel_name
		)
		await self.accept()

	async def disconnect(self, close_code):
		await self.channel_layer.group_discard(
			self.group_name,
			self.channel_name
		)

	# receives messages from the channel layer (sent by Celery worker)
	async def check_result(self, event):
		await self.send(text_data=json.dumps(event['data']))

	@database_sync_to_async
	def get_monitor(self):
		try:
			return Monitor.objects.get(
				id=self.monitor_id,
				owner=self.scope['user']
			)
		except Monitor.DoesNotExist:
			return None