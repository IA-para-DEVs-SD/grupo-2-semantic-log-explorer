<script setup>
/**
 * Main application component.
 * Provides the layout structure for the Semantic Log Explorer.
 */

import { ref } from 'vue'

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
        <div class="upload-placeholder">
          <!-- FileUpload component will be added here -->
          <p class="placeholder-text">Upload de arquivos (.log, .txt, .json)</p>
          <p v-if="uploadedFile" class="upload-info">
            Arquivo: {{ uploadedFile.filename }} | Chunks: {{ uploadedFile.chunks }}
          </p>
        </div>
      </section>

      <section class="chat-section">
        <div class="chat-placeholder">
          <!-- ChatWindow component will be added here -->
          <p class="placeholder-text">Interface de chat</p>
        </div>
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

.upload-placeholder,
.chat-placeholder {
  border: 2px dashed var(--border);
  border-radius: var(--radius);
  padding: 2rem;
  text-align: center;
  background: var(--muted);
}

.chat-placeholder {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.placeholder-text {
  color: var(--muted-foreground);
  margin: 0;
}

.upload-info {
  margin-top: 0.5rem;
  font-size: 0.875rem;
  color: var(--foreground);
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
