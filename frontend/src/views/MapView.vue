<template>
  <div class="panel active" style="display:grid">
    <article class="info-card wide-card map-card">
      <div class="map-toolbar">
        <form class="toolbar" @submit.prevent="onSearch">
          <input v-model="searchQuery" type="search" placeholder="Search places or regions">
          <select v-model="placeType">
            <option value="">All types</option>
            <option value="park">Park</option>
            <option value="restaurant">Restaurant</option>
            <option value="cafe">Cafe</option>
            <option value="cultural">Cultural</option>
            <option value="attraction">Attraction</option>
            <option value="hiking">Hiking</option>
            <option value="viewpoint">Viewpoint</option>
          </select>
          <button class="action-button" type="submit">Search</button>
          <button
            class="action-button secondary-button"
            type="button"
            :disabled="nearMeLoading"
            @click="onNearMe"
          >{{ nearMeText }}</button>
        </form>
      </div>

      <div ref="mapEl" id="map-view"></div>

      <div class="places-grid">
        <p v-if="loading" class="empty-state">Loading places...</p>
        <p v-else-if="!places.length" class="empty-state">No places matched the current filters.</p>
        <article
          v-for="place in places"
          :key="place.id"
          class="place-card"
          :data-place-id="place.id"
        >
          <div>
            <p class="card-eyebrow">{{ place.region || 'unknown region' }}</p>
            <h4>{{ place.name }}</h4>
            <p class="muted">{{ place.place_type }} · {{ place.lat.toFixed(3) }}, {{ place.lon.toFixed(3) }}</p>
          </div>
          <p>{{ place.description || 'No description yet.' }}</p>
          <div class="chip-row">
            <span class="chip">{{ place.place_type }}</span>
          </div>
          <form class="save-form" @submit.prevent="onSavePlace(place)">
            <select v-model="saveForms[place.id].status">
              <option value="want_to_visit">Want to visit</option>
              <option value="visited">Visited</option>
              <option value="favorite">Favorite</option>
            </select>
            <textarea v-model="saveForms[place.id].notes" placeholder="Quick note for future you"></textarea>
            <button class="action-button" type="submit">Save place</button>
            <p v-if="saveForms[place.id].feedback" class="feedback">{{ saveForms[place.id].feedback }}</p>
          </form>
        </article>
      </div>
    </article>

    <article class="callout-card">
      <p class="card-eyebrow">API</p>
      <h3>{{ healthTitle }}</h3>
      <p>{{ healthCopy }}</p>
    </article>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, reactive } from 'vue'
import L from 'leaflet'
import { usePlacesStore } from '../stores/places.js'
import { useSavedStore } from '../stores/saved.js'
import { useAdminStore } from '../stores/admin.js'

const placesStore = usePlacesStore()
const savedStore = useSavedStore()
const adminStore = useAdminStore()

const places = computed(() => placesStore.places)
const loading = computed(() => placesStore.loading)
const searchQuery = ref('')
const placeType = ref('')
const nearMeText = ref('Near me')
const nearMeLoading = ref(false)
const mapEl = ref(null)

const healthTitle = computed(() => {
  if (adminStore.health === 'ok') return 'Backend is responding.'
  if (adminStore.health === 'degraded') return 'API degraded.'
  return 'Waiting for health check.'
})
const healthCopy = computed(() => {
  if (adminStore.health === 'ok')
    return 'FastAPI answered through the proxy and the database is healthy.'
  if (adminStore.health === 'degraded')
    return 'The endpoint answered but the database check returned a warning.'
  return 'API container may not be up yet or the reverse proxy cannot reach it.'
})

// Per-place save forms
const saveForms = reactive({})
watch(
  places,
  (newPlaces) => {
    for (const p of newPlaces) {
      if (!saveForms[p.id]) {
        saveForms[p.id] = { status: 'want_to_visit', notes: '', feedback: '' }
      }
    }
  },
  { immediate: true }
)

