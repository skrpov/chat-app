from contextlib import asynccontextmanager

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
def message_count():
    return Message.objects.count()


@database_sync_to_async
def latest_message():
    return Message.objects.select_related("sender").latest("created_at")


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
        """Connect ``user`` to ``room_id`` and always disconnect in the same loop.

        Disconnecting here (rather than via addCleanup) keeps the websocket lifecycle on
        the single event loop the async test runs in, avoiding cross-loop errors.
        """
        communicator = WebsocketCommunicator(
            URLRouter(websocket_urlpatterns), f"/ws/chat/{room_id}/"
        )
        communicator.scope["user"] = user # type: ignore
        connected, _ = await communicator.connect()
        try:
            yield communicator, connected
        finally:
            # A rejected connection was never accepted, so there is nothing to tear
            # down (and the consumer only sets room_group_name once accepted).
            if connected:
                await communicator.disconnect()

    async def send(self, communicator, display_name, body):
        await communicator.send_json_to({"display_name": display_name, "body": body})

    async def test_authenticated_user_can_connect_to_saved_room(self):
        user = await create_user("alice")
        await save_room(user, "general")
        async with self.joined(user, "general") as (_, connected):
            self.assertTrue(connected)

    async def test_unauthenticated_user_is_rejected(self):
        async with self.joined(AnonymousUser(), "general") as (_, connected):
            self.assertFalse(connected)

    async def test_message_broadcast_to_others_in_same_room(self):
        alice = await create_user("alice")
        bob = await create_user("bob")
        await save_room(alice, "general")
        await save_room(bob, "general")
        async with self.joined(alice, "general") as (alice_comm, _), self.joined(
            bob, "general"
        ) as (bob_comm, _):
            await self.send(alice_comm, "alice", "hi")

            packet = await bob_comm.receive_json_from()
            self.assertEqual(packet["type"], "message")
            self.assertEqual(packet["username"], "alice")
            self.assertEqual(packet["message"], "hi")

    async def test_sender_receives_own_message(self):
        alice = await create_user("alice")
        await save_room(alice, "general")
        async with self.joined(alice, "general") as (alice_comm, _):
            await self.send(alice_comm, "alice", "hi")

            packet = await alice_comm.receive_json_from()
            self.assertEqual(packet["message"], "hi")
            self.assertEqual(packet["username"], "alice")

    async def test_message_is_persisted_with_room(self):
        alice = await create_user("alice")
        await save_room(alice, "general")
        async with self.joined(alice, "general") as (alice_comm, _):
            await self.send(alice_comm, "alice", "persist me")
            await alice_comm.receive_json_from()  # wait for the broadcast round-trip

        self.assertEqual(await message_count(), 1)
        message = await latest_message()
        self.assertEqual(message.body, "persist me")
        self.assertEqual(message.sender.username, "alice")
        self.assertEqual(message.room_id, "general")

    async def test_messages_not_broadcast_across_rooms(self):
        # Live broadcasts are scoped to the per-room channel group, so a client in a
        # different room must not receive the message.
        alice = await create_user("alice")
        bob = await create_user("bob")
        await save_room(alice, "room-a")
        await save_room(bob, "room-b")
        async with self.joined(alice, "room-a") as (alice_comm, _), self.joined(
            bob, "room-b"
        ) as (bob_comm, _):
            await self.send(alice_comm, "alice", "room-a only")

            self.assertTrue(await bob_comm.receive_nothing(timeout=0.5))

    async def test_history_is_scoped_to_room(self):
        """A client joining a room only receives that room's history.

        send_history filters by room_id and each Message carries a room FK, so a message
        posted in room-a is not replayed to a client joining room-b.
        """
        alice = await create_user("alice")
        bob = await create_user("bob")
        await save_room(alice, "room-a")
        await save_room(bob, "room-b")

        # alice posts in room-a; the message is persisted against room-a.
        async with self.joined(alice, "room-a") as (alice_comm, _):
            await self.send(alice_comm, "alice", "room-a history")
            await alice_comm.receive_json_from()  # ensure it is saved/broadcast

            # bob joins a different room and should receive no history from room-a.
            async with self.joined(bob, "room-b") as (bob_comm, _):
                self.assertTrue(await bob_comm.receive_nothing(timeout=0.5))

    async def test_history_replays_messages_from_same_room(self):
        """A client joining a room receives that room's prior messages on connect."""
        alice = await create_user("alice")
        bob = await create_user("bob")
        await save_room(alice, "general")
        await save_room(bob, "general")

        async with self.joined(alice, "general") as (alice_comm, _):
            await self.send(alice_comm, "alice", "earlier message")
            await alice_comm.receive_json_from()  # ensure it is persisted

            async with self.joined(bob, "general") as (bob_comm, _):
                packet = await bob_comm.receive_json_from()
                self.assertEqual(packet["message"], "earlier message")
                self.assertEqual(packet["username"], "alice")
