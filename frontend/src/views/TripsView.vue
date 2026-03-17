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
        </form>
      </div>

      <div class="trips-grid">
        <p v-if="loading" class="empty-state">Loading trips...</p>
        <p v-else-if="!trips.length" class="empty-state">No trips yet.</p>
        <article v-for="trip in trips" :key="trip.id" class="trip-card">
          <div>
            <p class="card-eyebrow">
              {{ trip.start_date || 'no start' }} to {{ trip.end_date || 'open end' }}
            </p>
            <h4>{{ trip.name }}</h4>
            <p class="muted">{{ trip.notes || 'No notes yet.' }}</p>
          </div>
          <div class="chip-row">
            <span class="chip">{{ trip.cities.length }} {{ trip.cities.length === 1 ? 'city' : 'cities' }}</span>
          </div>
          <ul class="cities-list">
            <li v-if="!trip.cities.length">No cities added yet.</li>
            <li v-for="city in trip.cities" :key="city.id">
              {{ city.name }}{{ city.country ? `, ${city.country}` : '' }}
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
const creating = ref(false)
const cityFeedback = reactive({})
const form = reactive({ name: '', start_date: '', end_date: '', notes: '' })

async function onCreate() {
  creating.value = true
  try {
    await tripsStore.createTrip({
      name: form.name,
      start_date: form.start_date || null,
      end_date: form.end_date || null,
      notes: form.notes || null,
    })
    Object.assign(form, { name: '', start_date: '', end_date: '', notes: '' })
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
    cityFeedback[tripId] = `${name} added — importing OSM places in background…`
    setTimeout(() => {
      cityFeedback[tripId] = ''
    }, 6000)
  } catch {
    cityFeedback[tripId] = 'Add failed'
  }
}
</script>
