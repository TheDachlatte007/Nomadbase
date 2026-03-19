<template>
  <div class="panel active" style="display:grid">
    <div v-if="placesStore.isOffline" class="offline-banner">
      <span v-if="placesStore.cacheSource">
        Offline — showing cached data
        <span class="muted">({{ placesStore.cacheSource === 'all' ? 'full cache' : placesStore.cacheSource }})</span>
      </span>
      <span v-else>Offline — no cached data available for this filter</span>
    </div>

    <article class="info-card wide-card map-card">
      <div class="map-toolbar">
        <form class="toolbar" @submit.prevent="onSearch">
          <input v-model="searchQuery" type="search" placeholder="Search places, food, or city…">
          <select v-model="selectedTripId">
            <option value="">All imported regions</option>
            <option v-for="trip in trips" :key="trip.id" :value="trip.id">{{ trip.name }}</option>
          </select>
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
        <div class="tag-filter-row">
          <span
            v-for="chip in TAG_CHIPS"
            :key="chip.key"
            class="chip tag-chip"
            :class="{ active: activeTagFilters.has(chip.key) }"
            @click="toggleTagFilter(chip.key)"
          >{{ chip.label }}</span>
        </div>
        <p class="muted map-helper">
          {{ activeTrip ? `Scoped to ${activeTrip.name}.` : 'No trip scope selected.' }}
          Search for things like <code>vegan restaurant</code> and refine with tags.
        </p>
      </div>

      <div ref="mapEl" id="map-view"></div>

      <div class="places-grid">
        <p v-if="loading && !places.length" class="empty-state">Loading places…</p>
        <div v-else-if="!loading && !places.length" class="empty-state-wrap">
          <p class="empty-state">No places found{{ searchQuery ? ` for "${searchQuery}"` : ' for the current filters' }}.</p>
          <template v-if="searchQuery && !activeTagFilters.size">
            <p class="muted" style="font-size:.88rem;margin:4px 0 8px">Not in the database yet? Import from OpenStreetMap:</p>
            <button
              class="action-button secondary-button"
              style="width:fit-content"
              :disabled="importing"
              @click="onInlineImport"
            >{{ importing ? 'Importing from OSM…' : `Import "${searchQuery}"` }}</button>
            <p v-if="importFeedback" class="feedback">{{ importFeedback }}</p>
          </template>
        </div>

        <article
          v-for="place in places"
          :key="place.id"
          class="place-card place-card--clickable"
          :data-place-id="place.id"
          @click.self="focusOnMap(place)"
        >
          <div @click="focusOnMap(place)" style="cursor:pointer">
            <p class="card-eyebrow">{{ place.region || 'unknown region' }}</p>
            <h4>{{ place.name }}</h4>
            <p class="muted">
              {{ place.context_line || `${place.place_type} · ${place.lat.toFixed(3)}, ${place.lon.toFixed(3)}` }}
            </p>
          </div>
          <p>{{ place.description || 'No description yet.' }}</p>

          <div class="chip-row">
            <span class="chip">{{ place.place_type }}</span>
            <span v-for="tag in getDisplayTags(place)" :key="tag" class="chip chip--tag">{{ tag }}</span>
          </div>

          <div v-if="place.website_url || place.wikipedia_url" class="link-row" @click.stop>
            <a v-if="place.website_url" :href="place.website_url" target="_blank" rel="noreferrer">Website</a>
            <a v-if="place.wikipedia_url" :href="place.wikipedia_url" target="_blank" rel="noreferrer">Wikipedia</a>
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

      <div v-if="places.length" class="load-more-row">
        <p class="muted">Showing {{ places.length }} of {{ totalAvailable }} places</p>
        <button
          v-if="hasMore"
          class="action-button secondary-button"
          :disabled="loading"
          @click="onLoadMore"
        >{{ loading ? 'Loading…' : 'Load more' }}</button>
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
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import L from 'leaflet'
import 'leaflet.markercluster'
import { useRoute } from 'vue-router'
import { useAdminStore } from '../stores/admin.js'
import { usePlacesStore } from '../stores/places.js'
import { useSavedStore } from '../stores/saved.js'
import { useTripsStore } from '../stores/trips.js'

const route = useRoute()
const placesStore = usePlacesStore()
const savedStore = useSavedStore()
const adminStore = useAdminStore()
const tripsStore = useTripsStore()

const places = computed(() => placesStore.places)
const loading = computed(() => placesStore.loading)
const hasMore = computed(() => placesStore.hasMore)
const totalAvailable = computed(() => placesStore.totalAvailable)
const trips = computed(() => tripsStore.trips)
const activeTrip = computed(() => tripsStore.activeTrip)

const searchQuery = ref('')
const placeType = ref('')
const selectedTripId = ref(tripsStore.activeTripId || '')
const nearMeText = ref('Near me')
const nearMeLoading = ref(false)
const mapEl = ref(null)
const importing = ref(false)
const importFeedback = ref('')

const TAG_CHIPS = [
  { key: 'vegan', label: 'Vegan' },
  { key: 'vegetarian', label: 'Vegetarian' },
  { key: 'outdoor_seating', label: 'Outdoor seating' },
  { key: 'wifi', label: 'WiFi' },
  { key: 'wheelchair', label: 'Wheelchair' },
]
const activeTagFilters = reactive(new Set())

