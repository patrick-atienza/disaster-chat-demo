import { getToken } from './keycloak.js'

const API_TIMEOUT = 5000


function fetchWithTimeout(resource, options = {}) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), API_TIMEOUT);
  return fetch(resource, { ...options, signal: controller.signal })
    .finally(() => clearTimeout(id));
}

export const fetchMe = () =>
  fetchWithTimeout('/api/me', {
    headers: { Authorization: `Bearer ${getToken()}` }
  }).then(r => r.json())

export const fetchGroups = () =>
  fetchWithTimeout('/api/groups').then(r => r.json())

export const fetchMessages = (groupId) =>
  fetchWithTimeout(`/api/groups/${groupId}/messages`).then(r => r.json())
  