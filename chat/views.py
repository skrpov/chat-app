from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader
from django.template.defaultfilters import slugify
from django.views.decorators.http import require_POST
from .models import Message, Room, SavedRoom
from django.contrib.auth.decorators import login_required


@login_required
def messenger_view(request, room_id=None):
    template = loader.get_template("messenger.html")
    messages = Message.objects.all().order_by("created_at")
    rooms = Room.objects.filter(id=room_id)
    room_name = rooms[0].name if len(rooms) > 0 else ""
    saved_rooms = SavedRoom.objects.filter(user=request.user).select_related("room")

    context = {
        "messages": messages,
        "username": request.user.username,
        "room_id": room_id,
        "room_name": room_name,
        "saved_rooms": saved_rooms,
    }
    return HttpResponse(template.render(context, request))


def _redirect_to_room(room_id):
    """htmx client-side navigation to the given room page."""
    return HttpResponse(status=204, headers={"HX-Redirect": f"/{room_id}/"})


@login_required
@require_POST
def create_room_view(request):
    name = request.POST.get("name", "").strip()
    room_id = request.POST.get("room_id", "").strip()

    errors = {}
    if not name:
        errors["name"] = "Please enter a room name."
    if not room_id:
        errors["room_id"] = "Please enter a room ID."
    elif slugify(room_id) != room_id:
        errors["room_id"] = "Use only lowercase letters, numbers and hyphens."
    elif Room.objects.filter(id=room_id).exists():
        errors["room_id"] = "That room ID is already taken."

    if errors:
        return render(
            request,
            "partials/create_room_form.html",
            {"errors": errors, "values": {"name": name, "room_id": room_id}},
        )

    room = Room.objects.create(id=room_id, owner=request.user, name=name)
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
    elif room is None:
        errors["room_id"] = "No room found with that ID."

    if errors:
        return render(
            request,
            "partials/join_room_form.html",
            {"errors": errors, "values": {"room_id": room_id}},
        )

    assert room is not None, "If room is None then errors is not and this path doesn't run"
    SavedRoom.objects.get_or_create(room=room, user=request.user)
    return _redirect_to_room(room.id)
