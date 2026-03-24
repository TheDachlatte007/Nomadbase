<template>
  <div class="panel active" style="display:grid">
    <article class="info-card wide-card">
      <div class="stack-between">
        <div>
          <p class="card-eyebrow">Trips</p>
          <h3>Organize places, people, and money around one trip context.</h3>
          <p>
            Cities scope your map exploration. Participants turn that trip into a
            shared expense space with clear settlements.
          </p>
        </div>
        <form class="trip-form" @submit.prevent="onCreate">
          <input v-model="form.name" type="text" placeholder="Trip name" required>
          <input v-model="form.start_date" type="date">
          <input v-model="form.end_date" type="date">
          <textarea v-model="form.notes" placeholder="Notes for this trip"></textarea>
          <button class="action-button" type="submit" :disabled="creating">
            {{ creating ? 'Creating...' : 'Create trip' }}
          </button>
          <p v-if="createFeedback" class="feedback">{{ createFeedback }}</p>
        </form>
      </div>

      <div class="trip-scope-bar">
        <div>
          <p class="card-eyebrow">Active trip</p>
          <p class="muted">
            Use one trip as the shared context for tracking balances and map work.
          </p>
        </div>
        <select :value="activeTripId" @change="onSetActiveTrip($event.target.value)">
          <option value="">All trips</option>
          <option v-for="trip in trips" :key="trip.id" :value="trip.id">
            {{ trip.name }}
          </option>
        </select>
      </div>

      <div class="trips-grid">
        <p v-if="loading" class="empty-state">Loading trips...</p>
        <p v-else-if="!trips.length" class="empty-state">
          No trips yet. Start with one itinerary and then add people to it.
        </p>

        <article
          v-for="trip in trips"
          :key="trip.id"
          class="trip-card"
          :class="{ 'trip-card--active': activeTripId === trip.id }"
        >
          <template v-if="editingId !== trip.id">
            <div>
              <p class="card-eyebrow">
                {{ trip.start_date || 'no start' }} → {{ trip.end_date || 'open end' }}
              </p>
              <h4>{{ trip.name }}</h4>
              <p class="muted">{{ trip.notes || 'No notes yet.' }}</p>
            </div>

            <div class="chip-row">
              <span class="chip">
                {{ trip.cities?.length || 0 }}
                {{ (trip.cities?.length || 0) === 1 ? 'city' : 'cities' }}
              </span>
              <span class="chip">
                {{ trip.participants?.length || 0 }}
                {{ (trip.participants?.length || 0) === 1 ? 'person' : 'people' }}
              </span>
              <span v-if="activeTripId === trip.id" class="chip chip--tag chip--active-context">
                active context
              </span>
            </div>

            <section
              v-if="activeTripId === trip.id && overview"
              class="trip-overview-card"
            >
              <div class="stack-between stack-between--tight">
                <div>
                  <p class="card-eyebrow">Route overview</p>
                  <h4>{{ overview.trip_name }}</h4>
                  <p class="muted">{{ overview.route_label }}</p>
                </div>
                <p class="muted">
                  {{ overview.total_saved_places }} trip saves ·
                  {{ overview.unassigned_saved_places }} unassigned
                </p>
              </div>

              <div class="summary-list">
                <article class="summary-item">
                  <strong>{{ overview.city_count }}</strong>
                  <span class="muted">{{ overview.city_count === 1 ? 'city in route' : 'cities in route' }}</span>
                </article>
                <article class="summary-item">
                  <strong>{{ overview.participant_count }}</strong>
                  <span class="muted">{{ overview.participant_count === 1 ? 'traveler' : 'travelers' }}</span>
                </article>
                <article class="summary-item">
                  <strong>{{ overview.assigned_saved_places }}</strong>
                  <span class="muted">saves already assigned to a city</span>
                </article>
                <article class="summary-item">
                  <strong>{{ overview.route_distance_km ? `${Math.round(overview.route_distance_km)} km` : 'n/a' }}</strong>
                  <span class="muted">mapped route distance</span>
                </article>
                <article class="summary-item">
                  <strong>{{ overview.cities_without_places }}</strong>
                  <span class="muted">stops still missing a shortlist</span>
                </article>
                <article class="summary-item">
                  <strong>{{ overview.cities_without_coordinates }}</strong>
                  <span class="muted">stops still missing map coordinates</span>
                </article>
              </div>
              <TripRoutePlanner v-if="overview.cities.length || overview.unassigned_places.length" :overview="overview" />
              <p v-else class="muted">Add cities first to build a route overview.</p>
            </section>

            <div class="trip-sections">
              <section class="trip-section">
                <div class="stack-between">
                  <div>
                    <p class="card-eyebrow">Cities</p>
                    <p class="muted">These shape what the map and import flows focus on.</p>
                  </div>
                  <button
                    class="secondary-button action-button"
                    type="button"
                    @click="openMap(trip.id)"
                  >
                    Open map
                  </button>
                </div>

                <ul class="cities-list">
                  <li v-if="!(trip.cities?.length)">No cities added yet.</li>
                  <li
                    v-for="city in trip.cities || []"
                    :key="city.id"
                    class="city-list-item"
                  >
                    <span>
                      {{ city.sort_order + 1 }}. {{ city.name }}{{ city.country ? `, ${city.country}` : '' }}
                      <span v-if="city.lat === null || city.lon === null" class="muted">· map pending</span>
                    </span>
                    <div class="city-actions">
                      <button
                        class="secondary-button action-button city-order-btn"
                        type="button"
                        :disabled="movingCity === city.id || city.sort_order === 0"
                        @click="onMoveCity(trip, city.id, -1)"
                      >
                        ↑
                      </button>
                      <button
                        class="secondary-button action-button city-order-btn"
                        type="button"
                        :disabled="movingCity === city.id || city.sort_order === (trip.cities?.length || 1) - 1"
                        @click="onMoveCity(trip, city.id, 1)"
                      >
                        ↓
                      </button>
                      <button
                        class="city-remove-btn"
                        :disabled="removingCity === city.id"
                        title="Remove city"
                        @click="onRemoveCity(trip.id, city.id)"
                      >
                        ×
                      </button>
                    </div>
                  </li>
                </ul>

                <form class="city-form" @submit.prevent="onAddCity(trip.id, $event)">
                  <div class="city-form-row">
                    <input name="name" type="text" placeholder="Add city" required>
                    <input name="country" type="text" placeholder="Country">
                  </div>
                  <button class="action-button" type="submit">Add city</button>
                  <p v-if="cityFeedback[trip.id]" class="feedback">{{ cityFeedback[trip.id] }}</p>
                </form>
              </section>

              <section class="trip-section">
                <div class="stack-between">
                  <div>
                    <p class="card-eyebrow">Participants</p>
                    <p class="muted">
                      Add everyone who shares costs so tracking can split payments cleanly.
                    </p>
                  </div>
                  <button
                    class="secondary-button action-button"
                    type="button"
                    @click="openTracking(trip.id)"
                  >
                    Open tracking
                  </button>
                </div>

                <ul class="cities-list">
                  <li v-if="!(trip.participants?.length)">No participants added yet.</li>
                  <li
                    v-for="participant in trip.participants || []"
                    :key="participant.id"
                    class="city-list-item"
                  >
                    <span>
                      {{ participant.name }}
                      <span v-if="participant.note" class="muted">· {{ participant.note }}</span>
                    </span>
                    <button
                      class="city-remove-btn"
                      :disabled="removingParticipant === participant.id"
                      title="Remove participant"
                      @click="onRemoveParticipant(trip.id, participant.id)"
                    >
                      ×
                    </button>
                  </li>
                </ul>

                <form class="city-form" @submit.prevent="onAddParticipant(trip.id, $event)">
                  <input name="name" type="text" placeholder="Add participant" required>
                  <input name="note" type="text" placeholder="Optional note, e.g. driver or roommate">
                  <button class="action-button" type="submit">Add participant</button>
                  <p v-if="participantFeedback[trip.id]" class="feedback">
                    {{ participantFeedback[trip.id] }}
                  </p>
                </form>
              </section>
            </div>

            <div class="trip-actions">
              <button class="secondary-button action-button" type="button" @click="onSetActiveTrip(trip.id)">
                {{ activeTripId === trip.id ? 'Active trip' : 'Set active trip' }}
              </button>
              <button class="secondary-button action-button" type="button" @click="startEdit(trip)">
                Edit
              </button>
              <button
                class="unsave-button"
                type="button"
                :disabled="deletingId === trip.id"
                @click="onDelete(trip.id)"
              >
                {{ deletingId === trip.id ? 'Deleting...' : 'Delete trip' }}
              </button>
            </div>
          </template>

          <template v-else>
            <p class="card-eyebrow">Editing trip</p>
            <form class="trip-form" @submit.prevent="onSaveEdit(trip.id)">
              <input v-model="editForm.name" type="text" placeholder="Trip name" required>
              <input v-model="editForm.start_date" type="date">
              <input v-model="editForm.end_date" type="date">
              <textarea v-model="editForm.notes" placeholder="Notes"></textarea>
              <div class="trip-actions">
                <button class="action-button" type="submit" :disabled="saving">
                  {{ saving ? 'Saving...' : 'Save changes' }}
                </button>
                <button
                  class="secondary-button action-button"
                  type="button"
                  @click="editingId = null"
                >
                  Cancel
                </button>
              </div>
            </form>
          </template>
        </article>
      </div>
    </article>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import TripRoutePlanner from '../components/TripRoutePlanner.vue'
