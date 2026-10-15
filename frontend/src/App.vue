<template>
  <div class="app-root">
    <!-- Toast Notification -->
    <div v-if="state.toast" class="toast-banner">
      {{ state.toast }}
    </div>

    <!-- Rich In-App Chat Notification Toast -->
    <transition name="chat-toast">
      <div
        v-if="state.chatNotification"
        class="chat-toast-banner"
        @click="openChatNotification"
        role="button"
        tabindex="0"
        title="Tap to open chat"
      >
        <div class="chat-toast-avatar">
          {{ state.chatNotification.initial }}
        </div>
        <div class="chat-toast-content">
          <div class="chat-toast-header">
            <span class="chat-toast-sender">{{ state.chatNotification.title }}</span>
            <span class="chat-toast-tag">New Message</span>
          </div>
          <p class="chat-toast-msg">{{ state.chatNotification.message }}</p>
        </div>
        <button
          class="chat-toast-close"
          @click.stop="state.dismissChatNotification()"
          title="Dismiss notification"
        >
          <X :size="14" />
        </button>
      </div>
    </transition>

    <!-- Mobile App Header -->
    <header class="app-header">
      <div class="app-brand" @click="resetToFeed" role="button" tabindex="0">
        <img src="/icon.svg" alt="Community Weave Logo" class="brand-icon" />
        <div class="brand-info">
          <div class="brand-title">Community<span class="brand-accent">Weave</span></div>
          <span class="brand-tagline">Hyperlocal Sharing</span>
        </div>
      </div>

      <div class="header-actions">
        <button
          v-if="!state.user"
          :class="['header-user-btn', 'header-guest-btn', { active: state.currentTab === 'profile' }]"
          @click="switchTab('profile')"
          title="Sign in / Neighbor Profile"
        >
          <div class="header-avatar-circle guest">
            <User :size="15" />
          </div>
          <span class="header-user-name">Sign In</span>
        </button>
        <button
          v-else
          :class="['header-user-btn', { active: state.currentTab === 'profile' }]"
          @click="switchTab('profile')"
          :title="state.user.profile?.display_name || state.user.username"
        >
          <div class="header-avatar-circle">
            {{ getUserInitial(state.user) }}
            <span class="header-online-dot"></span>
          </div>
          <span class="header-user-name">{{ state.user.profile?.display_name || state.user.username }}</span>
        </button>
      </div>
    </header>

    <!-- Main Content Area -->
    <main :class="['app-content', { 'in-chat': !!state.activeConversationId && !state.selectedPost, 'in-map': state.currentTab === 'map' && !state.selectedPost }]">
      <Transition name="page-fade" mode="out-in">
        <!-- Detail View takes precedence when a post is clicked -->
        <PostDetail v-if="state.selectedPost" key="detail" />

        <!-- Tab screens -->
        <Feed v-else-if="state.currentTab === 'feed'" key="feed" />
        <ExploreMap v-else-if="state.currentTab === 'map'" key="map" />
        <CreatePost v-else-if="state.currentTab === 'create'" key="create" />
        <Messages v-else-if="state.currentTab === 'messages'" key="messages" />
        <Profile v-else-if="state.currentTab === 'profile'" key="profile" />
      </Transition>
    </main>

    <!-- Bottom Navigation Bar -->
    <nav class="bottom-nav">
      <button
        type="button"
        :class="['nav-item', { active: state.currentTab === 'feed' && !state.selectedPost }]"
        @click="switchTab('feed')"
      >
        <House class="nav-icon" :size="22" />
        <span>Feed</span>
      </button>

      <button
        type="button"
        :class="['nav-item', { active: state.currentTab === 'map' }]"
        @click="switchTab('map')"
      >
        <Map class="nav-icon" :size="22" />
        <span>Map</span>
      </button>

      <button
        type="button"
        :class="['nav-item', { active: state.currentTab === 'create' }]"
        @click="switchTab('create')"
      >
        <SquarePen class="nav-icon" :size="22" />
        <span>Post</span>
      </button>

      <button
        type="button"
        :class="['nav-item', { active: state.currentTab === 'messages' }]"
        @click="switchTab('messages')"
      >
        <div class="nav-icon-wrapper">
          <MessagesSquare class="nav-icon" :size="22" />
          <span v-if="state.unreadMessagesCount > 0" class="nav-unread-badge">
            {{ state.unreadMessagesCount > 9 ? '9+' : state.unreadMessagesCount }}
          </span>
        </div>
        <span>Messages</span>
      </button>
    </nav>

    <!-- Authentication Modal -->
    <AuthModal v-if="state.showAuthModal" />
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, watch } from 'vue'
import { House, Map, SquarePen, MessagesSquare, User, LogIn, X } from 'lucide-vue-next'
import { state } from './state.js'
import { api } from './api.js'
import Feed from './components/Feed.vue'
import ExploreMap from './components/ExploreMap.vue'
import PostDetail from './components/PostDetail.vue'
import CreatePost from './components/CreatePost.vue'
import Messages from './components/Messages.vue'
import Profile from './components/Profile.vue'
import AuthModal from './components/AuthModal.vue'

