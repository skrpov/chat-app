from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template import loader
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.views.decorators.http import require_POST, require_http_methods
from .models import Message, Room, RoomMember, SavedRoom


def landing_view(request):
    if request.user.is_authenticated:
        return redirect("home")
    return render(request, "landing.html")


def _kick_user(user_id, room_id):
    async_to_sync(get_channel_layer().group_send)(
        f"user_{user_id}_room_{room_id}",
        {"type": "kick.user"},
    )


@login_required
def messenger_view(request, room_id=None):
    template = loader.get_template("messenger.html")
    room = None
    if room_id:
        candidate = Room.objects.filter(id=room_id).first()
        if candidate and candidate.can_access(request.user):
            room = candidate
            SavedRoom.objects.get_or_create(room=room, user=request.user)

    messages = Message.objects.all().order_by("created_at")
    saved_rooms = SavedRoom.objects.filter(user=request.user).select_related("room")

    context = {
        "messages": messages,
        "user": request.user,
        "room": room,
        "saved_rooms": sorted(saved_rooms, key=lambda sv: sv.room.name.lower()),
    }
    return HttpResponse(template.render(context, request))


def _redirect_to_room(room_id):
    url = reverse("room", kwargs={"room_id": room_id})
    return HttpResponse(status=204, headers={"HX-Redirect": url})


@login_required
@require_POST
def create_room_view(request):
    name = request.POST.get("name", "").strip()
    room_id = request.POST.get("room_id", "").strip()
    visibility = request.POST.get("visibility", "").strip()

    errors = {}
    if not name:
        errors["name"] = "Please enter a room name."
    if not room_id:
        errors["room_id"] = "Please enter a room ID."
    elif slugify(room_id) != room_id:
        errors["room_id"] = "Use only lowercase letters, numbers and hyphens."
    elif Room.objects.filter(id=room_id).exists():
        errors["room_id"] = "That room ID is already taken."
    if visibility not in (Room.PUBLIC, Room.PRIVATE):
        errors["visibility"] = "Please select a visibility."

    if errors:
        return render(
            request,
            "partials/create_room_form.html",
            {"errors": errors, "values": {"name": name, "room_id": room_id, "visibility": visibility}},
        )

    room = Room.objects.create(id=room_id, owner=request.user, name=name, visibility=visibility)
    SavedRoom.objects.create(room=room, user=request.user)
    return _redirect_to_room(room.id)


@login_required
@require_POST
def join_room_view(request):
    room_id = request.POST.get("room_id", "").strip()

    errors = {}
    room = Room.objects.filter(id=room_id).first()
    if not room_id:
        errors["room_id"] = "Please enter a room ID."
    elif room is None or not room.can_access(request.user):
        errors["room_id"] = "No room found with that ID."

    if errors:
        return render(
            request,
            "partials/join_room_form.html",
            {"errors": errors, "values": {"room_id": room_id}},
        )

    assert room is not None
    SavedRoom.objects.get_or_create(room=room, user=request.user)
    return _redirect_to_room(room.id)


@login_required
@require_http_methods(["GET", "POST"])
def room_settings_view(request, room_id):
    room = get_object_or_404(Room, id=room_id, owner=request.user)
    errors = {}

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "set_visibility":
            visibility = request.POST.get("visibility")
            if visibility in (Room.PUBLIC, Room.PRIVATE):
                old_visibility = room.visibility
                room.visibility = visibility
                room.save(update_fields=["visibility"])
                if visibility == Room.PRIVATE and old_visibility == Room.PUBLIC:
                    whitelisted_ids = RoomMember.objects.filter(
                        room=room, status=RoomMember.WHITELIST
                    ).values_list("user_id", flat=True)
                    to_evict = SavedRoom.objects.filter(room=room).exclude(
                        user=room.owner
                    ).exclude(user_id__in=whitelisted_ids)
                    evicted_ids = list(to_evict.values_list("user_id", flat=True))
                    to_evict.delete()
                    for uid in evicted_ids:
                        _kick_user(uid, room.id)

        elif action == "add_member":
            username = request.POST.get("username", "").strip()
            status = request.POST.get("status")
            User = get_user_model()
            target = User.objects.filter(username=username).first()
            error_key = f"{status}_username"
            if not username:
                errors[error_key] = "Please enter a username."
            elif target is None:
                errors[error_key] = "No user found with that username."
            elif target.pk == room.owner_id:
                errors[error_key] = "Cannot add the room owner to an access list."
            elif status in (RoomMember.WHITELIST, RoomMember.BLACKLIST):
                RoomMember.objects.update_or_create(
                    room=room, user=target, defaults={"status": status}
                )
                if status == RoomMember.BLACKLIST:
                    SavedRoom.objects.filter(room=room, user=target).delete()
                    _kick_user(target.pk, room.id)

        elif action == "remove_member":
            username = request.POST.get("username", "").strip()
            User = get_user_model()
            target = User.objects.filter(username=username).first()
            if target:
                entry = RoomMember.objects.filter(room=room, user=target).first()
                if entry:
                    if (
                        entry.status == RoomMember.WHITELIST
                        and room.visibility == Room.PRIVATE
                    ):
                        SavedRoom.objects.filter(room=room, user=target).delete()
                        _kick_user(target.pk, room.id)
                    entry.delete()

    whitelist = RoomMember.objects.filter(
        room=room, status=RoomMember.WHITELIST
    ).select_related("user")
    blacklist = RoomMember.objects.filter(
        room=room, status=RoomMember.BLACKLIST
    ).select_related("user")

    return render(
        request,
        "partials/room_settings_content.html",
        {"room": room, "whitelist": whitelist, "blacklist": blacklist, "errors": errors},
    )
