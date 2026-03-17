import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useSavedStore = defineStore('saved', () => {
  const savedPlaces = ref([])
  const loading = ref(false)

  async function fetchSaved() {
    loading.value = true
    try {
      const res = await fetch('/api/saves/')
      if (!res.ok) throw new Error('Failed to load saved')
      const payload = await res.json()
      savedPlaces.value = payload.data || []
    } finally {
      loading.value = false
    }
  }

  async function savePlace(placeId, status, notes = null) {
    const res = await fetch('/api/saves/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ place_id: placeId, status, notes }),
    })
    if (!res.ok) throw new Error('Save failed')
    await fetchSaved()
  }

  async function deleteSaved(savedId) {
    const res = await fetch(`/api/saves/${savedId}`, { method: 'DELETE' })
    if (!res.ok) throw new Error('Delete failed')
    savedPlaces.value = savedPlaces.value.filter((s) => s.id !== savedId)
  }

  return { savedPlaces, loading, fetchSaved, savePlace, deleteSaved }
})
