<template>
  <div class="explore-map-view">
    <!-- Map Top Filter Bar -->
    <div class="explore-top-bar card">
      <div class="explore-search-row">
        <Search class="search-icon" :size="15" />
        <input
          v-model="searchQuery"
          type="text"
          class="explore-search-input"
          placeholder="Filter barangay, tools, food..."
          @input="applyFilters"
        />
        <button v-if="searchQuery" class="clear-search-btn" @click="clearSearch" title="Clear search">
          <X :size="14" />
        </button>
      </div>

      <div class="explore-filter-pills">
        <button
          type="button"
          :class="['filter-pill', { active: activeType === '' }]"
          @click="setType('')"
        >
          <span>All</span>
          <span class="pill-count">{{ filteredPosts.length }}</span>
        </button>
        <button
          type="button"
          :class="['filter-pill', 'pill-offer', { active: activeType === 'offer' }]"
          @click="setType('offer')"
        >
          <Gift :size="12" class="pill-icon" />
          <span>Offers</span>
          <span class="pill-count">{{ offerCount }}</span>
        </button>
        <button
          type="button"
          :class="['filter-pill', 'pill-request', { active: activeType === 'request' }]"
          @click="setType('request')"
        >
          <HandHelping :size="12" class="pill-icon" />
          <span>Requests</span>
          <span class="pill-count">{{ requestCount }}</span>
        </button>

        <div class="brgy-select-wrap">
          <MapPin :size="12" class="brgy-select-pin" />
          <select v-model="selectedNeighborhood" class="explore-brgy-select" @change="applyFilters">
            <option value="">All Barangays</option>
            <option v-for="n in neighborhoods" :key="n" :value="n">{{ n }}</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Map Canvas Container -->
    <div class="map-stage">
      <div ref="mapContainer" class="full-leaflet-map"></div>

      <!-- Top Safety Indicator Pill -->
      <div class="map-safety-flag">
        <ShieldCheck :size="13" class="safety-icon-svg" />
        <span>Approx. ~400m Safe Radius Zones</span>
      </div>

      <!-- Floating Controls -->
      <div class="map-stage-controls">
        <button class="stage-locate-btn" @click="centerOnUser" :disabled="locating" title="Center map on my location">
          <LocateFixed v-if="!locating" :size="15" />
          <div v-else class="stage-spinner"></div>
          <span>{{ locating ? 'Locating...' : 'My Location' }}</span>
        </button>

        <div class="stage-legend">
          <span class="legend-chip"><span class="legend-dot dot-offer"></span> Offers</span>
          <span class="legend-chip"><span class="legend-dot dot-request"></span> Requests</span>
        </div>
      </div>

      <!-- Selected Post Floating Bottom Card -->
      <transition name="slide-up">
        <div v-if="selectedPostPreview" class="map-post-preview-card card" @click="openPost(selectedPostPreview)">
          <div class="preview-header">
            <span :class="['preview-badge', selectedPostPreview.type === 'offer' ? 'badge-offer' : 'badge-request']">
              <component :is="selectedPostPreview.type === 'offer' ? Gift : HandHelping" :size="12" class="badge-icon-svg" />
              <span>{{ selectedPostPreview.type === 'offer' ? 'Offer' : 'Request' }}</span>
            </span>
            <span class="preview-cat">{{ selectedPostPreview.category || 'General' }}</span>
            <button class="preview-close-btn" @click.stop="selectedPostPreview = null" title="Close preview">
              <X :size="14" />
            </button>
          </div>

          <h4 class="preview-title">
            {{ selectedPostPreview.title }}
          </h4>
          <p class="preview-desc">{{ truncateDesc(selectedPostPreview.description) }}</p>

          <div class="preview-meta-row">
            <div class="preview-loc">
              <MapPin :size="13" />
              <span>Approx. Area: {{ selectedPostPreview.neighborhood || 'Local Area' }}</span>
            </div>
            <button class="btn btn-primary btn-sm preview-action-btn" @click.stop="openPost(selectedPostPreview)">
              <span>View & Contact</span>
              <ChevronRight :size="14" />
            </button>
          </div>
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import {
  Search, X, LocateFixed, ShieldCheck, MapPin, Gift, HandHelping, ChevronRight
} from 'lucide-vue-next'
import { state } from '../state.js'
import { api } from '../api.js'
import { geo } from '../geo.js'