// --- Leaflet ---
const TYPE_COLORS = {
  park: '#2d7a2d',
  restaurant: '#c86f31',
  cafe: '#8b5e3c',
  cultural: '#5b4a8a',
  attraction: '#0f5c52',
  hiking: '#1a6e4a',
  viewpoint: '#1a5c8a',
}

let map = null
const placeMarkers = new Map()
let userMarker = null

function makeMarkerIcon(type) {
  const color = TYPE_COLORS[type] || '#5f6d69'
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="34" viewBox="0 0 24 34">
    <path d="M12 0C5.4 0 0 5.4 0 12c0 9 12 22 12 22s12-13 12-22C24 5.4 18.6 0 12 0z" fill="${color}" stroke="white" stroke-width="1.5"/>
    <circle cx="12" cy="12" r="5" fill="white"/>
  </svg>`
  return L.divIcon({ html: svg, className: '', iconSize: [24, 34], iconAnchor: [12, 34], popupAnchor: [0, -34] })
}

function syncMarkers(newPlaces) {
  if (!map) return
  const currentIds = new Set(newPlaces.map((p) => p.id))
  for (const [id, marker] of placeMarkers) {
    if (!currentIds.has(id)) {
      marker.remove()
      placeMarkers.delete(id)
    }
  }
  for (const place of newPlaces) {
    if (placeMarkers.has(place.id)) continue
    const marker = L.marker([place.lat, place.lon], {
      icon: makeMarkerIcon(place.place_type),
      title: place.name,
    }).addTo(map)
    marker.bindPopup(
      `<strong>${place.name}</strong><br>
       <span style="color:#5f6d69;font-size:.9em">${place.place_type}${place.region ? ` · ${place.region}` : ''}</span>
       ${place.description ? `<br><span style="font-size:.88em">${place.description}</span>` : ''}`,
      { maxWidth: 220 }
    )
    marker.on('click', () => {
      const card = document.querySelector(`[data-place-id="${place.id}"]`)
      if (card) {
        card.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
        card.classList.add('map-highlight')
        setTimeout(() => card.classList.remove('map-highlight'), 1800)
      }
    })
    placeMarkers.set(place.id, marker)
  }
  if (newPlaces.length > 0) {
    const group = L.featureGroup([...placeMarkers.values()])
    map.fitBounds(group.getBounds().pad(0.2))
  }
}

watch(places, syncMarkers)

onMounted(() => {
  map = L.map(mapEl.value, { zoomControl: true }).setView([20, 10], 2)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    maxZoom: 19,
  }).addTo(map)
  if (places.value.length > 0) syncMarkers(places.value)
})

onUnmounted(() => {
  map?.remove()
  map = null
  placeMarkers.clear()
})

async function onSearch() {
  await placesStore.fetchPlaces(searchQuery.value, placeType.value)
}

async function onNearMe() {
  if (!navigator.geolocation) {
    nearMeText.value = 'Not supported'
    return
  }
  nearMeText.value = 'Locating...'
  nearMeLoading.value = true

  navigator.geolocation.getCurrentPosition(
    async (pos) => {
      const { latitude, longitude } = pos.coords
      try {
        map?.setView([latitude, longitude], 14)
        if (userMarker) userMarker.remove()
        userMarker = L.circleMarker([latitude, longitude], {
          radius: 8,
          fillColor: '#0f5c52',
          color: '#fff',
          weight: 2,
          fillOpacity: 0.9,
        })
          .addTo(map)
          .bindPopup('You are here')
          .openPopup()

        const nearby = await placesStore.fetchNearby(latitude, longitude)
        nearMeText.value = `${nearby.length} nearby`
      } catch {
        nearMeText.value = 'Failed'
      } finally {
        nearMeLoading.value = false
      }
    },
    () => {
      nearMeText.value = 'Denied'
      nearMeLoading.value = false
    },
    { timeout: 8000 }
  )
}

async function onSavePlace(place) {
  const form = saveForms[place.id]
  form.feedback = 'Saving...'
  try {
    await savedStore.savePlace(place.id, form.status, form.notes || null)
    form.feedback = 'Saved'
    form.notes = ''
  } catch {
    form.feedback = 'Save failed'
  }
}
</script>
