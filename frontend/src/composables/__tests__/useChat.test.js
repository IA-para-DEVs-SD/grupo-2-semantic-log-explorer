/**
 * Unit tests for useChat composable.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useChat } from '../useChat.js'

describe('useChat', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('initializes with empty state', () => {
    const { messages, isLoading, isStreaming, error } = useChat()
    expect(messages.value).toEqual([])
    expect(isLoading.value).toBe(false)
    expect(isStreaming.value).toBe(false)
    expect(error.value).toBeNull()
  })

  it('adds a user message', () => {
    const { addUserMessage, messages } = useChat()
    addUserMessage('Hello')
    expect(messages.value).toHaveLength(1)
    expect(messages.value[0].sender).toBe('user')
    expect(messages.value[0].content).toBe('Hello')
  })

  it('trims user message content', () => {
    const { addUserMessage, messages } = useChat()
    addUserMessage('  Hello  ')
    expect(messages.value[0].content).toBe('Hello')
  })

  it('adds an AI message', () => {
    const { addAIMessage, messages } = useChat()
    addAIMessage('Response')
    expect(messages.value).toHaveLength(1)
    expect(messages.value[0].sender).toBe('ai')
    expect(messages.value[0].content).toBe('Response')
  })

  it('adds AI message with empty content by default', () => {
    const { addAIMessage, messages } = useChat()
    addAIMessage()
    expect(messages.value[0].content).toBe('')
  })

  it('sets error for empty question', async () => {
    const { sendMessage, error, messages } = useChat()
    await sendMessage('')
    expect(error.value).toBe('A pergunta não pode estar vazia')
    expect(messages.value).toHaveLength(0)
  })

  it('sets error for whitespace-only question', async () => {
    const { sendMessage, error } = useChat()
    await sendMessage('   ')
    expect(error.value).toBe('A pergunta não pode estar vazia')
  })

  it('sets error for null question', async () => {
    const { sendMessage, error } = useChat()
    await sendMessage(null)
    expect(error.value).toBe('A pergunta não pode estar vazia')
  })

  it('clears messages', () => {
    const { addUserMessage, addAIMessage, clearMessages, messages } = useChat()
    addUserMessage('Q')
    addAIMessage('A')
    expect(messages.value).toHaveLength(2)
    clearMessages()
    expect(messages.value).toHaveLength(0)
  })

  it('clears error', () => {
    const { sendMessage, clearError, error } = useChat()
    sendMessage('')
    expect(error.value).not.toBeNull()
    clearError()
    expect(error.value).toBeNull()
  })

  it('generates unique message IDs', () => {
    const { addUserMessage, messages } = useChat()
    addUserMessage('A')
    addUserMessage('B')
    expect(messages.value[0].id).not.toBe(messages.value[1].id)
  })

  it('includes timestamp on messages', () => {
    const { addUserMessage, messages } = useChat()
    addUserMessage('Test')
    expect(messages.value[0].timestamp).toBeInstanceOf(Date)
  })

  it('accepts custom apiUrl', () => {
    const chat = useChat({ apiUrl: '/custom/chat' })
    expect(chat).toBeDefined()
  })
})
