<script setup>
/**
 * LogSelector component — displays stored logs and allows selection/deletion.
 */

import { ref, onMounted } from 'vue'

const emit = defineEmits(['select', 'deleted'])

const logs = ref([])
const loading = ref(false)
const selectedCollection = ref(null)

const fetchLogs = async () => {
  loading.value = true
  try {
    const res = await fetch('/api/logs')
    if (res.ok) {
      logs.value = await res.json()
      // Auto-select first if nothing selected
      if (!selectedCollection.value && logs.value.length > 0) {
        selectLog(logs.value[0])
      }
    }
  } catch (err) {
    console.error('Failed to fetch logs:', err)
  } finally {
    loading.value = false
  }
}

const selectLog = (log) => {
  selectedCollection.value = log.collection
  emit('select', log.collection)
}

const deleteLog = async (log, event) => {
  event.stopPropagation()
  if (!confirm(`Remover "${log.filename}"?`)) return
  try {
    const res = await fetch(`/api/logs/${log.collection}`, { method: 'DELETE' })
    if (res.ok) {
      logs.value = logs.value.filter(l => l.collection !== log.collection)
      if (selectedCollection.value === log.collection) {
        selectedCollection.value = null
        if (logs.value.length > 0) {
          selectLog(logs.value[0])
        } else {
          emit('select', null)
        }
      }
      emit('deleted', log.collection)
    }
  } catch (err) {
    console.error('Failed to delete log:', err)
  }
}

const refresh = () => fetchLogs()

onMounted(fetchLogs)

defineExpose({ refresh })
</script>

<template>
  <div class="log-selector" v-if="logs.length > 0">
    <div class="log-selector__header">
      <span class="log-selector__label">Logs indexados</span>
      <span class="log-selector__count">{{ logs.length }}</span>
    </div>
    <div class="log-selector__list">
      <div
        v-for="log in logs"
        :key="log.collection"
        :class="['log-selector__item', { 'log-selector__item--active': selectedCollection === log.collection }]"
        @click="selectLog(log)"
        role="button"
        tabindex="0"
        @keydown.enter="selectLog(log)"
        :aria-pressed="selectedCollection === log.collection"
      >
        <div class="log-selector__item-info">
          <span class="log-selector__item-name">{{ log.filename }}</span>
          <span class="log-selector__item-meta">{{ log.chunks }} chunks</span>
        </div>
        <button
          class="log-selector__item-delete"
          @click="deleteLog(log, $event)"
          aria-label="Remover log"
          title="Remover"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.log-selector {
  background: var(--background);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
}

.log-selector__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.625rem 0.875rem;
  border-bottom: 1px solid var(--border);
  background: var(--secondary);
}

.log-selector__label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--muted-foreground);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.log-selector__count {
  font-size: 0.6875rem;
  font-weight: 600;
  background: var(--primary);
  color: var(--primary-foreground);
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
}

.log-selector__list {
  display: flex;
  flex-direction: column;
}

.log-selector__item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.625rem 0.875rem;
  border: none;
  background: transparent;
  cursor: pointer;
  text-align: left;
  font-family: inherit;
  transition: background-color 150ms ease;
  border-bottom: 1px solid var(--border);
}

.log-selector__item:last-child {
  border-bottom: none;
}

.log-selector__item:hover {
  background: var(--secondary);
}

.log-selector__item--active {
  background: var(--accent);
  border-left: 3px solid var(--primary);
}

.log-selector__item-info {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
  min-width: 0;
}

.log-selector__item-name {
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--foreground);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.log-selector__item-meta {
  font-size: 0.6875rem;
  color: var(--muted-foreground);
}

.log-selector__item-delete {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: var(--muted-foreground);
  cursor: pointer;
  border-radius: 4px;
  opacity: 0;
  transition: all 150ms ease;
}

.log-selector__item:hover .log-selector__item-delete {
  opacity: 1;
}

.log-selector__item-delete:hover {
  color: var(--destructive);
  background: #fef2f2;
}
</style>