const mapContainer = ref(null)
const posts = ref([])
const loading = ref(false)
const locating = ref(false)
const searchQuery = ref('')
const activeType = ref('')
const selectedNeighborhood = ref('')
const neighborhoods = ref(['Downtown', 'North Hills', 'Riverside', 'West End', 'Oakridge'])
const selectedPostPreview = ref(null)

let map = null
let markersLayer = null
let userMarker = null

const filteredPosts = computed(() => {
  return posts.value.filter(post => {
    if (activeType.value && post.type !== activeType.value) return false
    if (selectedNeighborhood.value && post.neighborhood !== selectedNeighborhood.value) return false
    if (searchQuery.value.trim()) {
      const q = searchQuery.value.toLowerCase().trim()
      const titleMatch = (post.title || '').toLowerCase().includes(q)
      const descMatch = (post.description || '').toLowerCase().includes(q)
      const nMatch = (post.neighborhood || '').toLowerCase().includes(q)
      const cMatch = (post.category || '').toLowerCase().includes(q)
      if (!titleMatch && !descMatch && !nMatch && !cMatch) return false
    }
    return true
  })
})

const offerCount = computed(() => {
  return posts.value.filter(p => p.type === 'offer').length
})

const requestCount = computed(() => {
  return posts.value.filter(p => p.type === 'request').length
})

function setType(type) {
  activeType.value = type
  renderMarkers()
}

function clearSearch() {
  searchQuery.value = ''
  renderMarkers()
}

function applyFilters() {
  renderMarkers()
}

function truncateDesc(desc) {
  if (!desc) return ''
  return desc.length > 90 ? desc.slice(0, 90) + '...' : desc
}

function openPost(post) {
  state.selectedPost = post
}

function createAreaIcon(type) {
  const isOffer = type === 'offer'
  const badgeClass = isOffer ? 'area-badge-offer' : 'area-badge-request'
  const label = isOffer ? 'Offer' : 'Request'
  const svgIcon = isOffer
    ? `<svg class="zone-svg-icon" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 12 20 22 4 22 4 12"/><rect width="20" height="5" x="2" y="7"/><line x1="12" x2="12" y1="22" y2="7"/><path d="M12 7H7.5a2.5 2.5 0 0 1 0-5C11 2 12 7 12 7z"/><path d="M12 7h4.5a2.5 2.5 0 0 0 0-5C13 2 12 7 12 7z"/></svg>`
    : `<svg class="zone-svg-icon" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M11 12h2a2 2 0 1 0 0-4h-3c-.6 0-1.1.2-1.4.6L3 14"/><path d="m7 18 1.6-1.4c.3-.4.8-.6 1.4-.6h4c1.1 0 2.1-.4 2.8-1.2l4.6-4.4a2 2 0 0 0-2.8-2.8L13 11"/><path d="M2 14v6"/><path d="M6 18v2"/></svg>`

  const html = `
    <div class="area-zone-pill ${badgeClass}">
      ${svgIcon}
      <span class="zone-pill-text">${label}</span>
    </div>
  `
  return L.divIcon({
    className: 'custom-zone-marker',
    html,
    iconSize: [76, 26],
    iconAnchor: [38, 13],
    popupAnchor: [0, -14]
  })
}

function createUserIcon() {
  const html = `
    <div class="user-pulse-marker">
      <div class="pulse-ring"></div>
      <div class="user-dot"></div>
    </div>
  `
  return L.divIcon({
    className: 'custom-user-marker',
    html,
    iconSize: [24, 24],
    iconAnchor: [12, 12]
  })
}

function initMap() {
  if (!mapContainer.value) return

  const defaultCenter = [37.7749, -122.4194]

  map = L.map(mapContainer.value, {
    zoomControl: false,
    attributionControl: false
  }).setView(defaultCenter, 13)

  // Standard OpenStreetMap tiles (100% free, no API key required)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map)

  L.control.zoom({ position: 'topright' }).addTo(map)

  markersLayer = L.layerGroup().addTo(map)

  renderMarkers()
}

