from django.db import models
from django.conf import settings


class Room(models.Model):
    id = models.SlugField(max_length=255, primary_key=True, unique=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)


class SavedRoom(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=255)
    body = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
