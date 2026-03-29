/**
 * useChat composable — manages chat communication with the backend API.
 * Handles SSE streaming, message state, loading, and error management.
 */

import { ref, readonly } from 'vue'

/**
 * Message object structure.
 * @typedef {Object} Message
 * @property {string} id - Unique message identifier
 * @property {'user' | 'ai'} sender - Message sender type
 * @property {string} content - Message content
 * @property {Date} timestamp - Message timestamp
 */

/**
 * Generate a unique ID for messages.
 * @returns {string} Unique identifier
 */
const generateId = () => `msg_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`

/**
 * Composable for chat functionality with SSE streaming support.
 * @param {Object} options - Configuration options
 * @param {string} [options.apiUrl='/api/chat'] - Chat API endpoint
 * @returns {Object} Chat state and methods
 */
export function useChat(options = {}) {
  const { apiUrl = '/api/chat' } = options

  // Reactive state
  const messages = ref([])
  const isLoading = ref(false)
  const error = ref(null)
  const isStreaming = ref(false)

  // AbortController for cancelling requests
  let abortController = null

  /**
   * Add a user message to the chat.
   * @param {string} content - Message content
   * @returns {Message} The created message
   */
  const addUserMessage = (content) => {
    const message = {
      id: generateId(),
      sender: 'user',
      content: content.trim(),
      timestamp: new Date()
    }
    messages.value.push(message)
    return message
  }

  /**
   * Add an AI message to the chat.
   * @param {string} [content=''] - Initial message content
   * @returns {Message} The created message
   */
  const addAIMessage = (content = '') => {
    const message = {
      id: generateId(),
      sender: 'ai',
      content,
      timestamp: new Date()
    }
    messages.value.push(message)
    return message
  }

  /**
   * Update the content of the last AI message (for streaming).
   * @param {string} content - Content to append
   */
  const appendToLastAIMessage = (content) => {
    const lastMessage = messages.value[messages.value.length - 1]
    if (lastMessage && lastMessage.sender === 'ai') {
      lastMessage.content += content
    }
  }

  /**
   * Parse SSE data from a line.
   * @param {string} line - Raw SSE line
   * @returns {string|null} Parsed data or null
   */
  const parseSSELine = (line) => {
    if (line.startsWith('data: ')) {
      return line.slice(6)
    }
    return null
  }

  /**
   * Send a question to the chat API and stream the response.
   * @param {string} question - User's question
   * @returns {Promise<void>}
   */
  const sendMessage = async (question) => {
    if (!question?.trim()) {
      error.value = 'A pergunta não pode estar vazia'
      return
    }

    // Reset error state
    error.value = null

    // Add user message
    addUserMessage(question)

    // Create AI message placeholder for streaming
    addAIMessage('')

    // Set loading states
    isLoading.value = true
    isStreaming.value = true

    // Create abort controller for this request
    abortController = new AbortController()

    try {
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream'
        },
        body: JSON.stringify({ question: question.trim() }),
        signal: abortController.signal
      })

      if (!response.ok) {
        let errorMessage = `Erro HTTP ${response.status}`
        try {
          const errorData = await response.json()
          errorMessage = errorData.detail || errorMessage
        } catch {
          // Keep default error message
        }
        throw new Error(errorMessage)
      }

      // Check if response is SSE
      const contentType = response.headers.get('content-type') || ''
      
      if (contentType.includes('text/event-stream')) {
        // Handle SSE streaming
        await handleSSEStream(response)
      } else {
        // Handle regular JSON response (fallback)
        const data = await response.json()
        appendToLastAIMessage(data.response || data.content || '')
      }

    } catch (err) {
      if (err.name === 'AbortError') {
        // Request was cancelled, not an error
        console.log('Request cancelled')
      } else {
        console.error('Chat error:', err)
        error.value = err.message || 'Erro ao comunicar com o servidor'
        
        // Remove empty AI message on error
        const lastMessage = messages.value[messages.value.length - 1]
        if (lastMessage?.sender === 'ai' && !lastMessage.content) {
          messages.value.pop()
        }
      }
    } finally {
      isLoading.value = false
      isStreaming.value = false
      abortController = null
    }
  }

  /**
   * Handle SSE stream from response.
   * @param {Response} response - Fetch response object
   */
  const handleSSEStream = async (response) => {
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    try {
      while (true) {
        const { done, value } = await reader.read()
        
        if (done) break

        // Decode chunk and add to buffer
        buffer += decoder.decode(value, { stream: true })

        // Process complete lines
        const lines = buffer.split('\n')
        
        // Keep incomplete line in buffer
        buffer = lines.pop() || ''

        for (const line of lines) {
          const trimmedLine = line.trim()
          
          if (!trimmedLine) continue

          const data = parseSSELine(trimmedLine)
          
          if (data !== null) {
            // Check for end signal
            if (data === '[DONE]') {
              return
            }
            
            // Append token to AI message
            appendToLastAIMessage(data)
          }
        }
      }

      // Process any remaining data in buffer
      if (buffer.trim()) {
        const data = parseSSELine(buffer.trim())
        if (data !== null && data !== '[DONE]') {
          appendToLastAIMessage(data)
        }
      }

    } finally {
      reader.releaseLock()
    }
  }

  /**
   * Cancel the current streaming request.
   */
  const cancelRequest = () => {
    if (abortController) {
      abortController.abort()
      abortController = null
    }
  }

  /**
   * Clear all messages from the chat.
   */
  const clearMessages = () => {
    messages.value = []
    error.value = null
  }

  /**
   * Clear the current error.
   */
  const clearError = () => {
    error.value = null
  }

  return {
    // State (readonly to prevent external mutations)
    messages: readonly(messages),
    isLoading: readonly(isLoading),
    isStreaming: readonly(isStreaming),
    error: readonly(error),
    
    // Methods
    sendMessage,
    cancelRequest,
    clearMessages,
    clearError,
    
    // For testing/advanced usage
    addUserMessage,
    addAIMessage
  }
}

export default useChat
