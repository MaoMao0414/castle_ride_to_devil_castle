<template>
  <div class="game-play-page">
    <!-- 右上角玩家資訊 -->
    <GameInfoPanel
    :players="players"
    :turnOrder="turnOrder"
    :currentTurnIndex="currentTurnIndex"
    :timer="timer"
    :myPlayerId="myPlayerId"
    />

    <!-- 輪到你回合時，顯示可選操作 -->
    <div v-if="myTurn" class="turn-action-menu">
      <div class="turn-action-inner">
        <div class="turn-hint-title">✨ 輪到你了！ ✨</div>
        <div class="turn-hint-sub">請選擇你的操作</div>
        <button class="action-btn" @click="submitAction('place')">放置卡牌</button>
        <button class="action-btn" @click="submitAction('pass')">跳過回合</button>
      </div>
    </div>
    <!-- 非你回合時淡提示 -->
    <div v-else class="wait-bar">
      等待其他玩家行動中...
    </div>

    <div class="game-main-content">
      <!-- 遊戲主體區塊，可以放牌桌、操作等等 -->
    </div>
  </div>
</template>

<script>
/* eslint-disable */
import GameInfoPanel from './GameInfoPanel.vue'
const API_BASE = process.env.VUE_APP_API_URL || 'http://localhost:9000';

export default {
  name: "GamePlay",
  components: { GameInfoPanel },
  props: ['roomCode'],
  data() {
    return {
      players: [],
      turnOrder: [],
      currentTurnIndex: 0,
      timer: 30,
      myPlayerId: parseInt(localStorage.getItem('playerId')),
      fetchInterval: null,
    }
  },
  computed: {
    currentTurnPlayerId() {
      return this.turnOrder && this.currentTurnIndex !== undefined
        ? this.turnOrder[this.currentTurnIndex]
        : null;
    },
    myTurn() {
      return this.myPlayerId && this.currentTurnPlayerId === this.myPlayerId;
    }
  },
  methods: {
    async fetchGameState() {
      try {
        const res = await fetch(`${API_BASE}/room/${this.roomCode}/players/`);
        const data = await res.json();
        if (data.status === 'ok') {
          this.players = data.players || [];
          this.turnOrder = data.turn_order || [];
          this.currentTurnIndex = data.current_turn_index ?? 0;
          this.timer = data.timer;
        } else {
          this.$router.push('/');
        }
      } catch (e) {}
    },
    async submitAction(action) {
      // 範例：執行動作後自動換回合
      // 這裡你可以加遊戲邏輯 API，再呼叫 next_turn
      await fetch(`${API_BASE}/next_turn/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ room_code: this.roomCode }),
      });
      // 不需特別操作，後端會自動推進回合與 timer
    }
  },
  mounted() {
    this.fetchGameState();
    this.fetchInterval = setInterval(this.fetchGameState, 1000);
  },
  beforeUnmount() {
    if (this.fetchInterval) clearInterval(this.fetchInterval);
  }
}
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&family=Roboto:wght@400;700&display=swap');
.game-play-page {
  position: relative;
  min-height: 100vh;
  background: url('@/assets/bg-main.png') center center/cover no-repeat, #fcfafc;
  font-family: 'Noto Sans TC', 'Roboto', sans-serif;
}
.game-main-content {
  padding-top: 48px;
}
.turn-action-menu {
  position: absolute;
  left: 50%;
  top: 32px;
  transform: translateX(-50%);
  z-index: 99;
  background: linear-gradient(120deg,#fffbe8 80%,#ffe791 100%);
  box-shadow: 0 8px 28px #ecd88d50;
  border-radius: 16px;
  padding: 26px 42px 22px 42px;
  display: flex;
  flex-direction: column;
  align-items: center;
  border: 3px solid #ffe175;
  min-width: 320px;
}
.turn-hint-title {
  font-size: 1.6em;
  color: #d8b108;
  font-weight: 800;
  letter-spacing: 2px;
  text-shadow: 0 2px 10px #fff9e4;
  margin-bottom: 6px;
}
.turn-hint-sub {
  font-size: 1.09em;
  color: #947a10;
  margin-bottom: 15px;
  letter-spacing: 1px;
}
.action-btn {
  background: linear-gradient(90deg, #ffd14d, #ffe89b 80%);
  border: 2px solid #ffeaac;
  color: #b58511;
  font-size: 1.14em;
  border-radius: 8px;
  font-weight: bold;
  padding: 10px 30px;
  margin: 0 10px;
  margin-top: 10px;
  box-shadow: 0 2px 9px #fae08550;
  cursor: pointer;
  transition: background 0.17s, color 0.15s;
}
.action-btn:hover {
  background: #ffe6b5;
  color: #af870a;
}
.wait-bar {
  position: absolute;
  left: 50%;
  top: 36px;
  transform: translateX(-50%);
  background: #fffbe5e8;
  color: #b8a166;
  padding: 7px 34px;
  border-radius: 20px;
  font-size: 1.09em;
  font-family: 'Noto Sans TC','Roboto',sans-serif;
  box-shadow: 0 2px 8px #f3e1b840;
  z-index: 10;
  font-weight: 500;
}
</style>
