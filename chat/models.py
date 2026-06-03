from django.db import models
from django.conf import settings
from asgiref.sync import async_to_sync


class Room(models.Model):
    PUBLIC = "public"
    PRIVATE = "private"
    VISIBILITY_CHOICES = [(PUBLIC, "Public"), (PRIVATE, "Private")]

    id = models.SlugField(max_length=255, primary_key=True, unique=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    visibility = models.CharField(
        max_length=10, choices=VISIBILITY_CHOICES, default=PUBLIC
    )

    def can_access(self, user):
        return async_to_sync(self.acan_access)(user)

    async def acan_access(self, user):
        if user.pk == self.owner_id:
            return True
        entry = await RoomMember.objects.filter(room=self, user=user).afirst()
        if self.visibility == Room.PRIVATE:
            return entry is not None and entry.status == RoomMember.WHITELIST
        return entry is None or entry.status != RoomMember.BLACKLIST


class RoomMember(models.Model):
    WHITELIST = "whitelist"
    BLACKLIST = "blacklist"
    STATUS_CHOICES = [(WHITELIST, "Whitelist"), (BLACKLIST, "Blacklist")]

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    class Meta:
        unique_together = ("room", "user")


class RoomJoinRecord(models.Model):
    """Persists across bans to prevent re-triggering first-join notifications."""
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("room", "user")


class SavedRoom(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


class Message(models.Model):
    CHAT = "chat"
    JOIN = "join"
    KIND_CHOICES = [(CHAT, "Chat"), (JOIN, "Join")]

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=255)
    body = models.CharField(max_length=255, blank=True)
    kind = models.CharField(max_length=10, choices=KIND_CHOICES, default=CHAT)
    created_at = models.DateTimeField(auto_now_add=True)
