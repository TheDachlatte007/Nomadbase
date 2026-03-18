/**
 * Thin IndexedDB wrapper for NomadBase offline caching.
 *
 * DB: nomadbase-offline  (version 1)
 * Store: places_cache
 *   key: string (e.g. "all", "type:restaurant", "region:Vienna, Austria")
 *   value: { key, places, totalAvailable, cachedAt }
 */

const DB_NAME = 'nomadbase-offline'
const DB_VERSION = 1
const STORE = 'places_cache'
const MAX_AGE_MS = 7 * 24 * 60 * 60 * 1000 // 7 days

let _db = null

function openDb() {
  if (_db) return Promise.resolve(_db)
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION)
    req.onupgradeneeded = (e) => {
      const db = e.target.result
      if (!db.objectStoreNames.contains(STORE)) {
        db.createObjectStore(STORE, { keyPath: 'key' })
      }
    }
    req.onsuccess = (e) => {
      _db = e.target.result
      resolve(_db)
    }
    req.onerror = () => reject(req.error)
  })
}

function tx(mode) {
  return openDb().then((db) => db.transaction(STORE, mode).objectStore(STORE))
}

function wrap(req) {
  return new Promise((resolve, reject) => {
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error)
  })
}

/** Store a places result under the given cache key. */
export async function setCache(key, places, totalAvailable) {
  const store = await tx('readwrite')
  await wrap(store.put({ key, places, totalAvailable, cachedAt: Date.now() }))
}

/** Retrieve a cached result. Returns null if missing or stale. */
export async function getCache(key) {
  const store = await tx('readonly')
  const entry = await wrap(store.get(key))
  if (!entry) return null
  if (Date.now() - entry.cachedAt > MAX_AGE_MS) return null
  return entry
}

/** List all cache entries (key + cachedAt + count). */
export async function listCacheEntries() {
  const store = await tx('readonly')
  const all = await wrap(store.getAll())
  return all.map(({ key, places, cachedAt }) => ({
    key,
    count: places.length,
    cachedAt,
  }))
}

/** Delete a single cache entry by key. */
export async function deleteCache(key) {
  const store = await tx('readwrite')
  await wrap(store.delete(key))
}

/** Build a deterministic cache key from fetchPlaces arguments. */
export function buildCacheKey(query, placeType, tagFilters) {
  // Normalise so "all" is the key when nothing is filtered
  const q = (query || '').trim().toLowerCase()
  const t = (placeType || '').trim()
  const f = (tagFilters || '').trim()
  if (!q && !t && !f) return 'all'
  const parts = []
  if (q) parts.push(`q:${q}`)
  if (t) parts.push(`type:${t}`)
  if (f) parts.push(`tags:${f}`)
  return parts.join('|')
}
