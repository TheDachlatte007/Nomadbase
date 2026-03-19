import { ref } from 'vue'
import { defineStore } from 'pinia'

async function readError(res, fallbackMessage) {
  try {
    const payload = await res.json()
    return payload.detail || payload.message || fallbackMessage
  } catch {
    return fallbackMessage
  }
}

export const useTrackingStore = defineStore('tracking', () => {
  const expenses = ref([])
  const visits = ref([])
  const summary = ref(null)
  const settlements = ref(null)
  const loading = ref(false)
  const currentTripId = ref('')

  function buildParams(tripId = '') {
    const params = new URLSearchParams()
    if (tripId) params.set('trip_id', tripId)
    return params.toString() ? `?${params.toString()}` : ''
  }

  async function fetchAll(tripId = currentTripId.value) {
    currentTripId.value = tripId || ''
    loading.value = true
    try {
      const suffix = buildParams(currentTripId.value)
      const [expRes, visRes, sumRes] = await Promise.all([
        fetch(`/api/tracking/expenses${suffix}`),
        fetch(`/api/tracking/visits${suffix}`),
        fetch(`/api/tracking/expenses/summary${suffix}`),
      ])
      if (!expRes.ok) throw new Error(await readError(expRes, 'Failed to load expenses'))
      if (!visRes.ok) throw new Error(await readError(visRes, 'Failed to load visits'))
      if (!sumRes.ok) throw new Error(await readError(sumRes, 'Failed to load summary'))
      expenses.value = (await expRes.json()).data || []
      visits.value = (await visRes.json()).data || []
      summary.value = await sumRes.json()
      if (currentTripId.value) await fetchSettlements(currentTripId.value)
      else settlements.value = null
    } finally {
      loading.value = false
    }
  }

  async function fetchSettlements(tripId = currentTripId.value) {
    currentTripId.value = tripId || ''
    if (!currentTripId.value) {
      settlements.value = null
      return null
    }

    const res = await fetch(`/api/tracking/expenses/settlements?trip_id=${currentTripId.value}`)
    if (!res.ok) throw new Error(await readError(res, 'Load settlements failed'))
    settlements.value = await res.json()
    return settlements.value
  }

  async function addExpense(data) {
    const res = await fetch('/api/tracking/expenses', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!res.ok) {
      throw new Error(await readError(res, 'Save expense failed'))
    }
    await fetchAll(data.trip_id || currentTripId.value)
  }

  async function addVisit(data) {
    const res = await fetch('/api/tracking/visits', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!res.ok) throw new Error(await readError(res, 'Log visit failed'))
    await fetchAll(data.trip_id || currentTripId.value)
  }

  async function deleteExpense(id) {
    const res = await fetch(`/api/tracking/expenses/${id}`, { method: 'DELETE' })
    if (!res.ok) throw new Error(await readError(res, 'Delete expense failed'))
    await fetchAll(currentTripId.value)
  }

  async function deleteVisit(id) {
    const res = await fetch(`/api/tracking/visits/${id}`, { method: 'DELETE' })
    if (!res.ok) throw new Error(await readError(res, 'Delete visit failed'))
    await fetchAll(currentTripId.value)
  }

  return {
    expenses,
    visits,
    summary,
    settlements,
    loading,
    currentTripId,
    fetchAll,
    fetchSettlements,
    addExpense,
    addVisit,
    deleteExpense,
    deleteVisit,
  }
})
