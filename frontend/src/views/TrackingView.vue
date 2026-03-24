<template>
  <div class="panel active" style="display:grid">
    <article class="info-card wide-card">
      <div class="stack-between">
        <div>
          <p class="card-eyebrow">Tracking</p>
          <h3>Keep one trip financially clear while you are on the move.</h3>
          <p>
            Choose the active trip, say who paid, split it across participants,
            and let NomadBase suggest who owes whom.
          </p>
        </div>

        <div class="tracking-scope">
          <label for="tracking-trip-select" class="card-eyebrow">Trip scope</label>
          <select id="tracking-trip-select" v-model="selectedTripId">
            <option value="">Select a trip</option>
            <option v-for="trip in trips" :key="trip.id" :value="trip.id">
              {{ trip.name }}
            </option>
          </select>
          <div class="trip-actions">
            <RouterLink class="secondary-button action-button" to="/trips">
              Manage trips
            </RouterLink>
            <RouterLink class="secondary-button action-button" to="/map">
              Open map
            </RouterLink>
          </div>
        </div>
      </div>

      <section v-if="!trips.length" class="tracking-callout">
        <p class="card-eyebrow">No trips yet</p>
        <h4>Create a trip first</h4>
        <p class="muted">
          Tracking is trip-scoped now, so the cleanest next step is to create one itinerary
          and add the people who are sharing costs.
        </p>
        <RouterLink class="action-button" to="/trips">Go to trips</RouterLink>
      </section>

      <template v-else>
        <section class="tracking-callout">
          <div>
            <p class="card-eyebrow">
              {{ activeTrip ? 'Current trip' : 'Select a trip to start tracking' }}
            </p>
            <h4>{{ activeTrip?.name || 'No active trip selected' }}</h4>
            <p class="muted">
              <template v-if="activeTrip">
                {{ activeTrip.cities?.length || 0 }} cities planned ·
                {{ activeParticipants.length }} participants in the split
              </template>
              <template v-else>
                Pick one trip and the forms below will lock onto that shared context.
              </template>
            </p>
          </div>

          <div v-if="activeTrip && activeParticipants.length" class="participant-chip-list">
            <span
              v-for="participant in activeParticipants"
              :key="participant.id"
              class="chip"
            >
              {{ participant.name }}
            </span>
          </div>
        </section>

        <section
          v-if="activeTrip && activeParticipants.length && expensesNeedingResplit.length"
          class="tracking-callout tracking-callout--warning"
        >
          <div>
            <p class="card-eyebrow">Shared split check</p>
            <h4>{{ expensesNeedingResplit.length }} expense{{ expensesNeedingResplit.length === 1 ? '' : 's' }} use an older split setup</h4>
            <p class="muted">
              Your current trip crew has {{ activeParticipants.length }} people, but some recorded expenses still use an older split. You can re-split them all to the current crew in one step.
            </p>
          </div>
          <div class="trip-actions">
            <button
              class="action-button"
              type="button"
              :disabled="rebalancingExpenses"
              @click="onRebalanceExpenses"
            >
              {{ rebalancingExpenses ? 'Re-splitting...' : `Re-split ${expensesNeedingResplit.length} expenses` }}
            </button>
          </div>
          <p v-if="rebalanceFeedback" class="feedback">{{ rebalanceFeedback }}</p>
        </section>

        <section v-if="activeTrip && !activeParticipants.length" class="tracking-callout">
          <p class="card-eyebrow">Participants needed</p>
          <h4>Add your travel crew first</h4>
          <p class="muted">
            Shared expenses only become useful once the trip has participants. Add them in
            Trips, then come back here for payer and split controls.
          </p>
          <RouterLink class="action-button" to="/trips">Add participants</RouterLink>
        </section>

        <div class="tracking-sections">
          <section class="info-card">
            <div class="stack-between stack-between--tight">
              <div>
                <p class="card-eyebrow">Shared expense</p>
                <h4>{{ editingExpenseId ? 'Edit expense' : 'Log a new expense' }}</h4>
              </div>
              <button
                v-if="editingExpenseId"
                class="secondary-button action-button"
                type="button"
                @click="resetExpenseForm()"
              >
                Cancel edit
              </button>
            </div>
            <form class="tracking-form" @submit.prevent="onAddExpense">
              <input
                v-model="expForm.amount"
                type="number"
                min="0"
                step="0.01"
                placeholder="Amount"
                :disabled="!activeTrip"
                required
              >
              <div class="city-form-row">
                <input
                  v-model="expForm.currency"
                  type="text"
                  maxlength="3"
                  placeholder="Currency"
                  :disabled="!activeTrip"
                  required
                >
                <input
                  v-model="expForm.category"
                  type="text"
                  placeholder="Category"
                  :disabled="!activeTrip"
                  required
                >
              </div>

              <select v-model="expForm.place_id" :disabled="!activeTrip">
                <option value="">Optional place</option>
                <option v-for="place in allPlaces" :key="place.id" :value="place.id">
                  {{ place.name }}{{ place.meta ? ` · ${place.meta}` : '' }}
                </option>
              </select>

              <input
                v-model="expForm.date"
                type="date"
                :disabled="!activeTrip"
              >

              <div v-if="activeParticipants.length" class="participant-select">
                <label class="card-eyebrow" for="payer-select">Who paid?</label>
                <select
                  id="payer-select"
                  v-model="expForm.paid_by_participant_id"
                  :disabled="!activeTrip"
                >
                  <option value="">Select payer</option>
                  <option
                    v-for="participant in activeParticipants"
                    :key="participant.id"
                    :value="participant.id"
                  >
                    {{ participant.name }}
                  </option>
                </select>
              </div>

              <div v-if="activeParticipants.length" class="participant-select">
                <div class="stack-between">
                  <label class="card-eyebrow">Split between</label>
                  <div class="trip-actions">
                    <button class="secondary-button action-button" type="button" @click="selectAllParticipants">
                      Select all
                    </button>
                    <button class="secondary-button action-button" type="button" @click="clearSplitParticipants">
                      Clear
                    </button>
                  </div>
                </div>

                <div class="participant-options">
                  <label
                    v-for="participant in activeParticipants"
                    :key="participant.id"
                    class="participant-option"
                  >
                    <input
                      type="checkbox"
                      :checked="expForm.split_participant_ids.includes(participant.id)"
                      @change="toggleSplitParticipant(participant.id)"
                    >
                    <span>{{ participant.name }}</span>
                  </label>
                </div>
              </div>

              <textarea
                v-model="expForm.description"
                placeholder="What was this for?"
                :disabled="!activeTrip"
              ></textarea>

              <button
                class="action-button"
                type="submit"
                :disabled="savingExpense || !canSubmitExpense"
              >
                {{ savingExpense ? 'Saving...' : expenseSubmitLabel }}
              </button>
              <div v-if="splitPreview.length" class="summary-list">
                <article
                  v-for="item in splitPreview"
                  :key="item.participantId"
                  class="summary-item"
                >
                  <strong>{{ item.name }}</strong>
                  <span>{{ formatMoney(item.amount, expForm.currency || 'EUR') }}</span>
                </article>
              </div>
              <div v-if="activeParticipants.length" class="trip-actions">
                <button class="secondary-button action-button" type="button" @click="selectAllParticipants">
                  Use current trip crew
                </button>
              </div>
              <p v-if="expenseFeedback" class="feedback">{{ expenseFeedback }}</p>
              <p v-if="expenseHint" class="muted">{{ expenseHint }}</p>
              <p v-if="editingExpenseId" class="muted">
                Existing expenses only change when you save this edit. If the crew changed since this expense was logged, you can also use the trip-wide re-split action above.
              </p>
            </form>
          </section>

          <section class="info-card">
            <p class="card-eyebrow">Visited place</p>
            <form class="tracking-form" @submit.prevent="onAddVisit">
              <select v-model="visForm.place_id" :disabled="!activeTrip" required>
                <option value="">Select place</option>
                <option v-for="place in allPlaces" :key="place.id" :value="place.id">
                  {{ place.name }}{{ place.meta ? ` · ${place.meta}` : '' }}
                </option>
              </select>
              <input
                v-model="visForm.visited_at"
                type="datetime-local"
                :disabled="!activeTrip"
              >
              <textarea
                v-model="visForm.notes"
                placeholder="What stood out?"
                :disabled="!activeTrip"
              ></textarea>
              <button
                class="action-button"
                type="submit"
                :disabled="savingVisit || !activeTrip"
              >
                {{ savingVisit ? 'Saving...' : 'Log visit' }}
              </button>
              <p v-if="visitFeedback" class="feedback">{{ visitFeedback }}</p>
              <p v-if="!activeTrip" class="muted">Pick a trip first so the visit lands in the right journey.</p>
            </form>
          </section>
        </div>

        <section v-if="activeTrip && settlementGroups.length" class="info-card wide-card">
          <div class="stack-between">
            <div>
              <p class="card-eyebrow">Settlements</p>
              <h4>Who should pay whom</h4>
            </div>
            <p class="muted">Based on expenses recorded for {{ activeTrip.name }}.</p>
          </div>

          <div class="tracking-grid">
            <article v-for="group in settlementGroups" :key="group.currency" class="tracking-card">
              <div>
                <p class="card-eyebrow">{{ group.currency }}</p>
                <h4>{{ formatMoney(group.total_expenses, group.currency) }} tracked</h4>
              </div>

              <div class="tracking-balance-grid">
                <article
                  v-for="participant in group.participants"
                  :key="participant.participant_id"
                  class="summary-item"
                >
                  <strong>{{ participant.participant_name }}</strong>
                  <span class="muted">Paid {{ formatMoney(participant.paid, group.currency) }}</span>
                  <span class="muted">Share {{ formatMoney(participant.owed, group.currency) }}</span>
                  <strong :class="participant.net >= 0 ? 'settlement-positive' : 'settlement-negative'">
                    {{ participant.net >= 0 ? '+' : '' }}{{ formatMoney(participant.net, group.currency) }}
                  </strong>
                </article>
              </div>

              <div>
                <p class="card-eyebrow">Suggested transfers</p>
                <ul v-if="group.transfers.length" class="transfer-list">
                  <li v-for="transfer in group.transfers" :key="transfer.from_participant_id + transfer.to_participant_id">
                    <strong>{{ transfer.from_participant_name }}</strong>
                    pays
                    <strong>{{ transfer.to_participant_name }}</strong>
                    <span>{{ formatMoney(transfer.amount, group.currency) }}</span>
                  </li>
                </ul>
                <p v-else class="muted">Everyone is settled up for this currency.</p>
              </div>
            </article>
          </div>
        </section>

        <section class="info-card wide-card">
          <div class="stack-between">
            <div>
              <p class="card-eyebrow">Overview</p>
              <h4>{{ activeTrip ? `${activeTrip.name} at a glance` : 'Tracking overview' }}</h4>
            </div>
            <p class="muted">
              {{ loading ? 'Refreshing data...' : `${expenses.length} expenses · ${visits.length} visits` }}
            </p>
          </div>

          <div class="tracking-sections">
            <section>
              <p class="card-eyebrow">Category summary</p>
              <div class="summary-list">
                <article v-if="summaryItems.length" v-for="item in summaryItems" :key="item.category" class="summary-item">
                  <strong>{{ item.category }}</strong>
                  <span>{{ formatMoney(item.total, summaryCurrency) }}</span>
                </article>
                <article v-if="summaryItems.length" class="summary-item">
                  <strong>Total</strong>
                  <span>{{ formatMoney(summaryTotal, summaryCurrency) }}</span>
                </article>
                <p v-else class="empty-state">No expense summary yet.</p>
              </div>
            </section>

            <section>
              <p class="card-eyebrow">Recent expenses</p>
              <div class="summary-list">
                <article v-if="expenses.length" v-for="expense in expenses" :key="expense.id" class="summary-item">
                  <div class="stack-between">
                    <strong>{{ expense.category }}</strong>
                    <div class="entry-actions">
                      <button class="secondary-button action-button" type="button" @click="onEditExpense(expense)">
                        Edit
                      </button>
                      <button class="unsave-button" type="button" @click="onDeleteExpense(expense.id)">Delete</button>
                    </div>
                  </div>
                  <span>{{ formatMoney(expense.amount, expense.currency) }}</span>
                  <div class="chip-row">
                    <span v-if="expense.paid_by_participant_name" class="chip">
                      Paid by {{ expense.paid_by_participant_name }}
                    </span>
                    <span v-if="expense.split_participant_names?.length" class="chip">
                      Split {{ expense.split_participant_names.length }} ways
                    </span>
                    <span v-if="expense.place_name" class="chip">{{ expense.place_name }}</span>
                  </div>
                  <span class="muted">
                    {{ formatDate(expense.date) }}
                    <template v-if="expense.description">· {{ expense.description }}</template>
                  </span>
                </article>
                <p v-else class="empty-state">No expenses recorded for this scope yet.</p>
              </div>
            </section>
          </div>

          <section class="tracking-visit-section">
            <p class="card-eyebrow">Recent visits</p>
            <div class="summary-list">
              <article v-if="visits.length" v-for="visit in visits" :key="visit.id" class="summary-item">
                <div class="stack-between">
                  <strong>{{ visit.place_name }}</strong>
                  <button class="unsave-button" type="button" @click="onDeleteVisit(visit.id)">Delete</button>
                </div>
                <span class="muted">{{ formatDateTime(visit.visited_at || visit.created_at) }}</span>
                <span class="muted">{{ visit.notes || 'No notes yet.' }}</span>
              </article>
              <p v-else class="empty-state">No visits logged yet.</p>
            </div>
          </section>
        </section>
      </template>
    </article>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { usePlacesStore } from '../stores/places.js'
