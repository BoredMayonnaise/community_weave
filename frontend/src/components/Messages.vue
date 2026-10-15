<template>
  <div :class="['messages-view', { 'in-conversation': !!state.activeConversationId }]">
    <div v-if="!state.user" class="card empty-card">
      <div class="empty-icon-wrap">
        <LockKeyhole :size="32" />
      </div>
      <h3>Sign in to View Messages</h3>
      <p>Your direct chats with neighbors about requests and offers will appear here.</p>
      <button class="btn btn-primary" style="margin-top: 16px" @click="openAuth">
        Sign In / Register
      </button>
    </div>

    <!-- Active Conversation View -->
    <ConversationView v-else-if="state.activeConversationId" />

    <!-- Conversations List -->
    <div v-else class="conv-container">
      <div class="messages-top-bar">
        <h2 class="section-title">Messages</h2>
        <span v-if="conversations.length" class="conv-count-badge">{{ conversations.length }}</span>
      </div>

      <!-- Quick Search Bar -->
      <div v-if="conversations.length > 2" class="conv-search-box">
        <Search class="search-icon" :size="15" />
        <input
          v-model="searchQuery"
          type="text"
          class="conv-search-input"
          placeholder="Search chats or neighbors..."
        />
        <button v-if="searchQuery" class="clear-btn" @click="searchQuery = ''">
          <X :size="14" />
        </button>
      </div>

      <div v-if="loading" class="state-msg">
        <div class="chat-spinner"></div>
        <p>Loading conversations...</p>
      </div>

      <div v-else-if="conversations.length === 0" class="card empty-card">
        <div class="empty-icon-wrap">
          <Inbox :size="32" />
        </div>
        <h4>No conversations yet</h4>
        <p>When you respond to a post or a neighbor contacts you, chats will appear here.</p>
        <button class="btn btn-secondary" style="margin-top: 14px" @click="goToFeed">
          Explore Feed
        </button>
      </div>

      <div v-else-if="filteredConversations.length === 0" class="card empty-card" style="padding: 24px">
        <p>No messages matching "{{ searchQuery }}"</p>
        <button class="btn btn-sm btn-secondary" style="margin-top: 8px" @click="searchQuery = ''">
          Clear Search
        </button>
      </div>

      <div v-else class="conv-list">
        <div
          v-for="conv in filteredConversations"
          :key="conv.id"
          class="card conv-card"
          @click="openConv(conv.id)"
        >
          <!-- Left: Partner Avatar -->
          <div class="conv-avatar">
            {{ getPartnerInitial(conv) }}
            <span :class="['avatar-dot', conv.partner_is_online ? 'avatar-online-dot' : 'avatar-offline-dot']"></span>
          </div>

          <!-- Middle: Info & Snippet -->
          <div class="conv-main">
            <div class="conv-header-row">
              <div class="partner-title-cell">
                <span class="conv-partner-name">{{ getPartner(conv) }}</span>
                <span v-if="conv.partner_is_online" class="inbox-online-tag">Online</span>
              </div>
              <span class="conv-time-text">{{ formatTimeAgo(conv.updated_at) }}</span>
            </div>

            <div class="conv-post-tag">
              <FileText :size="11" />
              <span>{{ conv.post_title || 'Post Conversation' }}</span>
            </div>

            <p class="conv-last-msg">
              <span v-if="conv.last_message">
                <span v-if="conv.last_message.sender === state.user.username" class="msg-you-prefix">
                  You
                  <CheckCheck v-if="conv.last_message.is_read" :size="12" class="inbox-msg-check seen" title="Seen" />
                  <Check v-else :size="12" class="inbox-msg-check sent" title="Sent" />:
                </span>
                {{ conv.last_message.text }}
              </span>
              <span v-else class="no-msg-text">Tap to start chatting</span>
            </p>
          </div>

          <!-- Right: Unread Badge & Chevron -->
          <div class="conv-right-meta">
            <span v-if="conv.unread_count > 0" class="unread-pill">{{ conv.unread_count }}</span>
            <ChevronRight class="conv-chevron" :size="18" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { LockKeyhole, Inbox, Search, X, FileText, ChevronRight, Check, CheckCheck } from 'lucide-vue-next'
import { state } from '../state.js'
import { api } from '../api.js'
import ConversationView from './ConversationView.vue'

const conversations = ref([])
const loading = ref(false)
const searchQuery = ref('')

const filteredConversations = computed(() => {
  if (!searchQuery.value.trim()) return conversations.value
  const q = searchQuery.value.toLowerCase().trim()
  return conversations.value.filter(c => {
    const partner = getPartner(c).toLowerCase()
    const title = (c.post_title || '').toLowerCase()
    const lastMsg = (c.last_message?.text || '').toLowerCase()
    return partner.includes(q) || title.includes(q) || lastMsg.includes(q)
  })
})

function openAuth() {
  state.showAuthModal = true
}

function openConv(id) {
  state.activeConversationId = id
}

function goToFeed() {
  state.currentTab = 'feed'
}

function getPartner(conv) {
  if (!state.user) return 'Neighbor'
  return conv.requester_username === state.user.username
    ? (conv.owner_display_name || conv.owner_username)
    : (conv.requester_display_name || conv.requester_username)
}

function getPartnerInitial(conv) {
  const name = getPartner(conv)
  return name.trim().charAt(0).toUpperCase()
}

