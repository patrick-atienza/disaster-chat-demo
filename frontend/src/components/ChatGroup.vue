<template>
  <div class="chat-wrapper d-flex vh-100">
    <div class="d-flex flex-column flex-grow-1" style="min-width: 0">
      <div class="chat-header d-flex justify-content-between align-items-center px-4 py-3">
        <div>
          <div class="fw-semibold fs-5">{{ groupName }}</div>
          <small class="status-dot" :class="connected ? 'text-success' : 'text-warning'">
            <span class="d-inline-block rounded-circle me-1" :class="connected ? 'bg-success' : 'bg-warning'" style="width: 6px; height: 6px"></span>
            {{ connected ? 'Connected' : 'Connecting...' }}
          </small>
        </div>
        <button class="btn btn-outline-secondary btn-sm px-3" @click="$emit('leave')">
          Leave
        </button>
      </div>

      <div class="flex-grow-1 overflow-auto px-4 py-3" ref="messagesEl" style="background: whitesmoke">
        <div
          v-for="msg in messages"
          :key="msg.id"
          class="d-flex flex-column mb-3"
          :class="msg.sender_id === currentUser.id ? 'align-items-end' : 'align-items-start'"
        >
          <small class="text-muted mb-1 px-1" style="font-size: 0.75rem" v-if="msg.sender_id !== currentUser.id">{{ msg.sender_name }}</small>
          <div
            class="msg-bubble px-3 py-2 d-inline-block rounded"
            style="max-width: 65%; word-break: break-word"
            :class="msg.sender_id === currentUser.id ? 'msg-mine' : 'msg-theirs'"
          >{{ msg.content }}</div>
          <small
            v-if="msg.sender_id === currentUser.id"
            class="px-1 mt-1"
            style="font-size: 0.65rem"
            :class="msg.sending ? 'text-warning' : 'text-muted'"
          >{{ msg.sending ? 'Sending...' : '✓ Sent' }}</small>
        </div>
      </div>

      <div class="chat-input px-4 py-3">
        <form class="d-flex gap-2" @submit.prevent="sendMessage">
          <input
            v-model="newMessage"
            class="form-control border-0"
            style="background: whitesmoke"
            placeholder="Type a message..."
            :disabled="!connected"
          />
          <button
            type="submit"
            class="btn btn-primary px-4"
            :disabled="!connected || !newMessage.trim()"
          >Send</button>
        </form>
      </div>
    </div>

    <div class="online-sidebar d-flex flex-column">
      <div class="px-3 py-3 border-bottom">
        <div class="fw-semibold text-muted text-uppercase small ls-wide">People in area</div>
      </div>
      <ul class="list-unstyled m-0 px-2 py-2 overflow-auto flex-grow-1">
        <li
          v-for="u in allMembers"
          :key="u.id"
          class="d-flex align-items-center gap-2 px-2 py-2 rounded-2 user-item"
          :class="[u.id === currentUser.id ? 'fw-semibold' : '', !isOnline(u.id) ? 'opacity-50' : '']"
        >
          <div class="user-avatar d-flex align-items-center justify-content-center rounded-circle text-white fw-bold" style="width: 32px; height: 32px; font-size: 0.8rem" :style="{ background: avatarColor(u.name) }">
            {{ u.name.charAt(0).toUpperCase() }}
          </div>
          <div class="d-flex flex-column text-truncate" style="min-width: 0">
            <span class="text-truncate small">{{ u.name }}{{ u.id === currentUser.id ? ' (you)' : '' }}</span>
            <a
              v-if="u.last_lat && u.last_lng"
              :href="`https://www.google.com/maps?q=${u.last_lat},${u.last_lng}`"
              target="_blank"
              class="text-muted text-truncate"
              style="font-size: 0.65rem; text-decoration: none"
              @click.stop
            >📍 {{ u.last_lat.toFixed(4) }}, {{ u.last_lng.toFixed(4) }}</a>
          </div>
          <span class="ms-auto rounded-circle d-inline-block flex-shrink-0" :class="isOnline(u.id) ? 'bg-success' : 'bg-secondary'" style="width: 8px; height: 8px"></span>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { fetchGroups, fetchMessages } from '../api.js'
import { createChatSocket } from '../socket.js'

const props = defineProps({
  currentUser: Object,
  groupId: Number,
})

defineEmits(['leave'])

const groupName = ref('')
const messages = ref([])
const newMessage = ref('')
const connected = ref(false)
const onlineUsers = ref([])
const allMembers = ref([])
const messagesEl = ref(null)

function isOnline(userId) {
  return onlineUsers.value.some(u => u.id === userId)
}

let socket = null

const userColors = {}
let colorIdx = 0
const palette = ['#3b82f6', '#dc2626', '#7c3aed', '#d97706', '#059669', '#ec4899', '#78716c', '#1e293b']
function avatarColor(name) {
  if (!userColors[name]) userColors[name] = palette[colorIdx++ % palette.length]
  return userColors[name]
}

let pendingId = 0

function sendMessage() {
  const text = newMessage.value.trim()
  if (!text || !socket) return
  const tempId = `pending-${++pendingId}`
  messages.value.push({
    id: tempId,
    content: text,
    sender_id: props.currentUser.id,
    sender_name: props.currentUser.name,
    sending: true,
  })
  socket.send(text)
  newMessage.value = ''
}

watch(messages, () => {
  // tried using IntersectionObserver here to only scroll if user is
  // already at the bottom but it was buggy with the pending messages
  // just always scroll, close enough
  nextTick(() => {
    if (messagesEl.value) messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  })
}, { deep: true })

onMounted(async () => {
  const groups = await fetchGroups()
  // console.log('groups', groups)
  const group = groups.find((g) => g.id === props.groupId)
  groupName.value = group?.name ?? ''
  allMembers.value = group?.members ?? []

  const history = await fetchMessages(props.groupId)
  messages.value = history.map((m) => ({
    id: m.id,
    content: m.content,
    sender_name: m.sender?.name || 'unknown',
    sender_id: m.sender_id,
  }))

  socket = createChatSocket(props.groupId, props.currentUser.id, {
    onOpen: () => { connected.value = true },
    onClose: () => { connected.value = false },
    onMessage: (data) => {
      if (data.type === 'message') {
        const pending = messages.value.find(
          m => m.sending && m.sender_id === data.sender_id && m.content === data.content
        )
        if (pending) {
          Object.assign(pending, data, { sending: false })
        } else {
          messages.value.push({ ...data, sending: false })
        }
      } else if (data.type === 'presence') {
        onlineUsers.value = data.online
      }
    },
  })
})

onUnmounted(() => {
  socket?.close()
})
</script>

<style scoped>
.chat-wrapper {
  max-width: 1100px;
  margin: 0 auto;
  background: white;
  /* safari needs explicit overflow here */
  box-shadow: 0 0 40px rgba(0, 0, 0, 0.08);
}

.chat-header {
  background: white;
  border-bottom: 1px solid silver;
}

.chat-input {
  background: white;
  border-top: 1px solid silver;
}

.msg-mine {
  background: #0d6efd;
  color: white;
  border-radius: 12px 12px 2px 12px;
}

.msg-theirs {
  background: white;
  border-radius: 12px 12px 12px 2px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
}

.online-sidebar {
  width: 214px;  /* 220 was clipping the green dot on some screens */
  border-left: 1px solid silver;
  background: white;
}

.user-item:hover {
  background: whitesmoke;
}

.ls-wide {
  letter-spacing: 0.08em;
}
</style>