import { defineStore } from 'pinia'
import { ref } from 'vue'
import { buildCacheKey, getCache, setCache } from '../utils/offlineDb.js'

const PAGE_SIZE = 100

export const usePlacesStore = defineStore('places', () => {
  const places = ref([])
  const loading = ref(false)
  const totalAvailable = ref(0)
  const hasMore = ref(false)
  const isOffline = ref(!navigator.onLine)
  const cacheSource = ref(null) // non-null when loaded from cache

  // Track current query params so "load more" can continue with same filters
  let _lastQuery = ''
  let _lastPlaceType = ''
  let _lastTagFilters = ''
  let _lastTripId = ''
  let _lastOffset = 0

  // Keep isOffline in sync with browser events
  window.addEventListener('online', () => { isOffline.value = false })
  window.addEventListener('offline', () => { isOffline.value = true })

  async function fetchPlaces(query = '', placeType = '', tagFilters = '', tripId = '') {
    loading.value = true
    cacheSource.value = null
    _lastQuery = query
    _lastPlaceType = placeType
    _lastTagFilters = tagFilters
    _lastTripId = tripId
    _lastOffset = 0

    const cacheKey = buildCacheKey(query, `${placeType}|${tagFilters}|${tripId || 'all-trips'}`, '')

    try {
      const params = new URLSearchParams()
      if (query) params.set('q', query)
      if (placeType) params.set('place_type', placeType)
      if (tagFilters) params.set('tag_filters', tagFilters)
      if (tripId) params.set('trip_id', tripId)
      params.set('limit', PAGE_SIZE)
      params.set('offset', 0)

      const res = await fetch(`/api/map/places?${params.toString()}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const payload = await res.json()

      places.value = payload.data || []
      totalAvailable.value = payload.total_available ?? payload.total
      hasMore.value = places.value.length < totalAvailable.value
      isOffline.value = false

      // Persist to IndexedDB (best-effort, non-blocking)
      if (places.value.length > 0) {
        setCache(cacheKey, places.value, totalAvailable.value).catch(() => {})
      }
    } catch {
      // Network or server error — try cache
      isOffline.value = true
      const cached = await getCache(cacheKey).catch(() => null)
      if (cached) {
        places.value = cached.places
        totalAvailable.value = cached.totalAvailable
        hasMore.value = false // no pagination when offline
        cacheSource.value = cacheKey
      } else {
        // Try "all" as a broader fallback
        const fallback = await getCache('all').catch(() => null)
        if (fallback) {
          places.value = fallback.places
          totalAvailable.value = fallback.totalAvailable
          hasMore.value = false
          cacheSource.value = 'all'
        } else {
          places.value = []
          totalAvailable.value = 0
          hasMore.value = false
        }
      }
    } finally {
      loading.value = false
    }
  }

  async function loadMore() {
    if (!hasMore.value || loading.value || isOffline.value) return
    loading.value = true
    _lastOffset += PAGE_SIZE
    try {
      const params = new URLSearchParams()
      if (_lastQuery) params.set('q', _lastQuery)
      if (_lastPlaceType) params.set('place_type', _lastPlaceType)
      if (_lastTagFilters) params.set('tag_filters', _lastTagFilters)
      if (_lastTripId) params.set('trip_id', _lastTripId)
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
    cacheSource.value = null
    try {
      const res = await fetch(
        `/api/map/places/nearby?lat=${lat}&lon=${lon}&radius_m=${radius}&limit=20`
      )
      if (!res.ok) throw new Error('Failed to load nearby')
      const payload = await res.json()
      places.value = payload.data || []
      totalAvailable.value = places.value.length
      isOffline.value = false
      return places.value
    } finally {
      loading.value = false
    }
  }

  return {
    places,
    loading,
    totalAvailable,
    hasMore,
    isOffline,
    cacheSource,
    fetchPlaces,
    loadMore,
    fetchNearby,
  }
})
