<template>
  <section class="trip-planner">
    <div class="stack-between stack-between--tight">
      <div>
        <p class="card-eyebrow">Trip planner</p>
        <h4>See the route and what is already attached to each city.</h4>
      </div>
      <p class="muted">
        {{ routeCities.length }} mapped cities · {{ assignedPlaces.length }} assigned places
      </p>
    </div>

    <div v-if="overview.route_highlights?.length" class="route-overview-list">
      <span v-for="highlight in overview.route_highlights" :key="highlight" class="fact-pill">
        {{ highlight }}
      </span>
    </div>

    <section class="coverage-summary-card">
      <div class="stack-between stack-between--tight">
        <div>
          <p class="card-eyebrow">Offline trip coverage</p>
          <p class="muted">
            Make sure each stop has enough cached places before the trip starts.
          </p>
        </div>
        <button
          v-if="overview.coverage_summary?.needs_import"
          class="action-button"
          type="button"
          :disabled="queueingAllImports || isRouteImporting"
          @click="queueMissingImports"
        >
          {{ queueingAllImports ? 'Queueing imports...' : 'Import missing stops' }}
        </button>
      </div>
      <div class="trip-readiness-strip" :data-state="overview.coverage_summary?.route_readiness || 'needs_imports'">
        <strong>{{ routeReadinessTitle }}</strong>
        <span>{{ routeReadinessCopy }}</span>
      </div>
      <div class="chip-row">
        <span class="chip">{{ overview.coverage_summary?.ready || 0 }} ready</span>
        <span class="chip">{{ overview.coverage_summary?.usable || 0 }} usable</span>
        <span class="chip">{{ overview.coverage_summary?.thin || 0 }} thin</span>
        <span class="chip">{{ overview.coverage_summary?.missing || 0 }} missing</span>
        <span v-if="overview.coverage_summary?.queued_imports" class="chip">
          {{ overview.coverage_summary.queued_imports }} queued
        </span>
        <span v-if="overview.coverage_summary?.running_imports" class="chip">
          {{ overview.coverage_summary.running_imports }} importing
        </span>
      </div>
      <p v-if="coverageFeedback" class="feedback">{{ coverageFeedback }}</p>
    </section>

    <div ref="mapEl" class="route-map"></div>

    <div class="trip-planner-grid">
      <article
        v-for="city in overview.cities"
        :key="city.id"
        class="trip-planner-city"
      >
        <div class="stack-between stack-between--tight">
          <div>
            <p class="card-eyebrow">Stop {{ city.sort_order + 1 }}</p>
            <h4>{{ city.name }}{{ city.country ? `, ${city.country}` : '' }}</h4>
          </div>
          <button
            v-if="city.lat !== null && city.lon !== null"
            class="secondary-button action-button"
            type="button"
            @click="focusCoordinates(city.lat, city.lon, 11)"
          >
            Focus
          </button>
        </div>

        <div class="chip-row">
          <span class="chip">{{ city.saved_count }} saved</span>
          <span class="chip">{{ city.favorite_count }} favorites</span>
          <span class="chip">{{ city.want_to_visit_count }} want to visit</span>
        </div>

        <section class="city-coverage-card" :data-level="city.coverage.level">
          <div class="stack-between stack-between--tight">
            <div>
              <p class="card-eyebrow">Local data coverage</p>
              <p class="muted">{{ city.coverage.summary }}</p>
            </div>
            <button
              v-if="city.coverage.needs_import"
              class="secondary-button action-button"
              type="button"
              :disabled="queueingCityId === city.id || ['queued', 'running'].includes(city.coverage.active_import_status)"
              @click="queueCityImport(city)"
            >
              {{
                queueingCityId === city.id
                  ? 'Queueing...'
                  : city.coverage.active_import_status === 'running'
                    ? 'Import running'
                    : city.coverage.active_import_status === 'queued'
                      ? 'Import queued'
                      : 'Import city'
              }}
            </button>
          </div>
          <div class="chip-row">
            <span class="chip">{{ city.coverage.level }}</span>
            <span class="chip">{{ city.coverage.local_place_count }} local places</span>
            <span class="chip">{{ city.coverage.nearby_place_count }} nearby</span>
            <span v-if="city.coverage.active_import_status" class="chip">
              {{ city.coverage.active_import_status }}
            </span>
          </div>
          <p v-if="city.coverage.active_import_created_at" class="muted">
            Import {{ city.coverage.active_import_status }} since {{ formatTimestamp(city.coverage.active_import_created_at) }}
          </p>
          <p v-if="city.coverage.last_imported_at" class="muted">
            Last imported {{ formatTimestamp(city.coverage.last_imported_at) }}
          </p>
        </section>

        <p class="muted">{{ summarizePlaceTypes(city.place_type_counts) }}</p>

        <div v-if="city.highlights?.length" class="route-highlights">
          <span v-for="highlight in city.highlights" :key="highlight" class="fact-pill">{{ highlight }}</span>
        </div>

        <form class="route-city-notes" @submit.prevent="saveCityNotes(city)">
          <label class="map-filter-field">
            <span class="card-eyebrow">City notes</span>
            <textarea
              v-model="cityNoteDrafts[city.id]"
              placeholder="Why this stop matters, what to book, what to remember..."
            ></textarea>
          </label>
          <button class="secondary-button action-button" type="submit">Save notes</button>
          <p v-if="cityFeedback[city.id]" class="feedback">{{ cityFeedback[city.id] }}</p>
        </form>

        <div v-if="city.places.length" class="route-place-list">
          <button
            v-for="place in city.places"
            :key="place.saved_place_id"
            class="route-place-button"
            type="button"
            @click="focusCoordinates(place.lat, place.lon, 14)"
          >
            <strong>{{ place.name }}</strong>
            <span class="muted">{{ place.place_type }} · {{ humanizeStatus(place.status) }}</span>
            <span v-if="place.notes" class="muted">{{ place.notes }}</span>
          </button>
        </div>
        <p v-else class="muted">No saved places assigned to this city yet.</p>

        <div v-if="city.suggested_unassigned_places?.length" class="route-suggestions">
          <p class="card-eyebrow">Suggested from unassigned</p>
          <div class="route-place-list">
            <article
              v-for="place in city.suggested_unassigned_places"
              :key="place.saved_place_id"
              class="route-place-button route-place-button--static"
            >
              <strong>{{ place.name }}</strong>
              <span class="muted">
                {{ place.place_type }} · {{ humanizeStatus(place.status) }} · score {{ place.suggestion_score }}
              </span>
              <span v-if="place.notes" class="muted">{{ place.notes }}</span>
              <button
                class="secondary-button action-button"
                type="button"
                :disabled="assigningPlaceId === place.saved_place_id"
                @click="assignSuggestedPlace(city, place)"
              >
                {{ assigningPlaceId === place.saved_place_id ? 'Assigning...' : `Assign to ${city.name}` }}
              </button>
            </article>
          </div>
        </div>

        <div v-if="city.discovery_candidates?.length" class="route-suggestions">
          <p class="card-eyebrow">Good next discoveries</p>
          <div class="route-place-list">
            <article
              v-for="place in city.discovery_candidates"
              :key="place.place_id"
              class="route-place-button route-place-button--static"
            >
              <strong>{{ place.name }}</strong>
              <span class="muted">
                {{ place.place_type }}
                <template v-if="place.distance_km !== null"> · {{ place.distance_km }} km away</template>
              </span>
              <span class="muted">{{ place.reason }}</span>
              <span v-if="place.description" class="muted">{{ place.description }}</span>
              <div class="trip-actions">
                <button
                  class="secondary-button action-button"
                  type="button"
                  @click="focusCoordinates(place.lat, place.lon, 14)"
                >
                  Focus
                </button>
                <button
                  class="action-button"
                  type="button"
                  :disabled="savingDiscoveryId === place.place_id"
                  @click="saveDiscoveryPlace(city, place)"
                >
                  {{ savingDiscoveryId === place.place_id ? 'Saving...' : `Save to ${city.name}` }}
                </button>
              </div>
            </article>
          </div>
        </div>
      </article>

      <article v-if="overview.unassigned_places.length" class="trip-planner-city trip-planner-city--muted">
        <div>
          <p class="card-eyebrow">Still unassigned</p>
          <h4>{{ overview.unassigned_places.length }} trip saves need a city</h4>
        </div>
        <div class="route-place-list">
          <button
            v-for="place in overview.unassigned_places"
            :key="place.saved_place_id"
            class="route-place-button"
            type="button"
            @click="focusCoordinates(place.lat, place.lon, 13)"
          >
            <strong>{{ place.name }}</strong>
            <span class="muted">{{ place.place_type }} · {{ humanizeStatus(place.status) }}</span>
            <span v-if="place.notes" class="muted">{{ place.notes }}</span>
          </button>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import L from 'leaflet'
