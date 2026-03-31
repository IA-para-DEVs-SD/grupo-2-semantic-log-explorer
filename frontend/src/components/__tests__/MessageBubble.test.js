/**
 * Unit tests for MessageBubble component.
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import MessageBubble from '../MessageBubble.vue'

describe('MessageBubble', () => {
  const userProps = { content: 'Hello', sender: 'user', timestamp: new Date() }
  const aiProps = { content: 'Hi there', sender: 'ai', timestamp: new Date() }

  it('renders user message with correct class', () => {
    const wrapper = mount(MessageBubble, { props: userProps })
    expect(wrapper.find('.message-bubble--user').exists()).toBe(true)
  })

  it('renders AI message with correct class', () => {
    const wrapper = mount(MessageBubble, { props: aiProps })
    expect(wrapper.find('.message-bubble--ai').exists()).toBe(true)
  })

  it('displays user label for user messages', () => {
    const wrapper = mount(MessageBubble, { props: userProps })
    expect(wrapper.text()).toContain('Você')
  })

  it('displays AI label for AI messages', () => {
    const wrapper = mount(MessageBubble, { props: aiProps })
    expect(wrapper.text()).toContain('Assistente IA')
  })

  it('renders message content', () => {
    const wrapper = mount(MessageBubble, { props: userProps })
    expect(wrapper.text()).toContain('Hello')
  })

  it('renders markdown for AI messages', () => {
    const props = { content: '**bold**', sender: 'ai', timestamp: new Date() }
    const wrapper = mount(MessageBubble, { props })
    expect(wrapper.find('.markdown-content').exists()).toBe(true)
    expect(wrapper.html()).toContain('<strong>')
  })

  it('escapes HTML in user messages', () => {
    const props = { content: '<script>alert("xss")</script>', sender: 'user', timestamp: new Date() }
    const wrapper = mount(MessageBubble, { props })
    expect(wrapper.html()).not.toContain('<script>')
  })

  it('shows formatted timestamp', () => {
    const wrapper = mount(MessageBubble, { props: userProps })
    expect(wrapper.find('.message-bubble__time').exists()).toBe(true)
  })

  it('has accessible aria-label', () => {
    const wrapper = mount(MessageBubble, { props: userProps })
    expect(wrapper.find('article').attributes('aria-label')).toContain('Você')
  })

  it('has accessible aria-label for AI', () => {
    const wrapper = mount(MessageBubble, { props: aiProps })
    expect(wrapper.find('article').attributes('aria-label')).toContain('Assistente IA')
  })
})
