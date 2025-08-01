from django.contrib import admin
from django.urls import path
from game import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('join/', views.join_room),
    path('room/<str:room_code>/players/', views.get_players),
    path('leave/', views.leave_room),
    path('start/', views.start_game),
    path('rooms/', views.list_rooms),
    path('admin_delete_room/', views.admin_delete_room),
    path('kick_player/', views.kick_player),
    path('transfer_owner/', views.transfer_owner),
    path('admin_delete_all_rooms/', views.admin_delete_all_rooms),
    path('admin_list_rooms/', views.admin_list_rooms),
    path('set_room_settings/', views.set_room_settings),
    path('heartbeat/', views.player_heartbeat),
]
