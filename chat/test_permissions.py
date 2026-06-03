from contextlib import asynccontextmanager

from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import TestCase, TransactionTestCase, override_settings

_IN_MEMORY_CHANNELS = override_settings(
    CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
)

from .models import Room, RoomMember, SavedRoom
from .routing import websocket_urlpatterns

User = get_user_model()


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def make_user(username):
    return User.objects.create_user(username=username, password="pw")


def make_room(owner, room_id, visibility=Room.PUBLIC):
    return Room.objects.create(id=room_id, owner=owner, name=room_id, visibility=visibility)


def add_member(room, user, status):
    return RoomMember.objects.create(room=room, user=user, status=status)


@database_sync_to_async
def async_make_user(username):
    return make_user(username)


@database_sync_to_async
def async_make_room(owner, room_id, visibility=Room.PUBLIC):
    return make_room(owner, room_id, visibility)


@database_sync_to_async
def async_add_member(room, user, status):
    return add_member(room, user, status)


# ---------------------------------------------------------------------------
# Room.can_access unit tests
# ---------------------------------------------------------------------------


class TestRoomAccess(TestCase):
    def setUp(self):
        self.owner = make_user("owner")
        self.alice = make_user("alice")

    def _room(self, visibility=Room.PUBLIC):
        return make_room(self.owner, "general", visibility=visibility)

    def test_owner_can_access_public_room(self):
        self.assertTrue(self._room(Room.PUBLIC).can_access(self.owner))

    def test_owner_can_access_private_room(self):
        self.assertTrue(self._room(Room.PRIVATE).can_access(self.owner))

    def test_public_room_allows_non_member(self):
        self.assertTrue(self._room(Room.PUBLIC).can_access(self.alice))

    def test_public_room_rejects_blacklisted_user(self):
        room = self._room(Room.PUBLIC)
        add_member(room, self.alice, RoomMember.BLACKLIST)
        self.assertFalse(room.can_access(self.alice))

    def test_private_room_rejects_non_whitelisted(self):
        self.assertFalse(self._room(Room.PRIVATE).can_access(self.alice))

    def test_private_room_allows_whitelisted_user(self):
        room = self._room(Room.PRIVATE)
        add_member(room, self.alice, RoomMember.WHITELIST)
        self.assertTrue(room.can_access(self.alice))


# ---------------------------------------------------------------------------
# join_room_view permission tests
# ---------------------------------------------------------------------------


class TestJoinRoomViewPermissions(TestCase):
    def setUp(self):
        self.owner = make_user("owner")
        self.alice = make_user("alice")
        self.client.force_login(self.alice)

    def _join(self, room_id):
        return self.client.post("/rooms/join/", {"room_id": room_id})

    def test_public_room_can_be_joined(self):
        make_room(self.owner, "general")
        self.assertEqual(self._join("general").status_code, 204)

    def test_private_room_non_whitelisted_gets_not_found(self):
        make_room(self.owner, "secret", visibility=Room.PRIVATE)
        self.assertContains(self._join("secret"), "No room found with that ID")

    def test_private_room_whitelisted_user_can_join(self):
        room = make_room(self.owner, "secret", visibility=Room.PRIVATE)
        add_member(room, self.alice, RoomMember.WHITELIST)
        self.assertEqual(self._join("secret").status_code, 204)

    def test_public_room_blacklisted_user_gets_not_found(self):
        room = make_room(self.owner, "general")
        add_member(room, self.alice, RoomMember.BLACKLIST)
        self.assertContains(self._join("general"), "No room found with that ID")

    def test_joining_saves_room(self):
        make_room(self.owner, "general")
        self._join("general")
        self.assertTrue(SavedRoom.objects.filter(room_id="general", user=self.alice).exists())

    def test_navigating_to_room_saves_it(self):
        make_room(self.owner, "general")
        self.client.get("/general/")
        self.assertTrue(SavedRoom.objects.filter(room_id="general", user=self.alice).exists())

    def test_navigating_to_private_room_without_whitelist_does_not_save(self):
        make_room(self.owner, "secret", visibility=Room.PRIVATE)
        self.client.get("/secret/")
        self.assertFalse(SavedRoom.objects.filter(room_id="secret", user=self.alice).exists())

    def test_navigating_to_room_while_blacklisted_does_not_save(self):
        room = make_room(self.owner, "general")
        add_member(room, self.alice, RoomMember.BLACKLIST)
        self.client.get("/general/")
        self.assertFalse(SavedRoom.objects.filter(room_id="general", user=self.alice).exists())


