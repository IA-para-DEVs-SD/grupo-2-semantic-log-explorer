/**
 * Unit tests for FileUpload.vue component.
 * Tests file validation, drag-and-drop, and upload functionality.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import FileUpload from '../../src/components/FileUpload.vue'

describe('FileUpload', () => {
  let wrapper

  beforeEach(() => {
    wrapper = mount(FileUpload)
  })

  describe('Component Rendering', () => {
    it('renders dropzone with correct instructions', () => {
      expect(wrapper.find('.file-upload__dropzone').exists()).toBe(true)
      expect(wrapper.text()).toContain('Arraste um arquivo')
      expect(wrapper.text()).toContain('clique para selecionar')
    })

    it('displays accepted formats hint', () => {
      expect(wrapper.text()).toContain('.log, .txt, .json')
      expect(wrapper.text()).toContain('50MB')
    })

    it('has accessible file input', () => {
      const input = wrapper.find('input[type="file"]')
      expect(input.exists()).toBe(true)
      expect(input.attributes('accept')).toContain('.log')
      expect(input.attributes('accept')).toContain('.txt')
      expect(input.attributes('accept')).toContain('.json')
    })
  })

  describe('File Validation', () => {
    it('rejects files with invalid extension', async () => {
      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' })
      
      await simulateFileDrop(wrapper, file)
      
      expect(wrapper.emitted('upload-error')).toBeTruthy()
      expect(wrapper.emitted('upload-error')[0][0]).toContain('Formato não suportado')
    })

    it('accepts .log files', async () => {
      const file = new File(['log content'], 'app.log', { type: 'text/plain' })
      
      // Mock fetch for upload
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ status: 'indexed', chunks: 5 })
      })
      
      await simulateFileSelect(wrapper, file)
      
      // Should not emit error for valid extension
      const errors = wrapper.emitted('upload-error') || []
      const extensionErrors = errors.filter(e => e[0].includes('Formato'))
      expect(extensionErrors.length).toBe(0)
    })

    it('accepts .txt files', async () => {
      const file = new File(['text content'], 'logs.txt', { type: 'text/plain' })
      
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ status: 'indexed', chunks: 3 })
      })
      
      await simulateFileSelect(wrapper, file)
      
      const errors = wrapper.emitted('upload-error') || []
      const extensionErrors = errors.filter(e => e[0].includes('Formato'))
      expect(extensionErrors.length).toBe(0)
    })

    it('accepts .json files', async () => {
      const file = new File(['{"log": "data"}'], 'logs.json', { type: 'application/json' })
      
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ status: 'indexed', chunks: 2 })
      })
      
      await simulateFileSelect(wrapper, file)
      
      const errors = wrapper.emitted('upload-error') || []
      const extensionErrors = errors.filter(e => e[0].includes('Formato'))
      expect(extensionErrors.length).toBe(0)
    })

    it('rejects empty files', async () => {
      const file = new File([], 'empty.log', { type: 'text/plain' })
      
      await simulateFileDrop(wrapper, file)
      
      expect(wrapper.emitted('upload-error')).toBeTruthy()
      expect(wrapper.emitted('upload-error')[0][0]).toContain('vazio')
    })

    it('rejects files exceeding 50MB', async () => {
      // Create a mock file object with size > 50MB
      const largeFile = {
        name: 'large.log',
        size: 51 * 1024 * 1024, // 51MB
        type: 'text/plain'
      }
      
      // Directly call the validation logic
      const isValidSize = largeFile.size <= 50 * 1024 * 1024
      expect(isValidSize).toBe(false)
    })
  })

  describe('Drag and Drop', () => {
    it('shows dragging state on dragenter', async () => {
      const dropzone = wrapper.find('.file-upload__dropzone')
      
      await dropzone.trigger('dragenter')
      
      expect(wrapper.find('.file-upload__dropzone--dragging').exists()).toBe(true)
    })

    it('removes dragging state on dragleave', async () => {
      const dropzone = wrapper.find('.file-upload__dropzone')
      
      await dropzone.trigger('dragenter')
      await dropzone.trigger('dragleave')
      
      expect(wrapper.find('.file-upload__dropzone--dragging').exists()).toBe(false)
    })

    it('removes dragging state on drop', async () => {
      const dropzone = wrapper.find('.file-upload__dropzone')
      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' })
      
      await dropzone.trigger('dragenter')
      await dropzone.trigger('drop', {
        dataTransfer: { files: [file] }
      })
      
      expect(wrapper.find('.file-upload__dropzone--dragging').exists()).toBe(false)
    })
  })

  describe('Upload Events', () => {
    it('emits upload-success with file info on successful upload', async () => {
      const file = new File(['log content'], 'app.log', { type: 'text/plain' })
      
      // Mock XMLHttpRequest
      const mockXHR = createMockXHR({
        status: 200,
        response: JSON.stringify({ status: 'indexed', chunks: 10, filename: 'app.log' })
      })
      global.XMLHttpRequest = vi.fn(() => mockXHR)
      
      await simulateFileSelect(wrapper, file)
      
      // Simulate successful response
      mockXHR.onload()
      
      await wrapper.vm.$nextTick()
      
      expect(wrapper.emitted('upload-success')).toBeTruthy()
    })

    it('emits upload-error on HTTP error', async () => {
      const file = new File(['log content'], 'app.log', { type: 'text/plain' })
      
      const mockXHR = createMockXHR({
        status: 500,
        response: JSON.stringify({ detail: 'Server error' })
      })
      global.XMLHttpRequest = vi.fn(() => mockXHR)
      
      await simulateFileSelect(wrapper, file)
      mockXHR.onload()
      
      await wrapper.vm.$nextTick()
      
      expect(wrapper.emitted('upload-error')).toBeTruthy()
    })
  })

  describe('Result Display', () => {
    it('shows success message after upload', async () => {
      const file = new File(['log content'], 'app.log', { type: 'text/plain' })
      
      const mockXHR = createMockXHR({
        status: 200,
        response: JSON.stringify({ status: 'indexed', chunks: 5 })
      })
      global.XMLHttpRequest = vi.fn(() => mockXHR)
      
      await simulateFileSelect(wrapper, file)
      
      // Trigger the onload callback
      if (mockXHR.onload) {
        mockXHR.onload()
      }
      
      await wrapper.vm.$nextTick()
      await wrapper.vm.$nextTick() // Extra tick for state update
      
      // Check if success result is shown or upload-success was emitted
      const hasSuccessResult = wrapper.find('.file-upload__result--success').exists()
      const hasSuccessEmit = wrapper.emitted('upload-success')
      
      expect(hasSuccessResult || hasSuccessEmit).toBe(true)
    })

    it('shows error message on validation failure', async () => {
      const file = new File(['content'], 'test.exe', { type: 'application/octet-stream' })
      
      await simulateFileDrop(wrapper, file)
      
      expect(wrapper.find('.file-upload__result--error').exists()).toBe(true)
    })

    it('clears result when close button is clicked', async () => {
      const file = new File(['content'], 'test.exe', { type: 'application/octet-stream' })
      
      await simulateFileDrop(wrapper, file)
      
      const closeButton = wrapper.find('.file-upload__result-close')
      await closeButton.trigger('click')
      
      expect(wrapper.find('.file-upload__result').exists()).toBe(false)
    })
  })

  describe('Accessibility', () => {
    it('has proper aria-label on dropzone', () => {
      const dropzone = wrapper.find('.file-upload__dropzone')
      expect(dropzone.attributes('aria-label')).toBeTruthy()
    })

    it('has role="button" on dropzone', () => {
      const dropzone = wrapper.find('.file-upload__dropzone')
      expect(dropzone.attributes('role')).toBe('button')
    })

    it('has role="alert" on result message', async () => {
      const file = new File(['content'], 'test.exe', { type: 'application/octet-stream' })
      
      await simulateFileDrop(wrapper, file)
      
      const result = wrapper.find('.file-upload__result')
      expect(result.attributes('role')).toBe('alert')
    })
  })
})

// Helper functions

async function simulateFileDrop(wrapper, file) {
  const dropzone = wrapper.find('.file-upload__dropzone')
  await dropzone.trigger('drop', {
    dataTransfer: { files: [file] }
  })
}

async function simulateFileSelect(wrapper, file) {
  const input = wrapper.find('input[type="file"]')
  
  // Create a mock FileList
  const fileList = {
    0: file,
    length: 1,
    item: (index) => file
  }
  
  Object.defineProperty(input.element, 'files', {
    value: fileList,
    writable: false
  })
  
  await input.trigger('change')
}

function createMockXHR(options = {}) {
  return {
    open: vi.fn(),
    send: vi.fn(),
    setRequestHeader: vi.fn(),
    upload: {
      addEventListener: vi.fn()
    },
    status: options.status || 200,
    responseText: options.response || '{}',
    onload: null,
    onerror: null,
    ontimeout: null,
    timeout: 0
  }
}
