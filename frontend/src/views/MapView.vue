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
          <select v-model="placeType">
            <option value="">All types</option>
            <option value="park">Park</option>
            <option value="restaurant">Restaurant</option>
            <option value="cafe">Cafe</option>
            <option value="cultural">Cultural</option>
            <option value="attraction">Attraction</option>
            <option value="hiking">Hiking</option>
            <option value="viewpoint">Viewpoint</option>
            <option value="stay">Stay</option>
            <option value="essentials">Essentials</option>
            <option value="transport">Transport</option>
          </select>
          <button class="action-button" type="submit">Search</button>
          <button
            class="action-button secondary-button"
            type="button"
            :disabled="nearMeLoading"
            @click="onNearMe"
          >{{ nearMeText }}</button>
        </form>
        <div class="map-preset-row">
          <button
            v-for="preset in SEARCH_PRESETS"
            :key="preset.label"
            class="secondary-button action-button map-preset-button"
            type="button"
            @click="applyPreset(preset)"
          >
            {{ preset.label }}
          </button>
        </div>
        <div class="map-scope-grid">
          <label class="map-filter-field">
            <span class="card-eyebrow">Trip scope</span>
            <select v-model="selectedTripId" @change="onScopeChange">
              <option value="">All trips</option>
              <option v-for="trip in trips" :key="trip.id" :value="trip.id">{{ trip.name }}</option>
            </select>
          </label>
          <label class="map-filter-field">
            <span class="card-eyebrow">Imported region</span>
            <select v-model="selectedRegion" @change="onScopeChange">
              <option value="">All imported regions</option>
              <option v-for="region in importedRegions" :key="region" :value="region">{{ region }}</option>
            </select>
          </label>
        </div>
        <div v-if="tripOverview?.cities?.length" class="route-overview-strip">
          <div>
            <p class="card-eyebrow">Active route</p>
            <p class="muted">
              {{ tripOverview.route_label }}
              <span v-if="tripOverview.route_distance_km">· {{ Math.round(tripOverview.route_distance_km) }} km</span>
            </p>
          </div>
          <div class="chip-row">
            <button
              v-for="city in tripOverview.cities"
              :key="city.id"
              class="secondary-button action-button route-city-chip"
              type="button"
              @click="applyTripCity(city)"
            >
              {{ city.sort_order + 1 }}. {{ city.name }}
            </button>
          </div>
        </div>
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
          {{ activeTrip ? `Trip scoped to ${activeTrip.name}.` : 'Trip scope is optional.' }}
          {{ selectedRegion ? ` Region filter: ${selectedRegion}.` : ' Imported region filter is optional.' }}
          Search for things like <code>vegan restaurant toronto</code>.
          The vegan chip is a strict OSM metadata filter.
        </p>
        <p v-if="resultMessage" class="muted map-helper">{{ resultMessage }}</p>
      </div>

      <div ref="mapEl" id="map-view"></div>

      <div class="places-grid">
        <p v-if="loading && !places.length" class="empty-state">Loading places…</p>
        <div v-else-if="!loading && !places.length" class="empty-state-wrap">
          <p class="empty-state">No places found{{ searchQuery ? ` for "${searchQuery}"` : ' for the current filters' }}.</p>
          <p v-if="activeTagFilters.has('vegan')" class="muted" style="font-size:.88rem;margin:0">
            The vegan filter only keeps places with explicit OSM vegan tags. Try the query without the chip for broader vegan-friendly matches.
          </p>
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

          <div v-if="place.facts?.length" class="place-facts">
            <span v-for="fact in place.facts" :key="fact" class="fact-pill">{{ fact }}</span>
          </div>

          <div class="chip-row">
            <span class="chip">{{ place.place_type }}</span>
            <span v-for="tag in getDisplayTags(place)" :key="tag" class="chip chip--tag">{{ tag }}</span>
          </div>

          <div v-if="place.website_url || place.wikipedia_url" class="link-row" @click.stop>
            <a v-if="place.website_url" :href="place.website_url" target="_blank" rel="noreferrer">Website</a>
            <a v-if="place.wikipedia_url" :href="place.wikipedia_url" target="_blank" rel="noreferrer">Wikipedia</a>
          </div>

          <details class="place-actions" @click.stop>
            <summary>Save or note</summary>
            <form class="save-form" @submit.prevent="onSavePlace(place)">
              <select v-model="saveForms[place.id].trip_id" @change="onSaveScopeChange(place.id)">
                <option value="">Global shortlist</option>
                <option v-for="trip in trips" :key="trip.id" :value="trip.id">
                  {{ trip.name }}
                </option>
              </select>
              <select
                v-if="getTripCities(saveForms[place.id].trip_id).length"
                v-model="saveForms[place.id].city_id"
              >
                <option value="">No city assignment yet</option>
                <option
                  v-for="city in getTripCities(saveForms[place.id].trip_id)"
                  :key="city.id"
                  :value="city.id"
                >
                  {{ city.sort_order + 1 }}. {{ city.name }}
                </option>
              </select>
              <select v-model="saveForms[place.id].status">
                <option value="want_to_visit">Want to visit</option>
                <option value="visited">Visited</option>
                <option value="favorite">Favorite</option>
              </select>
              <textarea v-model="saveForms[place.id].notes" placeholder="Quick note for future you"></textarea>
              <button class="action-button" type="submit">Save place</button>
              <p v-if="saveForms[place.id].feedback" class="feedback">{{ saveForms[place.id].feedback }}</p>
            </form>
          </details>
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
const resultMessage = computed(() => placesStore.message)
const trips = computed(() => tripsStore.trips)
const activeTrip = computed(() => tripsStore.activeTrip)
const tripOverview = computed(() => tripsStore.tripOverview)
const importedRegions = computed(() => {
  return (adminStore.imports || [])
    .map((item) => item.region)
    .filter(Boolean)
    .sort((a, b) => a.localeCompare(b))
})

