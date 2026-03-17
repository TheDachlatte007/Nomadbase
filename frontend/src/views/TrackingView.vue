<template>
  <div class="panel active" style="display:grid">
    <article class="info-card">
      <p class="card-eyebrow">Expenses</p>
      <h3>Track what the trip is costing.</h3>
      <form class="tracking-form" @submit.prevent="onExpense">
        <input v-model="expForm.amount" type="number" min="0.01" step="0.01" placeholder="Amount" required>
        <select v-model="expForm.currency">
          <option v-for="c in CURRENCIES" :key="c" :value="c">{{ c }}</option>
        </select>
        <input v-model="expForm.category" type="text" placeholder="Category e.g. food, transport" required>
        <input v-model="expForm.date" type="date">
        <select v-model="expForm.trip_id">
          <option value="">No linked trip</option>
          <option v-for="trip in trips" :key="trip.id" :value="trip.id">{{ trip.name }}</option>
        </select>
        <select v-model="expForm.place_id">
          <option value="">No linked place</option>
          <option v-for="place in allPlaces" :key="place.id" :value="place.id">
            {{ place.name }}{{ place.region ? ` (${place.region})` : '' }}
          </option>
        </select>
        <textarea v-model="expForm.description" placeholder="What did you spend this on?"></textarea>
        <button class="action-button" type="submit" :disabled="saving">Record expense</button>
        <p v-if="expFeedback" class="feedback">{{ expFeedback }}</p>
      </form>
    </article>

    <article class="info-card">
      <p class="card-eyebrow">Visits</p>
      <h3>Log where you actually went.</h3>
      <form class="tracking-form" @submit.prevent="onVisit">
        <select v-model="visForm.place_id" required>
          <option value="">Choose a place</option>
          <option v-for="place in allPlaces" :key="place.id" :value="place.id">
            {{ place.name }}{{ place.region ? ` (${place.region})` : '' }}
          </option>
        </select>
        <select v-model="visForm.trip_id">
          <option value="">No linked trip</option>
          <option v-for="trip in trips" :key="trip.id" :value="trip.id">{{ trip.name }}</option>
        </select>
        <input v-model="visForm.visited_at" type="datetime-local">
        <textarea v-model="visForm.notes" placeholder="Quick memory or field note"></textarea>
        <button class="action-button" type="submit" :disabled="logging">Log visit</button>
        <p v-if="visFeedback" class="feedback">{{ visFeedback }}</p>
      </form>
    </article>

    <article class="info-card wide-card">
      <div class="stack-between">
        <div>
          <p class="card-eyebrow">Overview</p>
          <h3>Recent activity and cost summary.</h3>
          <p class="muted">{{ summaryText }}</p>
        </div>
        <div class="summary-list">
          <div v-for="item in summaryItems" :key="item.category" class="summary-item">
            <strong>{{ item.category }}</strong>
            <span class="muted">{{ item.total.toFixed(2) }} {{ summary?.currency || 'EUR' }}</span>
          </div>
        </div>
      </div>
      <div class="tracking-sections">
        <div>
          <p class="card-eyebrow">Recent expenses</p>
          <div class="tracking-grid">
            <p v-if="!expenses.length" class="empty-state">No expenses yet.</p>
            <article v-for="exp in expenses" :key="exp.id" class="tracking-card">
              <div>
                <p class="card-eyebrow">{{ exp.category }}</p>
                <h4>{{ exp.amount.toFixed(2) }} {{ exp.currency }}</h4>
                <p class="muted">
                  {{ formatDate(exp.date) }}{{ exp.trip_name ? ` · ${exp.trip_name}` : '' }}
                </p>
              </div>
              <p>{{ exp.description || 'No description.' }}</p>
              <div class="chip-row">
                <span v-if="exp.place_name" class="chip">{{ exp.place_name }}</span>
              </div>
            </article>
          </div>
        </div>
        <div>
          <p class="card-eyebrow">Recent visits</p>
          <div class="tracking-grid">
            <p v-if="!visits.length" class="empty-state">No visits yet.</p>
            <article v-for="vis in visits" :key="vis.id" class="tracking-card">
              <div>
                <p class="card-eyebrow">{{ vis.city || 'visit' }}</p>
                <h4>{{ vis.place_name }}</h4>
                <p class="muted">{{ formatDateTime(vis.visited_at) }}</p>
              </div>
              <p>{{ vis.notes || 'No notes.' }}</p>
              <div class="chip-row">
                <span v-if="vis.trip_name" class="chip">{{ vis.trip_name }}</span>
              </div>
            </article>
          </div>
        </div>
      </div>
    </article>
  </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { useTrackingStore } from '../stores/tracking.js'
