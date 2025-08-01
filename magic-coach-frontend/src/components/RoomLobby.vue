<template>
  <div class="room-lobby-layout">
    <!-- 左側：遊戲設定 -->
    <div class="game-settings-block">
        <h3>遊戲設定</h3>

        <div class="setting-group">
            <label>回合時間：</label>
            <div class="option-buttons">
            <button
                v-for="opt in timeOptions"
                :key="opt.value"
                :class="{ selected: gameSettings.roundTime === opt.value }"
                :disabled="!isOwner"
                @click="updateSetting('roundTime', opt.value)"
            >
                {{ opt.label }}
            </button>
            </div>
        </div>

        <div style="font-size:0.95em;margin-top:10px;">
            <span v-if="isOwner" style="color:#666;">你是房主，可調整設定</span>
            <span v-else style="color:#aaa;">僅房主可調整</span>
        </div>

    </div>

    <!-- 右側：你的大廳內容，完全不動 -->
    <div class="room-lobby">
      <h2>房間大廳</h2>
      <p>房間代碼：{{ roomCode }}</p>
      <h3>已加入玩家：</h3>
      <ul>
        <li
          v-for="p in players"
          :key="p.id"
          :class="{ self: p.id == playerId, idle: p.idle }"
        >
          <span v-if="p.id == ownerId" class="crown" title="房主">👑</span>
          <span>{{ p.nickname }}</span>
          <span v-if="p.idle" style="color:#bbb; margin-left:6px;">(離線)</span>
          <span v-if="p.id == playerId" class="me">(我)</span>
          <!-- 踢人按鈕：只顯示給 idle 玩家、不是自己 -->
          <button
            v-if="p.idle && p.id != playerId"
            @click="kickPlayer(p.id)"
            style="margin-left:12px;background:#888;"
          >踢除離線玩家</button>
          <!-- 其餘權限按鈕不動 -->
          <template v-if="playerId == ownerId && p.id != playerId">
            <button @click="transferOwner(p.id)">轉移房主</button>
          </template>
        </li>
      </ul>
      <p v-if="players.length === 0">目前沒有玩家</p>

      <div style="margin-top:24px;">
        <button
          @click="startGame"
          :disabled="started"
          v-if="!started && playerId == ownerId"
        >開始遊戲</button>
        <span v-if="started" style="color:green;font-weight:bold;">遊戲已開始！</span>
      </div>

      <button @click="leaveRoom" style="margin-top:24px;">離開房間</button>

      <div style="margin-top:30px;">
        <button @click="adminMode = true" v-if="!isAdmin">Admin 功能</button>
        <div v-if="adminMode && !isAdmin" class="admin-dialog">
          <label>
            管理密碼：
            <input v-model="adminPassword" type="password" style="margin-left:8px;" />
          </label>
          <button @click="verifyAdmin">驗證</button>
          <button @click="adminMode = false">取消</button>
          <p v-if="adminError" style="color:red;">{{ adminError }}</p>
        </div>
        <div v-if="isAdmin" class="admin-panel">
          <p style="color:#a66;"><b>管理員已解鎖！</b></p>
          <button @click="deleteRoom" style="background:#e66;">直接刪除此房間</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
const API_BASE = process.env.VUE_APP_API_URL || 'http://localhost:9000';

