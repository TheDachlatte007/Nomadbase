import { defineStore } from 'pinia'
import { ref } from 'vue'

const PAGE_SIZE = 100

export const usePlacesStore = defineStore('places', () => {
  const places = ref([])
  const loading = ref(false)
  const totalAvailable = ref(0)
  const hasMore = ref(false)

  // Track current query params so "load more" can continue with same filters
  let _lastQuery = ''
  let _lastPlaceType = ''
  let _lastTagFilters = ''
  let _lastOffset = 0

  async function fetchPlaces(query = '', placeType = '', tagFilters = '') {
    loading.value = true
    _lastQuery = query
    _lastPlaceType = placeType
    _lastTagFilters = tagFilters
    _lastOffset = 0
    try {
      const params = new URLSearchParams()
      if (query) params.set('q', query)
      if (placeType) params.set('place_type', placeType)
      if (tagFilters) params.set('tag_filters', tagFilters)
      params.set('limit', PAGE_SIZE)
      params.set('offset', 0)
      const res = await fetch(`/api/map/places?${params.toString()}`)
      if (!res.ok) throw new Error('Failed to load places')
      const payload = await res.json()
      places.value = payload.data || []
      totalAvailable.value = payload.total_available ?? payload.total
      hasMore.value = places.value.length < totalAvailable.value
    } finally {
      loading.value = false
    }
  }

  async function loadMore() {
    if (!hasMore.value || loading.value) return
    loading.value = true
    _lastOffset += PAGE_SIZE
    try {
      const params = new URLSearchParams()
      if (_lastQuery) params.set('q', _lastQuery)
      if (_lastPlaceType) params.set('place_type', _lastPlaceType)
      if (_lastTagFilters) params.set('tag_filters', _lastTagFilters)
      params.set('limit', PAGE_SIZE)
      params.set('offset', _lastOffset)
      const res = await fetch(`/api/map/places?${params.toString()}`)
      if (!res.ok) throw new Error('Failed to load more places')
      const payload = await res.json()
      places.value = [...places.value, ...(payload.data || [])]
      totalAvailable.value = payload.total_available ?? payload.total
      hasMore.value = places.value.length < totalAvailable.value
    } finally {
      loading.value = false
    }
  }

  async function fetchNearby(lat, lon, radius = 2500) {
    loading.value = true
    hasMore.value = false
    try {
      const res = await fetch(
        `/api/map/places/nearby?lat=${lat}&lon=${lon}&radius_m=${radius}&limit=20`
      )
      if (!res.ok) throw new Error('Failed to load nearby')
      const payload = await res.json()
      places.value = payload.data || []
      totalAvailable.value = places.value.length
      return places.value
    } finally {
      loading.value = false
    }
  }

  return { places, loading, totalAvailable, hasMore, fetchPlaces, loadMore, fetchNearby }
})