import { useSavedStore } from '../stores/saved.js'
import { useTripsStore } from '../stores/trips.js'

const props = defineProps({
  overview: {
    type: Object,
    required: true,
  },
})

const savedStore = useSavedStore()
const tripsStore = useTripsStore()
const mapEl = ref(null)
const assigningPlaceId = ref('')
const savingDiscoveryId = ref('')
const queueingCityId = ref('')
const queueingAllImports = ref(false)
const coverageFeedback = ref('')
const cityNoteDrafts = reactive({})
const cityFeedback = reactive({})
const routeCities = computed(() =>
  (props.overview?.cities || []).filter((city) => city.lat !== null && city.lon !== null)
)
const assignedPlaces = computed(() =>
  (props.overview?.cities || []).flatMap((city) => city.places || [])
)
const isRouteImporting = computed(() => {
  const summary = props.overview?.coverage_summary
  return Boolean((summary?.queued_imports || 0) + (summary?.running_imports || 0))
})
const routeReadinessTitle = computed(() => {
  switch (props.overview?.coverage_summary?.route_readiness) {
    case 'ready':
      return 'Route looks road-ready.'
    case 'importing':
      return 'Route prep is still importing.'
    case 'partial':
      return 'Route is usable, but still uneven.'
    default:
      return 'Route still needs local data.'
  }
})
const routeReadinessCopy = computed(() => {
  const summary = props.overview?.coverage_summary
  if (!summary) return ''
  switch (summary.route_readiness) {
    case 'ready':
      return 'Every stop has at least usable local coverage already cached.'
    case 'importing':
      return `${summary.queued_imports + summary.running_imports} stop import(s) are queued or running right now.`
    case 'partial':
      return `${summary.thin + summary.missing} stop(s) still need stronger local coverage before departure.`
    default:
      return 'Queue the missing stops so the trip works more reliably on the road.'
  }
})

