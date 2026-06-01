from contextlib import asynccontextmanager
from unittest.mock import patch

from channels.db import database_sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TransactionTestCase, override_settings

from .models import Message, Room, SavedRoom
from .routing import websocket_urlpatterns

User = get_user_model()


@database_sync_to_async
def create_user(username):
    return User.objects.create_user(username=username, password="password123")


@database_sync_to_async
def save_room(user, room_id):
    """Create the room (if needed) and save it for the user.

    ChatConsumer.connect rejects users who have not saved the room, so this is the
    precondition for a successful connection.
    """
    room, _ = Room.objects.get_or_create(
        id=room_id, defaults={"owner": user, "name": room_id}
    )
    SavedRoom.objects.get_or_create(user=user, room=room)
    return room


@database_sync_to_async
def create_messages(room, sender, bodies):
    """Create messages in id (chronological) order; returns the created ids."""
    ids = []
    for body in bodies:
        m = Message.objects.create(
            room=room, sender=sender, display_name=sender.username, body=body
        )
        ids.append(m.id)
    return ids


@override_settings(
    CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
)
class ChatConsumerRoomTests(TransactionTestCase):
    """Room-related behavior of ChatConsumer.

    Tests drive a bare URLRouter (rather than the production AuthMiddlewareStack in
    config/asgi.py) so we can populate scope["url_route"]["kwargs"]["room_id"] while
    injecting scope["user"] directly to control authentication.
    """

    @asynccontextmanager
    async def joined(self, user, room_id):
        """Connect ``user`` to ``room_id``; drains the initial history packet.

        Yields ``(communicator, connected, initial_history)`` where ``initial_history``
        is the ``history`` packet the server sends on connect (None if rejected).
        Disconnecting happens here, in the same event loop the async test runs in.
        """
        communicator = WebsocketCommunicator(
            URLRouter(websocket_urlpatterns), f"/ws/chat/{room_id}/"
        )
        communicator.scope["user"] = user  # type: ignore
        connected, _ = await communicator.connect()
        initial_history = await communicator.receive_json_from() if connected else None
        try:
            yield communicator, connected, initial_history
        finally:
            if connected:
                await communicator.disconnect()

    async def send_message(self, communicator, display_name, body):
        await communicator.send_json_to(
            {"type": "send_message", "display_name": display_name, "body": body}
        )

    async def get_history(self, communicator, offset, count):
        await communicator.send_json_to(
            {"type": "get_history", "offset": offset, "count": count}
        )
        return await communicator.receive_json_from()

    # --- connection / auth -------------------------------------------------

    async def test_authenticated_user_can_connect_to_saved_room(self):
        user = await create_user("alice")
        await save_room(user, "general")
        async with self.joined(user, "general") as (_, connected, _):
            self.assertTrue(connected)

    async def test_unauthenticated_user_is_rejected(self):
        async with self.joined(AnonymousUser(), "general") as (_, connected, _):
            self.assertFalse(connected)

    # --- initial history block --------------------------------------------

    async def test_connect_sends_latest_block_not_everything(self):
        user = await create_user("alice")
        room = await save_room(user, "general")
        ids = await create_messages(room, user, [f"m{i}" for i in range(5)])

        with patch("chat.consumers.BLOCK_SIZE", 3):
            async with self.joined(user, "general") as (_, _, history):
                self.assertEqual(history["type"], "history")
                self.assertEqual(history["total"], 5)
                self.assertEqual(history["offset"], 2)  # latest block: 5 - 3
                returned = [m["id"] for m in history["messages"]]
                # oldest-first, only the latest BLOCK_SIZE messages
                self.assertEqual(returned, ids[2:5])

    # --- offset history blocks --------------------------------------------

    async def test_get_history_returns_block_at_offset(self):
        user = await create_user("alice")
        room = await save_room(user, "general")
        ids = await create_messages(room, user, [f"m{i}" for i in range(6)])

        async with self.joined(user, "general") as (comm, _, _):
            block = await self.get_history(comm, offset=0, count=3)
            self.assertEqual(block["offset"], 0)
            self.assertEqual(block["total"], 6)
            self.assertEqual([m["id"] for m in block["messages"]], ids[0:3])  # oldest-first

            block = await self.get_history(comm, offset=3, count=3)
            self.assertEqual(block["offset"], 3)
            self.assertEqual([m["id"] for m in block["messages"]], ids[3:6])

    async def test_get_history_offset_is_clamped(self):
        user = await create_user("alice")
        room = await save_room(user, "general")
        await create_messages(room, user, [f"m{i}" for i in range(3)])

        async with self.joined(user, "general") as (comm, _, _):
            block = await self.get_history(comm, offset=999, count=50)
            self.assertEqual(block["offset"], 3)  # clamped to total
            self.assertEqual(block["messages"], [])

    # --- live broadcast ----------------------------------------------------

    async def test_send_message_broadcasts_with_id_and_total(self):
        alice = await create_user("alice")
        bob = await create_user("bob")
        await save_room(alice, "general")
        await save_room(bob, "general")
        async with self.joined(alice, "general") as (alice_comm, _, _), \
                self.joined(bob, "general") as (bob_comm, _, _):
            await self.send_message(alice_comm, "alice", "hi")

            packet = await bob_comm.receive_json_from()
            self.assertEqual(packet["type"], "message")
            self.assertEqual(packet["username"], "alice")
            self.assertEqual(packet["message"], "hi")
            self.assertIsNotNone(packet["id"])
            self.assertEqual(packet["total"], 1)

    async def test_messages_not_broadcast_across_rooms(self):
        # Live broadcasts are scoped to the per-room channel group, so a client in a
        # different room must not receive the message.
        alice = await create_user("alice")
        bob = await create_user("bob")
        await save_room(alice, "room-a")
        await save_room(bob, "room-b")
        async with self.joined(alice, "room-a") as (alice_comm, _, _), \
                self.joined(bob, "room-b") as (bob_comm, _, _):
            await self.send_message(alice_comm, "alice", "room-a only")

            self.assertTrue(await bob_comm.receive_nothing(timeout=0.5))

    # --- history is room-scoped -------------------------------------------

    async def test_initial_history_is_scoped_to_room(self):
        """A client joining a room only gets that room's history on connect."""
        alice = await create_user("alice")
        bob = await create_user("bob")
        room_a = await save_room(alice, "room-a")
        await save_room(bob, "room-b")
        await create_messages(room_a, alice, ["room-a message"])

        async with self.joined(bob, "room-b") as (_, _, history):
            self.assertEqual(history["messages"], [])
            self.assertEqual(history["total"], 0)

    async def test_initial_history_replays_messages_from_same_room(self):
        """A client joining a room receives that room's prior messages on connect."""
        alice = await create_user("alice")
        bob = await create_user("bob")
        room = await save_room(alice, "general")
        await save_room(bob, "general")
        await create_messages(room, alice, ["earlier message"])

        async with self.joined(bob, "general") as (_, _, history):
            self.assertEqual(len(history["messages"]), 1)
            self.assertEqual(history["messages"][0]["message"], "earlier message")
            self.assertEqual(history["total"], 1)
