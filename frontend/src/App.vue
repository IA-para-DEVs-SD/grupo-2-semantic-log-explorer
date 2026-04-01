<script setup>
/**
 * Main application component.
 * Provides the layout structure for the Semantic Log Explorer.
 */

import { ref } from 'vue'
import FileUpload from './components/FileUpload.vue'
import ChatWindow from './components/ChatWindow.vue'
import LogSelector from './components/LogSelector.vue'

const selectedCollection = ref(null)
const logSelectorRef = ref(null)

const handleUploadSuccess = (fileInfo) => {
  // Refresh the log selector after upload
  logSelectorRef.value?.refresh()
}

const handleUploadError = (error) => {
  console.error('Upload error:', error)
}

const handleLogSelect = (collection) => {
  selectedCollection.value = collection
}
</script>

<template>
  <div class="app-container">
    <header class="app-header">
      <div class="app-header__inner">
        <div class="app-header__brand">
          <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="app-header__logo">
            <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
            <line x1="10" y1="9" x2="8" y2="9"/>
          </svg>
          <div>
            <h1 class="app-title">Semantic Log Explorer</h1>
            <p class="app-subtitle">Análise inteligente de logs com IA</p>
          </div>
        </div>
      </div>
    </header>

    <main class="app-main">
      <div class="app-main__inner">
        <section class="upload-section">
          <FileUpload
            @upload-success="handleUploadSuccess"
            @upload-error="handleUploadError"
          />
        </section>

        <section class="log-section">
          <LogSelector
            ref="logSelectorRef"
            @select="handleLogSelect"
            @deleted="() => {}"
          />
        </section>

        <section class="chat-section">
          <ChatWindow :collection="selectedCollection" />
        </section>
      </div>
    </main>
  </div>
</template>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: #f8fafc;
}

.app-header {
  background: var(--background);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 10;
}

.app-header__inner {
  max-width: 960px;
  margin: 0 auto;
  padding: 1rem 1.5rem;
}

.app-header__brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.app-header__logo {
  color: var(--primary);
  flex-shrink: 0;
}

.app-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--foreground);
  margin: 0;
  letter-spacing: -0.02em;
}

.app-subtitle {
  font-size: 0.8125rem;
  color: var(--muted-foreground);
  margin: 0;
}

.app-main {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.app-main__inner {
  max-width: 960px;
  width: 100%;
  margin: 0 auto;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  flex: 1;
}

.upload-section {
  flex-shrink: 0;
}

.log-section {
  flex-shrink: 0;
}

.chat-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 500px;
}
</style>
