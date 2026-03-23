<template>
  <div class="panel active" style="display:grid">
    <article class="info-card">
      <p class="card-eyebrow">System</p>
      <h3>Alpha status and preferences.</h3>
      <div class="admin-grid">
        <div class="status-block">
          <p class="muted">{{ statusText }}</p>
          <div class="chip-row">
            <span v-for="(value, key) in metrics" :key="key" class="chip">
              {{ key }}: {{ value }}
            </span>
          </div>
        </div>
        <form class="preferences-form" @submit.prevent="onSavePreferences">
          <input v-model="prefForm.interests" type="text" placeholder="Interests, comma separated">
          <input v-model="prefForm.dietary_filters" type="text" placeholder="Dietary filters, comma separated">
          <select v-model="prefForm.budget_level">
            <option value="budget">Budget</option>
            <option value="balanced">Balanced</option>
            <option value="comfort">Comfort</option>
          </select>
          <button class="action-button" type="submit" :disabled="savingPrefs">
            {{ savingPrefs ? 'Saving...' : 'Save preferences' }}
          </button>
          <p v-if="prefFeedback" class="feedback">{{ prefFeedback }}</p>
        </form>
      </div>
    </article>

    <article class="info-card">
      <p class="card-eyebrow">Offline cache</p>
      <h3>What's stored on this device.</h3>
      <p class="muted" style="margin-bottom:12px">Places are cached in IndexedDB when loaded online and served offline for up to 7 days.</p>
      <div v-if="cacheLoading" class="empty-state">Loading cache info...</div>
      <div v-else-if="!cacheEntries.length" class="empty-state">No cached data yet — search places while online to populate the cache.</div>
      <div v-else class="imports-list">
        <div v-for="entry in cacheEntries" :key="entry.key" class="import-item">
          <div>
            <strong>{{ entry.key }}</strong>
            <p class="muted">{{ entry.count }} places · cached {{ formatAge(entry.cachedAt) }}</p>
          </div>
          <button class="action-button secondary-button" style="font-size:.8rem;padding:4px 10px" @click="onDeleteCache(entry.key)">Clear</button>
        </div>
      </div>
    </article>

    <article class="info-card">
      <p class="card-eyebrow">Deployment notes</p>
      <h3>Built for a private homeserver setup.</h3>
      <ul class="simple-list">
        <li>DB data persists in a named Docker volume — survives app updates.</li>
        <li>Alembic migrations run automatically before API boot.</li>
        <li>Frontend is built with Vue 3 + Vite, served by nginx.</li>
        <li>OSM data imports automatically when cities are added to trips.</li>
        <li>Alpha seed places load on first boot if no data exists.</li>
      </ul>
    </article>

    <article class="info-card wide-card">
      <div class="stack-between">
        <div>
          <p class="card-eyebrow">Import from OpenStreetMap</p>
          <h3>Load real places for a city.</h3>
          <p>
            Fetches restaurants, cafes, parks, attractions, viewpoints, and more from OSM via
            Overpass API. Also triggered automatically when you add a city to a trip.
          </p>
        </div>
        <form class="import-form" @submit.prevent="onImport">
          <input v-model="importForm.city" type="text" placeholder="City e.g. Vienna" required>
          <input v-model="importForm.country" type="text" placeholder="Country e.g. Austria">
          <button class="action-button" type="submit" :disabled="importing">{{ importText }}</button>
          <p v-if="importFeedback" class="feedback">{{ importFeedback }}</p>
        </form>
      </div>
      <p class="card-eyebrow" style="margin-top:18px">Imported regions</p>
      <div class="imports-list">
        <p v-if="!imports.length" class="empty-state">No import regions recorded yet.</p>
        <div v-for="item in imports" :key="item.region" class="import-item">
          <div>
            <strong>{{ item.region }}</strong>
            <p class="muted">
              {{ item.place_count }} places
              <span v-if="item.last_imported_at">· last import {{ formatTimestamp(item.last_imported_at) }}</span>
            </p>
          </div>
          <div class="entry-actions">
            <div class="chip-row">
              <span v-for="source in item.sources" :key="source" class="chip">{{ source }}</span>
            </div>
          </div>
        </div>
      </div>
    </article>

    <article class="info-card wide-card">
      <p class="card-eyebrow">Recent import jobs</p>
      <h3>See which import runs finished cleanly and which need another try.</h3>
      <div class="imports-list">
        <p v-if="!importJobs.length" class="empty-state">No import jobs recorded yet.</p>
        <div
          v-for="job in importJobs"
          :key="job.id"
          class="import-item"
          :class="{ 'import-item--failed': job.status === 'failed' }"
        >
          <div>
            <strong>{{ job.region || job.city }}<span v-if="job.country">, {{ job.country }}</span></strong>
            <p class="muted">
              {{ formatTimestamp(job.created_at) }}
              <span v-if="job.finished_at">→ {{ formatTimestamp(job.finished_at) }}</span>
            </p>
          </div>
          <div class="entry-actions">
            <div class="chip-row">
              <span class="chip" :class="{ 'chip--tag': job.status === 'failed' }">{{ job.status }}</span>
              <span class="chip">{{ job.imported_count }} imported</span>
              <span class="chip">{{ job.total_elements }} raw elements</span>
            </div>
            <button
              class="secondary-button action-button"
              type="button"
              :disabled="importing"
              @click="rerunImport(job)"
            >
              {{ importing ? 'Importing…' : 'Run again' }}
            </button>
          </div>
          <p v-if="job.error" class="muted">{{ job.error }}</p>
        </div>
      </div>
    </article>
  </div>
