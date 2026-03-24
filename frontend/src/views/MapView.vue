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
            <p v-if="routePrepHint" class="muted">{{ routePrepHint }}</p>
          </div>
          <div class="trip-actions">
            <button
              v-if="showRoutePrepButton"
              class="secondary-button action-button"
              type="button"
              :disabled="routePrepLoading"
              @click="onPrepRoute"
            >
              {{ routePrepLoading ? 'Preparing route...' : 'Prep route' }}
            </button>
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
        <p v-if="tripOverview?.cities?.length && importFeedback" class="feedback">{{ importFeedback }}</p>
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
import { useRoute } from 'vue-router'
import { useAdminStore } from '../stores/admin.js'
import { usePlacesStore } from '../stores/places.js'
import { useSavedStore } from '../stores/saved.js'
import { useTripsStore } from '../stores/trips.js'
import {
  boundsToBboxString,
  cityToFeature,
  createRasterStyle,
  escapeHtml,
  featureCollection,
  fitMapToCoordinates,
  maplibregl,
  placeToFeature,
  routeLineFeature,
} from '../utils/maplibre.js'

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
const routePrepHint = computed(() => {
  const summary = tripOverview.value?.coverage_summary
  if (!summary) return ''
  if (summary.route_readiness === 'ready') return 'Trip route looks ready for local discovery.'
  if (summary.route_readiness === 'importing') {
    return `${summary.queued_imports + summary.running_imports} route import(s) are still running.`
  }
  const detailParts = []
  if (summary.core_gap_cities) detailParts.push(`${summary.core_gap_cities} stop(s) still miss route basics`)
  if (summary.refresh_recommended) detailParts.push(`${summary.refresh_recommended} stop(s) would benefit from refresh`)
  if (summary.unmapped_cities) detailParts.push(`${summary.unmapped_cities} stop(s) still need map coordinates`)
  if (!detailParts.length && (summary.thin || summary.missing)) {
    detailParts.push(`${summary.thin + summary.missing} stop(s) still need stronger local coverage`)
  }
  return detailParts.join(' · ')
})
const showRoutePrepButton = computed(() => {
  const summary = tripOverview.value?.coverage_summary
  if (!summary) return false
  return Boolean(summary.needs_import || summary.refresh_recommended || summary.core_gap_cities)
})
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
const routePrepLoading = ref(false)

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

let map = null
let mapReady = false
let activePopup = null
let viewportTimer = null
let lastRouteFitKey = ''
let lastPlacesFitKey = ''
let suppressViewportFetchUntil = 0

function buildPlacePopupHtml(place) {
  const links = [
    place.website_url
      ? `<a href="${escapeHtml(place.website_url)}" target="_blank" rel="noreferrer">Website</a>`
      : '',
    place.wikipedia_url
      ? `<a href="${escapeHtml(place.wikipedia_url)}" target="_blank" rel="noreferrer">Wikipedia</a>`
      : '',
  ]
    .filter(Boolean)
    .join(' · ')

  return `
    <div class="map-popup">
      <strong>${escapeHtml(place.name)}</strong>
      <div class="map-popup__meta">${escapeHtml(place.context_line || place.place_type)}</div>
      ${
        place.description
          ? `<div class="map-popup__body">${escapeHtml(place.description)}</div>`
          : ''
      }
      ${links ? `<div class="map-popup__links">${links}</div>` : ''}
    </div>
  `
}

function scrollCardIntoView(placeId) {
  const card = document.querySelector(`[data-place-id="${placeId}"]`)
  if (!card) return
  card.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  card.classList.add('map-highlight')
  setTimeout(() => card.classList.remove('map-highlight'), 1800)
}

function openPlacePopup(place, coordinates = [place.lon, place.lat]) {
  if (!map) return
  activePopup?.remove()
  activePopup = new maplibregl.Popup({ closeButton: false, offset: 14 })
    .setLngLat(coordinates)
    .setHTML(buildPlacePopupHtml(place))
    .addTo(map)
}

function setSourceData(sourceId, data) {
  const source = map?.getSource(sourceId)
  if (source) {
    source.setData(data)
  }
}

function syncMapSources() {
  if (!mapReady || !map) return

  setSourceData(
    'places',
    featureCollection(places.value.map((place) => placeToFeature(place)))
  )

  const routeCities = (tripOverview.value?.cities || [])
    .map((city) => cityToFeature(city))
    .filter(Boolean)
  setSourceData('route-cities', featureCollection(routeCities))

  const routeLine = routeLineFeature(tripOverview.value?.cities || [])
  setSourceData('route-line', featureCollection(routeLine ? [routeLine] : []))
}

function maybeFitRouteToMap() {
  const cities = (tripOverview.value?.cities || []).filter(
    (city) => city.lat !== null && city.lon !== null
  )
  if (!cities.length) return
  const fitKey = `${selectedTripId.value}:${cities.map((city) => city.id).join(',')}`
  if (fitKey === lastRouteFitKey) return
  lastRouteFitKey = fitKey
  fitMapToCoordinates(
    map,
    cities.map((city) => [city.lon, city.lat]),
    { maxZoom: 11, padding: 56 }
  )
}