import { useSavedStore } from '../stores/saved.js'
import { useTrackingStore } from '../stores/tracking.js'
import { useTripsStore } from '../stores/trips.js'

const route = useRoute()
const placesStore = usePlacesStore()
const savedStore = useSavedStore()
const trackingStore = useTrackingStore()
const tripsStore = useTripsStore()

const today = new Date().toISOString().slice(0, 10)
const trips = computed(() => tripsStore.trips)
const activeTrip = computed(() => tripsStore.activeTrip)
const activeParticipants = computed(() => activeTrip.value?.participants || [])
const expenses = computed(() => trackingStore.expenses)
const visits = computed(() => trackingStore.visits)
const loading = computed(() => trackingStore.loading)
const summaryItems = computed(() => trackingStore.summary?.data || [])
const summaryTotal = computed(() => trackingStore.summary?.total_amount || 0)
const summaryCurrency = computed(() => trackingStore.summary?.currency || 'EUR')
const settlementGroups = computed(() => trackingStore.settlements?.data || [])
const expensesNeedingResplit = computed(() => {
  const currentIds = [...activeParticipants.value].map((participant) => participant.id).sort()
  if (!currentIds.length) return []
  return expenses.value.filter((expense) => {
    const splitIds = [...(expense.split_participant_ids || [])].sort()
    if (splitIds.length !== currentIds.length) return true
    return splitIds.some((id, index) => id !== currentIds[index])
  })
})
const splitPreview = computed(() => {
  const total = Number(expForm.amount)
  const participantIds = expForm.split_participant_ids || []
  if (!participantIds.length || !Number.isFinite(total) || total <= 0) return []

  const totalCents = Math.round(total * 100)
  const baseCents = Math.floor(totalCents / participantIds.length)
  let remainder = totalCents - baseCents * participantIds.length

  return participantIds.map((participantId) => {
    const participant = activeParticipants.value.find((entry) => entry.id === participantId)
    const cents = baseCents + (remainder > 0 ? 1 : 0)
    remainder = Math.max(0, remainder - 1)
    return {
      participantId,
      name: participant?.name || 'Unknown participant',
      amount: cents / 100,
    }
  })
})