let map = null
let layerGroup = null

watch(
  () => props.overview?.cities || [],
  (cities) => {
    for (const city of cities) {
      cityNoteDrafts[city.id] = city.notes || ''
      if (!(city.id in cityFeedback)) {
        cityFeedback[city.id] = ''
      }
    }
  },
  { immediate: true, deep: true }
)

function humanizeStatus(status) {
  if (status === 'want_to_visit') return 'want to visit'
  return status.replace(/_/g, ' ')
}

function formatTimestamp(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function summarizePlaceTypes(placeTypeCounts) {
  const entries = Object.entries(placeTypeCounts || {})
  if (!entries.length) return 'No city-specific places yet.'
  return entries
    .sort((a, b) => b[1] - a[1])
    .slice(0, 4)
    .map(([type, count]) => `${type} ${count}`)
    .join(' · ')
}

function focusCoordinates(lat, lon, zoom = 13) {
  if (!map || lat === null || lon === null) return
  map.setView([lat, lon], zoom, { animate: true })
}

function placeColor(status) {
  if (status === 'favorite') return '#c86f31'
  if (status === 'visited') return '#0f5c52'
  return '#5b4a8a'
}

async function saveCityNotes(city) {
  cityFeedback[city.id] = 'Saving notes...'
  try {
    await tripsStore.updateCity(props.overview.trip_id, city.id, {
      notes: cityNoteDrafts[city.id] || null,
    })
    cityFeedback[city.id] = 'Notes saved.'
  } catch (error) {
    cityFeedback[city.id] = error.message || 'Save failed'
  }
}

async function assignSuggestedPlace(city, place) {
  assigningPlaceId.value = place.saved_place_id
  try {
    await savedStore.updateSaved(place.saved_place_id, { city_id: city.id })
    await tripsStore.fetchTripOverview(props.overview.trip_id)
  } finally {
    assigningPlaceId.value = ''
  }
}

async function saveDiscoveryPlace(city, place) {
  savingDiscoveryId.value = place.place_id
  try {
    await savedStore.savePlace(place.place_id, 'want_to_visit', null, props.overview.trip_id, city.id)
    await tripsStore.fetchTripOverview(props.overview.trip_id)
  } finally {
    savingDiscoveryId.value = ''
  }
}

async function queueMissingImports() {
  queueingAllImports.value = true
  coverageFeedback.value = 'Queueing missing city imports...'
  try {
    const payload = await tripsStore.queueCoverageImports(props.overview.trip_id)
    await tripsStore.fetchTripOverview(props.overview.trip_id)
    coverageFeedback.value = buildCoverageFeedback(payload)
  } catch (error) {
    coverageFeedback.value = error.message || 'Import queue failed'
  } finally {
    queueingAllImports.value = false
  }
}

async function queueCityImport(city) {
  queueingCityId.value = city.id
  coverageFeedback.value = `Queueing import for ${city.name}...`
  try {
    const payload = await tripsStore.queueCoverageImports(props.overview.trip_id, [city.id])
    await tripsStore.fetchTripOverview(props.overview.trip_id)
    coverageFeedback.value = buildCoverageFeedback(payload)
  } catch (error) {
    coverageFeedback.value = error.message || 'Import queue failed'
  } finally {
    queueingCityId.value = ''
  }
}

function buildCoverageFeedback(payload) {
  const queuedCount = payload?.queued_count || 0
  const reusedCount = payload?.reused_count || 0
  if (!queuedCount && !reusedCount) return payload?.message || 'No imports were queued.'
  if (queuedCount && reusedCount) {
    return `${queuedCount} import job(s) queued and ${reusedCount} existing job(s) reused.`
  }
  if (queuedCount) return `${queuedCount} import job(s) queued.`
  return `${reusedCount} existing import job(s) already running.`
}

async function renderMap() {
  await nextTick()
  if (!mapEl.value) return

  if (!map) {
    map = L.map(mapEl.value, { zoomControl: true, scrollWheelZoom: false }).setView([20, 10], 2)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(map)
    layerGroup = L.layerGroup().addTo(map)
  }

  layerGroup.clearLayers()
  const boundsPoints = []

  if (routeCities.value.length > 1) {
    const path = routeCities.value.map((city) => [city.lat, city.lon])
    L.polyline(path, {
      color: '#0f5c52',
      weight: 3,
      opacity: 0.8,
      dashArray: '6 8',
    }).addTo(layerGroup)
    boundsPoints.push(...path)
  }

  for (const city of routeCities.value) {
    const marker = L.circleMarker([city.lat, city.lon], {
      radius: 8,
      color: '#0f5c52',
      weight: 2,
      fillColor: '#d7ebe7',
      fillOpacity: 0.95,
    }).addTo(layerGroup)
    marker.bindPopup(`<strong>${city.sort_order + 1}. ${city.name}</strong>`)
    boundsPoints.push([city.lat, city.lon])
  }

  for (const place of assignedPlaces.value) {
    const marker = L.circleMarker([place.lat, place.lon], {
      radius: 6,
      color: '#fff',
      weight: 1.5,
      fillColor: placeColor(place.status),
      fillOpacity: 0.95,
    }).addTo(layerGroup)
    marker.bindPopup(
      `<strong>${place.name}</strong><br><span style="color:#5f6d69">${place.city_name || 'Unassigned'} · ${humanizeStatus(place.status)}</span>`
    )
    boundsPoints.push([place.lat, place.lon])
  }

  for (const place of props.overview?.unassigned_places || []) {
    const marker = L.circleMarker([place.lat, place.lon], {
      radius: 5,
      color: '#fff',
      weight: 1.2,
      fillColor: '#8f7c6a',
      fillOpacity: 0.85,
    }).addTo(layerGroup)
    marker.bindPopup(
      `<strong>${place.name}</strong><br><span style="color:#5f6d69">Unassigned trip save</span>`
    )
    boundsPoints.push([place.lat, place.lon])
  }

  if (boundsPoints.length) {
    map.fitBounds(boundsPoints, { padding: [28, 28] })
  } else {
    map.setView([20, 10], 2)
  }
}

watch(
  () => props.overview,
  () => {
    renderMap().catch(() => {})
  },
  { deep: true, immediate: true }
)

onMounted(() => {
  renderMap().catch(() => {})
})

onUnmounted(() => {
  map?.remove()
  map = null
  layerGroup = null
})
</script>
