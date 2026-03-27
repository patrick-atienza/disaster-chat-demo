<template>
  <ChatGroup
    v-if="currentUser && groupId"
    :current-user="currentUser"
    :group-id="groupId"
    @leave="handleLogout"
  />
  <div v-else-if="ready" class="d-flex flex-column align-items-center justify-content-center min-vh-100" style="background: whitesmoke">
    <div class="spinner-border text-primary mb-3" role="status"></div>
    <div class="text-muted">Loading group...</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { initKeycloak, logout } from './keycloak.js'
import { fetchMe, fetchGroups } from './api.js'
import ChatGroup from './components/ChatGroup.vue'

const ready = ref(false)
const currentUser = ref(null)
const groupId = ref(null)

onMounted(async () => {
  try {
    await initKeycloak()
    const user = await fetchMe()
    console.log('logged in as', user.name)
    currentUser.value = user
    const groups = await fetchGroups()
    const group = groups.find(g => g.members.some(m => m.id === user.id))
    groupId.value = group?.id
  } catch (err) {
    console.error('failed to init', err)
  }
  ready.value = true
})

function handleLogout() {
  logout()
}
</script>