# ---------------------------------------------------------------------------
# create_room_view tests
# ---------------------------------------------------------------------------


class TestCreateRoomView(TestCase):
    def setUp(self):
        self.owner = make_user("owner")
        self.client.force_login(self.owner)

    def _create(self, name, room_id, **extra):
        return self.client.post("/rooms/create/", {"name": name, "room_id": room_id, **extra})

    def test_create_room_requires_explicit_visibility(self):
        response = self._create("General", "general")
        self.assertContains(response, "Please select a visibility.")
        self.assertFalse(Room.objects.filter(id="general").exists())


# ---------------------------------------------------------------------------
# room_settings_view tests
# ---------------------------------------------------------------------------


@_IN_MEMORY_CHANNELS
class TestRoomSettingsView(TestCase):
    def setUp(self):
        self.owner = make_user("owner")
        self.alice = make_user("alice")
        self.room = make_room(self.owner, "general")
        self.client.force_login(self.owner)

    def _post(self, data, user=None):
        if user:
            self.client.force_login(user)
        return self.client.post("/general/settings/", data)

    def test_non_owner_gets_404(self):
        self.assertEqual(self._post({}, user=self.alice).status_code, 404)

    def test_add_to_blacklist_removes_saved_room(self):
        SavedRoom.objects.create(room=self.room, user=self.alice)
        self._post({"action": "add_member", "status": "blacklist", "username": "alice"})
        self.assertFalse(SavedRoom.objects.filter(room=self.room, user=self.alice).exists())

    def test_set_visibility_to_private_kicks_non_whitelisted(self):
        SavedRoom.objects.create(room=self.room, user=self.alice)
        self._post({"action": "set_visibility", "visibility": "private"})
        self.assertFalse(SavedRoom.objects.filter(room=self.room, user=self.alice).exists())

    def test_set_visibility_to_private_keeps_whitelisted(self):
        SavedRoom.objects.create(room=self.room, user=self.alice)
        add_member(self.room, self.alice, RoomMember.WHITELIST)
        self._post({"action": "set_visibility", "visibility": "private"})
        self.assertTrue(SavedRoom.objects.filter(room=self.room, user=self.alice).exists())

    def test_remove_from_whitelist_in_private_room_evicts_user(self):
        self.room.visibility = Room.PRIVATE
        self.room.save()
        add_member(self.room, self.alice, RoomMember.WHITELIST)
        SavedRoom.objects.create(room=self.room, user=self.alice)
        self._post({"action": "remove_member", "username": "alice"})
        self.assertFalse(SavedRoom.objects.filter(room=self.room, user=self.alice).exists())

    def test_add_unknown_username_returns_error(self):
        self.assertContains(
            self._post({"action": "add_member", "status": "whitelist", "username": "nobody"}),
            "No user found with that username",
        )

    def test_cannot_add_owner_to_access_list(self):
        self.assertContains(
            self._post({"action": "add_member", "status": "blacklist", "username": "owner"}),
            "Cannot add the room owner",
        )
        self.assertFalse(RoomMember.objects.filter(room=self.room, user=self.owner).exists())


# ---------------------------------------------------------------------------
# Consumer permission and kick tests
#
# Kick tests verify behavior that is not yet implemented. They will fail until:
#   - ChatConsumer.connect joins group f"user_{user_id}_room_{room_id}"
#   - ChatConsumer handles "kick.user" channel layer events by sending
#     {"type": "kicked"} to the client then closing the connection
#   - room_settings_view (and visibility changes) send "kick.user" to that
#     group for every evicted user
# ---------------------------------------------------------------------------


