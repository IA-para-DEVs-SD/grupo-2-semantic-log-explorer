/**
 * useChat composable — manages chat communication with the backend API.
 */

import { ref, readonly } from 'vue'

const generateId = () => `msg_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`

export function useChat(options = {}) {
  const { apiUrl = '/api/chat' } = options

  const messages = ref([])
  const isLoading = ref(false)
  const error = ref(null)
  const isStreaming = ref(false)

  let abortController = null

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

  const sendMessage = async (question, collection = null) => {
    if (!question?.trim()) {
      error.value = 'A pergunta não pode estar vazia'
      return
    }

    error.value = null
    addUserMessage(question)
    isLoading.value = true
    isStreaming.value = false
    abortController = new AbortController()

    try {
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: question.trim(), collection }),
        signal: abortController.signal
      })

      if (!response.ok) {
        let errorMessage = `Erro HTTP ${response.status}`
        try {
          const errorData = await response.json()
          errorMessage = errorData.detail || errorMessage
        } catch { /* keep default */ }
        throw new Error(errorMessage)
      }

      const data = await response.json()
      addAIMessage(data.response || '')
    } catch (err) {
      if (err.name !== 'AbortError') {
        console.error('Chat error:', err)
        error.value = err.message || 'Erro ao comunicar com o servidor'
      }
    } finally {
      isLoading.value = false
      isStreaming.value = false
      abortController = null
    }
  }

  const cancelRequest = () => {
    if (abortController) {
      abortController.abort()
      abortController = null
    }
  }

  const clearMessages = () => {
    messages.value = []
    error.value = null
  }

  const clearError = () => {
    error.value = null
  }

  return {
    messages: readonly(messages),
    isLoading: readonly(isLoading),
    isStreaming: readonly(isStreaming),
    error: readonly(error),
    sendMessage,
    cancelRequest,
    clearMessages,
    clearError,
    addUserMessage,
    addAIMessage
  }
}

export default useChat
