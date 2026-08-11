from django import forms

from .avatars import AVATAR_MAX_UPLOAD_BYTES, AVATAR_MAX_UPLOAD_PIXELS


class AvatarForm(forms.Form):
    # ImageField validates (via Pillow) that the upload is a real image before
    # we re-encode it; the actual downscaling happens in accounts.avatars.
    avatar = forms.ImageField()

    def clean_avatar(self):
        upload = self.cleaned_data["avatar"]
        if upload.size > AVATAR_MAX_UPLOAD_BYTES:
            raise forms.ValidationError("Image must be smaller than 8 MB.")
        width, height = upload.image.size
        if width * height > AVATAR_MAX_UPLOAD_PIXELS:
            raise forms.ValidationError("Image must be no larger than 3840x2160.")
        return upload
