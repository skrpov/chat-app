from django.urls import path
from .views import landing_view, messenger_view, create_room_view, join_room_view, room_settings_view

urlpatterns = [
    path("rooms/create/", create_room_view, name="create_room"),
    path("rooms/join/", join_room_view, name="join_room"),
    path("app/<str:room_id>/settings/", room_settings_view, name="room_settings"),
    path("app/", messenger_view, name="home"),
    path("app/<str:room_id>/", messenger_view, name="room"),
    path("", landing_view, name="landing"),
]
