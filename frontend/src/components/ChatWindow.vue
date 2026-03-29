<script setup>
/**
 * ChatWindow component — chat interface with auto-scroll,
 * message input field, and loading state.
 */

import { ref, watch, nextTick } from 'vue'
import MessageBubble from './MessageBubble.vue'
import { useChat } from '../composables/useChat.js'

const { messages, isLoading, isStreaming, error, sendMessage, clearError } = useChat()

const inputText = ref('')
const messagesContainer = ref(null)

/**
 * Auto-scroll to bottom when messages change.
 */
watch(
  () => messages.value.length,
  async () => {
    await nextTick()
    scrollToBottom()
  }
)

/**
 * Auto-scroll during streaming (content updates on last message).
 */
watch(
  () => messages.value[messages.value.length - 1]?.content,
  async () => {
    if (isStreaming.value) {
      await nextTick()
      scrollToBottom()
    }
  }
)

/**
 * Scroll messages container to the bottom.
 */
const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

/**
 * Handle form submission.
 */
const handleSubmit = () => {
  const text = inputText.value.trim()
  if (!text || isLoading.value) return
  clearError()
  sendMessage(text)
  inputText.value = ''
}
</script>

<template>
  <div class="chat-window">
    <!-- Messages area -->
    <div
      ref="messagesContainer"
      class="chat-window__messages"
      role="log"
      aria-live="polite"
      aria-label="Histórico de mensagens"
    >
      <div v-if="messages.length === 0" class="chat-window__empty">
        <p>Envie uma pergunta sobre os logs carregados.</p>
      </div>

      <MessageBubble
        v-for="msg in messages"
        :key="msg.id"
        :content="msg.content"
        :sender="msg.sender"
        :timestamp="msg.timestamp"
      />

      <!-- Loading indicator -->
      <div v-if="isLoading && !isStreaming" class="chat-window__loading">
        <span class="loading-indicator" aria-label="Carregando resposta">
          <span class="loading-dot"></span>
          <span class="loading-dot"></span>
          <span class="loading-dot"></span>
        </span>
      </div>
    </div>

    <!-- Error banner -->
    <div v-if="error" class="chat-window__error" role="alert">
      <span>{{ error }}</span>
      <button type="button" class="chat-window__error-close" @click="clearError" aria-label="Fechar erro">✕</button>
    </div>

    <!-- Input form -->
    <form class="chat-window__input-form" @submit.prevent="handleSubmit">
      <input
        v-model="inputText"
        type="text"
        class="chat-window__input input"
        placeholder="Digite sua pergunta sobre os logs..."
        :disabled="isLoading"
        aria-label="Campo de mensagem"
      />
      <button
        type="submit"
        class="chat-window__send-btn btn btn-primary"
        :disabled="isLoading || !inputText.trim()"
        aria-label="Enviar mensagem"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <line x1="22" y1="2" x2="11" y2="13" />
          <polygon points="22 2 15 22 11 13 2 9 22 2" />
        </svg>
      </button>
    </form>
  </div>
</template>

<style scoped>
.chat-window {
  display: flex;
  flex-direction: column;
  height: 100%;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--card);
  overflow: hidden;
}

.chat-window__messages {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.chat-window__empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--muted-foreground);
  font-size: 0.875rem;
}

.chat-window__empty p {
  margin: 0;
}

.chat-window__loading {
  align-self: flex-start;
  padding: 0.75rem 1rem;
  background: var(--muted);
  border-radius: var(--radius);
}

.loading-indicator {
  display: flex;
  gap: 0.25rem;
  align-items: center;
}

.loading-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--muted-foreground);
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dot:nth-child(1) { animation-delay: -0.32s; }
.loading-dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.chat-window__error {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 1rem;
  background: hsl(0, 84.2%, 60.2%, 0.1);
  border-top: 1px solid var(--destructive);
  color: var(--destructive);
  font-size: 0.8125rem;
}

.chat-window__error-close {
  background: none;
  border: none;
  color: inherit;
  cursor: pointer;
  padding: 0.25rem;
  font-size: 0.875rem;
  opacity: 0.7;
}

.chat-window__error-close:hover {
  opacity: 1;
}

.chat-window__input-form {
  display: flex;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border-top: 1px solid var(--border);
  background: var(--background);
}

.chat-window__input {
  flex: 1;
}

.chat-window__send-btn {
  flex-shrink: 0;
  width: 2.5rem;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
