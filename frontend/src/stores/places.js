import { defineStore } from 'pinia'
import { ref } from 'vue'

export const usePlacesStore = defineStore('places', () => {
  const places = ref([])
  const loading = ref(false)

  async function fetchPlaces(query = '', placeType = '') {
    loading.value = true
    try {
      const params = new URLSearchParams()
      if (query) params.set('q', query)
      if (placeType) params.set('place_type', placeType)
      const suffix = params.toString() ? `?${params.toString()}` : ''
      const res = await fetch(`/api/map/places${suffix}`)
      if (!res.ok) throw new Error('Failed to load places')
      const payload = await res.json()
      places.value = payload.data || []
    } finally {
      loading.value = false
    }
  }

  async function fetchNearby(lat, lon, radius = 2500) {
    loading.value = true
    try {
      const res = await fetch(
        `/api/map/places/nearby?lat=${lat}&lon=${lon}&radius_m=${radius}&limit=20`
      )
      if (!res.ok) throw new Error('Failed to load nearby')
      const payload = await res.json()
      places.value = payload.data || []
      return places.value
    } finally {
      loading.value = false
    }
  }

  return { places, loading, fetchPlaces, fetchNearby }
})
