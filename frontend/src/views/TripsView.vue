<template>
  <div class="panel active" style="display:grid">
    <article class="info-card wide-card">
      <div class="stack-between">
        <div>
          <p class="card-eyebrow">Trips</p>
          <h3>Organize your travel plans.</h3>
          <p>Create a trip, add cities, and track where you're going. Adding a city automatically imports OSM places in the background.</p>
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

      <div class="trips-grid">
        <p v-if="loading" class="empty-state">Loading trips...</p>
        <p v-else-if="!trips.length" class="empty-state">No trips yet.</p>

        <article v-for="trip in trips" :key="trip.id" class="trip-card">
          <!-- View mode -->
          <template v-if="editingId !== trip.id">
            <div>
              <p class="card-eyebrow">
                {{ trip.start_date || 'no start' }} → {{ trip.end_date || 'open end' }}
              </p>
              <h4>{{ trip.name }}</h4>
              <p class="muted">{{ trip.notes || 'No notes.' }}</p>
            </div>

            <div class="chip-row">
              <span class="chip">{{ trip.cities.length }} {{ trip.cities.length === 1 ? 'city' : 'cities' }}</span>
            </div>

            <ul class="cities-list">
              <li v-if="!trip.cities.length">No cities added yet.</li>
              <li v-for="city in trip.cities" :key="city.id" class="city-list-item">
                {{ city.name }}{{ city.country ? `, ${city.country}` : '' }}
                <button
                  class="city-remove-btn"
                  :disabled="removingCity === city.id"
                  @click="onRemoveCity(trip.id, city.id)"
                  title="Remove city"
                >×</button>
              </li>
            </ul>

            <div class="trip-actions">
              <button class="secondary-button action-button" @click="startEdit(trip)">Edit</button>
              <button
                class="unsave-button"
                :disabled="deletingId === trip.id"
                @click="onDelete(trip.id)"
              >{{ deletingId === trip.id ? 'Deleting...' : 'Delete trip' }}</button>
            </div>

            <form class="city-form" @submit.prevent="onAddCity(trip.id, $event)">
              <div class="city-form-row">
                <input name="name" type="text" placeholder="Add city" required>
                <input name="country" type="text" placeholder="Country">
              </div>
              <button class="action-button" type="submit">Add city</button>
              <p v-if="cityFeedback[trip.id]" class="feedback">{{ cityFeedback[trip.id] }}</p>
            </form>
          </template>

          <!-- Edit mode -->
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
                <button class="secondary-button action-button" type="button" @click="editingId = null">
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
import { ref, computed, reactive } from 'vue'
import { useTripsStore } from '../stores/trips.js'

const tripsStore = useTripsStore()
const trips = computed(() => tripsStore.trips)
const loading = computed(() => tripsStore.loading)

// Create form
const creating = ref(false)
const createFeedback = ref('')
const form = reactive({ name: '', start_date: '', end_date: '', notes: '' })

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
    createFeedback.value = 'Trip created!'
    setTimeout(() => { createFeedback.value = '' }, 3000)
  } catch (e) {
    createFeedback.value = `Failed: ${e.message}`
  } finally {
    creating.value = false
  }
}

// Add city
const cityFeedback = reactive({})

async function onAddCity(tripId, event) {
  const formEl = event.target
  const name = formEl.elements.name.value
  const country = formEl.elements.country.value || null

  cityFeedback[tripId] = 'Adding...'
  try {
    await tripsStore.addCity(tripId, { name, country })
    formEl.reset()
    cityFeedback[tripId] = `${name} added — importing OSM places in background…`
    setTimeout(() => { cityFeedback[tripId] = '' }, 6000)
  } catch {
    cityFeedback[tripId] = 'Add failed'
  }
}

// Remove city
const removingCity = ref(null)

async function onRemoveCity(tripId, cityId) {
  removingCity.value = cityId
  try {
    await tripsStore.removeCity(tripId, cityId)
  } finally {
    removingCity.value = null
  }
}

// Delete trip
const deletingId = ref(null)

async function onDelete(tripId) {
  deletingId.value = tripId
  try {
    await tripsStore.deleteTrip(tripId)
  } finally {
    deletingId.value = null
  }
}

// Edit trip
const editingId = ref(null)
const saving = ref(false)
const editForm = reactive({ name: '', start_date: '', end_date: '', notes: '' })

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
