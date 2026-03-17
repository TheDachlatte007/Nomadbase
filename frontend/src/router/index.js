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
    { path: '/map', component: MapView },
    { path: '/saved', component: SavedView },
    { path: '/trips', component: TripsView },
    { path: '/tracking', component: TrackingView },
    { path: '/more', component: MoreView },
  ],
})
