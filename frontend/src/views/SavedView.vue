<template>
  <div class="panel active" style="display:grid">
    <article class="info-card wide-card">
      <div class="stack-between">
        <div>
          <p class="card-eyebrow">Saved places</p>
          <h3>Global shortlist or trip-specific shortlist.</h3>
          <p>Save from the map into one trip, or keep a place in your general travel database.</p>
        </div>

        <div class="tracking-scope">
          <label class="card-eyebrow" for="saved-scope-select">Scope</label>
          <select id="saved-scope-select" v-model="selectedScope">
            <option value="all">All saved places</option>
            <option value="global">Global shortlist only</option>
            <option v-for="trip in trips" :key="trip.id" :value="`trip:${trip.id}`">
              {{ trip.name }}
            </option>
          </select>
          <label v-if="selectedTripScopeId" class="participant-option">
            <input v-model="includeGlobalWithTrip" type="checkbox">
            <span>Include global shortlist</span>
          </label>
        </div>
      </div>

      <section v-if="shortlists.length" class="tracking-sections">
        <article v-for="list in shortlists" :key="list.title" class="summary-item">
          <strong>{{ list.title }}</strong>
          <span class="muted">{{ list.count }} places</span>
          <span class="muted">{{ list.preview }}</span>
        </article>
      </section>

      <div class="saved-sections">
        <p v-if="loading" class="empty-state">Loading...</p>
        <p v-else-if="!filteredSaved.length" class="empty-state">No saved places yet for this scope.</p>

        <section v-for="section in groupedSaved" :key="section.status" class="saved-section">
          <div class="stack-between stack-between--tight">
            <div>
              <p class="card-eyebrow">{{ section.label }}</p>
              <h4>{{ section.items.length }} places</h4>
            </div>
          </div>

          <div class="saved-grid">
            <article v-for="s in section.items" :key="s.id" class="saved-card">
              <div>
                <p class="card-eyebrow">
                  {{ s.trip_name ? `Trip · ${s.trip_name}` : 'Global shortlist' }}
                </p>
                <h4>{{ s.place.name }}</h4>
                <p class="muted">{{ s.place.region || 'unknown' }} · {{ s.place.place_type }}</p>
              </div>
              <p>{{ s.notes || s.place.description || 'No notes yet.' }}</p>
              <div class="chip-row">
                <span class="chip">{{ s.place.place_type }}</span>
                <span class="chip">{{ s.place.source }}</span>
                <span v-if="s.trip_name" class="chip chip--tag">{{ s.trip_name }}</span>
              </div>
              <button
                class="unsave-button"
                :disabled="removing === s.id"
                @click="onRemove(s.id)"
              >{{ removing === s.id ? 'Removing...' : 'Remove' }}</button>
            </article>
          </div>
        </section>
      </div>
    </article>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useSavedStore } from '../stores/saved.js'
import { useTripsStore } from '../stores/trips.js'

const savedStore = useSavedStore()
const tripsStore = useTripsStore()
const saved = computed(() => savedStore.savedPlaces)
const loading = computed(() => savedStore.loading)
const trips = computed(() => tripsStore.trips)
const removing = ref(null)
const selectedScope = ref(tripsStore.activeTripId ? `trip:${tripsStore.activeTripId}` : 'all')
const includeGlobalWithTrip = ref(true)

const selectedTripScopeId = computed(() => {
  if (!selectedScope.value.startsWith('trip:')) return ''
  return selectedScope.value.slice(5)
})

const filteredSaved = computed(() => {
  if (selectedScope.value === 'global') {
    return saved.value.filter((item) => !item.trip_id)
  }
  return saved.value
})

const groupedSaved = computed(() => {
  const order = [
    ['favorite', 'Favorites'],
    ['want_to_visit', 'Want to visit'],
    ['visited', 'Visited'],
  ]

  return order
    .map(([status, label]) => ({
      status,
      label,
      items: filteredSaved.value.filter((item) => item.status === status),
    }))
    .filter((section) => section.items.length)
})

const shortlists = computed(() => {
  const collections = [
    {
      title: 'Food and coffee',
      items: filteredSaved.value.filter((item) => ['restaurant', 'cafe'].includes(item.place.place_type)),
    },
    {
      title: 'Nature',
      items: filteredSaved.value.filter((item) => ['park', 'hiking', 'viewpoint'].includes(item.place.place_type)),
    },
    {
      title: 'Culture and sights',
      items: filteredSaved.value.filter((item) => ['cultural', 'attraction'].includes(item.place.place_type)),
    },
    {
      title: 'Backup options',
      items: filteredSaved.value.filter((item) => item.status === 'want_to_visit'),
    },
  ]

  return collections
    .filter((collection) => collection.items.length)
    .map((collection) => ({
      title: collection.title,
      count: collection.items.length,
      preview: collection.items.slice(0, 3).map((item) => item.place.name).join(' · '),
    }))
})

watch(
  [selectedScope, includeGlobalWithTrip],
  async () => {
    if (selectedScope.value === 'all' || selectedScope.value === 'global') {
      await savedStore.fetchSaved()
      return
    }
    await savedStore.fetchSaved(selectedTripScopeId.value, includeGlobalWithTrip.value)
  },
  { immediate: true }
)

async function onRemove(id) {
  removing.value = id
  try {
    await savedStore.deleteSaved(id)
  } finally {
    removing.value = null
  }
}
</script>
