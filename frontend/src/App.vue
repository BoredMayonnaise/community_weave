<template>
  <div class="app-root">
    <!-- Toast Notification -->
    <div v-if="state.toast" class="toast-banner">
      {{ state.toast }}
    </div>

    <!-- Mobile App Header -->
    <header class="app-header">
      <div class="app-brand" @click="resetToFeed">
        <img src="/icon.svg" alt="Community Weave Logo" class="brand-icon" />
        <span>Community Weave</span>
      </div>

      <div class="header-actions">
        <button
          v-if="!state.user"
          class="btn btn-secondary btn-sm"
          @click="state.showAuthModal = true"
        >
          Sign In
        </button>
        <button
          v-else
          class="user-pill"
          @click="switchTab('profile')"
        >
          <span class="user-pill-dot"></span>
          <span>{{ state.user.profile?.display_name || state.user.username }}</span>
        </button>
      </div>
    </header>

    <!-- Main Content Area -->
    <main class="app-content">
      <!-- Detail View takes precedence when a post is clicked -->
      <PostDetail v-if="state.selectedPost" />

      <!-- Tab screens -->
      <Feed v-else-if="state.currentTab === 'feed'" />
      <CreatePost v-else-if="state.currentTab === 'create'" />
      <Messages v-else-if="state.currentTab === 'messages'" />
      <Profile v-else-if="state.currentTab === 'profile'" />
    </main>

    <!-- Bottom Navigation Bar -->
    <nav class="bottom-nav">
      <button
        type="button"
        :class="['nav-item', { active: state.currentTab === 'feed' && !state.selectedPost }]"
        @click="switchTab('feed')"
      >
        <span class="nav-icon">🏠</span>
        <span>Feed</span>
      </button>

      <button
        type="button"
        :class="['nav-item', { active: state.currentTab === 'create' }]"
        @click="switchTab('create')"
      >
        <span class="nav-icon">➕</span>
        <span>Post</span>
      </button>

      <button
        type="button"
        :class="['nav-item', { active: state.currentTab === 'messages' }]"
        @click="switchTab('messages')"
      >
        <span class="nav-icon">💬</span>
        <span>Messages</span>
      </button>

      <button
        type="button"
        :class="['nav-item', { active: state.currentTab === 'profile' }]"
        @click="switchTab('profile')"
      >
        <span class="nav-icon">👤</span>
        <span>Profile</span>
      </button>
    </nav>

    <!-- Authentication Modal -->
    <AuthModal v-if="state.showAuthModal" />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { state } from './state.js'
import { api } from './api.js'
import Feed from './components/Feed.vue'
import PostDetail from './components/PostDetail.vue'
import CreatePost from './components/CreatePost.vue'
import Messages from './components/Messages.vue'
import Profile from './components/Profile.vue'
import AuthModal from './components/AuthModal.vue'

function switchTab(tab) {
  state.selectedPost = null
  state.activeConversationId = null
  state.currentTab = tab
}

function resetToFeed() {
  state.selectedPost = null
  state.activeConversationId = null
  state.currentTab = 'feed'
}

onMounted(async () => {
  // Validate stored session with backend
  if (state.token) {
    try {
      const user = await api.getMe()
      state.user = user
      localStorage.setItem('cw_user', JSON.stringify(user))
    } catch (err) {
      // If token expired or invalid, clear auth
      state.setAuth('', null)
    }
  }
})
</script>

<style scoped>
.app-root {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 0.82rem;
  min-height: auto;
  border-radius: 8px;
}

.user-pill {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  background: #f1f5f9;
  border: 1px solid var(--border-color);
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
  color: #334155;
  cursor: pointer;
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-pill-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #10b981;
}
</style>
