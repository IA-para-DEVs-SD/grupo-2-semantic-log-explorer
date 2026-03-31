/**
 * Unit tests for FileUpload component.
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import FileUpload from '../FileUpload.vue'

describe('FileUpload', () => {
  it('renders the dropzone', () => {
    const wrapper = mount(FileUpload)
    expect(wrapper.find('.file-upload__dropzone').exists()).toBe(true)
  })

  it('shows upload instructions', () => {
    const wrapper = mount(FileUpload)
    expect(wrapper.text()).toContain('Arraste um arquivo')
    expect(wrapper.text()).toContain('clique para selecionar')
  })

  it('shows accepted formats hint', () => {
    const wrapper = mount(FileUpload)
    expect(wrapper.text()).toContain('.log, .txt, .json')
  })

  it('has accessible dropzone with role button', () => {
    const wrapper = mount(FileUpload)
    const dropzone = wrapper.find('.file-upload__dropzone')
    expect(dropzone.attributes('role')).toBe('button')
    expect(dropzone.attributes('tabindex')).toBe('0')
  })

  it('has a hidden file input', () => {
    const wrapper = mount(FileUpload)
    const input = wrapper.find('input[type="file"]')
    expect(input.exists()).toBe(true)
    expect(input.attributes('aria-hidden')).toBe('true')
  })

  it('accepts correct file extensions', () => {
    const wrapper = mount(FileUpload)
    const input = wrapper.find('input[type="file"]')
    expect(input.attributes('accept')).toContain('.log')
    expect(input.attributes('accept')).toContain('.txt')
    expect(input.attributes('accept')).toContain('.json')
  })

  it('does not show result message initially', () => {
    const wrapper = mount(FileUpload)
    expect(wrapper.find('.file-upload__result').exists()).toBe(false)
  })

  it('does not show progress bar initially', () => {
    const wrapper = mount(FileUpload)
    expect(wrapper.find('.file-upload__progress').exists()).toBe(false)
  })
})
