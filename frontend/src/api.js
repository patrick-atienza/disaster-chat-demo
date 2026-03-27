import { getToken } from './keycloak.js'

export async function fetchMe() {
  const r = await fetch('/api/me', {
    headers: { Authorization: `Bearer ${getToken()}` }
  })
  return r.json()
}

// const API_TIMEOUT = 5000  // TODO: wire this up
export const fetchGroups = () =>
  fetch('/api/groups')
    .then(r => r.json())
    .catch(() => [])
export const fetchMessages = (groupId) =>
  fetch(`/api/groups/${groupId}/messages`).then(r => r.json())
