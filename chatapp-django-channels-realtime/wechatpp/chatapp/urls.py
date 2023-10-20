from django.urls import path
from . import views
from .views import RoomList, RoomDetail, room


urlpatterns = [
    path("", views.rooms, name="rooms"),
    path("<str:slug>", views.room, name="room"),
    path('rooms/', RoomList.as_view(), name='room-list'),
    path('rooms/<slug:slug>/', RoomDetail.as_view(), name='room-detail'),
]