function renderMarkers(fit = false) {
  if (!map || !markersLayer) return
  markersLayer.clearLayers()

  const bounds = []

  filteredPosts.value.forEach((post, idx) => {
    const coords = geo.getCoordinatesForPost(post, idx)
    bounds.push(coords)

    const isOffer = post.type === 'offer'
    const primaryColor = isOffer ? '#059669' : '#2563eb'
    const fillColor = isOffer ? '#10b981' : '#3b82f6'

    // Approximate safety radius perimeter circle (~400m)
    const radiusCircle = L.circle(coords, {
      radius: 400,
      color: primaryColor,
      weight: 1.5,
      opacity: 0.65,
      dashArray: '4, 5',
      fillColor: fillColor,
      fillOpacity: 0.16
    })

    const marker = L.marker(coords, {
      icon: createAreaIcon(post.type)
    })

    // Click on circle or marker sets active preview card
    const handleSelect = () => {
      selectedPostPreview.value = post
      map.panTo(coords, { animate: true, duration: 0.6 })
    }

    marker.on('click', handleSelect)
    radiusCircle.on('click', handleSelect)

    markersLayer.addLayer(radiusCircle)
    markersLayer.addLayer(marker)
  })

  if (fit && bounds.length > 0 && map) {
    map.fitBounds(bounds, { padding: [50, 50], maxZoom: 14 })
  }
}

async function fetchPosts() {
  loading.value = true
  try {
    const res = await api.getPosts({ status: 'open' })
    posts.value = res || []
    posts.value.forEach(p => {
      if (p.neighborhood && !neighborhoods.value.includes(p.neighborhood)) {
        neighborhoods.value.push(p.neighborhood)
      }
    })
    renderMarkers(true)
  } catch (err) {
    state.showToast(err.message || 'Failed to load map posts')
  } finally {
    loading.value = false
  }
}

async function centerOnUser() {
  locating.value = true
  try {
    const pos = await geo.locateUser()
    const userCoords = [pos.latitude, pos.longitude]

    if (map) {
      if (userMarker) {
        userMarker.setLatLng(userCoords)
      } else {
        userMarker = L.marker(userCoords, {
          icon: createUserIcon(),
          zIndexOffset: 1000
        }).addTo(map)
        userMarker.bindTooltip('You are here', { permanent: false, direction: 'top' })
      }
      map.flyTo(userCoords, 14, { duration: 1.2 })
    }
  } catch (err) {
    state.showToast(err.message || 'Could not locate device')
  } finally {
    locating.value = false
  }
}

onMounted(() => {
  fetchPosts()
  api.getNeighborhoods().then(res => {
    if (res?.length) neighborhoods.value = res
  }).catch(() => {})

  nextTick(() => {
    initMap()
  })
})

onUnmounted(() => {
  if (map) {
    map.remove()
    map = null
  }
})
</script>

<style scoped>
.explore-map-view {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  height: 100%;
  margin-top: -8px;
}

.explore-top-bar {
  padding: 10px 12px;
  margin-bottom: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: rgba(255, 255, 255, 0.96);
  backdrop-filter: blur(12px);
  border-radius: 16px;
  box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
}

.explore-search-row {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 12px;
  color: #94a3b8;
  pointer-events: none;
}

.explore-search-input {
  width: 100%;
  padding: 7px 32px 7px 34px;
  border-radius: 9999px;
  border: 1px solid var(--border-color);
  background: #f8fafc;
  font-size: 0.85rem;
  color: #0f172a;
  outline: none;
  transition: all 0.15s ease;
}

.explore-search-input:focus {
  border-color: var(--primary);
  background: #ffffff;
  box-shadow: 0 0 0 3px var(--primary-light);
}