export default {
  props: ['roomCode'],
  data() {
    return {
      players: [],
      intervalId: null,
      playerId: null,
      started: false,
      ownerId: null,
      adminMode: false,
      adminPassword: "",
      isAdmin: false,
      adminError: "",
      gameSettings: {
        roundTime: 20,
      },
      timeOptions: [
        { label: '5秒', value: 5 },
        { label: '20秒', value: 20 },
        { label: '60秒', value: 60 },
        { label: '不限時', value: 0 },
      ],
      heartbeatTimer: null,
    };
  },
  computed: {
    isOwner() {
      return this.playerId == this.ownerId;
    },
  },
  methods: {
    async fetchPlayers() {
      console.log('fetchPlayers running', Date.now(), this.playerId)
      // 1. 每次查玩家列表前，主動送 heartbeat
      if (this.playerId) {
        fetch(`${API_BASE}/heartbeat/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ player_id: this.playerId })
        });
      }
      // 2. 原本查詢邏輯完全不動
      try {
        const res = await fetch(`${API_BASE}/room/${this.roomCode}/players/`);
        const data = await res.json();
        if (data.status === 'ok') {
          this.players = data.players;
          if ('started' in data) this.started = data.started;
          if ('owner_id' in data) this.ownerId = parseInt(data.owner_id);
          if ('round_time' in data)  this.gameSettings.roundTime = data.round_time;
          if (!this.players.some(p => p.id === this.playerId)) {
            localStorage.removeItem('playerId');
            this.$router.push('/');
          }
        } else if (data.message === '房間不存在') {
          localStorage.removeItem('playerId');
          this.$router.push('/');
        }
      } catch (err) {
        console.error(err);
      }
    },
    async leaveRoom() {
      if (!this.playerId) {
        alert('找不到玩家ID，無法離開');
        return;
      }
      try {
        const res = await fetch(`${API_BASE}/leave/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ player_id: this.playerId }),
        });
        const data = await res.json();
        if (data.status === 'ok') {
          localStorage.removeItem('playerId');
          this.$router.push('/');
        } else {
          alert(data.message || '離開失敗');
        }
      } catch (err) {
        alert('發生錯誤：' + err.message);
      }
    },
    async startGame() {
      if (this.players.length < 3) {
        alert('遊戲開始需要至少3人');
        return;
      }
      try {
        const res = await fetch(`${API_BASE}/start/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ room_code: this.roomCode }),
        });
        const data = await res.json();
        if (data.status === 'ok') {
          this.started = true;
        } else {
          alert(data.message || '開始失敗');
        }
      } catch (err) {
        alert('發生錯誤：' + err.message);
      }
    },
    verifyAdmin() {
      if (!this.adminPassword || this.adminPassword.length < 3) {
        this.adminError = "請輸入正確管理密碼";
        return;
      }
      this.isAdmin = true;
      this.adminMode = false;
      this.adminError = "";
    },
    async deleteRoom() {
      if (!confirm('確定要刪除此房間嗎？')) return;
      try {
        const res = await fetch(`${API_BASE}/admin_delete_room/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            room_code: this.roomCode,
            admin_password: this.adminPassword,
          }),
        });
        const data = await res.json();
        if (data.status === 'ok') {
          alert('房間已刪除！');
          this.$router.push('/');
        } else {
          alert('刪除失敗：' + (data.message || ''));
        }
      } catch (err) {
        alert('發生錯誤：' + err.message);
      }
    },
    async kickPlayer(targetId) {
      if (!confirm('確定要踢除該玩家嗎？')) return;
      try {
        const res = await fetch(`${API_BASE}/kick_player/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            room_code: this.roomCode,
            owner_id: this.ownerId,
            target_player_id: targetId,
          }),
        });
        const data = await res.json();
        if (data.status === 'ok') {
          this.fetchPlayers();
        } else {
          alert('錯誤：' + (data.message || ''));
        }
      } catch (err) {
        alert('發生錯誤：' + err.message);
      }
    },
    async transferOwner(newOwnerId) {
      if (!confirm('確定要將房主轉移給此玩家嗎？')) return;
      try {
        const res = await fetch(`${API_BASE}/transfer_owner/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            room_code: this.roomCode,
            owner_id: this.ownerId,
            new_owner_id: newOwnerId,
          }),
        });
        const data = await res.json();
        if (data.status === 'ok') {
          this.fetchPlayers();
        } else {
          alert('錯誤：' + (data.message || ''));
        }
      } catch (err) {
        alert('發生錯誤：' + err.message);
      }
    },
    async changeRoundTime(newValue) {
      if (!this.isOwner) return;
      this.gameSettings.roundTime = newValue;
      try {
        await fetch(`${API_BASE}/set_room_settings/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            room_code: this.roomCode,
            owner_id: this.playerId,
            round_time: newValue,
          }),
        });
      } catch (e) {
        alert('發生錯誤：' + e.message);
      }
    },

    updateSetting(key, value) {
      if (!this.isOwner) return;
      this.gameSettings[key] = value;

      if (key === 'roundTime') {
        this.changeRoundTime(value);
      }
    },

    handleBeforeUnload() {
      if (this.playerId && this.roomCode) {
        navigator.sendBeacon?.(
          `${API_BASE}/leave/`,
          new Blob([
            JSON.stringify({
              player_id: this.playerId,
              room_code: this.roomCode
            })
          ], { type: "application/json" })
        );
        localStorage.removeItem('playerId');
      }
    },
  },
  mounted() {
    this.playerId = parseInt(localStorage.getItem('playerId'));
    this.fetchPlayers();
    this.intervalId = setInterval(this.fetchPlayers, 1000);
    window.addEventListener('beforeunload', this.handleBeforeUnload);
  },
  beforeUnmount() {
    if (this.intervalId) clearInterval(this.intervalId);
    window.removeEventListener('beforeunload', this.handleBeforeUnload);
  },
  beforeRouteLeave(to, from, next) {
    if (this.playerId) {
      fetch(`${API_BASE}/leave/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ player_id: this.playerId }),
        keepalive: true,
      }).finally(() => {
        localStorage.removeItem('playerId');
        next();
      });
    } else {
      next();
    }
  },
};
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&family=Roboto:wght@400;700&display=swap');