import { useTripsStore } from '../stores/trips.js'

const router = useRouter()
const tripsStore = useTripsStore()
const trips = computed(() => tripsStore.trips)
const loading = computed(() => tripsStore.loading)
const activeTripId = computed(() => tripsStore.activeTripId)
const overview = computed(() => tripsStore.tripOverview)

const creating = ref(false)
const createFeedback = ref('')
const form = reactive({ name: '', start_date: '', end_date: '', notes: '' })

const cityFeedback = reactive({})
const participantFeedback = reactive({})
const removingCity = ref(null)
const movingCity = ref(null)
const removingParticipant = ref(null)
const deletingId = ref(null)
const editingId = ref(null)
const saving = ref(false)
const editForm = reactive({ name: '', start_date: '', end_date: '', notes: '' })

watch(
  activeTripId,
  async (tripId) => {
    if (!tripId) return
    await tripsStore.fetchTripOverview(tripId)
  },
  { immediate: true }
)

function onSetActiveTrip(tripId) {
  tripsStore.setActiveTrip(tripId)
}

function openTracking(tripId) {
  onSetActiveTrip(tripId)
  router.push({ name: 'tracking', query: { trip: tripId } })
}

function openMap(tripId) {
  onSetActiveTrip(tripId)
  router.push({ name: 'map', query: { trip: tripId } })
}

