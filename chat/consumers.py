from channels.generic.websocket import AsyncWebsocketConsumer
import json
import logging
from .models import Message


class ChatConsumer(AsyncWebsocketConsumer):

    async def send_message(self, message: Message):
        await self.send(
            text_data=json.dumps(
                {
                    "display_name": message.display_name,
                    "body": message.body,
                }
            )
        )

    async def send_history(self):
        promises = []
        async for message in Message.objects.all():
            promises.append(self.send_message(message))

        for promise in promises:
            await promise

    async def connect(self):
        await self.accept()
        await self.send_history()

    async def receive(self, text_data=None, bytes_data=None):
        if bytes_data:
            preview = bytes_data[:128]
            logging.warning(
                "bytes_data supplied but not handled. Total length: %d, preview (first %d bytes): %s",
                len(bytes_data),
                len(preview),
                preview,
            )

        if not text_data:
            return

        data = json.loads(text_data)
        body = data["body"]
        display_name = data["display_name"]

        message = Message(display_name=display_name, body=body)
        save_result = message.asave()

        await self.send_message(message)

        await save_result
