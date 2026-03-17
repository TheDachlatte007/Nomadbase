import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAdminStore = defineStore('admin', () => {
  const health = ref('checking')
  const systemStatus = ref(null)
  const imports = ref([])
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
    const result = await res.json()
    await Promise.all([fetchImports(), fetchStatus()])
    return result
  }

  return {
    health,
    systemStatus,
    imports,
    preferences,
    checkHealth,
    fetchStatus,
    fetchImports,
    fetchPreferences,
    savePreferences,
    importCity,
  }
})
