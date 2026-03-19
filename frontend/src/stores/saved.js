import { defineStore } from 'pinia'
import { ref } from 'vue'

async function readError(res, fallbackMessage) {
  try {
    const payload = await res.json()
    return payload.detail || payload.message || fallbackMessage
  } catch {
    return fallbackMessage
  }
}

export const useSavedStore = defineStore('saved', () => {
  const savedPlaces = ref([])
  const loading = ref(false)
  const currentTripId = ref('')
  const includeGlobal = ref(true)

  async function fetchSaved(tripId = '', includeGlobalScope = true) {
    loading.value = true
    currentTripId.value = tripId || ''
    includeGlobal.value = includeGlobalScope
    try {
      const params = new URLSearchParams()
      if (currentTripId.value) {
        params.set('trip_id', currentTripId.value)
        params.set('include_global', includeGlobal.value ? 'true' : 'false')
      }
      const suffix = params.toString() ? `?${params.toString()}` : ''
      const res = await fetch(`/api/saves/${suffix}`)
      if (!res.ok) throw new Error(await readError(res, 'Failed to load saved'))
      const payload = await res.json()
      savedPlaces.value = payload.data || []
    } finally {
      loading.value = false
    }
  }

  async function savePlace(placeId, status, notes = null, tripId = null) {
    const res = await fetch('/api/saves/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ place_id: placeId, trip_id: tripId, status, notes }),
    })
    if (!res.ok) throw new Error(await readError(res, 'Save failed'))
    await fetchSaved(currentTripId.value, includeGlobal.value)
  }

  async function deleteSaved(savedId) {
    const res = await fetch(`/api/saves/${savedId}`, { method: 'DELETE' })
    if (!res.ok) throw new Error(await readError(res, 'Delete failed'))
    savedPlaces.value = savedPlaces.value.filter((s) => s.id !== savedId)
  }

  return {
    savedPlaces,
    loading,
    currentTripId,
    includeGlobal,
    fetchSaved,
    savePlace,
    deleteSaved,
  }
})
