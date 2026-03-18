<template>
  <div class="app-shell">
    <header class="topbar">
      <div>
        <p class="eyebrow">Private Travel Basecamp</p>
        <h1>NomadBase</h1>
      </div>
      <div
        class="status-pill"
        :style="pillStyle"
      >{{ healthText }}</div>
    </header>

    <main class="content">
      <nav class="tab-nav" aria-label="Primary">
        <RouterLink
          v-for="tab in tabs"
          :key="tab.path"
          :to="tab.path"
          class="tab-button"
          active-class="active"
        >{{ tab.label }}</RouterLink>
      </nav>

      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useAdminStore } from './stores/admin.js'
import { usePlacesStore } from './stores/places.js'
import { useSavedStore } from './stores/saved.js'
import { useTripsStore } from './stores/trips.js'
import { useTrackingStore } from './stores/tracking.js'

const adminStore = useAdminStore()
const placesStore = usePlacesStore()
const savedStore = useSavedStore()
const tripsStore = useTripsStore()
const trackingStore = useTrackingStore()

const tabs = [
  { path: '/map', label: 'Map' },
  { path: '/saved', label: 'Saved' },
  { path: '/trips', label: 'Trips' },
  { path: '/tracking', label: 'Tracking' },
  { path: '/more', label: 'More' },
]

const healthText = computed(() => {
  if (adminStore.health === 'ok') return 'API reachable'
  if (adminStore.health === 'degraded') return 'API degraded'
  if (adminStore.health === 'offline') return 'API offline'
  return 'Checking API'
})

const pillStyle = computed(() => {
  if (adminStore.health === 'ok') return { background: '#d7ebe7', color: '#0f5c52' }
  if (adminStore.health === 'offline' || adminStore.health === 'degraded')
    return { background: '#f7ddcf', color: '#8f3f10' }
  return {}
})

onMounted(async () => {
  await adminStore.checkHealth()
  // Always fetch places — the store falls back to IndexedDB when offline
  await placesStore.fetchPlaces()
  if (adminStore.health !== 'offline') {
    await Promise.all([
      savedStore.fetchSaved(),
      tripsStore.fetchTrips(),
      trackingStore.fetchAll(),
      adminStore.fetchStatus(),
      adminStore.fetchImports(),
      adminStore.fetchPreferences(),
    ])
  }
})
</script>