const searchQuery = ref('')
const placeType = ref('')
const selectedTripId = ref(tripsStore.activeTripId || '')
const selectedRegion = ref('')
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
const SEARCH_PRESETS = [
  { label: 'Food', query: '', placeType: 'restaurant', tags: [] },
  { label: 'Coffee', query: 'coffee', placeType: 'cafe', tags: [] },
  { label: 'Vegan-friendly', query: 'vegan', placeType: 'restaurant', tags: [] },
  { label: 'Churches', query: 'church', placeType: 'cultural', tags: [] },
  { label: 'Sights', query: 'sights', placeType: 'attraction', tags: [] },
  { label: 'Nature', query: 'nature', placeType: 'park', tags: [] },
  { label: 'Stay', query: 'hotel', placeType: 'stay', tags: [] },
  { label: 'Essentials', query: 'supermarket', placeType: 'essentials', tags: [] },
  { label: 'Transport', query: 'station', placeType: 'transport', tags: [] },
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
        saveForms[place.id] = {
          trip_id: selectedTripId.value || tripsStore.activeTripId || '',
          city_id: '',
          status: 'want_to_visit',
          notes: '',
          feedback: '',
        }
      }
    }
  },
  { immediate: true }
)

watch(
  () => tripsStore.activeTripId,
  (tripId) => {
    selectedTripId.value = tripId || ''
    for (const form of Object.values(saveForms)) {
      if (!form.trip_id) {
        form.trip_id = tripId || ''
      }
      if (!form.trip_id) {
        form.city_id = ''
      }
    }
  }
)

watch(
  () => route.query.trip,
  async (tripId) => {
    if (typeof tripId === 'string') {
      selectedTripId.value = tripId
      tripsStore.setActiveTrip(tripId)
      await tripsStore.fetchTripOverview(tripId).catch(() => {})
      runSearch().catch(() => {})
    }
  },
  { immediate: true }
)

watch(selectedTripId, (tripId) => {
  if (tripId) {
    tripsStore.fetchTripOverview(tripId).catch(() => {})
  }
  for (const form of Object.values(saveForms)) {
    if (!form.trip_id) {
      form.trip_id = tripId || ''
    }
    if (!form.trip_id) {
      form.city_id = ''
    }
  }
})

function getTripCities(tripId) {
  return trips.value.find((trip) => trip.id === tripId)?.cities || []
}

function onSaveScopeChange(placeId) {
  const form = saveForms[placeId]
  const validCityIds = new Set(getTripCities(form.trip_id).map((city) => city.id))
  if (!validCityIds.has(form.city_id)) {
    form.city_id = ''
  }
}