const selectedTripId = computed({
  get: () => tripsStore.activeTripId,
  set: (value) => {
    tripsStore.setActiveTrip(value)
  },
})

const allPlaces = computed(() => {
  const byId = new Map()

  for (const place of placesStore.places || []) {
    byId.set(place.id, {
      id: place.id,
      name: place.name,
      meta: [place.city || place.region, place.country].filter(Boolean).join(', '),
    })
  }

  for (const saved of savedStore.savedPlaces || []) {
    const place = saved.place
    if (!place?.id || byId.has(place.id)) continue
    byId.set(place.id, {
      id: place.id,
      name: place.name,
      meta: [place.region, place.place_type].filter(Boolean).join(' · '),
    })
  }

  return Array.from(byId.values()).sort((a, b) => a.name.localeCompare(b.name))
})

const expForm = reactive({
  amount: '',
  currency: 'EUR',
  category: '',
  description: '',
  date: today,
  trip_id: '',
  place_id: '',
  paid_by_participant_id: '',
  split_participant_ids: [],
})

const visForm = reactive({
  place_id: '',
  trip_id: '',
  visited_at: '',
  notes: '',
})

const savingExpense = ref(false)
const savingVisit = ref(false)
const rebalancingExpenses = ref(false)
const expenseFeedback = ref('')
const visitFeedback = ref('')
const rebalanceFeedback = ref('')
const editingExpenseId = ref('')