.clear-search-btn {
  position: absolute;
  right: 10px;
  background: none;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.explore-filter-pills {
  display: flex;
  align-items: center;
  gap: 6px;
  overflow-x: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;
  padding-bottom: 2px;
}

.explore-filter-pills::-webkit-scrollbar {
  display: none;
}

.filter-pill {
  border: 1px solid var(--border-color);
  background: #ffffff;
  color: #475569;
  font-size: 0.72rem;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 9999px;
  white-space: nowrap;
  cursor: pointer;
  transition: all 0.15s ease;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.filter-pill:hover {
  border-color: #cbd5e1;
  background: #f8fafc;
}

.filter-pill.active {
  background: var(--primary);
  color: #ffffff;
  border-color: var(--primary);
  box-shadow: 0 2px 6px rgba(13, 148, 136, 0.3);
}

.filter-pill.pill-offer.active {
  background: #059669;
  border-color: #059669;
}

.filter-pill.pill-request.active {
  background: #2563eb;
  border-color: #2563eb;
}

.pill-icon {
  flex-shrink: 0;
}

.pill-count {
  font-size: 0.65rem;
  opacity: 0.8;
  background: rgba(0, 0, 0, 0.08);
  padding: 1px 5px;
  border-radius: 9999px;
  margin-left: 2px;
}

.filter-pill.active .pill-count {
  background: rgba(255, 255, 255, 0.25);
  color: #ffffff;
}

.brgy-select-wrap {
  position: relative;
  display: inline-flex;
  align-items: center;
  flex-shrink: 0;
}

.brgy-select-pin {
  position: absolute;
  left: 9px;
  color: #64748b;
  pointer-events: none;
}

.explore-brgy-select {
  border: 1px solid var(--border-color);
  background: #ffffff;
  color: #334155;
  font-size: 0.72rem;
  font-weight: 600;
  padding: 4px 10px 4px 26px;
  border-radius: 9999px;
  outline: none;
  cursor: pointer;
  white-space: nowrap;
}

/* Map Stage */
.map-stage {
  position: relative;
  flex: 1;
  min-height: 480px;
  border-radius: 18px;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.08);
  border: 1px solid var(--border-color);
}

.full-leaflet-map {
  width: 100%;
  height: 100%;
  min-height: 480px;
  background: #f1f5f9;
}

.map-safety-flag {
  position: absolute;
  top: 10px;
  left: 12px;
  z-index: 1000;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: rgba(240, 253, 250, 0.95);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(13, 148, 136, 0.3);
  color: #0f766e;
  font-size: 0.68rem;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 9999px;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.08);
  pointer-events: none;
}

.safety-icon-svg {
  color: #0d9488;
}

.map-stage-controls {
  position: absolute;
  bottom: 12px;
  left: 12px;
  right: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  z-index: 1000;
  pointer-events: none;
}

.stage-locate-btn {
  pointer-events: auto;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #ffffff;
  border: 1px solid var(--border-color);
  border-radius: 9999px;
  padding: 7px 13px;
  font-size: 0.78rem;
  font-weight: 600;
  color: #1e293b;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.15);
  cursor: pointer;
  transition: all 0.15s ease;
}

.stage-locate-btn:hover {
  background: var(--primary-light);
  color: var(--primary);
  border-color: var(--primary);
}

.stage-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(13, 148, 136, 0.3);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.stage-legend {
  pointer-events: auto;
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(8px);
  border: 1px solid var(--border-color);
  border-radius: 9999px;
  padding: 6px 12px;
  font-size: 0.72rem;
  font-weight: 600;
  color: #475569;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.1);
}

.legend-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.dot-offer {
  background-color: #059669;
}

.dot-request {
  background-color: #2563eb;
}

/* Floating Bottom Card Preview */
.map-post-preview-card {
  position: absolute;
  bottom: 58px;
  left: 12px;
  right: 12px;
  z-index: 1010;
  padding: 14px 16px;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(14px);
  border: 1px solid rgba(226, 232, 240, 0.95);
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.18);
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.map-post-preview-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.22);
}

.preview-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.preview-badge {
  font-size: 0.68rem;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 9999px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.badge-icon-svg {
  flex-shrink: 0;
}

.preview-cat {
  font-size: 0.72rem;
  color: #94a3b8;
  font-weight: 600;
}

.preview-close-btn {
  margin-left: auto;
  background: none;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  padding: 3px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}

.preview-close-btn:hover {
  color: #334155;
  background: #f1f5f9;
}

.preview-title {
  font-size: 0.98rem;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.25;
  margin-bottom: 4px;
}

.preview-desc {
  font-size: 0.8rem;
  color: #64748b;
  line-height: 1.4;
  margin-bottom: 10px;
}

.preview-meta-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding-top: 8px;
  border-top: 1px solid #f1f5f9;
}

.preview-loc {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.74rem;
  font-weight: 600;
  color: #0f766e;
}

.preview-action-btn {
  padding: 6px 12px;
  font-size: 0.75rem;
  border-radius: 9999px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

/* Slide up animation */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(20px);
  opacity: 0;
}
</style>
