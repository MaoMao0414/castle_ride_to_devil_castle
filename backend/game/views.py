from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from .models import Room, Player
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

@csrf_exempt
def join_room(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        room_code = data.get('room_code')
        nickname = data.get('nickname')
        max_player = int(data.get('max_player', 6))

        room, created = Room.objects.get_or_create(room_code=room_code)
        if not created and room.started:
            return JsonResponse({'status': 'error', 'message': '該房間遊戲已開始'})

        if created:
            if not (3 <= max_player <= 10):
                return JsonResponse({'status': 'error', 'message': '人數必須在3~10人之間'})
            room.max_player = max_player
            room.save()

        # 檢查重複暱稱
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
        clean_inactive_players(room, timeout_seconds=60)  # 1分鐘沒心跳自動清除
        if not Room.objects.filter(id=room.id).exists():
            return JsonResponse({'status': 'error', 'message': '房間已關閉或沒人'}, status=404)
        players = []
        now = timezone.now()
        for p in room.players.all():
            idle = (now - p.last_active) > timedelta(seconds=5)
            players.append({
                'id': p.id,
                'nickname': p.nickname,
                'idle': idle,  # 新增欄位，給前端判斷
            })
        return JsonResponse({
            'status': 'ok',
            'room_code': room_code,
            'players': players,
            'started': room.started,
            'owner_id': room.owner.id if room.owner else None,
            'round_time': room.round_time,
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
            # 房主離開，重新指定最早加入玩家為房主
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
            room.started = True
            room.save()
            return JsonResponse({'status': 'ok'})
        except Room.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': '房間不存在'})
    return JsonResponse({'status': 'error', 'message': 'Only POST allowed'})

def list_rooms(request):
    from .models import Room
    rooms = list(Room.objects.filter(started=False))  # 先轉 list，避免查詢異常
    deleted_room_ids = set()
    for room in rooms:
        # 呼叫清除，清掉房主時會刪除 room
        clean_inactive_players(room, timeout_seconds=60)
        # 如果房間被刪了，記錄下來
        if not Room.objects.filter(id=room.id).exists():
            deleted_room_ids.add(room.id)

    data = []
    for r in rooms:
        if r.id in deleted_room_ids:
            continue  # 跳過剛剛被刪除的房間
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

        try:
            room = Room.objects.get(room_code=room_code)
            player = room.players.get(id=target_player_id)

            # 只允許踢 idle (超過 5 秒沒心跳) 的玩家
            from datetime import timedelta
            from django.utils import timezone
            if (timezone.now() - player.last_active) <= timedelta(seconds=10):
                return JsonResponse({'status': 'error', 'message': '只能踢離線/暫離玩家'}, status=403)

            player.delete()
            # 若被踢掉的是房主，自動轉移房主
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

            # 簡單密碼驗證（可改成更安全機制）
            if admin_password != settings.ADMIN_PASSWORD:
                return JsonResponse({'status': 'error', 'message': '管理密碼錯誤'})

            Room.objects.all().delete()

            return JsonResponse({'status': 'ok', 'message': '所有房間已刪除'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Only POST allowed'})

def admin_list_rooms(request):
    rooms = Room.objects.all().order_by('-id')  # 新的在前面
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
            print(f"收到 heartbeat: {player.id} {player.nickname} @ {timezone.now()}")
            return JsonResponse({'status': 'ok'})
        except Player.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': '玩家不存在'}, status=400)
        
def clean_inactive_players(room, timeout_seconds=10):
    timeout = timezone.now() - timedelta(seconds=timeout_seconds)
    inactive_players = list(room.players.filter(last_active__lt=timeout))

    for player in inactive_players:
        player_id = player.id
        print("即將刪除：", player_id, player.nickname)
        player.delete()
        # 檢查是不是房主
        if room.owner_id == player_id:
            # 房主被刪除，要指定新房主
            remaining_players = room.players.all().order_by('join_time')
            if remaining_players.exists():
                room.owner = remaining_players.first()
                room.save()
            else:
                # 沒有其他人，刪除房間
                room.delete()
                return

