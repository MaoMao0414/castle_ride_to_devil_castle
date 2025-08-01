<template>
  <div class="admin-lobby">
    <h2>管理員大廳</h2>
    <label>
      管理密碼：
      <input v-model="adminPassword" type="password" />
    </label>
    <button @click="deleteAllRooms" :disabled="loading">刪除所有房間</button>
    <p v-if="message" :style="{ color: messageColor }">{{ message }}</p>

    <h3 style="margin-top:30px;">所有房間列表</h3>
    <button @click="fetchRooms" style="margin-bottom:10px;">刷新房間列表</button>
    <ul>
      <li v-for="room in rooms" :key="room.room_code" style="margin-bottom:10px;">
        <span><b>代碼：</b>{{ room.room_code }}</span>
        <span><b>人數：</b>{{ room.player_count }}/{{ room.max_player }}</span>
        <span><b>狀態：</b>
          <span :style="{color: room.started ? 'green' : '#666'}">
            {{ room.started ? "遊戲中" : "可加入" }}
          </span>
        </span>
        <button
          @click="deleteRoom(room.room_code)"
          style="margin-left:16px;background:#c44;"
        >刪除</button>
      </li>
    </ul>
  </div>
</template>

<script>
const API_BASE = process.env.VUE_APP_API_URL || 'http://localhost:9000';

export default {
  data() {
    return {
      adminPassword: '',
      loading: false,
      message: '',
      messageColor: 'green',
      rooms: [],
    };
  },
  methods: {
    async fetchRooms() {
      try {
        const res = await fetch(`${API_BASE}/admin_list_rooms/`);
        const data = await res.json();
        this.rooms = data.rooms;
      } catch (e) {
        this.rooms = [];
      }
    },
    async deleteAllRooms() {
      if (!this.adminPassword) {
        this.message = '請輸入管理密碼';
        this.messageColor = 'red';
        return;
      }
      if (!confirm('確定要刪除所有房間嗎？此動作無法復原！')) return;

      this.loading = true;
      this.message = '';
      try {
        const res = await fetch(`${API_BASE}/admin_delete_all_rooms/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ admin_password: this.adminPassword }),
        });
        const data = await res.json();
        if (data.status === 'ok') {
          this.message = '所有房間已成功刪除！';
          this.messageColor = 'green';
          this.fetchRooms();
        } else {
          this.message = '錯誤：' + (data.message || '刪除失敗');
          this.messageColor = 'red';
        }
      } catch (err) {
        this.message = '發生錯誤：' + err.message;
        this.messageColor = 'red';
      } finally {
        this.loading = false;
      }
    },
    async deleteRoom(roomCode) {
      if (!this.adminPassword) {
        this.message = '請先輸入管理密碼';
        this.messageColor = 'red';
        return;
      }
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
          this.message = `房間 ${roomCode} 已刪除！`;
          this.messageColor = 'green';
          this.fetchRooms();
        } else {
          this.message = '錯誤：' + (data.message || '');
          this.messageColor = 'red';
        }
      } catch (err) {
        this.message = '發生錯誤：' + err.message;
        this.messageColor = 'red';
      }
    },
  },
  mounted() {
    this.fetchRooms();
  },
};
</script>
