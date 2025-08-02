from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import random
from .models import Room, Player
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import math

def get_current_timer(room):
    if room.round_time == 0:
        return None
    if room.turn_timer_start_time and room.round_time:
        elapsed = (timezone.now() - room.turn_timer_start_time).total_seconds()
        timer = max(0, int(math.ceil(room.round_time - elapsed)))
        return timer
    return room.round_time or 0

def advance_turn(room):
    if room.turn_order and len(room.turn_order) > 0:
        room.current_turn_index = (room.current_turn_index + 1) % len(room.turn_order)
        room.turn_timer = room.round_time
        room.turn_timer_start_time = timezone.now()
        room.save()

@csrf_exempt
def join_room(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        room_code = data.get('room_code')
        nickname = data.get('nickname')
        max_player = int(data.get('max_player', 6))

        try:
            room = Room.objects.get(room_code=room_code)
            if room.started:
                return JsonResponse({'status': 'error', 'message': '該房間遊戲已開始'})
        except Room.DoesNotExist:
            if not (3 <= max_player <= 10):
                return JsonResponse({'status': 'error', 'message': '人數必須在3~10人之間'})
            room = Room.objects.create(room_code=room_code, max_player=max_player)
            room.save()

        if Player.objects.filter(room=room, nickname=nickname).exists():
            return JsonResponse({'status': 'error', 'message': '該房間已有相同暱稱玩家，請換一個暱稱'})

        if room.players.count() >= room.max_player:
            return JsonResponse({'status': 'error', 'message': '房間人數已滿，無法加入'})

        player = Player.objects.create(room=room, nickname=nickname)
        if room.owner is None:
            room.owner = player
            room.save()

        return JsonResponse({
            'status': 'ok',
            'player_id': player.id,
            'room_code': room.room_code,
            'max_player': room.max_player,
        })

def get_players(request, room_code):
    try:
        room = Room.objects.get(room_code=room_code)
        clean_inactive_players(room, timeout_seconds=60)
        if not Room.objects.filter(id=room.id).exists():
            return JsonResponse({'status': 'error', 'message': '房間已關閉或沒人'}, status=404)
        players = []
        now = timezone.now()
        for p in room.players.all():
            idle = (now - p.last_active) > timedelta(seconds=5)
            players.append({
                'id': p.id,
                'nickname': p.nickname,
                'handCount': getattr(p, 'hand_count', 0),
                'idle': idle,
            })
        timer = get_current_timer(room)
        # =========== ⏰ 不限時則不自動換人！ =============
        if (
            room.started and room.turn_order and room.round_time and 
            timer == 0 and room.round_time > 0
        ):
            advance_turn(room)
            timer = get_current_timer(room)
        return JsonResponse({
            'status': 'ok',
            'room_code': room_code,
            'players': players,
            'started': room.started,
            'owner_id': room.owner.id if room.owner else None,
            'round_time': room.round_time,
            'turn_order': room.turn_order,
            'current_turn_index': room.current_turn_index,
            'timer': timer,  # 若不限時則是 None
        })
    except Room.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': '房間不存在'})
    
@csrf_exempt
def leave_room(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        player_id = data.get('player_id')
        try:
            player = Player.objects.get(id=player_id)
        except Player.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': '玩家不存在或已離開'}, status=400)

        room = player.room
        is_owner = (room.owner_id == player.id)

        player.delete()

        if room.players.count() == 0:
            room.delete()
        elif is_owner:
            new_owner = room.players.order_by('join_time').first()
            room.owner = new_owner
            room.save()

        return JsonResponse({'status': 'ok'})

@csrf_exempt
def start_game(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        room_code = data.get('room_code')
        try:
            room = Room.objects.get(room_code=room_code)
            player_count = room.players.count()
            if player_count < 3:
                return JsonResponse({'status': 'error', 'message': '遊戲開始需要至少3人'})
            player_ids = list(room.players.values_list('id', flat=True))
            random.shuffle(player_ids)
            room.turn_order = player_ids
            room.current_turn_index = 0
            room.turn_timer = room.round_time
            room.turn_timer_start_time = timezone.now()
            room.started = True
            room.save()
            return JsonResponse({'status': 'ok', 'turn_order': player_ids})
        except Room.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': '房間不存在'})
    return JsonResponse({'status': 'error', 'message': 'Only POST allowed'})

@csrf_exempt
def next_turn(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        room_code = data.get('room_code')
        try:
            room = Room.objects.get(room_code=room_code)
            advance_turn(room)
            return JsonResponse({'status': 'ok'})
        except Room.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': '房間不存在'})

def list_rooms(request):
    from .models import Room
    rooms = list(Room.objects.filter(started=False))
    deleted_room_ids = set()
    for room in rooms:
        clean_inactive_players(room, timeout_seconds=60)
        if not Room.objects.filter(id=room.id).exists():
            deleted_room_ids.add(room.id)
    data = []
    for r in rooms:
        if r.id in deleted_room_ids:
            continue
        data.append({
            'room_code': r.room_code,
            'player_count': r.players.count(),
            'max_player': r.max_player,
        })
    return JsonResponse({'rooms': data})

@csrf_exempt
def admin_delete_room(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            room_code = data.get('room_code')
            admin_password = data.get('admin_password')
            if admin_password != settings.ADMIN_PASSWORD:
                return JsonResponse({'status': 'error', 'message': '管理密碼錯誤'})
            Room.objects.filter(room_code=room_code).delete()
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Only POST allowed'})

@csrf_exempt
def kick_player(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        room_code = data.get('room_code')
        target_player_id = data.get('target_player_id')
        requester_id = data.get('owner_id')  # 加一個欄位代表發出請求者id

        try:
            room = Room.objects.get(room_code=room_code)
            player = room.players.get(id=target_player_id)

            from datetime import timedelta
            from django.utils import timezone
            is_idle = (timezone.now() - player.last_active) > timedelta(seconds=10)

            # 若玩家在線（非idle），必須是房主才能踢
            if not is_idle:
                if requester_id != room.owner_id:
                    return JsonResponse({'status': 'error', 'message': '只能由房主踢在線玩家'}, status=403)

            # 允許踢除
            player.delete()

            # 如果被踢的是房主，自動轉移房主
            if room.owner_id == target_player_id:
                new_owner = room.players.order_by('join_time').first()
                if new_owner:
                    room.owner = new_owner
                    room.save()
                else:
                    room.delete()

            return JsonResponse({'status': 'ok'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})


@csrf_exempt
def transfer_owner(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            room_code = data.get('room_code')
            owner_id = data.get('owner_id')
            new_owner_id = data.get('new_owner_id')
            room = Room.objects.get(room_code=room_code)
            if room.owner_id != owner_id:
                return JsonResponse({'status': 'error', 'message': '沒有權限'})
            new_owner = Player.objects.get(id=new_owner_id, room=room)
            room.owner = new_owner
            room.save()
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Only POST allowed'})

@csrf_exempt
def admin_delete_all_rooms(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            admin_password = data.get('admin_password')
            if admin_password != settings.ADMIN_PASSWORD:
                return JsonResponse({'status': 'error', 'message': '管理密碼錯誤'})
            Room.objects.all().delete()
            return JsonResponse({'status': 'ok', 'message': '所有房間已刪除'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Only POST allowed'})

def admin_list_rooms(request):
    rooms = Room.objects.all().order_by('-id')
    data = []
    for r in rooms:
        data.append({
            'room_code': r.room_code,
            'player_count': r.players.count(),
            'max_player': r.max_player,
            'started': r.started,
        })
    return JsonResponse({'rooms': data})

@csrf_exempt
def set_room_settings(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            room_code = data.get('room_code')
            owner_id = data.get('owner_id')
            round_time = int(data.get('round_time'))
            room = Room.objects.get(room_code=room_code)
            if room.owner_id != owner_id:
                return JsonResponse({'status': 'error', 'message': '只有房主可修改設定'})
            room.round_time = round_time
            room.save()
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Only POST allowed'})

@csrf_exempt
def player_heartbeat(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        player_id = data.get('player_id')
        try:
            player = Player.objects.get(id=player_id)
            player.last_active = timezone.now()
            player.save(update_fields=['last_active'])
            return JsonResponse({'status': 'ok'})
        except Player.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': '玩家不存在'}, status=400)

def clean_inactive_players(room, timeout_seconds=10):
    if room.started:
        return
    timeout = timezone.now() - timedelta(seconds=timeout_seconds)
    inactive_players = list(room.players.filter(last_active__lt=timeout))
    for player in inactive_players:
        player_id = player.id
        player.delete()
        if room.owner_id == player_id:
            remaining_players = room.players.all().order_by('join_time')
            if remaining_players.exists():
                room.owner = remaining_players.first()
                room.save()
            else:
                room.delete()
                return