import { usePlacesStore } from '../stores/places.js'
import { useSavedStore } from '../stores/saved.js'
import { useTripsStore } from '../stores/trips.js'

const trackingStore = useTrackingStore()
const placesStore = usePlacesStore()
const savedStore = useSavedStore()
const tripsStore = useTripsStore()

const expenses = computed(() => trackingStore.expenses)
const visits = computed(() => trackingStore.visits)
const summary = computed(() => trackingStore.summary)
const summaryItems = computed(() => summary.value?.data || [])
const trips = computed(() => tripsStore.trips)

const allPlaces = computed(() => {
  const map = new Map()
  for (const s of savedStore.savedPlaces) {
    if (s.place) map.set(s.place.id, s.place)
  }
  for (const p of placesStore.places) {
    map.set(p.id, p)
  }
  return [...map.values()].sort((a, b) => a.name.localeCompare(b.name))
})

const summaryText = computed(() => {
  if (!summaryItems.value.length) return 'No tracked expenses yet.'
  return `Total: ${summary.value?.total_amount?.toFixed(2)} ${summary.value?.currency || 'EUR'} across ${summaryItems.value.length} categories.`
})

const CURRENCIES = ['EUR', 'USD', 'GBP', 'CHF', 'CZK', 'SEK', 'NOK', 'DKK', 'HUF', 'PLN', 'RON', 'HRK']

const expForm = reactive({
  amount: '',
  currency: 'EUR',
  category: '',
  date: '',
  trip_id: '',
  place_id: '',
  description: '',
})
const visForm = reactive({ place_id: '', trip_id: '', visited_at: '', notes: '' })
const expFeedback = ref('')
const visFeedback = ref('')
const saving = ref(false)
const logging = ref(false)

function formatDate(value) {
  if (!value) return 'not set'
  if (typeof value === 'string' && !value.includes('T')) return value
  return new Date(value).toLocaleDateString('en-GB')
}

function formatDateTime(value) {
  if (!value) return 'not set'
  return new Date(value).toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short' })
}

async function onExpense() {
  saving.value = true
  expFeedback.value = 'Saving...'
  try {
    await trackingStore.addExpense({
      amount: Number(expForm.amount),
      currency: expForm.currency,
      category: expForm.category,
      date: expForm.date || null,
      trip_id: expForm.trip_id || null,
      place_id: expForm.place_id || null,
      description: expForm.description || null,
    })
    Object.assign(expForm, {
      amount: '',
      category: '',
      date: '',
      trip_id: '',
      place_id: '',
      description: '',
    })
    expFeedback.value = 'Recorded'
  } catch {
    expFeedback.value = 'Save failed'
  } finally {
    saving.value = false
  }
}

async function onVisit() {
  logging.value = true
  visFeedback.value = 'Saving...'
  try {
    await trackingStore.addVisit({
      place_id: visForm.place_id,
      trip_id: visForm.trip_id || null,
      visited_at: visForm.visited_at ? new Date(visForm.visited_at).toISOString() : null,
      notes: visForm.notes || null,
    })
    Object.assign(visForm, { place_id: '', trip_id: '', visited_at: '', notes: '' })
    visFeedback.value = 'Logged'
  } catch {
    visFeedback.value = 'Log failed'
  } finally {
    logging.value = false
  }
}
</script>
