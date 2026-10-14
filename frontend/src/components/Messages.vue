<template>
  <div class="messages-view">
    <div v-if="!state.user" class="card empty-card">
      <div class="empty-icon">💬</div>
      <h3>Sign in to View Messages</h3>
      <p>Your direct chats with neighbors about requests and offers will appear here.</p>
      <button class="btn btn-primary" style="margin-top: 16px" @click="openAuth">
        Sign In / Register
      </button>
    </div>

    <!-- Active Conversation View -->
    <ConversationView v-else-if="state.activeConversationId" />

    <!-- Conversations List -->
    <div v-else>
      <h2 class="section-title">Messages</h2>

      <div v-if="loading" class="state-msg">
        <p>Loading conversations...</p>
      </div>

      <div v-else-if="conversations.length === 0" class="card empty-card">
        <div class="empty-icon">📫</div>
        <h4>No conversations yet</h4>
        <p>When you respond to a post or a neighbor contacts you, chats will appear here.</p>
      </div>

      <div v-else class="conv-list">
        <div
          v-for="conv in conversations"
          :key="conv.id"
          class="card conv-card"
          @click="openConv(conv.id)"
        >
          <div class="conv-header">
            <span class="partner-title">
              👤 {{ getPartner(conv) }}
            </span>
            <span class="conv-time">{{ formatDate(conv.updated_at) }}</span>
          </div>

          <div class="post-subject">Re: {{ conv.post_title }}</div>

          <p class="last-msg">
            <span v-if="conv.last_message">
              <strong>{{ conv.last_message.sender === state.user.username ? 'You: ' : '' }}</strong>
              {{ conv.last_message.text }}
            </span>
            <span v-else class="no-msg">No messages yet</span>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { state } from '../state.js'
import { api } from '../api.js'
import ConversationView from './ConversationView.vue'

const conversations = ref([])
const loading = ref(false)

function openAuth() {
  state.showAuthModal = true
}

function openConv(id) {
  state.activeConversationId = id
}

function getPartner(conv) {
  if (!state.user) return 'Neighbor'
  return conv.requester_username === state.user.username
    ? conv.owner_username
    : conv.requester_username
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

function formatDate(isoStr) {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

onMounted(() => {
  fetchConversations()
})
</script>

<style scoped>
.section-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 14px;
}

.empty-card {
  text-align: center;
  padding: 40px 20px;
}

.empty-icon {
  font-size: 2.5rem;
  margin-bottom: 10px;
}

.conv-list {
  display: flex;
  flex-direction: column;
}

.conv-card {
  cursor: pointer;
  transition: transform 0.1s ease;
}

.conv-card:active {
  transform: scale(0.99);
}

.conv-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.partner-title {
  font-weight: 700;
  font-size: 0.95rem;
  color: #0f172a;
}

.conv-time {
  font-size: 0.72rem;
  color: var(--text-muted);
}

.post-subject {
  font-size: 0.8rem;
  color: var(--primary);
  font-weight: 600;
  margin-bottom: 6px;
}

.last-msg {
  font-size: 0.86rem;
  color: #64748b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.no-msg {
  font-style: italic;
  opacity: 0.7;
}

.state-msg {
  text-align: center;
  padding: 30px;
  color: #94a3b8;
}
</style>
