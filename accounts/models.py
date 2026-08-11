from django.conf import settings
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    avatar = models.BinaryField(null=True, blank=True, editable=False)
    avatar_updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Profile({self.user})"

    @property
    def has_avatar(self):
        return bool(self.avatar)