@override_settings(
    CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
)
class ChatConsumerPermissionsTests(TransactionTestCase):

    @asynccontextmanager
    async def joined(self, user, room_id):
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

    async def _kick(self, user_id, room_id):
        """Send kick.user to the per-user-per-room group the consumer is expected to join."""
        await get_channel_layer().group_send(
            f"user_{user_id}_room_{room_id}",
            {"type": "kick.user"},
        )

    # --- connection ---

    async def test_public_room_no_saved_room_required(self):
        owner = await async_make_user("owner")
        alice = await async_make_user("alice")
        await async_make_room(owner, "general")
        async with self.joined(alice, "general") as (_, connected, _):
            self.assertTrue(connected)

    async def test_blacklisted_user_rejected_from_public_room(self):
        owner = await async_make_user("owner")
        alice = await async_make_user("alice")
        room = await async_make_room(owner, "general")
        await async_add_member(room, alice, RoomMember.BLACKLIST)
        async with self.joined(alice, "general") as (_, connected, _):
            self.assertFalse(connected)

    async def test_non_whitelisted_user_rejected_from_private_room(self):
        owner = await async_make_user("owner")
        alice = await async_make_user("alice")
        await async_make_room(owner, "secret", visibility=Room.PRIVATE)
        async with self.joined(alice, "secret") as (_, connected, _):
            self.assertFalse(connected)

    async def test_whitelisted_user_connects_to_private_room(self):
        owner = await async_make_user("owner")
        alice = await async_make_user("alice")
        room = await async_make_room(owner, "secret", visibility=Room.PRIVATE)
        await async_add_member(room, alice, RoomMember.WHITELIST)
        async with self.joined(alice, "secret") as (_, connected, _):
            self.assertTrue(connected)

    async def test_owner_connects_to_private_room_without_whitelist(self):
        owner = await async_make_user("owner")
        await async_make_room(owner, "secret", visibility=Room.PRIVATE)
        async with self.joined(owner, "secret") as (_, connected, _):
            self.assertTrue(connected)

    # --- kick: connection closed with prior notification ---

    async def _assert_kicked(self, comm):
        """Assert the consumer sent a kicked packet followed by a close frame."""
        packet = await comm.receive_json_from()
        self.assertEqual(packet["type"], "kicked")
        close = await comm.receive_output()
        self.assertEqual(close["type"], "websocket.close")

    async def test_blacklisted_user_receives_kicked_packet_then_disconnects(self):
        owner = await async_make_user("owner")
        alice = await async_make_user("alice")
        await async_make_room(owner, "general")
        async with self.joined(alice, "general") as (comm, connected, _):
            self.assertTrue(connected)
            await self._kick(alice.pk, "general")
            await self._assert_kicked(comm)

    async def test_whitelist_removal_receives_kicked_packet_then_disconnects(self):
        owner = await async_make_user("owner")
        alice = await async_make_user("alice")
        room = await async_make_room(owner, "secret", visibility=Room.PRIVATE)
        await async_add_member(room, alice, RoomMember.WHITELIST)
        async with self.joined(alice, "secret") as (comm, connected, _):
            self.assertTrue(connected)
            await self._kick(alice.pk, "secret")
            await self._assert_kicked(comm)

    async def test_visibility_flip_receives_kicked_packet_then_disconnects(self):
        owner = await async_make_user("owner")
        alice = await async_make_user("alice")
        await async_make_room(owner, "general")
        async with self.joined(alice, "general") as (comm, connected, _):
            self.assertTrue(connected)
            await self._kick(alice.pk, "general")
            await self._assert_kicked(comm)

    # --- kick: evicted user cannot send ---

    async def test_kicked_user_cannot_broadcast_messages(self):
        owner = await async_make_user("owner")
        alice = await async_make_user("alice")
        bob = await async_make_user("bob")
        await async_make_room(owner, "general")
        async with self.joined(alice, "general") as (alice_comm, _, _), \
                self.joined(bob, "general") as (bob_comm, _, _):
            await self._kick(alice.pk, "general")
            await self._assert_kicked(alice_comm)  # drain kicked + close
            await alice_comm.send_json_to(
                {"type": "send_message", "display_name": "alice", "body": "ghost"}
            )
            self.assertTrue(await bob_comm.receive_nothing(timeout=0.5))

    # --- kick: room-scoped ---

    async def test_kick_does_not_affect_other_room_connections(self):
        owner = await async_make_user("owner")
        alice = await async_make_user("alice")
        await async_make_room(owner, "room-a")
        await async_make_room(owner, "room-b")
        async with self.joined(alice, "room-a") as (room_a_comm, _, _), \
                self.joined(alice, "room-b") as (room_b_comm, connected_b, _):
            self.assertTrue(connected_b)
            await self._kick(alice.pk, "room-a")
            await self._assert_kicked(room_a_comm)
            self.assertTrue(await room_b_comm.receive_nothing(timeout=0.5))
