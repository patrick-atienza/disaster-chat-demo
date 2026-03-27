export function createChatSocket(groupId, userId, { onMessage, onOpen, onClose }) {
  const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
  const url = `${protocol}://${location.host}/ws/${groupId}/${userId}`
  // console.log('connecting to', url)
  const ws = new WebSocket(url)
  let reconnectTimer = null

  ws.onopen = () => onOpen?.()
  ws.onclose = () => {
    // clearTimeout(reconnectTimer)
    onClose?.()
  }
  ws.onerror = (e) => console.warn('ws error', e)  // happens sometimes on chrome
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    // console.log('ws message', data.type)
    onMessage?.(data)
  }

  function send(content) {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ content }))
    }
  }

  function close() {
    ws.close()
  }

  return { send, close }
}