async function onCreate() {
  creating.value = true
  createFeedback.value = ''
  try {
    await tripsStore.createTrip({
      name: form.name,
      start_date: form.start_date || null,
      end_date: form.end_date || null,
      notes: form.notes || null,
    })
    Object.assign(form, { name: '', start_date: '', end_date: '', notes: '' })
    createFeedback.value = 'Trip created and ready for cities or participants.'
  } catch (error) {
    createFeedback.value = `Failed: ${error.message}`
  } finally {
    creating.value = false
  }
}

async function onAddCity(tripId, event) {
  const formEl = event.target
  const name = formEl.elements.name.value
  const country = formEl.elements.country.value || null

  cityFeedback[tripId] = 'Adding...'
  try {
    await tripsStore.addCity(tripId, { name, country })
    formEl.reset()
    cityFeedback[tripId] = `${name} added.`
  } catch (error) {
    cityFeedback[tripId] = error.message || 'Add failed'
  }
}

async function onRemoveCity(tripId, cityId) {
  removingCity.value = cityId
  try {
    await tripsStore.removeCity(tripId, cityId)
  } finally {
    removingCity.value = null
  }
}

async function onMoveCity(trip, cityId, direction) {
  const cities = [...(trip.cities || [])].sort((a, b) => a.sort_order - b.sort_order)
  const index = cities.findIndex((city) => city.id === cityId)
  const targetIndex = index + direction
  if (index < 0 || targetIndex < 0 || targetIndex >= cities.length) return

  const [city] = cities.splice(index, 1)
  cities.splice(targetIndex, 0, city)

  movingCity.value = cityId
  try {
    await tripsStore.reorderCities(trip.id, cities.map((item) => item.id))
  } finally {
    movingCity.value = null
  }
}

async function onAddParticipant(tripId, event) {
  const formEl = event.target
  const name = formEl.elements.name.value
  const note = formEl.elements.note.value || null

  participantFeedback[tripId] = 'Adding...'
  try {
    await tripsStore.addParticipant(tripId, { name, note })
    formEl.reset()
    participantFeedback[tripId] = `${name} added to the trip.`
  } catch (error) {
    participantFeedback[tripId] = error.message || 'Add failed'
  }
}

async function onRemoveParticipant(tripId, participantId) {
  removingParticipant.value = participantId
  try {
    await tripsStore.removeParticipant(tripId, participantId)
  } finally {
    removingParticipant.value = null
  }
}

async function onDelete(tripId) {
  deletingId.value = tripId
  try {
    await tripsStore.deleteTrip(tripId)
  } finally {
    deletingId.value = null
  }
}

function startEdit(trip) {
  editingId.value = trip.id
  editForm.name = trip.name
  editForm.start_date = trip.start_date || ''
  editForm.end_date = trip.end_date || ''
  editForm.notes = trip.notes || ''
}

async function onSaveEdit(tripId) {
  saving.value = true
  try {
    await tripsStore.updateTrip(tripId, {
      name: editForm.name,
      start_date: editForm.start_date || null,
      end_date: editForm.end_date || null,
      notes: editForm.notes || null,
    })
    editingId.value = null
  } finally {
    saving.value = false
  }
}
</script>
