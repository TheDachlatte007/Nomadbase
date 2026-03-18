import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useTripsStore = defineStore('trips', () => {
  const trips = ref([])
  const loading = ref(false)

  async function fetchTrips() {
    loading.value = true
    try {
      const res = await fetch('/api/trips/')
      if (!res.ok) throw new Error('Failed to load trips')
      const payload = await res.json()
      trips.value = payload.data || []
    } finally {
      loading.value = false
    }
  }

  async function createTrip(data) {
    const res = await fetch('/api/trips/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!res.ok) throw new Error('Create trip failed')
    await fetchTrips()
  }

  async function addCity(tripId, data) {
    const res = await fetch(`/api/trips/${tripId}/cities`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!res.ok) throw new Error('Add city failed')
    await fetchTrips()

    // Fire-and-forget background OSM import
    fetch('/api/admin/imports', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ city: data.name, country: data.country || null }),
    }).catch(() => {})
  }

  async function removeCity(tripId, cityId) {
    const res = await fetch(`/api/trips/${tripId}/cities/${cityId}`, {
      method: 'DELETE',
    })
    if (!res.ok) throw new Error('Remove city failed')
    await fetchTrips()
  }

  async function updateTrip(tripId, data) {
    const res = await fetch(`/api/trips/${tripId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!res.ok) throw new Error('Update trip failed')
    await fetchTrips()
  }

  async function deleteTrip(tripId) {
    const res = await fetch(`/api/trips/${tripId}`, { method: 'DELETE' })
    if (!res.ok) throw new Error('Delete trip failed')
    trips.value = trips.value.filter((t) => t.id !== tripId)
  }

  return { trips, loading, fetchTrips, createTrip, addCity, removeCity, updateTrip, deleteTrip }
})