.room-lobby-layout {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  gap: 40px;
  max-width: 1100px;    /* 讓整體最大不會太窄 */
  margin: 0 auto;
}
.game-settings-block {
  min-width: 240px;
  background: #faf6ea;
  padding: 22px 18px 30px;
  border-radius: 14px;
  box-shadow: 0 0 8px #eee;
  font-family: 'Noto Sans TC', 'Roboto', sans-serif;
  margin-top: 10px;
}
.setting-group {
  margin-bottom: 18px;
}
.setting-group label {
  font-weight: bold;
  margin-bottom: 8px;
  display: block;
  color: #444;
}
.option-buttons {
  display: flex;
  gap: 10px;
  flex-wrap: nowrap;
}
.option-buttons button {
  flex: 1;
  min-width: 80px;
  text-align: center;
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid #ccc;
  background: #f2f2f2;
  color: #333;
  cursor: pointer;
  font-size: 0.95rem;
  transition: background 0.2s, color 0.2s;
}
.option-buttons button.selected {
  background: #8c6cfb;
  color: white;
  font-weight: bold;
  border-color: #7b5be3;
}
.option-buttons button:hover:enabled {
  background: #eee;
}
.option-buttons button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.room-lobby {
  flex: 1;
  min-width: 380px;    /* 右側最小寬，不會太窄 */
  /* max-width: 700px; */ /* 可取消或設大一點 */
  margin: 40px 0;
  padding: 30px;
  border-radius: 18px;
  box-shadow: 0 0 14px #ddd;
  background: #f7f7fa;
  font-family: 'Noto Sans TC', 'Roboto', sans-serif;
}

.round-time-btn-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 10px;
}
.rt-btn {
  padding: 9px 0;
  border: none;
  border-radius: 8px;
  background: #e5e2f3;
  color: #594b8c;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}
.rt-btn.selected {
  background: #7e68e8;
  color: #fff;
  border: 2px solid #4d3399;
}
.rt-btn:disabled,
.rt-btn.disabled {
  cursor: not-allowed;
  opacity: 0.65;
}
h2, h3 {
  font-weight: 700;
  letter-spacing: 1px;
  color: #5b4ca0;
}
ul {
  padding-left: 0;
}
li {
  padding: 4px 0;
  list-style: none;
  font-size: 1.15rem;
  border-bottom: 1px solid #eee;
  display: flex;
  align-items: center;
}
li.self {
  background: #ece7fa;
  font-weight: bold;
  border-bottom: 2px solid #bca4fa;
}
.crown {
  margin-right: 6px;
  color: #f4b942;
  font-size: 1.1em;
}
.me {
  margin-left: 8px;
  color: #7a4aed;
  font-size: 0.98em;
}
button {
  padding: 8px 24px;
  border-radius: 8px;
  background: #a88fee;
  color: #fff;
  border: none;
  font-size: 1.02rem;
  cursor: pointer;
  margin-right: 12px;
}
button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
button:hover:enabled {
  background: #8267c5;
}
button {
  margin-left: 8px;
  padding: 4px 8px;
  border-radius: 6px;
  border: none;
  background: #f56565;
  color: white;
  cursor: pointer;
  font-size: 0.9rem;
}
button:hover {
  background: #c53030;
}
.admin-dialog {
  margin-top: 8px;
  background: #f7f5e6;
  padding: 12px;
  border-radius: 9px;
  max-width: 340px;
}
.admin-panel {
  margin-top: 10px;
  padding: 10px;
  background: #faede9;
  border-radius: 7px;
}
li.idle {
  color: #bbb;
  font-style: italic;
  background: #f2f2f2;
}


</style>