const canSubmitExpense = computed(() => {
  if (!activeTrip.value) return false
  if (!activeParticipants.value.length) return false
  return true
})
const expenseSubmitLabel = computed(() => (editingExpenseId.value ? 'Save changes' : 'Log expense'))

const expenseHint = computed(() => {
  if (!activeTrip.value) return 'Select a trip first.'
  if (!activeParticipants.value.length) return 'Add at least one participant on the Trips screen.'
  if (!expForm.paid_by_participant_id) return 'Choose who paid for this expense.'
  if (!expForm.split_participant_ids.length) return 'Select who should share this cost.'
  return ''
})

watch(
  selectedTripId,
  async (tripId) => {
    expForm.trip_id = tripId || ''
    visForm.trip_id = tripId || ''
    expenseFeedback.value = ''
    visitFeedback.value = ''
    rebalanceFeedback.value = ''
    resetExpenseForm()
    await trackingStore.fetchAll(tripId || '')
  },
  { immediate: true }
)

watch(
  activeParticipants,
  (participants) => {
    const ids = participants.map((participant) => participant.id)

    if (!ids.length) {
      expForm.paid_by_participant_id = ''
      expForm.split_participant_ids = []
      return
    }

    if (!ids.includes(expForm.paid_by_participant_id)) {
      expForm.paid_by_participant_id = ids[0]
    }

    const validSplits = expForm.split_participant_ids.filter((id) => ids.includes(id))
    expForm.split_participant_ids = validSplits.length ? validSplits : [...ids]
  },
  { immediate: true }
)