async function fetchConversations() {
  if (!state.user) return
  loading.value = true
  try {
    conversations.value = await api.getConversations()
  } catch (err) {
    state.showToast(err.message || 'Failed to load conversations')
  } finally {
    loading.value = false
  }
}

function formatTimeAgo(isoStr) {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  const diffSec = Math.floor((Date.now() - d.getTime()) / 1000)
  if (diffSec < 60) return 'Just now'
  const diffMin = Math.floor(diffSec / 60)
  if (diffMin < 60) return `${diffMin}m ago`
  const diffHours = Math.floor(diffMin / 60)
  if (diffHours < 24) return `${diffHours}h ago`
  const diffDays = Math.floor(diffHours / 24)
  if (diffDays === 1) return 'Yesterday'
  if (diffDays < 7) return `${diffDays}d ago`
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

onMounted(() => {
  fetchConversations()
})

watch(() => state.user, (u) => { if (u) fetchConversations() })
watch(() => state.activeConversationId, (id) => { if (!id && state.user) fetchConversations() })
</script>

<style scoped>
.messages-view {
  display: flex;
  flex-direction: column;
}

.messages-view.in-conversation {
  height: 100%;
  flex: 1;
  min-height: 0;
}

.conv-container {
  display: flex;
  flex-direction: column;
}

.messages-top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.section-title {
  font-size: 1.3rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: #0f172a;
}

.conv-count-badge {
  background: var(--primary-light);
  color: var(--primary);
  border: 1px solid rgba(13, 148, 136, 0.25);
  font-size: 0.75rem;
  font-weight: 700;
  padding: 2px 9px;
  border-radius: 9999px;
}

/* Search Box */
.conv-search-box {
  position: relative;
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.conv-search-input {
  width: 100%;
  padding: 9px 34px 9px 34px;
  border-radius: 9999px;
  border: 1px solid var(--border-color);
  background: #ffffff;
  font-size: 0.88rem;
  color: #0f172a;
  outline: none;
  transition: all 0.15s ease;
}

.conv-search-input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-glow);
}

.search-icon {
  position: absolute;
  left: 12px;
  color: #94a3b8;
  pointer-events: none;
}

.clear-btn {
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

/* Empty Card */
.empty-card {
  text-align: center;
  padding: 40px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.empty-icon-wrap {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: #f1f5f9;
  color: var(--primary);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 14px;
}

/* Conversations List */
.conv-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.conv-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  cursor: pointer;
  transition: all 0.15s cubic-bezier(0.16, 1, 0.3, 1);
  border: 1px solid rgba(226, 232, 240, 0.85);
  margin-bottom: 0;
}

.conv-card:hover {
  transform: translateY(-1.5px);
  box-shadow: 0 4px 14px -2px rgba(15, 23, 42, 0.08);
  border-color: #cbd5e1;
}

.conv-card:active {
  transform: scale(0.99);
}

.conv-avatar {
  position: relative;
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: linear-gradient(135deg, #0d9488 0%, #0284c7 100%);
  color: #ffffff;
  font-weight: 700;
  font-size: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 2px 6px rgba(13, 148, 136, 0.25);
}

.avatar-dot {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 2px solid #ffffff;
}

.avatar-online-dot {
  background-color: #22c55e;
}

.avatar-offline-dot {
  background-color: #94a3b8;
}

.conv-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.conv-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  margin-bottom: 2px;
}

.partner-title-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.inbox-online-tag {
  font-size: 0.65rem;
  font-weight: 700;
  color: #15803d;
  background: #dcfce7;
  padding: 1px 6px;
  border-radius: 9999px;
  letter-spacing: 0.02em;
  flex-shrink: 0;
}

.conv-partner-name {
  font-weight: 700;
  font-size: 0.95rem;
  color: #0f172a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.conv-time-text {
  font-size: 0.72rem;
  font-weight: 500;
  color: #94a3b8;
  white-space: nowrap;
}

.conv-post-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.72rem;
  color: var(--primary);
  background: var(--primary-light);
  border-radius: 9999px;
  padding: 1px 7px;
  margin-bottom: 5px;
  max-width: fit-content;
}

.conv-post-tag span {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 220px;
}

.conv-last-msg {
  font-size: 0.83rem;
  color: #64748b;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.35;
}

.msg-you-prefix {
  color: #334155;
  display: inline-flex;
  align-items: center;
  gap: 2px;
}

.inbox-msg-check {
  display: inline-block;
  vertical-align: middle;
}

.inbox-msg-check.sent {
  color: #94a3b8;
}

.inbox-msg-check.seen {
  color: #0d9488;
}

.no-msg-text {
  font-style: italic;
  color: #94a3b8;
}

.conv-right-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.unread-pill {
  background: var(--primary);
  color: #ffffff;
  font-size: 0.72rem;
  font-weight: 700;
  min-width: 19px;
  height: 19px;
  line-height: 19px;
  text-align: center;
  padding: 0 5px;
  border-radius: 9999px;
  box-shadow: 0 1px 4px rgba(13, 148, 136, 0.35);
}

.conv-chevron {
  color: #cbd5e1;
  flex-shrink: 0;
  transition: transform 0.15s ease, color 0.15s ease;
}

.conv-card:hover .conv-chevron {
  color: var(--primary);
  transform: translateX(2px);
}

.chat-spinner {
  width: 24px;
  height: 24px;
  border: 3px solid rgba(13, 148, 136, 0.2);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 10px auto;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
