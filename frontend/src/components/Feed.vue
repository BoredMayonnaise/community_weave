<template>
  <div class="feed-view">
    <!-- Search & Neighborhood Filters -->
    <div class="filter-card">
      <div class="search-row">
        <Search class="search-glyph" :size="16" />
        <input
          v-model="search"
          @input="debouncedFetch"
          type="text"
          class="form-input search-input"
          placeholder="Search requests & offers..."
        />
        <button v-if="search" class="clear-search-btn" @click="clearSearch" title="Clear search">
          <X :size="14" />
        </button>
      </div>

      <div class="filter-row">
        <select v-model="selectedNeighborhood" @change="fetchPosts" class="form-select filter-select">
          <option value="">All Areas / Barangays</option>
          <option v-for="n in neighborhoods" :key="n" :value="n">{{ n }}</option>
        </select>

        <select v-model="selectedCategory" @change="fetchPosts" class="form-select filter-select">
          <option value="All">All Categories</option>
          <option value="Tools">Tools</option>
          <option value="Food">Food</option>
          <option value="Goods">Goods</option>
          <option value="Skills">Skills</option>
          <option value="Help">Help</option>
          <option value="Other">Other</option>
        </select>
      </div>

      <!-- View Mode & Type Bar -->
      <div class="toolbar-row">
        <!-- Segmented Type Selector -->
        <div class="type-segmented">
          <button
            type="button"
            :class="['segmented-btn', { active: activeType === '' }]"
            @click="setType('')"
          >
            All
          </button>
          <button
            type="button"
            :class="['segmented-btn', { active: activeType === 'request' }]"
            @click="setType('request')"
          >
            Requests
          </button>
          <button
            type="button"
            :class="['segmented-btn', { active: activeType === 'offer' }]"
            @click="setType('offer')"
          >
            Offers
          </button>
        </div>

        <!-- Action Buttons -->
        <div style="display: flex; gap: 6px; margin-left: auto;">
          <button
            type="button"
            class="map-shortcut-btn"
            @click="fetchPosts"
            :disabled="loading"
            title="Refresh latest posts"
          >
            <RotateCw :size="13" :class="{ 'spin-icon': loading }" />
            <span>{{ loading ? '...' : 'Refresh' }}</span>
          </button>

          <button
            type="button"
            class="map-shortcut-btn"
            @click="state.currentTab = 'map'"
            title="Explore neighborhood on map"
          >
            <Map :size="13" />
            <span>Map</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Posts Feed -->
    <div v-if="loading && posts.length === 0" class="state-msg">
      <div class="spinner"></div>
      <p>Finding neighborhood posts...</p>
    </div>

    <div v-else-if="!loading && posts.length === 0" class="empty-box card">
      <Sprout class="empty-icon" :size="40" />
      <h4>No posts found</h4>
      <p>Be the first neighbor to post a request or offer in this area!</p>
      <button class="btn btn-primary" style="margin-top: 12px" @click="goToCreate">
        <Plus class="inline-icon" :size="16" /> Create Post
      </button>
    </div>

    <div v-else class="posts-list-wrap">
      <!-- Subtle top refreshing bar when re-filtering -->
      <div v-if="loading" class="refresh-indicator-bar">
        <div class="refresh-bar-indeterminate"></div>
      </div>

      <TransitionGroup name="post-fade" tag="div" :class="['posts-list', { 'feed-refreshing': loading }]">
        <div
          v-for="post in posts"
          :key="post.id"
          class="card post-card"
          @click="openPost(post)"
        >
          <div class="post-header">
            <span :class="['badge', post.type === 'offer' ? 'badge-offer' : 'badge-request']">
              <component :is="post.type === 'offer' ? Gift : HandHelping" class="inline-icon" :size="12" />
              {{ post.type === 'offer' ? 'Offer' : 'Request' }}
            </span>
            <span class="badge badge-category">{{ post.category }}</span>
            <span class="post-time">{{ formatDate(post.created_at) }}</span>
          </div>

          <h3 class="post-title">{{ post.title }}</h3>
          <p class="post-desc">{{ post.description }}</p>

          <div class="post-footer">
            <span class="location-tag" :title="post.address && post.address !== post.neighborhood ? `${post.neighborhood} • ${post.address}` : post.neighborhood">
              <MapPin class="loc-pin" :size="13" />
              <span class="loc-main">{{ post.neighborhood }}</span>
              <span v-if="post.address && post.address.trim() && post.address !== post.neighborhood" class="loc-sub">
                • {{ post.address }}
              </span>
            </span>
            <span class="author-tag">
              <span class="author-avatar-dot">{{ (post.author_display_name || 'N').charAt(0).toUpperCase() }}</span>
              <span>{{ post.author_display_name }}</span>
            </span>
          </div>
        </div>
      </TransitionGroup>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { Sprout, Search, X, Plus, Gift, HandHelping, MapPin, Map, RotateCw } from 'lucide-vue-next'
