<template>
  <div class="join-room">
    <!-- Admin 功能按鈕右上角 -->
    <div class="admin-top">
      <button @click="adminMode = true" v-if="!isAdmin">Admin 功能</button>
      <div v-if="adminMode && !isAdmin" class="admin-dialog">
        <label>
          管理密碼：
          <input v-model="adminPassword" type="password" />
        </label>
        <button @click="verifyAdmin">驗證</button>
        <button @click="adminMode = false">取消</button>
        <p v-if="adminError" style="color:red;">{{ adminError }}</p>
      </div>
      <div v-if="isAdmin" class="admin-panel">
        <p style="color:#a66;"><b>管理員已解鎖！</b></p>
      </div>
    </div>

    <h2>可加入的房間</h2>
    <ul class="room-list">
      <li v-for="room in rooms" :key="room.room_code">
        <span class="room-code">{{ room.room_code }}</span>
        <span class="room-players">{{ room.player_count }}/{{ room.max_player }}</span>
        <div class="room-actions">
          <button
            v-if="isAdmin"
            @click="deleteRoom(room.room_code)"
            class="delete-btn"
          >刪除</button>
          <button
            @click="quickJoin(room.room_code)"
            class="join-btn"
            :disabled="room.player_count >= room.max_player"
          >
            {{ room.player_count >= room.max_player ? '已滿' : '加入' }}
          </button>
        </div>
      </li>
    </ul>

    <h3 style="margin-top: 36px;">建立新房間</h3>
    <form @submit.prevent="createRoom">
      <label>
        暱稱：
        <input v-model="nickname" maxlength="12" placeholder="最多12字" required />
      </label>
      <label>
        房間代碼：
        <input v-model="roomCode" maxlength="10" required />
      </label>
      <label>
        最大人數：
        <select v-model.number="maxPlayer" required>
          <option v-for="n in maxPlayerOptions" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <button type="submit">建立</button>
    </form>
    <div v-if="result">
      <p>結果：{{ result }}</p>
    </div>
  </div>
</template>

<script>
const API_BASE = process.env.VUE_APP_API_URL || 'http://localhost:9000';

