<template>
  <div class="game-info-panel">
    <!-- 計時器（不限時就顯示不限時） -->
    <div v-if="timer !== null && timer !== undefined" class="timer-block">
      <span class="timer-label">倒數：</span>
      <span class="timer-value">{{ timer }}</span>
      <span class="timer-unit">秒</span>
    </div>
    <div v-else class="timer-block" style="color: #bbb; text-align: center;">
      <span class="timer-label">不限時</span>
    </div>
    <!-- 玩家列表 -->
    <div class="players-list">
      <div
        v-for="p in orderedPlayers"
        :key="p.id"
        :class="['player-item', { active: p.id === currentTurnPlayerId }]"
      >
        <div class="player-info">
          <span class="player-id">
            {{ p.nickname }}
            <span v-if="myPlayerId === p.id" class="self-me">(我)</span>
          </span>
          <span class="player-hand" style="position: relative;">
            <span
              class="hand-icon"
              @mouseover="showHandTooltip = p.id"
              @mouseleave="showHandTooltip = null"
              >🂡</span>
            <span class="hand-count">{{ p.handCount }}</span>
            <!-- icon 說明浮窗 -->
            <span
              v-if="showHandTooltip === p.id"
              class="hand-tooltip"
            >手牌數量</span>
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
/* eslint-disable */
/* eslint-disable no-empty, no-unused-vars */
export default {
  name: "GameInfoPanel",
  props: {
    players: Array,           // [{id, nickname, handCount}]
    turnOrder: Array,         // [id, id, ...]，照順序排
    currentTurnIndex: Number, // 目前輪到第幾位（建議由後端算好傳來）
    timer: Number,            // 回合倒數（null 表示不限時）
    myPlayerId: Number,       // 自己的 id
  },
  data() {
    return {
      showHandTooltip: null,
    };
  },
  computed: {
    orderedPlayers() {
      if (!this.players || !this.turnOrder) return [];
      // 依回合順序排序
      return this.turnOrder
        .map(id => this.players.find(p => p.id === id))
        .filter(Boolean);
    },
    currentTurnPlayerId() {
      return this.turnOrder && this.currentTurnIndex !== undefined
        ? this.turnOrder[this.currentTurnIndex]
        : null;
    },
  },
};
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&family=Roboto:wght@400;700&display=swap');

.game-info-panel {
  position: absolute;
  top: 32px;
  right: 40px;
  width: 270px;
  background: rgba(255, 250, 230, 0.96); /* 淡黃底 */
  border-radius: 15px;
  box-shadow: 0 4px 14px #f3e4a5; /* 黃金色陰影 */
  padding: 18px 16px 14px 16px;
  z-index: 10;
  min-height: 240px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  font-family: 'Noto Sans TC', 'Roboto', sans-serif;
}

.timer-block {
  display: flex;
  align-items: center;
  font-size: 1.2rem;
  font-weight: bold;
  color: #b38f00; /* 金黃 */
  margin-bottom: 14px;
  justify-content: center;
}
.timer-label { margin-right: 6px; }
.timer-value { font-size: 1.7rem; margin: 0 4px; }
.timer-unit { font-size: 1.1rem; color: #e6d165; }

.players-list {
  max-height: 260px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.player-item {
  background: #fff9d0; /* 輕柔黃底 */
  border-radius: 9px;
  padding: 10px 12px;
  display: flex;
  align-items: center;
  box-shadow: 0 2px 8px #f2e5a7aa; /* 黃色陰影 */
  border: 2px solid transparent;
  transition: border 0.18s;
  min-height: 54px;
}
.player-item.active {
  border: 2.5px solid #d4af37; /* 金色邊框 */
  box-shadow: 0 0 9px #f0d86e90; /* 黃色光暈 */
}
.player-info {
  display: flex;
  align-items: center;
  width: 100%;
  justify-content: space-between;
}
.player-id {
  font-weight: bold;
  font-size: 1.09rem;
  color: #b8860b; /* 黃褐色字 */
  letter-spacing: 1.5px;
}
.self-me {
  margin-left: 8px;
  color: #e0b84f; /* 明亮金黃 */
  font-size: 0.96em;
  font-weight: bold;
  letter-spacing: 0.5px;
}
.player-hand {
  display: flex;
  align-items: center;
  gap: 3px;
  position: relative;
}
.hand-icon {
  width: 22px;
  height: 22px;
  margin-right: 3px;
  vertical-align: middle;
  cursor: pointer;
  font-size: 1.18em;
  transition: filter 0.12s;
}
.hand-icon:hover {
  filter: drop-shadow(0 2px 3px #ffefadbb);
}
.hand-count {
  font-weight: 700;
  font-size: 1.13rem;
  color: #d4af37; /* 金色字 */
}
.hand-tooltip {
  position: absolute;
  top: -28px;
  left: 50%;
  transform: translateX(-50%);
  background: #fff9d0;
  border: 1px solid #f0e68c;
  color: #b8860b;
  padding: 2.5px 13px;
  border-radius: 8px;
  font-size: 0.93em;
  box-shadow: 0 2px 10px #f4d88499;
  white-space: nowrap;
  z-index: 20;
  pointer-events: none;
}
</style>
