from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import condition

from .avatars import AVATAR_CONTENT_TYPE, encode_avatar
from .forms import AvatarForm
from .models import Profile


def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})


@login_required
def profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = AvatarForm(request.POST, request.FILES)
        if form.is_valid():
            profile.avatar = encode_avatar(form.cleaned_data["avatar"])
            profile.avatar_updated_at = timezone.now()
            profile.save()
            return redirect("profile")
    else:
        form = AvatarForm()
    return render(request, "registration/profile.html", {"form": form, "profile": profile})


def _avatar_last_modified(request, user_id):
    return (
        Profile.objects.filter(user_id=user_id)
        .values_list("avatar_updated_at", flat=True)
        .first()
    )


@login_required
@condition(last_modified_func=_avatar_last_modified)
def avatar_view(request, user_id):
    profile = get_object_or_404(Profile, user_id=user_id)
    if not profile.avatar:
        raise Http404("No avatar")
    response = HttpResponse(bytes(profile.avatar), content_type=AVATAR_CONTENT_TYPE)
    response["Cache-Control"] = "private, no-cache"
    return response
