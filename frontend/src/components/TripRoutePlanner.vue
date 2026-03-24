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
          v-if="overview.coverage_summary?.needs_import || overview.coverage_summary?.refresh_recommended"
          class="action-button"
          type="button"
          :disabled="queueingAllImports || isRouteImporting"
          @click="queueMissingImports"
        >
          {{ queueingAllImports ? 'Queueing imports...' : 'Prep weak stops' }}
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
        <span v-if="overview.coverage_summary?.core_gap_cities" class="chip">
          {{ overview.coverage_summary.core_gap_cities }} core gaps
        </span>
        <span v-if="overview.coverage_summary?.refresh_recommended" class="chip">
          {{ overview.coverage_summary.refresh_recommended }} refresh suggested
        </span>
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
              v-if="city.coverage.needs_import || city.coverage.refresh_recommended"
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
                      : city.coverage.refresh_recommended
                        ? 'Refresh city'
                        : 'Import city'
              }}
            </button>
          </div>
          <div class="chip-row">
            <span class="chip">{{ city.coverage.level }}</span>
            <span class="chip">{{ city.coverage.local_place_count }} local places</span>
            <span class="chip">{{ city.coverage.nearby_place_count }} nearby</span>
            <span
              v-for="dimension in city.coverage.missing_core_dimensions"
              :key="`${city.id}-${dimension}`"
              class="chip"
            >
              missing {{ dimension }}
            </span>
            <span v-if="city.coverage.refresh_recommended" class="chip">refresh suggested</span>
            <span v-if="city.coverage.active_import_status" class="chip">
              {{ city.coverage.active_import_status }}
            </span>
          </div>
          <p v-if="coreCoverageLine(city.coverage)" class="muted">
            {{ coreCoverageLine(city.coverage) }}
          </p>
          <p v-if="city.coverage.active_import_created_at" class="muted">
            Import {{ city.coverage.active_import_status }} since {{ formatTimestamp(city.coverage.active_import_created_at) }}
          </p>
          <p v-if="city.coverage.last_imported_at" class="muted">
            Last imported {{ formatTimestamp(city.coverage.last_imported_at) }}
            <template v-if="city.coverage.last_import_age_days !== null">
              · {{ city.coverage.last_import_age_days }} day<span v-if="city.coverage.last_import_age_days !== 1">s</span> ago
            </template>
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
import { useSavedStore } from '../stores/saved.js'
import { useTripsStore } from '../stores/trips.js'
import {
  cityToFeature,
  createRasterStyle,
  escapeHtml,
  featureCollection,
  fitMapToCoordinates,
  maplibregl,
  routeLineFeature,
} from '../utils/maplibre.js'

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
      return 'Every stop has usable local coverage, core trip categories, and fresh-enough imports.'
    case 'importing':
      return `${summary.queued_imports + summary.running_imports} stop import(s) are queued or running right now.`
    case 'partial':
      if (summary.core_gap_cities || summary.refresh_recommended) {
        return `${summary.core_gap_cities} stop(s) still miss route basics and ${summary.refresh_recommended} stop(s) would benefit from a refresh before departure.`
      }
      if (summary.unmapped_cities) {
        return `${summary.unmapped_cities} stop(s) still need map coordinates, and ${summary.thin + summary.missing} stop(s) need stronger local coverage.`
      }
      return `${summary.thin + summary.missing} stop(s) still need stronger local coverage before departure.`
    default:
      if (summary.unmapped_cities) {
        return `${summary.unmapped_cities} stop(s) still need map coordinates before the route can feel reliable.`
      }
      return 'Queue the missing stops so the trip works more reliably on the road.'
  }
})

let map = null
let mapReady = false
let activePopup = null

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
  map.easeTo({
    center: [lon, lat],
    zoom,
    duration: 550,
  })
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