import { state } from '../state.js'
import { api } from '../api.js'

const posts = ref([])
const loading = ref(false)
const search = ref('')
const activeType = ref('')
const selectedNeighborhood = ref('')
const selectedCategory = ref('All')

const neighborhoods = ref(['Downtown', 'North Hills', 'Riverside', 'West End', 'Oakridge'])

let debounceTimer = null
function debouncedFetch() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    fetchPosts()
  }, 300)
}

onUnmounted(() => {
  if (debounceTimer) clearTimeout(debounceTimer)
})

function setType(type) {
  activeType.value = type
  fetchPosts()
}

async function fetchPosts() {
  loading.value = true
  try {
    const params = { status: 'open' }
    if (activeType.value) params.type = activeType.value
    if (selectedNeighborhood.value) params.neighborhood = selectedNeighborhood.value
    if (selectedCategory.value !== 'All') params.category = selectedCategory.value
    if (search.value.trim()) params.search = search.value.trim()

    posts.value = await api.getPosts(params)

    // Collect any new unique neighborhoods from posts
    posts.value.forEach(p => {
      if (p.neighborhood && !neighborhoods.value.includes(p.neighborhood)) {
        neighborhoods.value.push(p.neighborhood)
      }
    })
  } catch (err) {
    state.showToast(err.message || 'Could not load posts')
  } finally {
    loading.value = false
  }
}

function clearSearch() {
  search.value = ''
  fetchPosts()
}

function openPost(post) {
  state.selectedPost = post
}

function goToCreate() {
  state.currentTab = 'create'
}

function formatDate(isoStr) {
  if (!isoStr) return ''
  const date = new Date(isoStr)
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

onMounted(() => {
  fetchPosts()
  api.getNeighborhoods().then(res => { if (res?.length) neighborhoods.value = res }).catch(() => {})
})
</script>

<style scoped>
.filter-card {
  background: #ffffff;
  border-radius: var(--radius-md);
  padding: 14px;
  border: 1px solid rgba(226, 232, 240, 0.85);
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  box-shadow: var(--shadow-sm);
}

.search-row {
  position: relative;
}

.search-glyph {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
  pointer-events: none;
}

.search-input {
  padding: 10px 34px 10px 36px;
  font-size: 0.9rem;
  border-radius: 9999px;
  background: #f8fafc;
  border: 1px solid var(--border-color);
  width: 100%;
  outline: none;
  transition: all 0.15s ease;
}

.search-input:focus {
  background: #ffffff;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-glow);
}

.clear-search-btn {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2px;
}

.clear-search-btn:hover {
  color: var(--text-main);
}

.filter-row {
  display: flex;
  gap: 8px;
}

.filter-select {
  flex: 1;
  padding: 8px 12px;
  font-size: 0.84rem;
  border-radius: 9999px;
  background: #f8fafc;
  border: 1px solid var(--border-color);
  color: #334155;
  font-weight: 500;
}

.filter-select:focus {
  background: #ffffff;
  border-color: var(--primary);
}

.toolbar-row {
  display: flex;
  align-items: center;
  gap: 10px;
  justify-content: space-between;
}

.type-segmented {
  flex: 1;
  display: flex;
  background: #f1f5f9;
  padding: 3px;
  border-radius: 10px;
}

.segmented-btn {
  flex: 1;
  border: none;
  background: transparent;
  padding: 7px;
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--text-muted);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s cubic-bezier(0.16, 1, 0.3, 1);
}

