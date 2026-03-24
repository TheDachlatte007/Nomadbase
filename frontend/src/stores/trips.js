import { computed, ref, watch } from 'vue'
import { defineStore } from 'pinia'

const ACTIVE_TRIP_KEY = 'nomadbase.activeTripId'

async function readError(res, fallbackMessage) {
  try {
    const payload = await res.json()
    return payload.detail || payload.message || fallbackMessage
  } catch {
    return fallbackMessage
  }
}

export const useTripsStore = defineStore('trips', () => {
  const trips = ref([])
  const loading = ref(false)
  const overviewLoading = ref(false)
  const activeTripId = ref(window.localStorage.getItem(ACTIVE_TRIP_KEY) || '')
  const tripOverview = ref(null)

  const activeTrip = computed(
    () => trips.value.find((trip) => trip.id === activeTripId.value) || null
  )

  watch(activeTripId, (value) => {
    if (value) window.localStorage.setItem(ACTIVE_TRIP_KEY, value)
    else window.localStorage.removeItem(ACTIVE_TRIP_KEY)
  })

  async function fetchTrips() {
    loading.value = true
    try {
      const res = await fetch('/api/trips/')
      if (!res.ok) throw new Error(await readError(res, 'Failed to load trips'))
      const payload = await res.json()
      trips.value = payload.data || []
      if (activeTripId.value && !trips.value.some((trip) => trip.id === activeTripId.value)) {
        activeTripId.value = ''
      }
    } finally {
      loading.value = false
    }
  }

  async function fetchTripOverview(tripId = activeTripId.value) {
    if (!tripId) {
      tripOverview.value = null
      return null
    }

    overviewLoading.value = true
    try {
      const res = await fetch(`/api/trips/${tripId}/overview`)
      if (!res.ok) throw new Error(await readError(res, 'Failed to load trip overview'))
      tripOverview.value = await res.json()
      return tripOverview.value
    } finally {
      overviewLoading.value = false
    }
  }

  async function createTrip(data) {
    const res = await fetch('/api/trips/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!res.ok) throw new Error(await readError(res, 'Create trip failed'))
    const payload = await res.json()
    await fetchTrips()
    if (payload?.id) {
      activeTripId.value = payload.id
      await fetchTripOverview(payload.id)
    } else if (!activeTripId.value && trips.value.length) {
      activeTripId.value = trips.value[0].id
      await fetchTripOverview(activeTripId.value)
    }
    return payload
  }

  async function addCity(tripId, data) {
    const res = await fetch(`/api/trips/${tripId}/cities`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!res.ok) throw new Error(await readError(res, 'Add city failed'))
    await fetchTrips()
    if (activeTripId.value === tripId) {
      await fetchTripOverview(tripId)
    }
  }

  async function removeCity(tripId, cityId) {
    const res = await fetch(`/api/trips/${tripId}/cities/${cityId}`, {
      method: 'DELETE',
    })
    if (!res.ok) throw new Error(await readError(res, 'Remove city failed'))
    await fetchTrips()
    if (activeTripId.value === tripId) {
      await fetchTripOverview(tripId)
    }
  }

  async function updateCity(tripId, cityId, data) {
    const res = await fetch(`/api/trips/${tripId}/cities/${cityId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!res.ok) throw new Error(await readError(res, 'Update city failed'))
    await fetchTrips()
    if (activeTripId.value === tripId) {
      await fetchTripOverview(tripId)
    }
  }

  async function reorderCities(tripId, cityIds) {
    const res = await fetch(`/api/trips/${tripId}/cities/reorder`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ city_ids: cityIds }),
    })
    if (!res.ok) throw new Error(await readError(res, 'Reorder cities failed'))
    await fetchTrips()
    if (activeTripId.value === tripId) {
      await fetchTripOverview(tripId)
    }
  }

  async function addParticipant(tripId, data) {
    const res = await fetch(`/api/trips/${tripId}/participants`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!res.ok) throw new Error(await readError(res, 'Add participant failed'))
    await fetchTrips()
    if (activeTripId.value === tripId) {
      await fetchTripOverview(tripId)
    }
  }

  async function removeParticipant(tripId, participantId) {
    const res = await fetch(`/api/trips/${tripId}/participants/${participantId}`, {
      method: 'DELETE',
    })
    if (!res.ok) throw new Error(await readError(res, 'Remove participant failed'))
    await fetchTrips()
    if (activeTripId.value === tripId) {
      await fetchTripOverview(tripId)
    }
  }

  async function updateTrip(tripId, data) {
    const res = await fetch(`/api/trips/${tripId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!res.ok) throw new Error(await readError(res, 'Update trip failed'))
    await fetchTrips()
    if (activeTripId.value === tripId) {
      await fetchTripOverview(tripId)
    }
  }

  async function queueCoverageImports(tripId, cityIds = []) {
    const res = await fetch(`/api/trips/${tripId}/coverage/imports`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ city_ids: cityIds }),
    })
    if (!res.ok) throw new Error(await readError(res, 'Queue imports failed'))
    const payload = await res.json()
    return payload
  }

  async function deleteTrip(tripId) {
    const res = await fetch(`/api/trips/${tripId}`, { method: 'DELETE' })
    if (!res.ok) throw new Error(await readError(res, 'Delete trip failed'))
    trips.value = trips.value.filter((trip) => trip.id !== tripId)
    if (activeTripId.value === tripId) {
      activeTripId.value = trips.value[0]?.id || ''
      if (activeTripId.value) {
        await fetchTripOverview(activeTripId.value)
      } else {
        tripOverview.value = null
      }
    }
  }

  function setActiveTrip(tripId) {
    activeTripId.value = tripId || ''
    if (!activeTripId.value) {
      tripOverview.value = null
    }
  }

  return {
    trips,
    loading,
    overviewLoading,
    activeTripId,
    activeTrip,
    tripOverview,
    fetchTrips,
    fetchTripOverview,
    createTrip,
    addCity,
    removeCity,
    updateCity,
    reorderCities,
    addParticipant,
    removeParticipant,
    updateTrip,
    queueCoverageImports,
    deleteTrip,
    setActiveTrip,
  }
})
