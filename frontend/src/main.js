/**
 * Main entry point for the Semantic Log Explorer frontend.
 * Initializes Vue 3 application with Composition API.
 */

import { createApp } from 'vue'
import App from './App.vue'
import './assets/styles.css'

const app = createApp(App)

app.mount('#app')