.segmented-btn.active {
  background: #ffffff;
  color: var(--text-main);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
}

.map-shortcut-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: var(--primary-light);
  border: 1px solid rgba(13, 148, 136, 0.25);
  color: var(--primary);
  font-size: 0.78rem;
  font-weight: 700;
  padding: 6px 12px;
  border-radius: 9999px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.map-shortcut-btn:hover {
  background: #ccfbf1;
  border-color: var(--primary);
  transform: translateY(-0.5px);
}

.posts-list {
  display: flex;
  flex-direction: column;
}

.post-card {
  cursor: pointer;
  background: #ffffff;
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: var(--radius-md);
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: var(--shadow-sm);
  transition: transform 0.18s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.18s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.18s ease;
}

.post-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: rgba(13, 148, 136, 0.3);
}

.post-card:active {
  transform: scale(0.99);
}

.post-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.post-time {
  margin-left: auto;
  font-size: 0.72rem;
  color: var(--text-muted);
  font-weight: 500;
}

.post-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 6px;
  line-height: 1.35;
  letter-spacing: -0.015em;
}

.post-desc {
  font-size: 0.88rem;
  color: #475569;
  line-height: 1.5;
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.post-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.8rem;
  color: #64748b;
  border-top: 1px solid #f1f5f9;
  padding-top: 10px;
}

.location-tag {
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  max-width: 68%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.loc-pin {
  color: var(--primary);
  flex-shrink: 0;
}

.loc-main {
  font-weight: 600;
  color: #334155;
}

.loc-sub {
  color: #64748b;
  font-weight: 400;
}

.author-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: #334155;
}

.author-avatar-dot {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: linear-gradient(135deg, #0d9488 0%, #0284c7 100%);
  color: #ffffff;
  font-size: 0.65rem;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.empty-box {
  text-align: center;
  padding: 40px 20px;
}

.state-msg {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px;
  color: var(--text-muted);
  font-size: 0.9rem;
}

.spinner {
  width: 28px;
  height: 28px;
  border: 3px solid #e2e8f0;
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Smooth Transitions & Loading State */
.posts-list-wrap {
  position: relative;
  display: flex;
  flex-direction: column;
}

.refresh-indicator-bar {
  height: 3px;
  width: 100%;
  background: #f1f5f9;
  border-radius: 9999px;
  overflow: hidden;
  margin-bottom: 8px;
}

.refresh-bar-indeterminate {
  width: 40%;
  height: 100%;
  background: linear-gradient(90deg, #0d9488, #14b8a6);
  border-radius: 9999px;
  animation: barSlide 1s cubic-bezier(0.4, 0, 0.2, 1) infinite;
}

@keyframes barSlide {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(350%); }
}

.feed-refreshing {
  opacity: 0.65;
  transition: opacity 0.2s ease;
  pointer-events: none;
}

/* Vue TransitionGroup for post items */
.post-fade-enter-active,
.post-fade-leave-active {
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.post-fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.post-fade-leave-to {
  opacity: 0;
  transform: scale(0.96);
}

/* Tablet Responsive Grid */
@media (min-width: 640px) {
  .posts-list {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 14px;
  }
  .filter-card {
    padding: 14px 18px;
  }
}
</style>
