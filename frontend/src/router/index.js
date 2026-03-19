import { createRouter, createWebHistory } from 'vue-router'
import MapView from '../views/MapView.vue'
import SavedView from '../views/SavedView.vue'
import TripsView from '../views/TripsView.vue'
import TrackingView from '../views/TrackingView.vue'
import MoreView from '../views/MoreView.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/map' },
    { path: '/map', name: 'map', component: MapView },
    { path: '/saved', name: 'saved', component: SavedView },
    { path: '/trips', name: 'trips', component: TripsView },
    { path: '/tracking', name: 'tracking', component: TrackingView },
    { path: '/more', name: 'more', component: MoreView },
  ],
})
