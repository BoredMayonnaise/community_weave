<template>
  <div class="profile-view">
    <div v-if="!state.user" class="card empty-card">
      <div class="empty-icon">👤</div>
      <h3>Neighbor Profile</h3>
      <p>Sign in to manage your posts, profile, and neighborhood settings.</p>
      <button class="btn btn-primary" style="margin-top: 16px" @click="openAuth">
        Sign In / Register
      </button>
    </div>

    <div v-else>
      <!-- User Card -->
      <div class="card user-card">
        <div class="avatar-circle">
          {{ (state.user.profile?.display_name || state.user.username)[0].toUpperCase() }}
        </div>
        <div class="user-info">
          <h3 class="user-name">{{ state.user.profile?.display_name || state.user.username }}</h3>
          <span class="user-handle">@{{ state.user.username }}</span>
          <span class="user-neighborhood">📍 {{ state.user.profile?.neighborhood || 'No neighborhood set' }}</span>
        </div>
      </div>

      <!-- Quick Edit Neighborhood / Display Name -->
      <div class="card edit-card">
        <h4 style="font-size: 0.95rem; margin-bottom: 12px">Update Neighborhood</h4>
        <div class="form-row">
          <input
            v-model="editNeighborhood"
            class="form-input"
            placeholder="e.g. North Hills"
          />
          <button class="btn btn-secondary" :disabled="savingProfile" @click="saveProfile">
            {{ savingProfile ? '...' : 'Save' }}
          </button>
        </div>
      </div>

      <!-- My Posts -->
      <div class="my-posts-section">
        <h3 class="section-title">My Posts</h3>

        <div v-if="loadingPosts" class="state-msg">Loading your posts...</div>

        <div v-else-if="myPosts.length === 0" class="card empty-card" style="padding: 24px">
          <p>You haven't posted any requests or offers yet.</p>
          <button class="btn btn-secondary" style="margin-top: 10px" @click="goToCreate">
            + Create First Post
          </button>
        </div>

        <div v-else class="posts-list">
          <div v-for="post in myPosts" :key="post.id" class="card my-post-card">
            <div class="post-top">
              <span :class="['badge', post.type === 'offer' ? 'badge-offer' : 'badge-request']">
                {{ post.type === 'offer' ? 'Offer' : 'Request' }}
              </span>
              <span :class="['badge', post.status === 'open' ? 'badge-offer' : 'badge-closed']">
                {{ post.status === 'open' ? 'Active' : 'Closed' }}
              </span>
            </div>

            <h4 class="post-title" @click="openPost(post)">{{ post.title }}</h4>

            <div class="post-actions">
              <button
                v-if="post.status === 'open'"
                class="btn-text text-danger"
                @click="togglePostStatus(post, 'closed')"
              >
                Mark Closed
              </button>
              <button
                v-else
                class="btn-text text-primary"
                @click="togglePostStatus(post, 'open')"
              >
                Reopen Post
              </button>
              <button class="btn-text" @click="openPost(post)">View →</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Sign Out -->
      <button class="btn btn-secondary btn-block logout-btn" @click="logout">
        Sign Out
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { state } from '../state.js'
import { api } from '../api.js'

const editNeighborhood = ref('')
const savingProfile = ref(false)
const myPosts = ref([])
const loadingPosts = ref(false)

function openAuth() {
  state.showAuthModal = true
}

function openPost(post) {
  state.selectedPost = post
  state.currentTab = 'feed'
}

function goToCreate() {
  state.currentTab = 'create'
}

function logout() {
  api.logout().catch(() => {})
  state.logout()
}

async function saveProfile() {
  if (!editNeighborhood.value.trim()) return
  savingProfile.value = true
  try {
    const updated = await api.updateProfile({ neighborhood: editNeighborhood.value.trim() })
    state.user = updated
    localStorage.setItem('cw_user', JSON.stringify(updated))
    state.showToast('Neighborhood updated!')
  } catch (err) {
    state.showToast(err.message || 'Failed to update')
  } finally {
    savingProfile.value = false
  }
}

async function fetchMyPosts() {
  if (!state.user) return
  loadingPosts.value = true
  try {
    myPosts.value = await api.getPosts({ author: state.user.username, status: 'all' })
  } catch (err) {
    // Ignore error
  } finally {
    loadingPosts.value = false
  }
}

async function togglePostStatus(post, newStatus) {
  try {
    const updated = await api.updatePost(post.id, { status: newStatus })
    post.status = updated.status
    state.showToast(`Post marked as ${newStatus}`)
  } catch (err) {
    state.showToast(err.message || 'Action failed')
  }
}

onMounted(() => {
  if (state.user) {
    editNeighborhood.value = state.user.profile?.neighborhood || ''
    fetchMyPosts()
  }
})
</script>

<style scoped>
.empty-card {
  text-align: center;
  padding: 40px 20px;
}

.empty-icon {
  font-size: 2.5rem;
  margin-bottom: 10px;
}

.user-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 18px;
}

.avatar-circle {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: var(--primary);
  color: #ffffff;
  font-size: 1.4rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-name {
  font-size: 1.15rem;
  font-weight: 700;
  color: #0f172a;
}

.user-handle {
  display: block;
  font-size: 0.8rem;
  color: #94a3b8;
}

.user-neighborhood {
  display: block;
  font-size: 0.82rem;
  color: var(--primary);
  font-weight: 500;
  margin-top: 2px;
}

.form-row {
  display: flex;
  gap: 8px;
}

.my-posts-section {
  margin-top: 20px;
}

.section-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 12px;
}

.my-post-card {
  padding: 12px 14px;
}

.post-top {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}

.post-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #1e293b;
  cursor: pointer;
  margin-bottom: 10px;
}

.post-actions {
  display: flex;
  justify-content: flex-end;
  gap: 14px;
  border-top: 1px solid #f1f5f9;
  padding-top: 8px;
}

.btn-text {
  background: none;
  border: none;
  font-size: 0.82rem;
  font-weight: 600;
  color: #64748b;
  cursor: pointer;
}

.text-danger {
  color: #dc2626;
}

.text-primary {
  color: var(--primary);
}

.logout-btn {
  margin-top: 24px;
  color: #dc2626;
}

.state-msg {
  text-align: center;
  padding: 20px;
  color: #94a3b8;
}
</style>