function getDisplayTags(place) {
  const tags = place.tags || {}
  const chips = []
  if (place.cuisine) chips.push(place.cuisine.replace(/_/g, ' '))
  if (['yes', 'only'].includes(tags['diet:vegan'])) chips.push('vegan')
  if (['yes', 'only'].includes(tags['diet:vegetarian'])) chips.push('vegetarian')
  if (tags.outdoor_seating === 'yes') chips.push('outdoor')
  if (['wlan', 'yes'].includes(tags.internet_access)) chips.push('wifi')
  if (['yes', 'limited', 'designated'].includes(tags.wheelchair)) chips.push('wheelchair')
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
  stay: '#8c4f6f',
  essentials: '#7a6336',
  transport: '#355d8a',
}

let map = null
let clusterGroup = null
let routeLayerGroup = null
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

function syncRouteOverlay(overview) {
  if (!map || !routeLayerGroup) return
  routeLayerGroup.clearLayers()

  const cities = (overview?.cities || []).filter((city) => city.lat !== null && city.lon !== null)
  if (!cities.length) return

  if (cities.length > 1) {
    L.polyline(
      cities.map((city) => [city.lat, city.lon]),
      {
        color: '#0f5c52',
        weight: 3,
        opacity: 0.75,
        dashArray: '6 8',
      }
    ).addTo(routeLayerGroup)
  }

  for (const city of cities) {
    const marker = L.circleMarker([city.lat, city.lon], {
      radius: 8,
      color: '#0f5c52',
      weight: 2,
      fillColor: '#f8f6f1',
      fillOpacity: 0.95,
    }).addTo(routeLayerGroup)
    marker.bindPopup(`<strong>${city.sort_order + 1}. ${city.name}</strong>`)
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
watch(tripOverview, syncRouteOverlay, { deep: true })

onMounted(() => {
  adminStore.fetchImports().catch(() => {})
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
  routeLayerGroup = L.layerGroup().addTo(map)

  if (places.value.length) syncMarkers(places.value)
  if (selectedTripId.value) {
    tripsStore.fetchTripOverview(selectedTripId.value).catch(() => {})
  }
  if (tripOverview.value) syncRouteOverlay(tripOverview.value)
})

onUnmounted(() => {
  map?.remove()
  map = null
  clusterGroup = null
  routeLayerGroup = null
  placeMarkers.clear()
})

function runSearch() {
  const tagStr = [...activeTagFilters].join(',')
  return placesStore.fetchPlaces(
    searchQuery.value,
    placeType.value,
    tagStr,
    selectedTripId.value,
    selectedRegion.value
  )
}

function applyPreset(preset) {
  searchQuery.value = preset.query
  placeType.value = preset.placeType
  activeTagFilters.clear()
  for (const tag of preset.tags || []) {
    activeTagFilters.add(tag)
  }
  runSearch().catch(() => {})
}

function applyTripCity(city) {
  searchQuery.value = city.name
  const exactRegion = city.country ? `${city.name}, ${city.country}` : city.name
  selectedRegion.value = importedRegions.value.includes(exactRegion) ? exactRegion : ''
  runSearch().catch(() => {})
  if (city.lat !== null && city.lon !== null) {
    map?.setView([city.lat, city.lon], 12, { animate: true })
  }
}

function onScopeChange() {
  importFeedback.value = ''
  tripsStore.setActiveTrip(selectedTripId.value)
  if (selectedTripId.value) {
    tripsStore.fetchTripOverview(selectedTripId.value).catch(() => {})
  }
  runSearch().catch(() => {})
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
  importFeedback.value = `Queueing OSM import for "${searchQuery.value}"… this may take up to a minute.`
  try {
    const job = await adminStore.importCity(searchQuery.value, null)
    const result = await adminStore.waitForImportJob(job.id)
    if (result.imported_count === 0) {
      importFeedback.value = `No named places found for "${searchQuery.value}". Try a different spelling or add the country.`
    } else {
      selectedRegion.value = result.region || selectedRegion.value
      importFeedback.value = `Imported ${result.imported_count} places for ${result.region || searchQuery.value}. Loading…`
      await adminStore.fetchImports().catch(() => {})
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
    await savedStore.savePlace(
      place.id,
      form.status,
      form.notes || null,
      form.trip_id || null,
      form.trip_id ? (form.city_id || null) : null
    )
    if (form.trip_id && tripsStore.activeTripId === form.trip_id) {
      await tripsStore.fetchTripOverview(form.trip_id)
    }
    form.feedback = form.trip_id ? 'Saved to trip shortlist' : 'Saved to global shortlist'
    form.notes = ''
  } catch {
    form.feedback = 'Save failed'
  }
}
</script>
