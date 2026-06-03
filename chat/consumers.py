from channels.generic.websocket import AsyncWebsocketConsumer
import json
import logging
from .crypto import decrypt, encrypt
from .models import Message, Room, RoomJoinRecord, SavedRoom
from datetime import datetime

# How many messages a single history block contains.
BLOCK_SIZE = 50


def make_packet(
    message_id: int, username: str, message: str, sent_at: datetime, total: int,
    kind: str = Message.CHAT,
) -> dict:
    return {
        "type": "message",
        "id": message_id,
        "username": username,
        "message": message,
        "sent_at": datetime.isoformat(sent_at),
        "total": total,
        "kind": kind,
    }


def make_message_item(message: Message) -> dict:
    return {
        "id": message.id,
        "username": message.sender.get_username(),
        "message": decrypt(message.body) if message.kind == Message.CHAT else message.body,
        "sent_at": datetime.isoformat(message.created_at),
        "kind": message.kind,
    }


def make_history_packet(items: list[dict], total: int, offset: int) -> dict:
    """A block of messages.

    `offset` is the index (from the oldest message, 0-based) of `items[0]`; `items` are
    in chronological (oldest-first) order. The client places the block at this offset.
    """
    return {
        "type": "history",
        "messages": items,
        "total": total,
        "offset": offset,
    }


class ChatConsumer(AsyncWebsocketConsumer):

    async def send_packet(self, packet: dict[str, str]):
        await self.send(text_data=json.dumps(packet))

    async def send_packet_to_group(self, packet: dict[str, str]):
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "chat.message", "packet": packet},
        )

    def room_messages(self):
        return Message.objects.filter(room_id=self.room_id).select_related("sender")

    async def room_total(self) -> int:
        return await self.room_messages().acount()

    async def block_at(self, offset: int, count: int) -> list[dict]:
        """`count` messages starting at `offset` from the oldest, chronological order."""
        qs = self.room_messages().order_by("id")[offset : offset + count]
        return [make_message_item(m) async for m in qs]

    async def send_history_block(self, offset: int, count: int):
        total = await self.room_total()
        offset = max(0, min(offset, total))
        items = await self.block_at(offset, count)
        await self.send_packet(make_history_packet(items, total, offset))

    async def send_latest_block(self):
        total = await self.room_total()
        start = max(0, total - BLOCK_SIZE)
        await self.send_history_block(start, BLOCK_SIZE)

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
        self.user_room_group_name = f"user_{self.user.pk}_room_{self.room_id}"

        room = await Room.objects.filter(id=self.room_id).afirst()
        if room is None or not await room.acan_access(self.user):
            await self.close()
            return

        await self.accept()
        room_group_add = self.channel_layer.group_add(self.room_group_name, self.channel_name)
        user_room_group_add = self.channel_layer.group_add(self.user_room_group_name, self.channel_name)
        await self.send_latest_block()
        await room_group_add
        await user_room_group_add

        _, is_first_join = await RoomJoinRecord.objects.aget_or_create(
            room_id=self.room_id, user=self.user
        )
        if is_first_join:
            created_at = datetime.now()
            join_msg = Message(
                room_id=self.room_id,
                sender=self.user,
                display_name=self.user.get_username(),
                body="",
                kind=Message.JOIN,
                created_at=created_at,
            )
            await join_msg.asave()
            total = await self.room_total()
            await self.send_packet_to_group(
                make_packet(
                    message_id=join_msg.id,
                    username=self.user.get_username(),
                    message="",
                    sent_at=created_at,
                    total=total,
                    kind=Message.JOIN,
                )
            )

    async def disconnect(self, code: int) -> None:
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        if hasattr(self, "user_room_group_name"):
            await self.channel_layer.group_discard(self.user_room_group_name, self.channel_name)
        return await super().disconnect(code)

    async def receive(self, text_data=None, bytes_data=None):
        if getattr(self, "_kicked", False):
            return
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
        packet_type = data.get("type")

        if packet_type == "send_message":
            await self.handle_send_message(data)
        elif packet_type == "get_history":
            await self.handle_get_history(data)
        else:
            logging.warning("Unknown client packet type: %r", packet_type)

    async def handle_send_message(self, data: dict):
        body = data["body"]
        display_name = data["display_name"]
        created_at = datetime.now()

        message = Message(
            room_id=self.room_id,
            sender=self.user,
            display_name=display_name,
            body=encrypt(body),
            created_at=created_at,
        )
        # Await the save so the broadcast packet can carry the real db id (used as a
        # pagination cursor) and an up-to-date room total.
        await message.asave()
        total = await self.room_total()

        await self.send_packet_to_group(
            make_packet(
                message_id=message.id,
                username=display_name,
                message=body,
                sent_at=created_at,
                total=total,
            )
        )

    async def handle_get_history(self, data: dict):
        offset = int(data.get("offset", 0))
        count = int(data.get("count", BLOCK_SIZE))
        await self.send_history_block(offset, count)

    async def chat_message(self, event):
        await self.send_packet(event["packet"])

    async def kick_user(self, event):
        self._kicked = True
        await self.send_packet({"type": "kicked"})
        await self.close()
