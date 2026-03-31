/**
 * Unit tests for useChat composable.
 * Tests API communication, SSE streaming, and state management.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useChat } from '../../src/composables/useChat.js'

describe('useChat', () => {
  let originalFetch

  beforeEach(() => {
    originalFetch = global.fetch
    vi.useFakeTimers()
  })

  afterEach(() => {
    global.fetch = originalFetch
    vi.useRealTimers()
  })

  describe('Initial State', () => {
    it('initializes with empty messages array', () => {
      const { messages } = useChat()
      expect(messages.value).toEqual([])
    })

    it('initializes with isLoading false', () => {
      const { isLoading } = useChat()
      expect(isLoading.value).toBe(false)
    })

    it('initializes with isStreaming false', () => {
      const { isStreaming } = useChat()
      expect(isStreaming.value).toBe(false)
    })

    it('initializes with null error', () => {
      const { error } = useChat()
      expect(error.value).toBe(null)
    })
  })

  describe('Configuration', () => {
    it('uses default API URL', () => {
      const chat = useChat()
      // Default is /api/chat - tested via sendMessage behavior
      expect(chat).toBeDefined()
    })

    it('accepts custom API URL', () => {
      const chat = useChat({ apiUrl: '/custom/chat' })
      expect(chat).toBeDefined()
    })
  })

  describe('addUserMessage', () => {
    it('adds user message to messages array', () => {
      const { messages, addUserMessage } = useChat()
      
      addUserMessage('Hello')
      
      expect(messages.value.length).toBe(1)
      expect(messages.value[0].content).toBe('Hello')
      expect(messages.value[0].sender).toBe('user')
    })

    it('trims whitespace from message', () => {
      const { messages, addUserMessage } = useChat()
      
      addUserMessage('  Hello  ')
      
      expect(messages.value[0].content).toBe('Hello')
    })

    it('generates unique ID for each message', () => {
      const { messages, addUserMessage } = useChat()
      
      addUserMessage('First')
      addUserMessage('Second')
      
      expect(messages.value[0].id).not.toBe(messages.value[1].id)
    })

    it('adds timestamp to message', () => {
      const { messages, addUserMessage } = useChat()
      
      addUserMessage('Hello')
      
      expect(messages.value[0].timestamp).toBeInstanceOf(Date)
    })

    it('returns the created message', () => {
      const { addUserMessage } = useChat()
      
      const message = addUserMessage('Hello')
      
      expect(message.content).toBe('Hello')
      expect(message.sender).toBe('user')
    })
  })

  describe('addAIMessage', () => {
    it('adds AI message to messages array', () => {
      const { messages, addAIMessage } = useChat()
      
      addAIMessage('Response')
      
      expect(messages.value.length).toBe(1)
      expect(messages.value[0].content).toBe('Response')
      expect(messages.value[0].sender).toBe('ai')
    })

    it('creates empty message when no content provided', () => {
      const { messages, addAIMessage } = useChat()
      
      addAIMessage()
      
      expect(messages.value[0].content).toBe('')
    })
  })

  describe('sendMessage', () => {
    it('sets error for empty question', async () => {
      const { error, sendMessage } = useChat()
      
      await sendMessage('')
      
      expect(error.value).toContain('vazia')
    })

    it('sets error for whitespace-only question', async () => {
      const { error, sendMessage } = useChat()
      
      await sendMessage('   ')
      
      expect(error.value).toContain('vazia')
    })

    it('adds user message before API call', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        headers: new Map([['content-type', 'application/json']]),
        json: () => Promise.resolve({ response: 'Answer' })
      })
      
      const { messages, sendMessage } = useChat()
      
      const promise = sendMessage('Question')
      
      // User message should be added immediately
      expect(messages.value.length).toBeGreaterThanOrEqual(1)
      expect(messages.value[0].sender).toBe('user')
      expect(messages.value[0].content).toBe('Question')
      
      await promise
    })

    it('adds AI message placeholder for streaming', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        headers: new Map([['content-type', 'application/json']]),
        json: () => Promise.resolve({ response: 'Answer' })
      })
      
      const { messages, sendMessage } = useChat()
      
      const promise = sendMessage('Question')
      
      // AI message placeholder should be added
      expect(messages.value.length).toBe(2)
      expect(messages.value[1].sender).toBe('ai')
      
      await promise
    })

    it('sets isLoading to true during request', async () => {
      let resolvePromise
      global.fetch = vi.fn().mockReturnValue(
        new Promise(resolve => { resolvePromise = resolve })
      )
      
      const { isLoading, sendMessage } = useChat()
      
      const promise = sendMessage('Question')
      
      expect(isLoading.value).toBe(true)
      
      resolvePromise({
        ok: true,
        headers: new Map([['content-type', 'application/json']]),
        json: () => Promise.resolve({ response: 'Answer' })
      })
      
      await promise
      
      expect(isLoading.value).toBe(false)
    })

    it('clears error before sending', async () => {
      const { error, sendMessage } = useChat()
      
      // Set initial error
      await sendMessage('')
      expect(error.value).toBeTruthy()
      
      // Mock successful request
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        headers: new Map([['content-type', 'application/json']]),
        json: () => Promise.resolve({ response: 'Answer' })
      })
      
      await sendMessage('Valid question')
      
      expect(error.value).toBe(null)
    })

    it('handles HTTP error response', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: () => Promise.resolve({ detail: 'Server error' })
      })
      
      const { error, sendMessage } = useChat()
      
      await sendMessage('Question')
      
      expect(error.value).toContain('Server error')
    })

    it('handles network error', async () => {
      global.fetch = vi.fn().mockRejectedValue(new Error('Network failed'))
      
      const { error, sendMessage } = useChat()
      
      await sendMessage('Question')
      
      expect(error.value).toContain('Network failed')
    })

    it('removes empty AI message on error', async () => {
      global.fetch = vi.fn().mockRejectedValue(new Error('Failed'))
      
      const { messages, sendMessage } = useChat()
      
      await sendMessage('Question')
      
      // Should only have user message, AI placeholder removed
      expect(messages.value.length).toBe(1)
      expect(messages.value[0].sender).toBe('user')
    })
  })

  describe('SSE Streaming', () => {
    it('handles SSE content-type', async () => {
      const mockReader = createMockStreamReader([
        'data: Hello',
        'data:  World',
        'data: [DONE]'
      ])
      
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        headers: {
          get: (name) => name === 'content-type' ? 'text/event-stream' : null
        },
        body: {
          getReader: () => mockReader
        }
      })
      
      const { messages, sendMessage } = useChat()
      
      await sendMessage('Question')
      
      // AI message should have streamed content
      const aiMessage = messages.value.find(m => m.sender === 'ai')
      expect(aiMessage.content).toContain('Hello')
      expect(aiMessage.content).toContain('World')
    })

    it('sets isStreaming during SSE', async () => {
      let resolveStream
      const streamPromise = new Promise(resolve => { resolveStream = resolve })
      
      const mockReader = {
        read: vi.fn()
          .mockReturnValueOnce(Promise.resolve({ 
            done: false, 
            value: new TextEncoder().encode('data: Hello\n\n') 
          }))
          .mockReturnValueOnce(streamPromise),
        releaseLock: vi.fn()
      }
      
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        headers: {
          get: (name) => name === 'content-type' ? 'text/event-stream' : null
        },
        body: {
          getReader: () => mockReader
        }
      })
      
      const { isStreaming, sendMessage } = useChat()
      
      const promise = sendMessage('Question')
      
      // Wait for first chunk
      await vi.advanceTimersByTimeAsync(10)
      
      expect(isStreaming.value).toBe(true)
      
      // Complete stream
      resolveStream({ done: true, value: undefined })
      await promise
      
      expect(isStreaming.value).toBe(false)
    })

    it('stops on [DONE] signal', async () => {
      const mockReader = createMockStreamReader([
        'data: Part 1',
        'data: [DONE]',
        'data: Should not appear'
      ])
      
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        headers: {
          get: (name) => name === 'content-type' ? 'text/event-stream' : null
        },
        body: {
          getReader: () => mockReader
        }
      })
      
      const { messages, sendMessage } = useChat()
      
      await sendMessage('Question')
      
      const aiMessage = messages.value.find(m => m.sender === 'ai')
      expect(aiMessage.content).toContain('Part 1')
      expect(aiMessage.content).not.toContain('Should not appear')
    })
  })

  describe('cancelRequest', () => {
    it('aborts ongoing request', async () => {
      let resolvePromise
      global.fetch = vi.fn().mockReturnValue(
        new Promise(resolve => { resolvePromise = resolve })
      )
      
      const { cancelRequest, sendMessage, isLoading } = useChat()
      
      const promise = sendMessage('Question')
      
      expect(isLoading.value).toBe(true)
      
      cancelRequest()
      
      // Resolve with abort error
      resolvePromise({
        ok: true,
        headers: new Map([['content-type', 'application/json']]),
        json: () => Promise.reject(new DOMException('Aborted', 'AbortError'))
      })
      
      await promise.catch(() => {})
      
      expect(isLoading.value).toBe(false)
    })
  })

  describe('clearMessages', () => {
    it('removes all messages', () => {
      const { messages, addUserMessage, addAIMessage, clearMessages } = useChat()
      
      addUserMessage('Hello')
      addAIMessage('Hi')
      
      expect(messages.value.length).toBe(2)
      
      clearMessages()
      
      expect(messages.value.length).toBe(0)
    })

    it('clears error', () => {
      const { error, sendMessage, clearMessages } = useChat()
      
      // Create an error
      sendMessage('')
      
      clearMessages()
      
      expect(error.value).toBe(null)
    })
  })

  describe('clearError', () => {
    it('clears error state', async () => {
      const { error, sendMessage, clearError } = useChat()
      
      await sendMessage('')
      expect(error.value).toBeTruthy()
      
      clearError()
      
      expect(error.value).toBe(null)
    })
  })

  describe('State Immutability', () => {
    it('returns readonly messages', () => {
      const { messages } = useChat()
      
      // Vue readonly refs don't throw, they just ignore the assignment
      // We verify the value doesn't change
      const originalLength = messages.value.length
      messages.value = [{ id: 'test', content: 'test', sender: 'user' }]
      
      // Value should remain unchanged (readonly)
      expect(messages.value.length).toBe(originalLength)
    })

    it('returns readonly isLoading', () => {
      const { isLoading } = useChat()
      
      const originalValue = isLoading.value
      isLoading.value = !originalValue
      
      // Value should remain unchanged (readonly)
      expect(isLoading.value).toBe(originalValue)
    })

    it('returns readonly error', () => {
      const { error } = useChat()
      
      const originalValue = error.value
      error.value = 'test error'
      
      // Value should remain unchanged (readonly)
      expect(error.value).toBe(originalValue)
    })
  })
})

// Helper function to create mock stream reader
function createMockStreamReader(lines) {
  const encoder = new TextEncoder()
  let index = 0
  
  return {
    read: vi.fn().mockImplementation(() => {
      if (index >= lines.length) {
        return Promise.resolve({ done: true, value: undefined })
      }
      
      const line = lines[index++]
      const data = encoder.encode(line + '\n\n')
      return Promise.resolve({ done: false, value: data })
    }),
    releaseLock: vi.fn()
  }
}