watch(
  () => route.query.trip,
  (tripId) => {
    if (typeof tripId === 'string') {
      tripsStore.setActiveTrip(tripId)
    }
  },
  { immediate: true }
)

function toggleSplitParticipant(participantId) {
  if (expForm.split_participant_ids.includes(participantId)) {
    expForm.split_participant_ids = expForm.split_participant_ids.filter((id) => id !== participantId)
    return
  }

  expForm.split_participant_ids = [...expForm.split_participant_ids, participantId]
}

function selectAllParticipants() {
  expForm.split_participant_ids = activeParticipants.value.map((participant) => participant.id)
}

function clearSplitParticipants() {
  expForm.split_participant_ids = []
}

function resetExpenseForm() {
  editingExpenseId.value = ''
  expForm.amount = ''
  expForm.currency = 'EUR'
  expForm.category = ''
  expForm.description = ''
  expForm.date = today
  expForm.place_id = ''
  expForm.paid_by_participant_id = activeParticipants.value[0]?.id || ''
  expForm.split_participant_ids = activeParticipants.value.map((participant) => participant.id)
}

function loadExpenseIntoForm(expense) {
  editingExpenseId.value = expense.id
  expForm.amount = String(expense.amount ?? '')
  expForm.currency = expense.currency || 'EUR'
  expForm.category = expense.category || ''
  expForm.description = expense.description || ''
  expForm.date = expense.date || today
  expForm.place_id = expense.place_id || ''
  expForm.paid_by_participant_id = expense.paid_by_participant_id || ''
  expForm.split_participant_ids = [...(expense.split_participant_ids || [])]
}

