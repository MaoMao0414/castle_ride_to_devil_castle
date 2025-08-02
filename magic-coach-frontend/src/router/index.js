import { createRouter, createWebHistory } from 'vue-router'
import JoinRoom from '../components/JoinRoom.vue'
import RoomLobby from '../components/RoomLobby.vue'
import AdminLobby from '@/components/AdminLobby.vue'
import GamePlay from '../components/GamePlay.vue'   // <--- 新增這行

const routes = [
  { path: '/', component: JoinRoom },
  { path: '/room/:roomCode', component: RoomLobby, props: true },
  { path: '/admin-lobby', name: 'AdminLobby', component: AdminLobby },
  { path: '/game/:roomCode', component: GamePlay, props: true },  // <--- 新增這行
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
