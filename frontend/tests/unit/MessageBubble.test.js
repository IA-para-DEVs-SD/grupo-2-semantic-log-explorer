/**
 * Unit tests for MessageBubble.vue component.
 * Tests message rendering, Markdown support, and accessibility.
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import MessageBubble from '../../src/components/MessageBubble.vue'

describe('MessageBubble', () => {
  describe('Basic Rendering', () => {
    it('renders user message with correct class', () => {
      const wrapper = mount(MessageBubble, {
        props: {
          content: 'Hello',
          sender: 'user'
        }
      })
      
      expect(wrapper.find('.message-bubble--user').exists()).toBe(true)
      expect(wrapper.find('.message-bubble--ai').exists()).toBe(false)
    })

    it('renders AI message with correct class', () => {
      const wrapper = mount(MessageBubble, {
        props: {
          content: 'Hello',
          sender: 'ai'
        }
      })
      
      expect(wrapper.find('.message-bubble--ai').exists()).toBe(true)
      expect(wrapper.find('.message-bubble--user').exists()).toBe(false)
    })

    it('displays message content', () => {
      const wrapper = mount(MessageBubble, {
        props: {
          content: 'Test message content',
          sender: 'user'
        }
      })
      
      expect(wrapper.text()).toContain('Test message content')
    })

    it('displays sender label for user', () => {
      const wrapper = mount(MessageBubble, {
        props: {
          content: 'Hello',
          sender: 'user'
        }
      })
      
      expect(wrapper.text()).toContain('Você')
    })

    it('displays sender label for AI', () => {
      const wrapper = mount(MessageBubble, {
        props: {
          content: 'Hello',
          sender: 'ai'
        }
      })
      
      expect(wrapper.text()).toContain('Assistente IA')
    })
  })

  describe('Timestamp Display', () => {
    it('displays formatted timestamp when provided', () => {
      const wrapper = mount(MessageBubble, {
        props: {
          content: 'Hello',
          sender: 'user',
          timestamp: new Date('2024-01-15T14:30:00')
        }
      })
      
      expect(wrapper.find('.message-bubble__time').exists()).toBe(true)
    })

    it('hides timestamp when not provided', () => {
      const wrapper = mount(MessageBubble, {
        props: {
          content: 'Hello',
          sender: 'user'
        }
      })
      
      expect(wrapper.find('.message-bubble__time').exists()).toBe(false)
    })

    it('accepts timestamp as string', () => {
      const wrapper = mount(MessageBubble, {
        props: {
          content: 'Hello',
          sender: 'user',
          timestamp: '2024-01-15T14:30:00'
        }
      })
      
      expect(wrapper.find('.message-bubble__time').exists()).toBe(true)
    })
  })

  describe('Markdown Rendering (AI Messages)', () => {
    it('renders bold text in AI messages', () => {
      const wrapper = mount(MessageBubble, {
        props: {
          content: 'This is **bold** text',
          sender: 'ai'
        }
      })
      
      const html = wrapper.find('.message-bubble__content').html()
      expect(html).toContain('<strong>')
    })

    it('renders italic text in AI messages', () => {
      const wrapper = mount(MessageBubble, {
        props: {
          content: 'This is *italic* text',
          sender: 'ai'
        }
      })
      
      const html = wrapper.find('.message-bubble__content').html()
      expect(html).toContain('<em>')
    })

    it('renders inline code in AI messages', () => {
      const wrapper = mount(MessageBubble, {
        props: {
          content: 'Use `console.log()` for debugging',
          sender: 'ai'
        }
      })
      
      const html = wrapper.find('.message-bubble__content').html()
      expect(html).toContain('<code>')
      expect(html).toContain('console.log()')
    })

    it('renders code blocks in AI messages', () => {
      const wrapper = mount(MessageBubble, {
        props: {
          content: '```javascript\nconst x = 1;\n```',
          sender: 'ai'
        }
      })
      
      const html = wrapper.find('.message-bubble__content').html()
      expect(html).toContain('<pre>')
      expect(html).toMatch(/<code[^>]*>/) // Match <code> with any attributes
    })

    it('renders lists in AI messages', () => {
      const wrapper = mount(MessageBubble, {
        props: {
          content: '- Item 1\n- Item 2\n- Item 3',
          sender: 'ai'
        }
      })
      
      const html = wrapper.find('.message-bubble__content').html()
      expect(html).toContain('<ul>')
      expect(html).toContain('<li>')
    })

    it('renders numbered lists in AI messages', () => {
      const wrapper = mount(MessageBubble, {
        props: {
          content: '1. First\n2. Second\n3. Third',
          sender: 'ai'
        }
      })
      
      const html = wrapper.find('.message-bubble__content').html()
      expect(html).toContain('<ol>')
    })

    it('renders links in AI messages', () => {
      const wrapper = mount(MessageBubble, {
        props: {
          content: 'Check [this link](https://example.com)',
          sender: 'ai'
        }
      })
      
      const html = wrapper.find('.message-bubble__content').html()
      expect(html).toContain('<a')
      expect(html).toContain('href="https://example.com"')
    })

    it('renders blockquotes in AI messages', () => {
      const wrapper = mount(MessageBubble, {
        props: {
          content: '> This is a quote',
          sender: 'ai'
        }
      })
      
      const html = wrapper.find('.message-bubble__content').html()
      expect(html).toContain('<blockquote>')
    })

    it('renders headings in AI messages', () => {
      const wrapper = mount(MessageBubble, {
        props: {
          content: '## Section Title',
          sender: 'ai'
        }
      })
      
      const html = wrapper.find('.message-bubble__content').html()
      expect(html).toContain('<h2>')
    })
  })

  describe('User Message Rendering (No Markdown)', () => {
    it('does not render Markdown in user messages', () => {
      const wrapper = mount(MessageBubble, {
        props: {
          content: 'This is **not bold**',
          sender: 'user'
        }
      })
      
      const html = wrapper.find('.message-bubble__content').html()
      expect(html).not.toContain('<strong>')
      expect(wrapper.text()).toContain('**not bold**')
    })

    it('preserves line breaks in user messages', () => {
      const wrapper = mount(MessageBubble, {
        props: {
          content: 'Line 1\nLine 2',
          sender: 'user'
        }
      })
      
      const html = wrapper.find('.message-bubble__content').html()
      expect(html).toContain('<br>')
    })
  })

  describe('XSS Protection', () => {
    it('escapes HTML in user messages', () => {
      const wrapper = mount(MessageBubble, {
        props: {
          content: '<script>alert("xss")</script>',
          sender: 'user'
        }
      })
      
      const html = wrapper.find('.message-bubble__content').html()
      expect(html).not.toContain('<script>')
      expect(html).toContain('&lt;script&gt;')
    })

    it('escapes HTML tags in user messages', () => {
      const wrapper = mount(MessageBubble, {
        props: {
          content: '<img src="x" onerror="alert(1)">',
          sender: 'user'
        }
      })
      
      const html = wrapper.find('.message-bubble__content').html()
      expect(html).not.toContain('<img')
    })
  })

  describe('Accessibility', () => {
    it('has article role', () => {
      const wrapper = mount(MessageBubble, {
        props: {
          content: 'Hello',
          sender: 'user'
        }
      })
      
      expect(wrapper.find('article').exists()).toBe(true)
    })

    it('has aria-label for user message', () => {
      const wrapper = mount(MessageBubble, {
        props: {
          content: 'Hello',
          sender: 'user'
        }
      })
      
      const article = wrapper.find('article')
      expect(article.attributes('aria-label')).toContain('Você')
    })

    it('has aria-label for AI message', () => {
      const wrapper = mount(MessageBubble, {
        props: {
          content: 'Hello',
          sender: 'ai'
        }
      })
      
      const article = wrapper.find('article')
      expect(article.attributes('aria-label')).toContain('Assistente')
    })

    it('icons have aria-hidden', () => {
      const wrapper = mount(MessageBubble, {
        props: {
          content: 'Hello',
          sender: 'user'
        }
      })
      
      const icon = wrapper.find('svg')
      expect(icon.attributes('aria-hidden')).toBe('true')
    })
  })

  describe('Props Validation', () => {
    it('requires content prop', () => {
      const wrapper = mount(MessageBubble, {
        props: {
          content: 'Test',
          sender: 'user'
        }
      })
      
      expect(wrapper.props('content')).toBe('Test')
    })

    it('requires sender prop', () => {
      const wrapper = mount(MessageBubble, {
        props: {
          content: 'Test',
          sender: 'ai'
        }
      })
      
      expect(wrapper.props('sender')).toBe('ai')
    })

    it('accepts only user or ai as sender', () => {
      // Valid values should work
      const userWrapper = mount(MessageBubble, {
        props: { content: 'Test', sender: 'user' }
      })
      expect(userWrapper.props('sender')).toBe('user')
      
      const aiWrapper = mount(MessageBubble, {
        props: { content: 'Test', sender: 'ai' }
      })
      expect(aiWrapper.props('sender')).toBe('ai')
    })
  })

  describe('Complex Markdown Content', () => {
    it('renders mixed content correctly', () => {
      const content = `
## Error Analysis

The error occurred at **line 42** in \`app.js\`:

\`\`\`javascript
throw new Error('Connection failed');
\`\`\`

Possible causes:
- Network timeout
- Invalid credentials
- Server unavailable
      `.trim()
      
      const wrapper = mount(MessageBubble, {
        props: {
          content,
          sender: 'ai'
        }
      })
      
      const html = wrapper.find('.message-bubble__content').html()
      expect(html).toContain('<h2>')
      expect(html).toContain('<strong>')
      expect(html).toContain('<code>')
      expect(html).toContain('<pre>')
      expect(html).toContain('<ul>')
    })

    it('renders tables in AI messages', () => {
      const content = `
| Status | Count |
|--------|-------|
| ERROR  | 15    |
| WARN   | 42    |
      `.trim()
      
      const wrapper = mount(MessageBubble, {
        props: {
          content,
          sender: 'ai'
        }
      })
      
      const html = wrapper.find('.message-bubble__content').html()
      expect(html).toContain('<table>')
      expect(html).toContain('<th>')
      expect(html).toContain('<td>')
    })
  })
})
