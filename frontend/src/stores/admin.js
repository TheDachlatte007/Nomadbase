import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAdminStore = defineStore('admin', () => {
  const health = ref('checking')
  const systemStatus = ref(null)
  const imports = ref([])
  const importJobs = ref([])
  const activeImportJobId = ref('')
  const preferences = ref({
    interests: [],
    dietary_filters: [],
    budget_level: 'balanced',
  })

  async function checkHealth() {
    try {
      const res = await fetch('/api/health', { headers: { Accept: 'application/json' } })
      const payload = await res.json()
      health.value = res.ok && payload.database ? 'ok' : 'degraded'
    } catch {
      health.value = 'offline'
    }
  }

  async function fetchStatus() {
    const res = await fetch('/api/admin/status')
    if (!res.ok) return
    systemStatus.value = await res.json()
  }

  async function fetchImports() {
    const res = await fetch('/api/admin/imports')
    if (!res.ok) return
    const payload = await res.json()
    imports.value = payload.data || []
  }

  async function fetchImportJobs() {
    const res = await fetch('/api/admin/import-jobs')
    if (!res.ok) return
    const payload = await res.json()
    importJobs.value = payload.data || []
    if (activeImportJobId.value) {
      const activeJob = importJobs.value.find((job) => job.id === activeImportJobId.value)
      if (activeJob && !['queued', 'running'].includes(activeJob.status)) {
        activeImportJobId.value = ''
      }
    }
  }

  async function fetchImportJob(jobId) {
    const res = await fetch(`/api/admin/import-jobs/${jobId}`)
    if (!res.ok) throw new Error('Import job not found')
    const payload = await res.json()
    const job = payload.data
    const existingIndex = importJobs.value.findIndex((item) => item.id === job.id)
    if (existingIndex >= 0) {
      importJobs.value.splice(existingIndex, 1, job)
    } else {
      importJobs.value = [job, ...importJobs.value].slice(0, 20)
    }
    return job
  }

  async function fetchPreferences() {
    const res = await fetch('/api/admin/preferences')
    if (!res.ok) return
    const payload = await res.json()
    preferences.value = payload.data || preferences.value
  }

  async function savePreferences(data) {
    const res = await fetch('/api/admin/preferences', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!res.ok) throw new Error('Save preferences failed')
    await fetchPreferences()
  }

  async function importCity(city, country) {
    const res = await fetch('/api/admin/imports', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ city, country }),
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || 'Import failed')
    }
    const payload = await res.json()
    const job = payload.data
    activeImportJobId.value = job.id
    await Promise.all([fetchImportJobs(), fetchStatus()])
    return job
  }

  async function waitForImportJob(jobId, options = {}) {
    const intervalMs = options.intervalMs ?? 3000
    const timeoutMs = options.timeoutMs ?? 180000
    const startedAt = Date.now()
    let job = await fetchImportJob(jobId)

    while (['queued', 'running'].includes(job.status)) {
      if (Date.now() - startedAt > timeoutMs) {
        throw new Error('Import is still running. Check back in a moment.')
      }

      await new Promise((resolve) => window.setTimeout(resolve, intervalMs))
      job = await fetchImportJob(jobId)
    }

    activeImportJobId.value = ''
    await Promise.all([fetchImports(), fetchImportJobs(), fetchStatus()])
    if (job.status === 'failed') {
      throw new Error(job.error || 'Import failed')
    }
    return job
  }

  return {
    health,
    systemStatus,
    imports,
    importJobs,
    activeImportJobId,
    preferences,
    checkHealth,
    fetchStatus,
    fetchImports,
    fetchImportJobs,
    fetchImportJob,
    fetchPreferences,
    savePreferences,
    importCity,
    waitForImportJob,
  }
})