export default {
  data() {
    return {
      nickname: "",
      roomCode: "",
      maxPlayer: 6,
      maxPlayerOptions: [3,4,5,6,7,8,9,10],
      result: null,
      rooms: [],
      intervalId: null,
      adminMode: false,
      adminPassword: "",
      isAdmin: false,
      adminError: "",
    };
  },
  methods: {
    async fetchPlayersInRoom(roomCode) {
      try {
        const res = await fetch(`${API_BASE}/room/${roomCode}/players/`);
        const data = await res.json();
        if (data.status === 'ok') {
          return data.players;  // 回傳玩家陣列
        }
        return [];
      } catch (e) {
        return [];
      }
    },

    async checkNicknameExists(roomCode, nickname) {
      const players = await this.fetchPlayersInRoom(roomCode);
      return players.some(p => p.nickname === nickname);
    },

    async checkRoomExists(roomCode) {
      const res = await fetch(`${API_BASE}/rooms/`);
      const data = await res.json();
      return data.rooms.some(r => r.room_code === roomCode);
    },

    async fetchRooms() {
      try {
        const res = await fetch(`${API_BASE}/rooms/`);
        const data = await res.json();
        this.rooms = data.rooms;
      } catch (err) {
        this.rooms = [];
      }
    },

    generateRandomName() {
      return 'player' + Math.floor(Math.random() * 90000 + 10000);
    },

    async quickJoin(roomCode) {
      const nick = this.nickname && this.nickname.trim() ? this.nickname.trim() : this.generateRandomName();
      try {
        const res = await fetch(`${API_BASE}/join/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            nickname: nick,
            room_code: roomCode,
          }),
        });
        const data = await res.json();
        if (data.status === 'ok') {
          localStorage.setItem('playerId', data.player_id);
          this.$router.push({ path: `/room/${roomCode}` });
        } else {
          alert(data.message || '加入失敗');
        }
      } catch (err) {
        alert('發生錯誤：' + err.message);
      }
    },

    async createRoom() {
      if (!this.nickname || !this.roomCode || !this.maxPlayer) {
        this.result = "請填寫完整";
        return;
      }
      if (await this.checkRoomExists(this.roomCode.trim())) {
        this.result = '房間名稱已存在，請換一個';
        return;
      }
      if (await this.checkNicknameExists(this.roomCode.trim(), this.nickname.trim())) {
        this.result = '該房間已有相同暱稱玩家，請換一個暱稱';
        return;
      }
      try {
        const res = await fetch(`${API_BASE}/join/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            nickname: this.nickname.trim(),
            room_code: this.roomCode.trim(),
            max_player: this.maxPlayer,
          }),
        });
        const data = await res.json();
        if (data.status === 'ok') {
          localStorage.setItem('playerId', data.player_id);
          this.$router.push({ path: `/room/${this.roomCode}` });
        } else {
          this.result = data.message || '建立失敗';
        }
      } catch (err) {
        this.result = '發生錯誤：' + err.message;
      }
    },

    verifyAdmin() {
      if (!this.adminPassword || this.adminPassword.length < 3) {
        this.adminError = "請輸入正確管理密碼";
        return;
      }
      this.isAdmin = true;
      this.adminError = "";
      this.adminMode = false;
    },

    async deleteRoom(roomCode) {
      if (!confirm(`確定要刪除房間 ${roomCode} 嗎？`)) return;
      try {
        const res = await fetch(`${API_BASE}/admin_delete_room/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            room_code: roomCode,
            admin_password: this.adminPassword,
          }),
        });
        const data = await res.json();
        if (data.status === 'ok') {
          alert('房間已刪除！');
          this.fetchRooms();
        } else {
          alert('刪除失敗：' + (data.message || ''));
        }
      } catch (err) {
        alert('發生錯誤：' + err.message);
      }
    },
  },
  mounted() {
    this.fetchRooms();
    this.intervalId = setInterval(this.fetchRooms, 3000); // 每 3 秒
  },
  beforeUnmount() {
    clearInterval(this.intervalId);
  },
};
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&family=Roboto:wght@400;700&display=swap');

.join-room {
  max-width: 500px;
  margin: 40px auto;
  padding: 28px;
  border-radius: 16px;
  box-shadow: 0 0 12px #ddd;
  background: #f6f7fb;
  font-family: 'Noto Sans TC', 'Roboto', sans-serif;
  position: relative;
}
.admin-top {
  position: absolute;
  top: 22px;
  right: 36px;
  z-index: 10;
  text-align: right;
}
h2, h3 {
  font-weight: 700;
  letter-spacing: 1px;
  color: #5746af;
  margin-top: 24px;
}
.room-list {
  padding-left: 0;
  margin-bottom: 16px;
}
.room-list li {
  list-style: none;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  background: #ece9ff;
  border-radius: 8px;
  padding: 7px 12px;
  font-size: 1.13rem;
  justify-content: space-between;
}
.room-code {
  font-weight: bold;
  margin-right: 10px;
  letter-spacing: 1px;
  flex-shrink: 0;
}
.room-players {
  margin-left: 18px;
  color: #7660e2;
  font-size: 0.97em;
  min-width: 50px;
  display: inline-block;
}
.room-actions {
  display: flex;
  align-items: center;
}
.room-actions .delete-btn {
  background: #d73a3a;
  margin-right: 10px;
  order: 1;
}
.room-actions .delete-btn:hover {
  background: #b32525;
}
.room-actions .join-btn {
  background: #7b6dee;
  order: 2;
}
.room-actions .join-btn:hover {
  background: #6151b7;
}
form {
  margin-top: 18px;
}
label {
  display: block;
  margin: 14px 0 6px;
}
input, select {
  width: 100%;
  padding: 7px;
  border-radius: 7px;
  border: 1px solid #ccc;
  margin-top: 2px;
  margin-bottom: 10px;
  font-size: 1.08rem;
  font-family: inherit;
}
button[type="submit"] {
  margin-top: 10px;
  padding: 8px 28px;
  border-radius: 8px;
  background: #6a5acd;
  color: #fff;
  border: none;
  font-size: 1.1rem;
  cursor: pointer;
}
button[type="submit"]:hover {
  background: #5746af;
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
</style>
