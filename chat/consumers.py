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

    async def send_message_to_group(self, message: Message):
        await self.channel_layer.group_send(
            "group_name",
            {
                "type": "chat.message",
                "display_name": message.display_name,
                "body": message.body,
            },
        )

    async def send_history(self):
        promises = []
        async for message in Message.objects.all():
            promises.append(self.send_message(message))

        for promise in promises:
            await promise

    async def connect(self):
        await self.accept()
        group_add_result = self.channel_layer.group_add("group_name", self.channel_name)
        await self.send_history()
        await group_add_result

    async def disconnect(self, code: int) -> None:
        await self.channel_layer.group_discard("group_name", self.channel_name)
        return await super().disconnect(code)

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

        await self.send_message_to_group(message)

        await save_result

    async def chat_message(self, event):
        display_name = event["display_name"]
        body = event["body"]
        message = Message(body=body, display_name=display_name)
        await self.send_message(message)