function maybeFitPlacesToMap() {
  if (!places.value.length || selectedTripId.value) return
  const fitKey = `${searchQuery.value}|${placeType.value}|${selectedRegion.value}|${places.value.length}|${places.value[0]?.id || ''}`
  if (fitKey === lastPlacesFitKey) return
  lastPlacesFitKey = fitKey
  fitMapToCoordinates(
    map,
    places.value.map((place) => [place.lon, place.lat]),
    { maxZoom: 12, padding: 48 }
  )
}

function applyCursor(layerId) {
  map.on('mouseenter', layerId, () => {
    map.getCanvas().style.cursor = 'pointer'
  })
  map.on('mouseleave', layerId, () => {
    map.getCanvas().style.cursor = ''
  })
}

function attachMapEvents() {
  applyCursor('places-clusters')
  applyCursor('places-points')
  applyCursor('route-cities-points')

  map.on('click', 'places-clusters', (event) => {
    const feature = event.features?.[0]
    if (!feature) return
    const clusterId = feature.properties.cluster_id
    map.getSource('places').getClusterExpansionZoom(clusterId, (error, zoom) => {
      if (error) return
      map.easeTo({
        center: feature.geometry.coordinates,
        zoom,
        duration: 500,
      })
    })
  })

  map.on('click', 'places-points', (event) => {
    const feature = event.features?.[0]
    if (!feature) return
    const place = places.value.find((item) => item.id === feature.properties.id)
    if (!place) return
    openPlacePopup(place, feature.geometry.coordinates.slice())
    scrollCardIntoView(place.id)
  })

  map.on('click', 'route-cities-points', (event) => {
    const feature = event.features?.[0]
    if (!feature) return
    const city = tripOverview.value?.cities?.find((item) => item.id === feature.properties.id)
    if (!city) return
    map.easeTo({
      center: [city.lon, city.lat],
      zoom: Math.max(map.getZoom(), 11),
      duration: 500,
    })
  })

  map.on('moveend', () => {
    clearTimeout(viewportTimer)
    viewportTimer = setTimeout(() => {
      if (!mapReady) return
      if (Date.now() < suppressViewportFetchUntil) return
      runSearch({ useViewport: true }).catch(() => {})
    }, 180)
  })
}

function initMap() {
  map = new maplibregl.Map({
    container: mapEl.value,
    style: createRasterStyle(),
    center: [10, 20],
    zoom: 2,
  })

  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right')

  map.on('load', () => {
    map.addSource('places', {
      type: 'geojson',
      data: featureCollection(),
      cluster: true,
      clusterMaxZoom: 13,
      clusterRadius: 48,
    })
    map.addLayer({
      id: 'places-clusters',
      type: 'circle',
      source: 'places',
      filter: ['has', 'point_count'],
      paint: {
        'circle-color': [
          'step',
          ['get', 'point_count'],
          '#d7ebe7',
          20,
          '#0f5c52',
          80,
          '#c86f31',
        ],
        'circle-radius': ['step', ['get', 'point_count'], 18, 20, 24, 80, 30],
        'circle-stroke-color': '#fff',
        'circle-stroke-width': 2,
      },
    })
    map.addLayer({
      id: 'places-cluster-count',
      type: 'symbol',
      source: 'places',
      filter: ['has', 'point_count'],
      layout: {
        'text-field': ['get', 'point_count_abbreviated'],
        'text-size': 12,
        'text-font': ['Open Sans Bold', 'Arial Unicode MS Bold'],
      },
      paint: {
        'text-color': '#f8f6f1',
      },
    })
    map.addLayer({
      id: 'places-points',
      type: 'circle',
      source: 'places',
      filter: ['!', ['has', 'point_count']],
      paint: {
        'circle-color': ['coalesce', ['get', 'color'], '#5f6d69'],
        'circle-radius': 7,
        'circle-stroke-color': '#fff',
        'circle-stroke-width': 2,
      },
    })

    map.addSource('route-line', {
      type: 'geojson',
      data: featureCollection(),
    })
    map.addLayer({
      id: 'route-line-layer',
      type: 'line',
      source: 'route-line',
      paint: {
        'line-color': '#0f5c52',
        'line-width': 3,
        'line-dasharray': [2, 2],
        'line-opacity': 0.75,
      },
    })

    map.addSource('route-cities', {
      type: 'geojson',
      data: featureCollection(),
    })
    map.addLayer({
      id: 'route-cities-points',
      type: 'circle',
      source: 'route-cities',
      paint: {
        'circle-color': '#f8f6f1',
        'circle-radius': 8,
        'circle-stroke-color': '#0f5c52',
        'circle-stroke-width': 3,
      },
    })
    map.addLayer({
      id: 'route-cities-labels',
      type: 'symbol',
      source: 'route-cities',
      layout: {
        'text-field': ['get', 'label'],
        'text-size': 11,
        'text-offset': [0, 1.6],
        'text-anchor': 'top',
      },
      paint: {
        'text-color': '#1f2b2a',
        'text-halo-color': '#fff9f0',
        'text-halo-width': 1.2,
      },
    })

    map.addSource('user-location', {
      type: 'geojson',
      data: featureCollection(),
    })
    map.addLayer({
      id: 'user-location-point',
      type: 'circle',
      source: 'user-location',
      paint: {
        'circle-color': '#0f5c52',
        'circle-radius': 7,
        'circle-stroke-color': '#ffffff',
        'circle-stroke-width': 3,
      },
    })

    attachMapEvents()
    mapReady = true
    syncMapSources()
    if (selectedTripId.value) {
      maybeFitRouteToMap()
    } else {
      maybeFitPlacesToMap()
    }
  })
}

