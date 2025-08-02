from django.db import models
from django.utils import timezone

class Room(models.Model):
    room_code = models.CharField(max_length=10, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started = models.BooleanField(default=False)
    owner = models.ForeignKey('Player', null=True, blank=True, on_delete=models.SET_NULL, related_name='owned_rooms')  # 新增
    max_player = models.IntegerField(default=6)
    round_time = models.IntegerField(default=20)
    turn_order = models.JSONField(default=list)         # 存玩家 ID 的亂數順序
    current_turn_index = models.IntegerField(default=0) # 輪到哪一位 (順序中的 index)
    turn_timer = models.IntegerField(default=30)        # 本回合剩餘秒數
    turn_timer_start_time = models.DateTimeField(null=True, blank=True)

class Player(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='players')
    nickname = models.CharField(max_length=20)
    join_time = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(default=timezone.now)
    hand_count = models.IntegerField(default=0)

