<script setup>
/**
 * MessageBubble component — renders chat messages with Markdown support.
 * During streaming: shows plain text with line breaks.
 * After streaming: renders full markdown via markdown-it.
 */

import { computed } from 'vue'
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt({
  html: false,
  breaks: true,
  linkify: true,
  typographer: false,
})

const props = defineProps({
  content: {
    type: String,
    required: true
  },
  sender: {
    type: String,
    required: true,
    validator: (value) => ['user', 'ai'].includes(value)
  },
  streaming: {
    type: Boolean,
    default: false
  },
  timestamp: {
    type: [Date, String],
    default: null
  }
})

/**
 * Escape HTML special characters to prevent XSS.
 */
function escapeHtml(text) {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

/**
 * Render content based on sender and streaming state.
 * - User messages: always escaped plain text
 * - AI streaming: escaped plain text with line breaks
 * - AI done: full markdown render
 */
const renderedContent = computed(() => {
  if (props.sender === 'user') {
    return escapeHtml(props.content).replace(/\n/g, '<br>')
  }
  if (props.streaming) {
    return escapeHtml(props.content).replace(/\n/g, '<br>')
  }
  return md.render(props.content)
})

const formattedTime = computed(() => {
  if (!props.timestamp) return null
  const date = props.timestamp instanceof Date 
    ? props.timestamp 
    : new Date(props.timestamp)
  return date.toLocaleTimeString('pt-BR', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
})

const bubbleClasses = computed(() => ({
  'message-bubble': true,
  'message-bubble--user': props.sender === 'user',
  'message-bubble--ai': props.sender === 'ai'
}))

const ariaLabel = computed(() => {
  const senderLabel = props.sender === 'user' ? 'Você' : 'Assistente IA'
  return `Mensagem de ${senderLabel}`
})
</script>

<template>
  <article :class="bubbleClasses" :aria-label="ariaLabel">
    <!-- Sender indicator -->
    <div class="message-bubble__header">
      <span class="message-bubble__sender">
        <!-- User icon -->
        <svg
          v-if="sender === 'user'"
          class="message-bubble__icon"
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" />
          <circle cx="12" cy="7" r="4" />
        </svg>
        <!-- AI icon -->
        <svg
          v-else
          class="message-bubble__icon"
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <path d="M12 8V4H8" />
          <rect width="16" height="12" x="4" y="8" rx="2" />
          <path d="M2 14h2" />
          <path d="M20 14h2" />
          <path d="M15 13v2" />
          <path d="M9 13v2" />
        </svg>
        {{ sender === 'user' ? 'Você' : 'Assistente IA' }}
      </span>
      <span v-if="formattedTime" class="message-bubble__time">
        {{ formattedTime }}
      </span>
    </div>

    <!-- Message content -->
    <div 
      class="message-bubble__content"
      :class="{ 'markdown-content': sender === 'ai' }"
      v-html="renderedContent"
    />
  </article>
</template>

<style scoped>
.message-bubble {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  padding: 0.875rem 1rem;
  border-radius: var(--radius);
  max-width: 85%;
}

.message-bubble--user {
  align-self: flex-end;
  background-color: var(--primary);
  color: var(--primary-foreground);
}

.message-bubble--ai {
  align-self: flex-start;
  background-color: var(--secondary);
  color: var(--foreground);
  border: 1px solid var(--border);
  width: 85%;
  max-width: 85%;
}

.message-bubble__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  font-size: 0.75rem;
}

.message-bubble__sender {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-weight: 600;
}

.message-bubble__icon {
  flex-shrink: 0;
}

.message-bubble__time {
  opacity: 0.6;
  font-size: 0.6875rem;
}

.message-bubble__content {
  font-size: 0.875rem;
  line-height: 1.6;
  word-break: break-word;
  overflow-wrap: break-word;
  min-width: 0;
}

/* AI message markdown styles */
.message-bubble--ai .message-bubble__content :deep(p) {
  margin: 0 0 0.625em 0;
}

.message-bubble--ai .message-bubble__content :deep(p:last-child) {
  margin-bottom: 0;
}

.message-bubble--ai .message-bubble__content :deep(ul),
.message-bubble--ai .message-bubble__content :deep(ol) {
  margin: 0 0 0.625em 0;
  padding-left: 1.25em;
}

.message-bubble--ai .message-bubble__content :deep(li) {
  margin-bottom: 0.2em;
}

.message-bubble--ai .message-bubble__content :deep(code) {
  font-family: var(--font-mono);
  font-size: 0.8125em;
  background-color: #fff;
  padding: 0.15em 0.4em;
  border-radius: 0.375rem;
  border: 1px solid var(--border);
  color: #be185d;
}

.message-bubble--ai .message-bubble__content :deep(pre) {
  margin: 0.625em 0;
  padding: 0.75rem 1rem;
  background-color: #1e293b;
  color: #e2e8f0;
  border-radius: 0.5rem;
  overflow-x: auto;
  border: none;
  max-width: 100%;
  white-space: pre;
  word-break: normal;
  overflow-wrap: normal;
}

.message-bubble--ai .message-bubble__content :deep(pre code) {
  background: none;
  padding: 0;
  font-size: 0.75rem;
  line-height: 1.5;
  border: none;
  color: inherit;
  white-space: pre;
}

.message-bubble--ai .message-bubble__content :deep(blockquote) {
  margin: 0.625em 0;
  padding-left: 0.75rem;
  border-left: 3px solid var(--primary);
  color: var(--muted-foreground);
}

.message-bubble--ai .message-bubble__content :deep(h1),
.message-bubble--ai .message-bubble__content :deep(h2),
.message-bubble--ai .message-bubble__content :deep(h3),
.message-bubble--ai .message-bubble__content :deep(h4) {
  margin: 0.875em 0 0.375em 0;
  font-weight: 600;
}

.message-bubble--ai .message-bubble__content :deep(h1) {
  font-size: 1.05rem;
}

.message-bubble--ai .message-bubble__content :deep(h2) {
  font-size: 1rem;
}

.message-bubble--ai .message-bubble__content :deep(h3) {
  font-size: 0.9375rem;
}

.message-bubble--ai .message-bubble__content :deep(h4) {
  font-size: 0.9375rem;
}

.message-bubble--ai .message-bubble__content :deep(h1:first-child),
.message-bubble--ai .message-bubble__content :deep(h2:first-child),
.message-bubble--ai .message-bubble__content :deep(h3:first-child),
.message-bubble--ai .message-bubble__content :deep(h4:first-child) {
  margin-top: 0;
}

.message-bubble--ai .message-bubble__content :deep(a) {
  color: var(--primary);
  text-decoration: underline;
  text-underline-offset: 2px;
}

.message-bubble--ai .message-bubble__content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 0.625em 0;
  font-size: 0.8125rem;
}

.message-bubble--ai .message-bubble__content :deep(th),
.message-bubble--ai .message-bubble__content :deep(td) {
  border: 1px solid var(--border);
  padding: 0.375rem 0.5rem;
  text-align: left;
}

.message-bubble--ai .message-bubble__content :deep(th) {
  background-color: #fff;
  font-weight: 600;
}

.message-bubble--ai .message-bubble__content :deep(hr) {
  border: none;
  border-top: 1px solid var(--border);
  margin: 0.875em 0;
}

/* User message styles */
.message-bubble--user .message-bubble__content {
  white-space: pre-wrap;
}
</style>