function destroyMap() {
  activePopup?.remove()
  activePopup = null
  clearTimeout(viewportTimer)
  if (map) map.remove()
  map = null
  mapReady = false
}

function focusOnMap(place) {
  if (!map) return
  map.easeTo({
    center: [place.lon, place.lat],
    zoom: 14.5,
    duration: 600,
  })
  openPlacePopup(place)
}

watch(places, () => {
  syncMapSources()
  if (mapReady && !selectedTripId.value) {
    maybeFitPlacesToMap()
  }
}, { deep: true })

watch(tripOverview, () => {
  syncMapSources()
  if (mapReady && selectedTripId.value) {
    maybeFitRouteToMap()
  }
}, { deep: true })

onMounted(() => {
  adminStore.fetchImports().catch(() => {})
  initMap()
  if (selectedTripId.value) {
    tripsStore.fetchTripOverview(selectedTripId.value).catch(() => {})
  }
})

onUnmounted(() => {
  destroyMap()
})

function runSearch(options = {}) {
  const tagStr = [...activeTagFilters].join(',')
  const bbox =
    options.useViewport && mapReady && map
      ? boundsToBboxString(map.getBounds())
      : ''
  return placesStore.fetchPlaces(
    searchQuery.value,
    placeType.value,
    tagStr,
    selectedTripId.value,
    selectedRegion.value,
    bbox
  )
}

function applyPreset(preset) {
  searchQuery.value = preset.query
  placeType.value = preset.placeType
  activeTagFilters.clear()
  for (const tag of preset.tags || []) {
    activeTagFilters.add(tag)
  }
  runSearch({ useViewport: true }).catch(() => {})
}

function applyTripCity(city) {
  searchQuery.value = city.name
  const exactRegion = city.country ? `${city.name}, ${city.country}` : city.name
  selectedRegion.value = importedRegions.value.includes(exactRegion) ? exactRegion : ''
  if (city.lat !== null && city.lon !== null) {
    map?.easeTo({
      center: [city.lon, city.lat],
      zoom: 11.5,
      duration: 600,
    })
  }
  runSearch({ useViewport: true }).catch(() => {})
}

function onScopeChange() {
  importFeedback.value = ''
  tripsStore.setActiveTrip(selectedTripId.value)
  if (selectedTripId.value) {
    tripsStore.fetchTripOverview(selectedTripId.value).catch(() => {})
  }
  runSearch({ useViewport: true }).catch(() => {})
}

function toggleTagFilter(key) {
  if (activeTagFilters.has(key)) {
    activeTagFilters.delete(key)
  } else {
    activeTagFilters.add(key)
  }
  runSearch({ useViewport: true }).catch(() => {})
}

async function onSearch() {
  importFeedback.value = ''
  tripsStore.setActiveTrip(selectedTripId.value)
  await runSearch({ useViewport: true })
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
        suppressViewportFetchUntil = Date.now() + 2200
        map?.easeTo({
          center: [coords.longitude, coords.latitude],
          zoom: 13.5,
          duration: 700,
        })
        setSourceData(
          'user-location',
          featureCollection([
            {
              type: 'Feature',
              geometry: {
                type: 'Point',
                coordinates: [coords.longitude, coords.latitude],
              },
              properties: {},
            },
          ])
        )
        activePopup?.remove()
        activePopup = new maplibregl.Popup({ closeButton: false, offset: 12 })
          .setLngLat([coords.longitude, coords.latitude])
          .setHTML('<strong>You are here</strong>')
          .addTo(map)

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
      await runSearch({ useViewport: true })
    }
  } catch (error) {
    importFeedback.value = `Import failed: ${error.message}`
  } finally {
    importing.value = false
  }
}

async function onPrepRoute() {
  if (!selectedTripId.value || routePrepLoading.value) return
  routePrepLoading.value = true
  importFeedback.value = 'Queueing route prep imports...'
  try {
    const payload = await tripsStore.queueCoverageImports(selectedTripId.value, [], 'auto')
    await tripsStore.fetchTripOverview(selectedTripId.value).catch(() => {})
    await adminStore.fetchImports().catch(() => {})
    importFeedback.value = payload?.message || 'Route prep imports queued.'
  } catch (error) {
    importFeedback.value = error.message || 'Route prep failed'
  } finally {
    routePrepLoading.value = false
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
