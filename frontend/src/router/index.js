import { createRouter, createWebHistory } from 'vue-router'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/map' },
    { path: '/map', name: 'map', component: () => import('../views/MapView.vue') },
    { path: '/saved', name: 'saved', component: () => import('../views/SavedView.vue') },
    { path: '/trips', name: 'trips', component: () => import('../views/TripsView.vue') },
    { path: '/tracking', name: 'tracking', component: () => import('../views/TrackingView.vue') },
    { path: '/more', name: 'more', component: () => import('../views/MoreView.vue') },
  ],
})