const healthTitle = computed(() => {
  if (adminStore.health === 'ok') return 'Backend is responding.'
  if (adminStore.health === 'degraded') return 'API degraded.'
  return 'Waiting for health check.'
})
const healthCopy = computed(() => {
  if (adminStore.health === 'ok') return 'FastAPI answered through the proxy and the database is healthy.'
  if (adminStore.health === 'degraded') return 'The endpoint answered but the database check returned a warning.'
  return 'API container may not be up yet or the reverse proxy cannot reach it.'
})

const saveForms = reactive({})
watch(
  places,
  (newPlaces) => {
    for (const place of newPlaces) {
      if (!saveForms[place.id]) {
        saveForms[place.id] = { status: 'want_to_visit', notes: '', feedback: '' }
      }
    }
  },
  { immediate: true }
)

watch(
  () => tripsStore.activeTripId,
  (tripId) => {
    selectedTripId.value = tripId || ''
  }
)

watch(
  () => route.query.trip,
  (tripId) => {
    if (typeof tripId === 'string') {
      selectedTripId.value = tripId
      tripsStore.setActiveTrip(tripId)
      runSearch().catch(() => {})
    }
  },
  { immediate: true }
)

function getDisplayTags(place) {
  const tags = place.tags || {}
  const chips = []
  if (place.cuisine) chips.push(place.cuisine.replace(/_/g, ' '))
  if (tags['diet:vegan'] === 'yes') chips.push('vegan')
  if (tags['diet:vegetarian'] === 'yes') chips.push('vegetarian')
  if (tags.outdoor_seating === 'yes') chips.push('outdoor')
  if (tags.internet_access === 'wlan') chips.push('wifi')
  if (tags.wheelchair === 'yes') chips.push('wheelchair')
  return chips.slice(0, 4)
}

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
let clusterGroup = null
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

function focusOnMap(place) {
  if (!map || !clusterGroup) return
  const marker = placeMarkers.get(place.id)
  if (marker) {
    clusterGroup.zoomToShowLayer(marker, () => marker.openPopup())
  } else {
    map.setView([place.lat, place.lon], 15, { animate: true })
  }
}

function syncMarkers(newPlaces) {
  if (!map || !clusterGroup) return

  const currentIds = new Set(newPlaces.map((place) => place.id))
  for (const [id, marker] of placeMarkers) {
    if (!currentIds.has(id)) {
      clusterGroup.removeLayer(marker)
      placeMarkers.delete(id)
    }
  }

  const toAdd = []
  for (const place of newPlaces) {
    if (placeMarkers.has(place.id)) continue
    const marker = L.marker([place.lat, place.lon], {
      icon: makeMarkerIcon(place.place_type),
      title: place.name,
    })
    marker.bindPopup(
      `<strong>${place.name}</strong><br>
       <span style="color:#5f6d69;font-size:.9em">${place.context_line || place.place_type}</span>
       ${place.description ? `<br><span style="font-size:.88em">${place.description}</span>` : ''}`,
      { maxWidth: 240 }
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
    toAdd.push(marker)
  }

  if (toAdd.length) clusterGroup.addLayers(toAdd)
  if (newPlaces.length && placeMarkers.size) {
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

  clusterGroup = L.markerClusterGroup({
    chunkedLoading: true,
    maxClusterRadius: 60,
    spiderfyOnMaxZoom: true,
    showCoverageOnHover: false,
  })
  map.addLayer(clusterGroup)

  if (places.value.length) syncMarkers(places.value)
})

onUnmounted(() => {
  map?.remove()
  map = null
  clusterGroup = null
  placeMarkers.clear()
})

function runSearch() {
  const tagStr = [...activeTagFilters].join(',')
  return placesStore.fetchPlaces(searchQuery.value, placeType.value, tagStr, selectedTripId.value)
}

function toggleTagFilter(key) {
  if (activeTagFilters.has(key)) {
    activeTagFilters.delete(key)
  } else {
    activeTagFilters.add(key)
  }
  runSearch().catch(() => {})
}

async function onSearch() {
  importFeedback.value = ''
  tripsStore.setActiveTrip(selectedTripId.value)
  await runSearch()
}

async function onLoadMore() {
  await placesStore.loadMore()
}

async function onNearMe() {
  if (!navigator.geolocation) {
    nearMeText.value = 'Not supported'
    return
  }

  nearMeText.value = 'Locating...'
  nearMeLoading.value = true
  navigator.geolocation.getCurrentPosition(
    async ({ coords }) => {
      try {
        map?.setView([coords.latitude, coords.longitude], 14)
        if (userMarker) userMarker.remove()
        userMarker = L.circleMarker([coords.latitude, coords.longitude], {
          radius: 8,
          fillColor: '#0f5c52',
          color: '#fff',
          weight: 2,
          fillOpacity: 0.9,
        }).addTo(map).bindPopup('You are here').openPopup()

        const nearby = await placesStore.fetchNearby(coords.latitude, coords.longitude)
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

async function onInlineImport() {
  if (!searchQuery.value || importing.value) return
  importing.value = true
  importFeedback.value = `Fetching OSM data for "${searchQuery.value}"… this may take up to 60s.`
  try {
    const result = await adminStore.importCity(searchQuery.value, null)
    if (result.imported === 0) {
      importFeedback.value = `No named places found for "${searchQuery.value}". Try a different spelling or add the country.`
    } else {
      importFeedback.value = `Imported ${result.imported} places for ${result.region}. Loading…`
      await runSearch()
    }
  } catch (error) {
    importFeedback.value = `Import failed: ${error.message}`
  } finally {
    importing.value = false
  }
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
