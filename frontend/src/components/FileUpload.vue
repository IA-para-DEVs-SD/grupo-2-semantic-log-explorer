<script setup>
/**
 * FileUpload component — drag-and-drop file upload with validation.
 * Accepts .log, .txt, .json files up to 50MB.
 * Emits upload-success and upload-error events.
 */

import { ref, computed } from 'vue'

const emit = defineEmits(['upload-success', 'upload-error'])

// State
const isDragging = ref(false)
const isUploading = ref(false)
const uploadProgress = ref(0)
const uploadResult = ref(null) // { type: 'success' | 'error', message: string, filename?: string, chunks?: number }

// Constants
const ALLOWED_EXTENSIONS = ['.log', '.txt', '.json']
const MAX_FILE_SIZE = 50 * 1024 * 1024 // 50MB

/**
 * Validate file extension.
 * @param {string} filename - Name of the file
 * @returns {boolean} True if extension is valid
 */
const isValidExtension = (filename) => {
  const ext = filename.toLowerCase().slice(filename.lastIndexOf('.'))
  return ALLOWED_EXTENSIONS.includes(ext)
}

/**
 * Validate file size.
 * @param {number} size - File size in bytes
 * @returns {boolean} True if size is within limit
 */
const isValidSize = (size) => {
  return size <= MAX_FILE_SIZE && size > 0
}

/**
 * Format file size for display.
 * @param {number} bytes - Size in bytes
 * @returns {string} Formatted size string
 */
const formatFileSize = (bytes) => {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

/**
 * Handle drag enter event.
 * @param {DragEvent} event
 */
const handleDragEnter = (event) => {
  event.preventDefault()
  isDragging.value = true
}

/**
 * Handle drag leave event.
 * @param {DragEvent} event
 */
const handleDragLeave = (event) => {
  event.preventDefault()
  isDragging.value = false
}

/**
 * Handle drag over event.
 * @param {DragEvent} event
 */
const handleDragOver = (event) => {
  event.preventDefault()
}

/**
 * Handle drop event.
 * @param {DragEvent} event
 */
const handleDrop = (event) => {
  event.preventDefault()
  isDragging.value = false
  
  const files = event.dataTransfer?.files
  if (files && files.length > 0) {
    processFile(files[0])
  }
}

/**
 * Handle file input change.
 * @param {Event} event
 */
const handleFileSelect = (event) => {
  const files = event.target.files
  if (files && files.length > 0) {
    processFile(files[0])
  }
  // Reset input to allow selecting the same file again
  event.target.value = ''
}

/**
 * Process and upload a file.
 * @param {File} file - The file to upload
 */
const processFile = async (file) => {
  // Reset previous result
  uploadResult.value = null
  
  // Validate extension
  if (!isValidExtension(file.name)) {
    const error = `Formato não suportado. Use ${ALLOWED_EXTENSIONS.join(', ')}`
    uploadResult.value = { type: 'error', message: error }
    emit('upload-error', error)
    return
  }
  
  // Validate size
  if (!isValidSize(file.size)) {
    let error
    if (file.size === 0) {
      error = 'Arquivo vazio'
    } else {
      error = `Arquivo excede o limite de 50MB (${formatFileSize(file.size)})`
    }
    uploadResult.value = { type: 'error', message: error }
    emit('upload-error', error)
    return
  }
  
  // Upload file
  await uploadFile(file)
}

/**
 * Upload file to the backend.
 * @param {File} file - The file to upload
 */
const uploadFile = async (file) => {
  isUploading.value = true
  uploadProgress.value = 0
  
  const formData = new FormData()
  formData.append('file', file)
  
  try {
    const xhr = new XMLHttpRequest()
    
    // Track upload progress
    xhr.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable) {
        uploadProgress.value = Math.round((event.loaded / event.total) * 100)
      }
    })
    
    // Handle response
    const response = await new Promise((resolve, reject) => {
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            resolve(JSON.parse(xhr.responseText))
          } catch (parseError) {
            console.warn('Failed to parse response, using defaults:', parseError)
            resolve({ status: 'indexed', chunks: 0 })
          }
        } else {
          try {
            const errorData = JSON.parse(xhr.responseText)
            reject(new Error(errorData.detail || `Erro HTTP ${xhr.status}`))
          } catch {
            reject(new Error(`Erro HTTP ${xhr.status}`))
          }
        }
      }
      xhr.onerror = () => reject(new Error('Erro de conexão'))
      xhr.ontimeout = () => reject(new Error('Timeout na requisição'))
      
      xhr.open('POST', '/api/upload')
      xhr.timeout = 300000 // 5 minutes timeout
      xhr.send(formData)
    })
    
    // Success
    uploadProgress.value = 100
    const result = {
      type: 'success',
      message: 'Upload concluído com sucesso',
      filename: file.name,
      chunks: response.chunks || 0
    }
    uploadResult.value = result
    emit('upload-success', { filename: file.name, chunks: response.chunks || 0 })
    
  } catch (error) {
    uploadResult.value = { type: 'error', message: error.message }
    emit('upload-error', error.message)
  } finally {
    isUploading.value = false
  }
}

/**
 * Clear the current result.
 */
const clearResult = () => {
  uploadResult.value = null
  uploadProgress.value = 0
}

// Computed
const dropzoneClasses = computed(() => ({
  'file-upload__dropzone': true,
  'file-upload__dropzone--dragging': isDragging.value,
  'file-upload__dropzone--uploading': isUploading.value
}))
</script>