const knownMessageIds = new Set()
let isFirstCheck = true
let unreadPollTimer = null

function getUserInitial(user) {
  if (!user) return '?'
  const name = user.profile?.display_name || user.username || '?'
  return name.trim().charAt(0).toUpperCase()
}

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

function openChatNotification() {
  if (state.chatNotification?.conversationId) {
    const convId = state.chatNotification.conversationId
    state.dismissChatNotification()
    state.selectedPost = null
    state.currentTab = 'messages'
    state.activeConversationId = convId
  }
}

async function checkUnreadMessages() {
  if (!state.user || !state.token) {
    state.unreadMessagesCount = 0
    return
  }

  try {
    const convs = await api.getConversations()
    let totalUnread = 0

    convs.forEach(conv => {
      const unread = conv.unread_count || 0
      totalUnread += unread

      const lastMsg = conv.last_message
      if (lastMsg && unread > 0 && lastMsg.sender !== state.user.username) {
        if (!isFirstCheck && !knownMessageIds.has(lastMsg.id)) {
          // If the user is not currently inside this active conversation, alert with toast
          if (state.currentTab !== 'messages' || state.activeConversationId !== conv.id) {
            state.showChatNotification({
              title: conv.partner_display_name || conv.partner_username || 'Neighbor',
              message: lastMsg.text || 'Sent you a message',
              conversationId: conv.id,
              initial: (conv.partner_display_name || conv.partner_username || 'N').charAt(0).toUpperCase()
            })
          }
        }
      }

      if (conv.last_message?.id) {
        knownMessageIds.add(conv.last_message.id)
      }
    })

    state.unreadMessagesCount = totalUnread
    isFirstCheck = false
  } catch (err) {
    // Silent background poll
  }
}

watch(() => state.user, (u) => {
  if (u) {
    isFirstCheck = true
    checkUnreadMessages()
  } else {
    state.unreadMessagesCount = 0
    knownMessageIds.clear()
  }
})

watch(() => state.activeConversationId, (id) => {
  // When leaving or switching a conversation, refresh unread status immediately
  if (!id && state.user) {
    checkUnreadMessages()
  }
})

onMounted(async () => {
  // Validate stored session with backend
  if (state.token) {
    try {
      const user = await api.getMe()
      state.user = user
      localStorage.setItem('cw_user', JSON.stringify(user))
    } catch (err) {
      if (err.status === 401) {
        state.setAuth('', null)
      }
    }
  }

  checkUnreadMessages()
  unreadPollTimer = setInterval(checkUnreadMessages, 5000)
})

onUnmounted(() => {
  if (unreadPollTimer) {
    clearInterval(unreadPollTimer)
  }
})
</script>

<style scoped>
.app-root {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.16s ease, transform 0.16s cubic-bezier(0.16, 1, 0.3, 1);
}

.page-fade-enter-from {
  opacity: 0;
  transform: translateY(4px);
}

.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
