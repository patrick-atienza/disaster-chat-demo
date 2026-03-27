import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import ChatGroup from '../components/ChatGroup.vue'

const mockGroups = [{ id: 1, name: 'Test Group', members: [] }]
const mockMessages = [
  { id: 1, content: 'Hello!', created_at: '2025-01-01T12:00:00Z', sender_id: 2, group_id: 1, sender: { id: 2, name: 'Bob Miller' } },
]

let mockSocketCallbacks = {}
const mockSend = vi.fn()
const mockClose = vi.fn()

vi.mock('../api.js', () => ({
  fetchGroups: vi.fn(() => Promise.resolve(mockGroups)),
  fetchMessages: vi.fn(() => Promise.resolve(mockMessages)),
}))

vi.mock('../socket.js', () => ({
  createChatSocket: vi.fn((groupId, userId, cbs) => {
    mockSocketCallbacks = cbs
    return { send: mockSend, close: mockClose }
  }),
}))

describe('ChatGroup', () => {
  const currentUser = { id: 1, name: 'alice', email: 'alice@email.com' }

  beforeEach(() => {
    mockSend.mockClear()
    mockClose.mockClear()
  })

  it('shows group name and messages after mount', async () => {
    const wrapper = mount(ChatGroup, { props: { currentUser, groupId: 1 } })
    await vi.dynamicImportSettled()
    await wrapper.vm.$nextTick()
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('Test Group')
    expect(wrapper.text()).toContain('Hello!')
  })

  it('sends message through socket', async () => {
    const wrapper = mount(ChatGroup, { props: { currentUser, groupId: 1 } })
    await vi.dynamicImportSettled()
    await wrapper.vm.$nextTick()
    await wrapper.vm.$nextTick()

    mockSocketCallbacks.onOpen?.()
    await wrapper.vm.$nextTick()

    await wrapper.find('input').setValue('Hi!')
    await wrapper.find('form').trigger('submit')
    expect(mockSend).toHaveBeenCalledWith('Hi!')
  })

  it('cleans up socket on unmount', async () => {
    const wrapper = mount(ChatGroup, { props: { currentUser, groupId: 1 } })
    await vi.dynamicImportSettled()
    await wrapper.vm.$nextTick()
    wrapper.unmount()
    expect(mockClose).toHaveBeenCalled()
  })
})