<template>
  <div class="file-upload">
    <div
      :class="dropzoneClasses"
      @dragenter="handleDragEnter"
      @dragleave="handleDragLeave"
      @dragover="handleDragOver"
      @drop="handleDrop"
      role="button"
      tabindex="0"
      :aria-label="isUploading ? 'Enviando arquivo...' : 'Área de upload. Arraste um arquivo ou clique para selecionar'"
      @keydown.enter="$refs.fileInput.click()"
      @keydown.space.prevent="$refs.fileInput.click()"
    >
      <input
        ref="fileInput"
        type="file"
        class="file-upload__input"
        :accept="ALLOWED_EXTENSIONS.join(',')"
        @change="handleFileSelect"
        :disabled="isUploading"
        aria-hidden="true"
      />
      
      <!-- Upload icon -->
      <div class="file-upload__icon" aria-hidden="true">
        <svg
          v-if="!isUploading"
          xmlns="http://www.w3.org/2000/svg"
          width="48"
          height="48"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="17 8 12 3 7 8" />
          <line x1="12" y1="3" x2="12" y2="15" />
        </svg>
        <svg
          v-else
          class="animate-spin"
          xmlns="http://www.w3.org/2000/svg"
          width="48"
          height="48"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path d="M21 12a9 9 0 1 1-6.219-8.56" />
        </svg>
      </div>
      
      <!-- Instructions -->
      <div class="file-upload__text">
        <p v-if="!isUploading" class="file-upload__title">
          Arraste um arquivo ou <span class="file-upload__link">clique para selecionar</span>
        </p>
        <p v-else class="file-upload__title">
          Enviando arquivo...
        </p>
        <p class="file-upload__hint">
          Formatos aceitos: .log, .txt, .json (máx. 50MB)
        </p>
      </div>
      
      <!-- Progress bar -->
      <div v-if="isUploading" class="file-upload__progress" role="progressbar" :aria-valuenow="uploadProgress" aria-valuemin="0" aria-valuemax="100">
        <div class="file-upload__progress-bar" :style="{ width: `${uploadProgress}%` }"></div>
        <span class="file-upload__progress-text">{{ uploadProgress }}%</span>
      </div>
    </div>
    
    <!-- Result message -->
    <div v-if="uploadResult" :class="['file-upload__result', `file-upload__result--${uploadResult.type}`]" role="alert">
      <div class="file-upload__result-content">
        <!-- Success icon -->
        <svg
          v-if="uploadResult.type === 'success'"
          class="file-upload__result-icon"
          xmlns="http://www.w3.org/2000/svg"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
          <polyline points="22 4 12 14.01 9 11.01" />
        </svg>
        <!-- Error icon -->
        <svg
          v-else
          class="file-upload__result-icon"
          xmlns="http://www.w3.org/2000/svg"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
        
        <div class="file-upload__result-text">
          <p class="file-upload__result-message">{{ uploadResult.message }}</p>
          <p v-if="uploadResult.type === 'success'" class="file-upload__result-details">
            {{ uploadResult.filename }} — {{ uploadResult.chunks }} chunks indexados
          </p>
        </div>
      </div>
      
      <button
        type="button"
        class="file-upload__result-close"
        @click="clearResult"
        aria-label="Fechar mensagem"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>
    </div>
  </div>
</template>

<style scoped>
.file-upload {
  width: 100%;
}

.file-upload__dropzone {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 2rem;
  border: 2px dashed #cbd5e1;
  border-radius: var(--radius);
  background-color: var(--background);
  cursor: pointer;
  transition: all 200ms ease;
  min-height: 160px;
}

.file-upload__dropzone:hover,
.file-upload__dropzone:focus {
  border-color: var(--primary);
  background-color: var(--accent);
  outline: none;
}

.file-upload__dropzone--dragging {
  border-color: var(--primary);
  background-color: var(--accent);
  border-style: solid;
}

.file-upload__dropzone--uploading {
  cursor: default;
  pointer-events: none;
}

.file-upload__input {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
}

.file-upload__input:disabled {
  cursor: default;
}

.file-upload__icon {
  color: #94a3b8;
}

.file-upload__dropzone:hover .file-upload__icon,
.file-upload__dropzone--dragging .file-upload__icon {
  color: var(--primary);
}

.file-upload__text {
  text-align: center;
}

.file-upload__title {
  font-size: 0.9375rem;
  color: var(--foreground);
  margin: 0;
}

.file-upload__link {
  color: var(--primary);
  font-weight: 500;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.file-upload__hint {
  font-size: 0.8125rem;
  color: var(--muted-foreground);
  margin: 0.25rem 0 0 0;
}

.file-upload__progress {
  width: 100%;
  max-width: 300px;
  height: 6px;
  background-color: #e2e8f0;
  border-radius: 3px;
  overflow: hidden;
  position: relative;
}

.file-upload__progress-bar {
  height: 100%;
  background-color: var(--primary);
  transition: width 150ms ease;
  border-radius: 3px;
}

.file-upload__progress-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 0.625rem;
  font-weight: 600;
  color: var(--foreground);
}

.file-upload__result {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
  margin-top: 0.75rem;
  padding: 0.75rem 1rem;
  border-radius: var(--radius);
  font-size: 0.875rem;
}

.file-upload__result--success {
  background-color: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #15803d;
}

.file-upload__result--error {
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
}

.file-upload__result-content {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
}

.file-upload__result-icon {
  flex-shrink: 0;
  margin-top: 0.125rem;
}

.file-upload__result-text {
  flex: 1;
}

.file-upload__result-message {
  margin: 0;
  font-weight: 500;
}

.file-upload__result-details {
  margin: 0.25rem 0 0 0;
  opacity: 0.85;
  font-size: 0.8125rem;
}

.file-upload__result-close {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  padding: 0;
  border: none;
  background: transparent;
  color: inherit;
  cursor: pointer;
  border-radius: 4px;
  opacity: 0.6;
  transition: opacity 150ms ease;
}

.file-upload__result-close:hover {
  opacity: 1;
}
</style>