async function onAddExpense() {
  expenseFeedback.value = ''
  rebalanceFeedback.value = ''
  if (!activeTrip.value) {
    expenseFeedback.value = 'Select a trip first.'
    return
  }
  if (!activeParticipants.value.length) {
    expenseFeedback.value = 'Add participants to this trip before logging shared expenses.'
    return
  }
  if (!expForm.paid_by_participant_id) {
    expenseFeedback.value = 'Select who paid.'
    return
  }
  if (!expForm.split_participant_ids.length) {
    expenseFeedback.value = 'Select who should split this expense.'
    return
  }

  savingExpense.value = true
  try {
    const payload = {
      amount: Number(expForm.amount),
      currency: expForm.currency.toUpperCase(),
      category: expForm.category,
      description: expForm.description || null,
      date: expForm.date || null,
      trip_id: activeTrip.value.id,
      place_id: expForm.place_id || null,
      paid_by_participant_id: expForm.paid_by_participant_id,
      split_participant_ids: expForm.split_participant_ids,
    }

    if (editingExpenseId.value) {
      await trackingStore.updateExpense(editingExpenseId.value, payload)
      expenseFeedback.value = 'Expense updated.'
    } else {
      await trackingStore.addExpense(payload)
      expenseFeedback.value = 'Expense logged.'
    }

    resetExpenseForm()
  } catch (error) {
    expenseFeedback.value = error.message || 'Could not save expense.'
  } finally {
    savingExpense.value = false
  }
}

async function onAddVisit() {
  visitFeedback.value = ''
  rebalanceFeedback.value = ''
  if (!activeTrip.value) {
    visitFeedback.value = 'Select a trip first.'
    return
  }

  savingVisit.value = true
  try {
    await trackingStore.addVisit({
      place_id: visForm.place_id,
      trip_id: activeTrip.value.id,
      visited_at: visForm.visited_at ? new Date(visForm.visited_at).toISOString() : null,
      notes: visForm.notes || null,
    })
    visForm.place_id = ''
    visForm.visited_at = ''
    visForm.notes = ''
    visitFeedback.value = 'Visit logged.'
  } catch (error) {
    visitFeedback.value = error.message || 'Could not log visit.'
  } finally {
    savingVisit.value = false
  }
}

async function onDeleteExpense(id) {
  await trackingStore.deleteExpense(id)
  if (editingExpenseId.value === id) {
    resetExpenseForm()
  }
}

async function onRebalanceExpenses() {
  if (!activeTrip.value || !expensesNeedingResplit.value.length) return
  rebalancingExpenses.value = true
  expenseFeedback.value = ''
  rebalanceFeedback.value = ''
  try {
    const payload = await trackingStore.rebalanceExpenses({
      trip_id: activeTrip.value.id,
      expense_ids: expensesNeedingResplit.value.map((expense) => expense.id),
    })
    rebalanceFeedback.value = payload.message
    if (editingExpenseId.value) {
      const updatedExpense = trackingStore.expenses.find((expense) => expense.id === editingExpenseId.value)
      if (updatedExpense) {
        loadExpenseIntoForm(updatedExpense)
      }
    }
  } catch (error) {
    rebalanceFeedback.value = error.message || 'Could not re-split expenses.'
  } finally {
    rebalancingExpenses.value = false
  }
}

async function onDeleteVisit(id) {
  await trackingStore.deleteVisit(id)
}

function onEditExpense(expense) {
  loadExpenseIntoForm(expense)
}

function formatMoney(amount, currency = 'EUR') {
  const safeAmount = Number(amount || 0)
  try {
    return new Intl.NumberFormat(undefined, {
      style: 'currency',
      currency,
      maximumFractionDigits: 2,
    }).format(safeAmount)
  } catch {
    return `${safeAmount.toFixed(2)} ${currency}`
  }
}

function formatDate(value) {
  if (!value) return 'No date'
  return new Date(value).toLocaleDateString()
}

function formatDateTime(value) {
  if (!value) return 'No timestamp'
  return new Date(value).toLocaleString()
}
</script>
