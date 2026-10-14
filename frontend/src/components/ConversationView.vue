<template>
  <div class="chat-container">
    <div class="chat-header">
      <button class="back-btn" @click="closeChat">← Back</button>
      <div class="chat-partner-info">
        <h4 class="partner-name">{{ partnerName }}</h4>
        <span class="chat-subject">{{ conversation?.post_title || 'Post Conversation' }}</span>
      </div>
    </div>

    <!-- Message Stream -->
    <div ref="messagesBox" class="messages-stream">
      <div v-if="loading" class="chat-loading">Loading messages...</div>
      <div v-else-if="messages.length === 0" class="empty-chat">
        <p>No messages yet. Send a greeting to start chatting!</p>
      </div>

      <div
        v-for="msg in messages"
        :key="msg.id"
        :class="['message-row', isMe(msg) ? 'me' : 'them']"
      >
        <div class="message-bubble">
          <p class="bubble-text">{{ msg.text }}</p>
          <span class="bubble-time">{{ formatTime(msg.created_at) }}</span>
        </div>
      </div>
    </div>

    <!-- Message Input Bar -->
    <div class="input-bar">
      <input
        v-model="newText"
        @keyup.enter="send"
        type="text"
        class="form-input chat-input"
        placeholder="Type a message..."
        :disabled="sending"
      />
      <button class="btn btn-primary send-btn" :disabled="sending || !newText.trim()" @click="send">
        ➤
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { state } from '../state.js'
import { api } from '../api.js'

const messages = ref([])
const conversation = ref(null)
const loading = ref(true)
const sending = ref(false)
const newText = ref('')
const messagesBox = ref(null)
let pollTimer = null

const partnerName = computed(() => {
  if (!conversation.value || !state.user) return 'Neighbor'
  return conversation.value.requester_username === state.user.username
    ? conversation.value.owner_username
    : conversation.value.requester_username
})

function isMe(msg) {
  return state.user && msg.sender_username === state.user.username
}

function closeChat() {
  state.activeConversationId = null
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesBox.value) {
      messagesBox.value.scrollTop = messagesBox.value.scrollHeight
    }
  })
}

async function loadData() {
  try {
    const convs = await api.getConversations()
    conversation.value = convs.find(c => c.id === state.activeConversationId) || null
    messages.value = await api.getMessages(state.activeConversationId)
    scrollToBottom()
  } catch (err) {
    // Ignore silent poll errors
  } finally {
    loading.value = false
  }
}

async function send() {
  if (!newText.value.trim() || sending.value) return
  const text = newText.value.trim()
  newText.value = ''
  sending.value = true
  try {
    const msg = await api.sendMessage(state.activeConversationId, text)
    messages.value.push(msg)
    scrollToBottom()
  } catch (err) {
    state.showToast(err.message || 'Failed to send message')
  } finally {
    sending.value = false
  }
}

function formatTime(isoStr) {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

onMounted(() => {
  loadData()
  pollTimer = setInterval(loadData, 4000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 120px);
}

.chat-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 8px;
}

.back-btn {
  background: none;
  border: none;
  color: var(--primary);
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  padding: 4px;
}

.chat-partner-info {
  display: flex;
  flex-direction: column;
}

.partner-name {
  font-size: 1rem;
  font-weight: 700;
  color: #0f172a;
}

.chat-subject {
  font-size: 0.75rem;
  color: #64748b;
  max-width: 240px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.messages-stream {
  flex: 1;
  overflow-y: auto;
  padding: 8px 4px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.message-row {
  display: flex;
  width: 100%;
}

.message-row.me {
  justify-content: flex-end;
}

.message-row.them {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 78%;
  padding: 9px 13px;
  border-radius: 16px;
  position: relative;
}

.message-row.me .message-bubble {
  background: var(--primary);
  color: #ffffff;
  border-bottom-right-radius: 4px;
}

.message-row.them .message-bubble {
  background: #e2e8f0;
  color: #0f172a;
  border-bottom-left-radius: 4px;
}

.bubble-text {
  font-size: 0.92rem;
  line-height: 1.4;
  word-break: break-word;
}

.bubble-time {
  display: block;
  font-size: 0.68rem;
  opacity: 0.7;
  text-align: right;
  margin-top: 3px;
}

.input-bar {
  display: flex;
  gap: 8px;
  padding-top: 10px;
  border-top: 1px solid var(--border-color);
  background: var(--bg-page);
}

.chat-input {
  flex: 1;
  border-radius: 20px;
  padding: 10px 16px;
  font-size: 0.92rem;
}

.send-btn {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  padding: 0;
  font-size: 1rem;
}

.chat-loading, .empty-chat {
  text-align: center;
  color: #94a3b8;
  font-size: 0.85rem;
  padding: 30px;
}
</style>
