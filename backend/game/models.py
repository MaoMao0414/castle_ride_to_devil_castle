from django.db import models
from django.utils import timezone

class Room(models.Model):
    room_code = models.CharField(max_length=10, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started = models.BooleanField(default=False)
    owner = models.ForeignKey('Player', null=True, blank=True, on_delete=models.SET_NULL, related_name='owned_rooms')  # 新增
    max_player = models.IntegerField(default=6)
    round_time = models.IntegerField(default=20)

class Player(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='players')
    nickname = models.CharField(max_length=20)
    join_time = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(default=timezone.now)

