<template>
  <div class="panel active" style="display:grid">
    <article class="info-card wide-card">
      <p class="card-eyebrow">Saved places</p>
      <h3>Want to visit, visited, favorite.</h3>
      <p>Save places from the Map tab — they'll appear here grouped by status.</p>
      <div class="saved-grid">
        <p v-if="loading" class="empty-state">Loading...</p>
        <p v-else-if="!saved.length" class="empty-state">No saved places yet.</p>
        <article v-for="s in saved" :key="s.id" class="saved-card">
          <div>
            <p class="card-eyebrow">{{ s.status.replace(/_/g, ' ') }}</p>
            <h4>{{ s.place.name }}</h4>
            <p class="muted">{{ s.place.region || 'unknown' }} · {{ s.place.place_type }}</p>
          </div>
          <p>{{ s.notes || s.place.description || 'No notes yet.' }}</p>
          <div class="chip-row">
            <span class="chip">{{ s.place.place_type }}</span>
            <span class="chip">{{ s.place.source }}</span>
          </div>
          <button
            class="unsave-button"
            :disabled="removing === s.id"
            @click="onRemove(s.id)"
          >{{ removing === s.id ? 'Removing...' : 'Remove' }}</button>
        </article>
      </div>
    </article>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useSavedStore } from '../stores/saved.js'

const savedStore = useSavedStore()
const saved = computed(() => savedStore.savedPlaces)
const loading = computed(() => savedStore.loading)
const removing = ref(null)

async function onRemove(id) {
  removing.value = id
  try {
    await savedStore.deleteSaved(id)
  } finally {
    removing.value = null
  }
}
</script>