</template>

<script setup>
import { ref, computed, reactive, watch, onMounted } from 'vue'
import { useAdminStore } from '../stores/admin.js'
import { listCacheEntries, deleteCache } from '../utils/offlineDb.js'

const adminStore = useAdminStore()
const imports = computed(() => adminStore.imports)
const importJobs = computed(() => adminStore.importJobs)
const systemStatus = computed(() => adminStore.systemStatus)

const statusText = computed(() => {
  if (!systemStatus.value) return 'Waiting for system status...'
  const s = systemStatus.value
  return `Status: ${s.status}. Database: ${s.database ? 'ok' : 'down'}. Seed: ${s.alpha_seed_enabled ? 'on' : 'off'}.`
})
const metrics = computed(() => systemStatus.value?.metrics || {})

// Preferences
const prefForm = reactive({ interests: '', dietary_filters: '', budget_level: 'balanced' })
const savingPrefs = ref(false)
const prefFeedback = ref('')

watch(
  () => adminStore.preferences,
  (prefs) => {
    prefForm.interests = (prefs.interests || []).join(', ')
    prefForm.dietary_filters = (prefs.dietary_filters || []).join(', ')
    prefForm.budget_level = prefs.budget_level || 'balanced'
  },
  { immediate: true }
)

async function onSavePreferences() {
  savingPrefs.value = true
  prefFeedback.value = 'Saving...'
  try {
    await adminStore.savePreferences({
      interests: prefForm.interests
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean),
      dietary_filters: prefForm.dietary_filters
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean),
      budget_level: prefForm.budget_level,
    })
    prefFeedback.value = 'Saved'
  } catch {
    prefFeedback.value = 'Save failed'
  } finally {
    savingPrefs.value = false
  }
}

// Offline cache
const cacheEntries = ref([])
const cacheLoading = ref(false)

function formatAge(ts) {
  const mins = Math.round((Date.now() - ts) / 60000)
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.round(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.round(hrs / 24)}d ago`
}

function formatTimestamp(value) {
  if (!value) return 'n/a'
  return new Date(value).toLocaleString()
}

async function loadCacheEntries() {
  cacheLoading.value = true
  try {
    cacheEntries.value = await listCacheEntries()
    cacheEntries.value.sort((a, b) => b.cachedAt - a.cachedAt)
  } catch {
    cacheEntries.value = []
  } finally {
    cacheLoading.value = false
  }
}

async function onDeleteCache(key) {
  await deleteCache(key).catch(() => {})
  await loadCacheEntries()
}

onMounted(() => {
  loadCacheEntries().catch(() => {})
  adminStore.fetchImportJobs().catch(() => {})
})

// Import
const importForm = reactive({ city: '', country: '' })
const importing = ref(false)
const importFeedback = ref('')
const importText = computed(() => (importing.value ? 'Importing… (may take 60s)' : 'Import places'))

async function onImport() {
  await runImport(importForm.city, importForm.country || null, true)
}

async function runImport(city, country = null, resetForm = false) {
  importing.value = true
  importFeedback.value = `Fetching OSM data for ${city}…`
  try {
    const result = await adminStore.importCity(city, country)
    importFeedback.value = `Done — ${result.imported} places imported for ${result.region}.`
    if (resetForm) {
      importForm.city = ''
      importForm.country = ''
    }
  } catch (e) {
    importFeedback.value = `Error: ${e.message}`
  } finally {
    importing.value = false
  }
}

async function rerunImport(job) {
  await runImport(job.city, job.country || null, false)
}
</script>
