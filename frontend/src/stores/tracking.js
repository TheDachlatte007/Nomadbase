import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useTrackingStore = defineStore('tracking', () => {
  const expenses = ref([])
  const visits = ref([])
  const summary = ref(null)
  const loading = ref(false)

  async function fetchAll() {
    loading.value = true
    try {
      const [expRes, visRes, sumRes] = await Promise.all([
        fetch('/api/tracking/expenses'),
        fetch('/api/tracking/visits'),
        fetch('/api/tracking/expenses/summary'),
      ])
      expenses.value = (await expRes.json()).data || []
      visits.value = (await visRes.json()).data || []
      summary.value = await sumRes.json()
    } finally {
      loading.value = false
    }
  }

  async function addExpense(data) {
    const res = await fetch('/api/tracking/expenses', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!res.ok) throw new Error('Save expense failed')
    await fetchAll()
  }

  async function addVisit(data) {
    const res = await fetch('/api/tracking/visits', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!res.ok) throw new Error('Log visit failed')
    await fetchAll()
  }

  return { expenses, visits, summary, loading, fetchAll, addExpense, addVisit }
})
