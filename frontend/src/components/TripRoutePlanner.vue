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

        <p class="muted">{{ summarizePlaceTypes(city.place_type_counts) }}</p>

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
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import L from 'leaflet'

const props = defineProps({
  overview: {
    type: Object,
    required: true,
  },
})

const mapEl = ref(null)
const routeCities = computed(() =>
  (props.overview?.cities || []).filter((city) => city.lat !== null && city.lon !== null)
)
const assignedPlaces = computed(() =>
  (props.overview?.cities || []).flatMap((city) => city.places || [])
)

let map = null
let layerGroup = null

function humanizeStatus(status) {
  if (status === 'want_to_visit') return 'want to visit'
  return status.replace(/_/g, ' ')
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
