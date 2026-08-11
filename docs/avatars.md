# Avatars

How profile pictures are stored and served.

---

## Storage

Avatars are stored as a blob on `accounts.Profile.avatar`, not as files on disk.
The app should be able to run as more than one instance, and filesystem state
does not survive that — an upload through one instance would be missing from
every other. The database is the one place every instance already shares.

`bytes(profile.avatar)` on read: SQLite returns `bytes`, PostgreSQL returns a
`memoryview`.

## Encoding

`encode_avatar` re-encodes every upload, so the column holds one format at one
bounded size regardless of what was uploaded, and the variability of
user-supplied images is handled at the upload boundary.

- **256px on the longest side, quality 80.** Estimated rather than measured:
  above every size an avatar is shown at today (96px on the profile page, 28px
  in the sidebar), and small enough to avoid storing large images for no reason.
- **WebP.** Smaller than JPEG at comparable quality, and supports alpha, so a
  transparent avatar is not flattened onto black.
- **`ImageOps.exif_transpose`.** Pillow does not apply the EXIF orientation tag
  on open, and WebP does not carry the tag forward.

## Upload limits

Defined in `accounts/avatars.py`, enforced by `AvatarForm`:

- `AVATAR_MAX_UPLOAD_PIXELS` (3840x2160). Decoding happens in full before
  downscaling, at 4 bytes per pixel, so pixel count determines peak memory. 4K is
  roughly 33MB.
- `AVATAR_MAX_UPLOAD_BYTES` (8MB). Rejects oversized uploads before they are
  decoded. A byte limit alone is not sufficient, since a small compressed image
  can expand to far more memory once decoded.

The pixel check reads `upload.image.size`, the Pillow image Django's `ImageField`
attaches during validation, so it costs no second decode.

## Serving

`avatar_view` serves the blob at `/accounts/avatar/<user_id>/`.

`@login_required` is applied outside `@condition` so unauthenticated requests are
redirected before the condition function queries the database. Without it, user
IDs can be walked to harvest pictures and to determine which accounts exist.

`Profile.avatar_updated_at` is written on every upload and feeds `@condition`,
which answers conditional requests with a `304`. The response sets
`Cache-Control: private, no-cache` so the browser revalidates. A `max-age` would
serve the old picture after an upload, because the page the upload redirects to
has an unchanged `<img src>`.
