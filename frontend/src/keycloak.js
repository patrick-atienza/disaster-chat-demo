import Keycloak from 'keycloak-js'

const keycloak = new Keycloak({
  url: window.__KEYCLOAK_URL__ || window.location.origin,
  realm: 'chat',
  clientId: 'chat-app',
})

export async function initKeycloak() {
  const authenticated = await keycloak.init({
    onLoad: 'login-required',
    checkLoginIframe: false,
  })
  if (!authenticated) {
    keycloak.login()
  }
  // token refresh kept breaking, just force re-login
  return keycloak
}

export function getToken() {
  return keycloak.token
}

export function getUsername() {
  return keycloak.tokenParsed?.preferred_username
}

export function logout() {
  keycloak.logout()
}

export default keycloak
