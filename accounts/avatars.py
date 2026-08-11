from io import BytesIO

from PIL import Image, ImageOps

AVATAR_MAX_SIZE = 256
AVATAR_WEBP_QUALITY = 80
AVATAR_CONTENT_TYPE = "image/webp"
AVATAR_MAX_UPLOAD_PIXELS = 3840 * 2160
AVATAR_MAX_UPLOAD_BYTES = 8 * 1024 * 1024


def encode_avatar(image_file):
    """Downscale and re-encode an uploaded image to a small WebP blob."""
    image = Image.open(image_file)
    image = ImageOps.exif_transpose(image)
    image = image.convert("RGBA")
    image.thumbnail((AVATAR_MAX_SIZE, AVATAR_MAX_SIZE))
    buffer = BytesIO()
    image.save(buffer, format="WEBP", quality=AVATAR_WEBP_QUALITY)
    return buffer.getvalue()