function coreCoverageLine(coverage) {
  if (!coverage) return ''
  const parts = []
  const labels = Object.entries(coverage.core_dimensions || {})
    .map(([dimension, count]) => `${dimension} ${count}`)
  if (labels.length) {
    parts.push(`Core coverage: ${labels.join(' · ')}`)
  }
  if (coverage.stale_import) {
    parts.push('Import snapshot is getting stale')
  }
  return parts.join('. ')
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
  coverageFeedback.value = 'Queueing weak or stale city imports...'
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

function setSourceData(sourceId, data) {
  const source = map?.getSource(sourceId)
  if (source) {
    source.setData(data)
  }
}

function buildPlannerPopup(title, subtitle) {
  return `
    <div class="map-popup">
      <strong>${escapeHtml(title)}</strong>
      ${subtitle ? `<div class="map-popup__meta">${escapeHtml(subtitle)}</div>` : ''}
    </div>
  `
}

function plannerPointFeature(place, color, subtitle) {
  return {
    type: 'Feature',
    geometry: {
      type: 'Point',
      coordinates: [place.lon, place.lat],
    },
    properties: {
      id: place.saved_place_id || place.place_id,
      name: place.name,
      subtitle,
      color,
    },
  }
}

function syncPlannerSources() {
  if (!mapReady) return

  const routeCitiesFeatures = routeCities.value
    .map((city) => cityToFeature(city))
    .filter(Boolean)
  setSourceData('planner-route-cities', featureCollection(routeCitiesFeatures))

  const routeFeature = routeLineFeature(props.overview?.cities || [])
  setSourceData('planner-route-line', featureCollection(routeFeature ? [routeFeature] : []))

  setSourceData(
    'planner-assigned-places',
    featureCollection(
      assignedPlaces.value.map((place) =>
        plannerPointFeature(place, placeColor(place.status), `${place.city_name || 'Assigned'} · ${humanizeStatus(place.status)}`)
      )
    )
  )

  setSourceData(
    'planner-unassigned-places',
    featureCollection(
      (props.overview?.unassigned_places || []).map((place) =>
        plannerPointFeature(place, '#8f7c6a', 'Unassigned trip save')
      )
    )
  )
}

function attachPlannerMapEvents() {
  const hoverLayers = [
    'planner-route-cities-layer',
    'planner-assigned-places-layer',
    'planner-unassigned-places-layer',
  ]
  for (const layerId of hoverLayers) {
    map.on('mouseenter', layerId, () => {
      map.getCanvas().style.cursor = 'pointer'
    })
    map.on('mouseleave', layerId, () => {
      map.getCanvas().style.cursor = ''
    })
  }

  for (const layerId of hoverLayers) {
    map.on('click', layerId, (event) => {
      const feature = event.features?.[0]
      if (!feature) return
      const coordinates = feature.geometry.coordinates.slice()
      activePopup?.remove()
      activePopup = new maplibregl.Popup({ closeButton: false, offset: 12 })
        .setLngLat(coordinates)
        .setHTML(buildPlannerPopup(feature.properties.name, feature.properties.subtitle))
        .addTo(map)
    })
  }
}

async function renderMap() {
  await nextTick()
  if (!mapEl.value) return

  if (!map) {
    map = new maplibregl.Map({
      container: mapEl.value,
      style: createRasterStyle(),
      center: [10, 20],
      zoom: 2,
    })
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right')
    map.on('load', () => {
      map.addSource('planner-route-line', {
        type: 'geojson',
        data: featureCollection(),
      })
      map.addLayer({
        id: 'planner-route-line-layer',
        type: 'line',
        source: 'planner-route-line',
        paint: {
          'line-color': '#0f5c52',
          'line-width': 3,
          'line-dasharray': [2, 2],
          'line-opacity': 0.8,
        },
      })

      map.addSource('planner-route-cities', {
        type: 'geojson',
        data: featureCollection(),
      })
      map.addLayer({
        id: 'planner-route-cities-layer',
        type: 'circle',
        source: 'planner-route-cities',
        paint: {
          'circle-color': '#d7ebe7',
          'circle-radius': 8,
          'circle-stroke-color': '#0f5c52',
          'circle-stroke-width': 3,
        },
      })
      map.addLayer({
        id: 'planner-route-cities-labels',
        type: 'symbol',
        source: 'planner-route-cities',
        layout: {
          'text-field': ['get', 'label'],
          'text-size': 11,
          'text-offset': [0, 1.5],
          'text-anchor': 'top',
        },
        paint: {
          'text-color': '#1f2b2a',
          'text-halo-color': '#fff9f0',
          'text-halo-width': 1.2,
        },
      })

      map.addSource('planner-assigned-places', {
        type: 'geojson',
        data: featureCollection(),
      })
      map.addLayer({
        id: 'planner-assigned-places-layer',
        type: 'circle',
        source: 'planner-assigned-places',
        paint: {
          'circle-color': ['coalesce', ['get', 'color'], '#5b4a8a'],
          'circle-radius': 6,
          'circle-stroke-color': '#ffffff',
          'circle-stroke-width': 1.5,
        },
      })

      map.addSource('planner-unassigned-places', {
        type: 'geojson',
        data: featureCollection(),
      })
      map.addLayer({
        id: 'planner-unassigned-places-layer',
        type: 'circle',
        source: 'planner-unassigned-places',
        paint: {
          'circle-color': '#8f7c6a',
          'circle-radius': 5,
          'circle-stroke-color': '#ffffff',
          'circle-stroke-width': 1.2,
        },
      })

      attachPlannerMapEvents()
      mapReady = true
      syncPlannerSources()
      renderMap().catch(() => {})
    })
  }

  if (!mapReady) return

  syncPlannerSources()

  const coordinates = [
    ...routeCities.value.map((city) => [city.lon, city.lat]),
    ...assignedPlaces.value.map((place) => [place.lon, place.lat]),
    ...(props.overview?.unassigned_places || []).map((place) => [place.lon, place.lat]),
  ]

  if (coordinates.length) {
    fitMapToCoordinates(map, coordinates, { maxZoom: 13, padding: 34 })
  } else {
    map.easeTo({ center: [10, 20], zoom: 2, duration: 400 })
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
  activePopup?.remove()
  activePopup = null
  map?.remove()
  map = null
  mapReady = false
})
</script>
