import { getToken } from './keycloak.js'


export const fetchMe = () =>
  fetch('/api/me', {
    headers: { Authorization: `Bearer ${getToken()}` }
  }).then(r => r.json())

// const API_TIMEOUT = 5000  // TODO: wire this up
export const fetchGroups = () =>
  fetch('/api/groups').then(r => r.json())

export const fetchMessages = (groupId) =>
  fetch(`/api/groups/${groupId}/messages`).then(r => r.json())
  