#!/usr/bin/env python
"""Seed a room with messages by driving the real ChatConsumer.

This connects to a room through the actual websocket consumer (the same
``connect`` / ``send_message`` path the browser uses) and sends N messages, so the
rows it writes are indistinguishable from real chat traffic. It runs the consumer
in-process with channels' WebsocketCommunicator over an in-memory channel layer, so it
needs no running server and no Redis — only access to the project's database.

Usage:
    python seed_messages.py                       # zamboni-fan-club, 1000 messages
    python seed_messages.py --room my-room --count 250 --user my_bot

The room, the sending user, and that user's SavedRoom membership are created if missing.
"""

import argparse
import asyncio
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from channels.db import database_sync_to_async  # noqa: E402
from channels.routing import URLRouter  # noqa: E402
from channels.testing import WebsocketCommunicator  # noqa: E402
from django.contrib.auth import get_user_model  # noqa: E402
from django.test import override_settings  # noqa: E402

from chat.models import Message, Room, SavedRoom  # noqa: E402
from chat.routing import websocket_urlpatterns  # noqa: E402

# In-memory layer so group_send works without Redis (matches the test setup).
IN_MEMORY_CHANNEL_LAYER = {
    "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}
}


@database_sync_to_async
def ensure_user_room_membership(username, room_id):
    User = get_user_model()
    user, created = User.objects.get_or_create(username=username)
    if created:
        user.set_password("seed-password")
        user.save()
    room, _ = Room.objects.get_or_create(
        id=room_id, defaults={"owner": user, "name": room_id.replace("-", " ").title()}
    )
    SavedRoom.objects.get_or_create(user=user, room=room)
    return user


@database_sync_to_async
def message_count(room_id):
    return Message.objects.filter(room_id=room_id).count()


async def seed(room_id, count, username):
    user = await ensure_user_room_membership(username, room_id)

    communicator = WebsocketCommunicator(
        URLRouter(websocket_urlpatterns), f"/ws/chat/{room_id}/"
    )
    communicator.scope["user"] = user

    connected, _ = await communicator.connect()
    if not connected:
        raise SystemExit(f"Failed to connect to room {room_id!r} as {username!r}")

    # Drain the initial history block the consumer sends on connect.
    await communicator.receive_json_from(timeout=10)

    for i in range(1, count + 1):
        await communicator.send_json_to(
            {
                "type": "send_message",
                "display_name": username,
                "body": f"Zamboni fact #{i}: the ice resurfacer was invented in 1949.",
            }
        )
        # Wait for the broadcast echo; the consumer only broadcasts after the row is
        # saved, so this keeps us in lockstep and confirms each insert landed.
        await communicator.receive_json_from(timeout=10)
        if i % 100 == 0:
            print(f"  sent {i}/{count}")

    await communicator.disconnect()
    total = await message_count(room_id)
    print(f"Done. Room {room_id!r} now has {total} messages.")


def main():
    parser = argparse.ArgumentParser(description="Seed a chat room with messages.")
    parser.add_argument("--room", default="zamboni-fan-club", help="room id")
    parser.add_argument("--count", type=int, default=1000, help="messages to send")
    parser.add_argument("--user", default="zamboni_bot", help="sending username")
    args = parser.parse_args()

    print(f"Seeding {args.count} messages into {args.room!r} as {args.user!r}...")
    with override_settings(CHANNEL_LAYERS=IN_MEMORY_CHANNEL_LAYER):
        asyncio.run(seed(args.room, args.count, args.user))


if __name__ == "__main__":
    main()
