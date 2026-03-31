<script setup>
/**
 * Main application component.
 * Provides the layout structure for the Semantic Log Explorer.
 */

import { ref } from 'vue'
import FileUpload from './components/FileUpload.vue'
import ChatWindow from './components/ChatWindow.vue'

// State for uploaded file info
const uploadedFile = ref(null)

/**
 * Handle successful file upload.
 * @param {Object} fileInfo - Object with filename and chunks count
 */
const handleUploadSuccess = (fileInfo) => {
  uploadedFile.value = fileInfo
}

/**
 * Handle upload error.
 * @param {string} error - Error message
 */
const handleUploadError = (error) => {
  console.error('Upload error:', error)
}
</script>

<template>
  <div class="app-container">
    <header class="app-header">
      <h1 class="app-title">Semantic Log Explorer</h1>
      <p class="app-subtitle">Análise inteligente de logs com IA</p>
    </header>

    <main class="app-main">
      <section class="upload-section">
        <FileUpload
          @upload-success="handleUploadSuccess"
          @upload-error="handleUploadError"
        />
      </section>

      <section class="chat-section">
        <ChatWindow />
      </section>
    </main>

    <footer class="app-footer">
      <p>Semantic Log Explorer — Observabilidade com IA Generativa</p>
    </footer>
  </div>
</template>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.app-header {
  padding: 1.5rem 2rem;
  border-bottom: 1px solid var(--border);
  background: var(--background);
}

.app-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--foreground);
  margin: 0;
}

.app-subtitle {
  font-size: 0.875rem;
  color: var(--muted-foreground);
  margin: 0.25rem 0 0 0;
}

.app-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 1.5rem 2rem;
  gap: 1.5rem;
}

.upload-section {
  flex-shrink: 0;
}

.chat-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 400px;
}



.app-footer {
  padding: 1rem 2rem;
  border-top: 1px solid var(--border);
  text-align: center;
  font-size: 0.75rem;
  color: var(--muted-foreground);
}

.app-footer p {
  margin: 0;
}
</style>
