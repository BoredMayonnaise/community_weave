<template>
  <div class="feed-view">
    <!-- Search & Neighborhood Filters -->
    <div class="filter-card">
      <div class="search-row">
        <input
          v-model="search"
          @input="debouncedFetch"
          type="text"
          class="form-input search-input"
          placeholder="🔍 Search requests & offers..."
        />
      </div>

      <div class="filter-row">
        <select v-model="selectedNeighborhood" @change="fetchPosts" class="form-select filter-select">
          <option value="">All Neighborhoods</option>
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
    </div>

    <!-- Posts Feed -->
    <div v-if="loading" class="state-msg">
      <div class="spinner"></div>
      <p>Finding neighborhood posts...</p>
    </div>

    <div v-else-if="posts.length === 0" class="empty-box card">
      <div class="empty-icon">🌱</div>
      <h4>No posts found</h4>
      <p>Be the first neighbor to post a request or offer in this area!</p>
      <button class="btn btn-primary" style="margin-top: 12px" @click="goToCreate">
        + Create Post
      </button>
    </div>

    <div v-else class="posts-list">
      <div
        v-for="post in posts"
        :key="post.id"
        class="card post-card"
        @click="openPost(post)"
      >
        <div class="post-header">
          <span :class="['badge', post.type === 'offer' ? 'badge-offer' : 'badge-request']">
            {{ post.type === 'offer' ? '🎁 Offer' : '🙋 Request' }}
          </span>
          <span class="badge badge-category">{{ post.category }}</span>
          <span class="post-time">{{ formatDate(post.created_at) }}</span>
        </div>

        <h3 class="post-title">{{ post.title }}</h3>
        <p class="post-desc">{{ post.description }}</p>

        <div class="post-footer">
          <span class="location-tag">📍 {{ post.neighborhood }}</span>
          <span class="author-tag">👤 {{ post.author_display_name }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
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
})
</script>

<style scoped>
.filter-card {
  background: #ffffff;
  border-radius: var(--radius-md);
  padding: 12px;
  border: 1px solid var(--border-color);
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.search-input {
  padding: 10px 14px;
  font-size: 0.92rem;
  border-radius: var(--radius-sm);
}

.filter-row {
  display: flex;
  gap: 8px;
}

.filter-select {
  flex: 1;
  padding: 8px 10px;
  font-size: 0.85rem;
}

.type-segmented {
  display: flex;
  background: #f1f5f9;
  padding: 3px;
  border-radius: var(--radius-sm);
}

.segmented-btn {
  flex: 1;
  border: none;
  background: transparent;
  padding: 7px;
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--text-muted);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.segmented-btn.active {
  background: #ffffff;
  color: var(--text-main);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.posts-list {
  display: flex;
  flex-direction: column;
}

.post-card {
  cursor: pointer;
  transition: transform 0.1s ease, box-shadow 0.1s ease;
}

.post-card:active {
  transform: scale(0.99);
}

.post-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.post-time {
  margin-left: auto;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.post-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 6px;
  line-height: 1.3;
}

.post-desc {
  font-size: 0.88rem;
  color: #475569;
  line-height: 1.45;
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
  padding-top: 8px;
}

.location-tag {
  font-weight: 500;
}

.empty-box {
  text-align: center;
  padding: 40px 20px;
}

.empty-icon {
  font-size: 2.5rem;
  margin-bottom: 8px;
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
</style>
