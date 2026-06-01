from channels.generic.websocket import AsyncWebsocketConsumer
import json
import logging
from .models import Message, SavedRoom, Room
from datetime import datetime


def make_packet(username: str, message: str, sent_at: datetime) -> dict[str, str]:
    return {
        "type": "message",
        "username": username,
        "message": message,
        "sent_at": datetime.isoformat(sent_at),
    }


class ChatConsumer(AsyncWebsocketConsumer):

    async def send_packet(self, packet: dict[str, str]):
        await self.send(text_data=json.dumps(packet))

    async def send_packet_to_group(self, packet: dict[str, str]):
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "chat.message", "packet": packet},
        )

    async def send_history(self):
        promises = []
        history = Message.objects.filter(room_id=self.room_id).select_related("sender")
        async for message in history:
            promises.append(
                self.send_packet(
                    make_packet(
                        username=message.sender.get_username(),
                        message=message.body,
                        sent_at=message.created_at,
                    )
                )
            )

        for promise in promises:
            await promise

    async def connect(self):

        assert (
            "user" in self.scope
        ), "User must be provided by authentication stack middleware"
        assert self.scope["user"] is not None, "Provided auth user must not be None"

        self.user = self.scope["user"]

        if not self.user.is_authenticated:
            await self.close()
            return

        assert "url_route" in self.scope
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chat_{self.room_id}"

        is_saved_and_exists = await SavedRoom.objects.filter(
            user=self.user, room_id=self.room_id
        ).aexists()

        if not is_saved_and_exists:
            await self.close()
            return

        await self.accept()
        group_add_result = self.channel_layer.group_add(
            self.room_group_name, self.channel_name
        )
        await self.send_history()
        await group_add_result

    async def disconnect(self, code: int) -> None:
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
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

        # TODO: Error handling?
        data = json.loads(text_data)
        body = data["body"]
        display_name = data["display_name"]
        created_at = datetime.now()

        # If we let the db add the send time then we have to block until the operation
        # finishes. Instead we supply the time to the db so that it can save in the background,
        # and we can still have synced times.
        message = Message(
            room_id=self.room_id,
            sender=self.user,
            display_name=display_name,
            body=body,
            created_at=created_at,
        )
        save_result = message.asave()

        await self.send_packet_to_group(
            make_packet(username=display_name, message=body, sent_at=created_at)
        )
        await save_result

    async def chat_message(self, event):
        await self.send_packet(event["packet"])
