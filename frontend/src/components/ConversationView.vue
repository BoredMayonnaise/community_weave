<template>
  <div class="chat-container">
    <!-- Chat Header Bar -->
    <div class="chat-header">
      <div class="chat-header-left">
        <button class="chat-back-btn" @click="closeChat" title="Back to messages">
          <ArrowLeft :size="18" />
        </button>

        <div class="chat-partner-avatar">
          {{ partnerInitial }}
          <span :class="['avatar-dot', partnerIsOnline ? 'avatar-online-dot' : 'avatar-offline-dot']"></span>
        </div>

        <div class="chat-header-meta">
          <div class="partner-name-row">
            <span class="partner-name">{{ partnerName }}</span>
            <span :class="['status-badge', partnerIsOnline ? 'online' : 'offline']">
              <span v-if="partnerIsOnline" class="status-pulse"></span>
              {{ partnerIsOnline ? 'Active now' : (partnerLastActive ? `Active ${formatTimeAgo(partnerLastActive)}` : 'Offline') }}
            </span>
          </div>
          <button
            v-if="conversation?.post"
            class="chat-post-chip"
            @click="viewRelatedPost"
            title="View original post"
          >
            <FileText :size="11" />
            <span>Re: {{ conversation.post_title || 'Post' }}</span>
          </button>
          <span v-else class="chat-post-chip static">
            <FileText :size="11" />
            <span>{{ conversation?.post_title || 'Direct Conversation' }}</span>
          </span>
        </div>
      </div>

      <div class="chat-header-right">
        <button
          v-if="conversation?.post"
          class="chat-action-btn report-btn"
          @click="showReportModal = true"
          title="Report this post or user"
        >
          <TriangleAlert :size="15" />
        </button>
        <button
          v-if="conversation?.post"
          class="chat-action-btn"
          @click="viewRelatedPost"
          title="Open Post Details"
        >
          <ExternalLink :size="16" />
        </button>
      </div>
    </div>

    <!-- Neighborhood Safety Tip -->
    <div v-if="showSafetyTip" class="safety-tip-bar">
      <div class="safety-tip-left">
        <ShieldCheck :size="15" class="safety-icon" />
        <span class="safety-text">
          <strong>Safety Tip:</strong> Meet in public, well-lit spots (e.g. Barangay Hall, plaza, or local store) for item handoffs.
        </span>
      </div>
      <button class="safety-dismiss-btn" @click="showSafetyTip = false" title="Dismiss safety tip">
        <X :size="13" />
      </button>
    </div>

    <!-- Message Stream -->
    <div ref="messagesBox" class="messages-stream">
      <div v-if="loading" class="chat-loading-state">
        <div class="chat-spinner-large"></div>
        <p>Loading conversation...</p>
      </div>

      <!-- Modern Empty State with Starter Prompts -->
      <div v-else-if="messages.length === 0" class="empty-chat-panel">
        <div class="empty-chat-badge">
          <Sparkles :size="24" class="empty-sparkle" />
        </div>
        <h4 class="empty-title">Chat with {{ partnerName }}</h4>
        <p class="empty-subtitle">
          Regarding: <strong>{{ conversation?.post_title || 'Neighborhood post' }}</strong>
        </p>

        <div class="quick-prompts-label">Tap to send a quick greeting:</div>
        <div class="quick-prompts-list">
          <button
            v-for="prompt in starterPrompts"
            :key="prompt"
            class="quick-prompt-btn"
            @click="useStarter(prompt)"
          >
            {{ prompt }}
          </button>
        </div>
      </div>

      <!-- Messages List -->
      <template v-else>
        <!-- Top Post Reference Card with generous spacing -->
        <div v-if="conversation?.post_title" class="chat-post-banner" @click="viewRelatedPost" title="Tap to view full post">
          <div class="banner-icon-badge">
            <FileText :size="16" />
          </div>
          <div class="banner-body">
            <span class="banner-label">Post Reference</span>
            <span class="banner-title">{{ conversation.post_title }}</span>
          </div>
          <div class="banner-view-action">
            <span>View Post</span>
            <ExternalLink :size="13" />
          </div>
        </div>

        <template v-for="(msg, index) in messages" :key="msg.id">
          <!-- Calendar Date Divider -->
          <div v-if="showDateDivider(index)" class="date-divider">
            <span>{{ formatDateDivider(msg.created_at) }}</span>
          </div>

          <div :class="['message-row', isMe(msg) ? 'me' : 'them']">
            <!-- Incoming Avatar -->
            <div v-if="!isMe(msg)" class="msg-avatar" :title="partnerName">
              {{ partnerInitial }}
            </div>

            <div class="message-bubble-col">
              <div class="message-bubble">
                <p class="bubble-text">{{ msg.text }}</p>
                <div class="bubble-meta">
                  <span class="bubble-time">{{ formatTime(msg.created_at) }}</span>
                  <template v-if="isMe(msg)">
                    <CheckCheck v-if="msg.is_read" :size="13" class="delivery-icon seen" title="Seen" />
                    <Check v-else :size="13" class="delivery-icon sent" title="Sent" />
                  </template>
                </div>
              </div>
              <div v-if="isLastSentMessage(index) && msg.is_read" class="seen-receipt-text">
                <CheckCheck :size="11" />
                <span>Seen {{ formatTime(msg.read_at) }}</span>
              </div>
            </div>
          </div>
        </template>
      </template>
    </div>

    <!-- Message Input Bar (Fixed Docked) -->
    <div class="input-bar">
      <div class="input-wrapper">
        <input
          ref="chatInput"
          v-model="newText"
          @keyup.enter="send"
          type="text"
          class="chat-input"
          placeholder="Write a message..."
          :disabled="sending"
        />
      </div>
      <button
        class="send-btn"
        :disabled="sending || !newText.trim()"
        @click="send"
        aria-label="Send message"
      >
        <div v-if="sending" class="chat-spinner-sm"></div>
        <Send v-else :size="17" />
      </button>
    </div>

    <!-- Report Modal -->
    <ReportModal
      v-if="showReportModal && conversation?.post"
      :post="{
        id: conversation.post,
        title: conversation.post_title,
        author_display_name: partnerName,
        author_username: partnerUsername
      }"
      @close="showReportModal = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import {
  ArrowLeft, Send, Check, CheckCheck, FileText, Sparkles,
  ExternalLink, ShieldCheck, X, TriangleAlert
} from 'lucide-vue-next'
import { state } from '../state.js'
import { api } from '../api.js'
import ReportModal from './ReportModal.vue'

const showSafetyTip = ref(true)
const showReportModal = ref(false)
const messages = ref([])
const conversation = ref(null)
const loading = ref(true)
const sending = ref(false)
const newText = ref('')
const messagesBox = ref(null)
const chatInput = ref(null)
let pollTimer = null

const starterPrompts = [
  'Hi! Is this still available?',
  'What time or location works best for pickup?',
  'Thanks for posting, I can help with this!'
]

const partnerName = computed(() => {
  if (!conversation.value || !state.user) return 'Neighbor'
  return conversation.value.requester_username === state.user.username
    ? (conversation.value.owner_display_name || conversation.value.owner_username)
    : (conversation.value.requester_display_name || conversation.value.requester_username)
})

const partnerUsername = computed(() => {
  if (!conversation.value || !state.user) return ''
  return conversation.value.requester_username === state.user.username
    ? conversation.value.owner_username
    : conversation.value.requester_username
})

const partnerInitial = computed(() => {
  const name = partnerName.value || 'N'
  return name.trim().charAt(0).toUpperCase()
})

const partnerIsOnline = computed(() => {
  if (!conversation.value) return false
  return Boolean(conversation.value.partner_is_online)
})

const partnerLastActive = computed(() => {
  if (!conversation.value) return null
  return conversation.value.partner_last_active
})

function isMe(msg) {
  return state.user && msg.sender_username === state.user.username
}

function isLastSentMessage(index) {
  for (let i = messages.value.length - 1; i >= 0; i--) {
    if (isMe(messages.value[i])) {
      return i === index
    }
  }
  return false
}

function formatTimeAgo(isoStr) {
  if (!isoStr) return ''
  const diffSec = Math.floor((Date.now() - new Date(isoStr).getTime()) / 1000)
  if (diffSec < 60) return 'just now'
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`
  return `${Math.floor(diffSec / 86400)}d ago`
}

function closeChat() {
  state.activeConversationId = null
}

function useStarter(text) {
  newText.value = text
  nextTick(() => {
    chatInput.value?.focus()
  })
}

async function viewRelatedPost() {
  if (!conversation.value?.post) return
  try {
    const post = await api.getPost(conversation.value.post)
    state.selectedPost = post
  } catch (err) {
    state.showToast('Could not load post details')
  }
}

function scrollToBottom(force = false) {
  nextTick(() => {
    if (messagesBox.value) {
      const box = messagesBox.value
      const isNearBottom = box.scrollHeight - box.scrollTop - box.clientHeight < 90
      if (force || isNearBottom) {
        box.scrollTop = box.scrollHeight
      }
    }
  })
}

function showDateDivider(index) {
  if (index === 0) return true
  const prevDate = new Date(messages.value[index - 1].created_at).toDateString()
  const currDate = new Date(messages.value[index].created_at).toDateString()
  return prevDate !== currDate
}

function formatDateDivider(isoStr) {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  const today = new Date().toDateString()
  const yesterday = new Date(Date.now() - 86400000).toDateString()
  if (d.toDateString() === today) return 'Today'
  if (d.toDateString() === yesterday) return 'Yesterday'
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

function formatTime(isoStr) {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

let pollCount = 0

async function loadData(initial = false) {
  try {
    const fetchConv = initial || (pollCount % 4 === 0)
    pollCount++

    if (fetchConv) {
      const [convs, msgs] = await Promise.all([
        api.getConversations(),
        api.getMessages(state.activeConversationId)
      ])
      const found = convs.find(c => c.id === state.activeConversationId)
      if (found) {
        if (found.unread_count > 0) {
          state.unreadMessagesCount = Math.max(0, state.unreadMessagesCount - found.unread_count)
        }
        conversation.value = found
      }
      messages.value = msgs
    } else {
      const msgs = await api.getMessages(state.activeConversationId)
      messages.value = msgs
    }
    scrollToBottom(initial)
  } catch (err) {
    // Ignore transient poll blips
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
    scrollToBottom(true)
  } catch (err) {
    state.showToast(err.message || 'Failed to send message')
  } finally {
    sending.value = false
    nextTick(() => {
      chatInput.value?.focus()
    })
  }
}

onMounted(() => {
  loadData(true)
  pollTimer = setInterval(() => loadData(false), 4000)
  nextTick(() => {
    chatInput.value?.focus()
  })
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  flex: 1;
  min-height: 0;
  background: var(--bg-page);
  position: relative;
}

/* Header */
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--border-color);
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.03);
  flex-shrink: 0;
  z-index: 10;
}

.safety-tip-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  background: #f0fdf4;
  border-bottom: 1px solid #bbf7d0;
  padding: 8px 14px;
  font-size: 0.75rem;
  color: #166534;
  flex-shrink: 0;
  z-index: 5;
}

.safety-tip-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.safety-icon {
  color: #16a34a;
  flex-shrink: 0;
}

.safety-text {
  line-height: 1.35;
}

.safety-dismiss-btn {
  background: none;
  border: none;
  color: #166534;
  cursor: pointer;
  padding: 3px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.65;
  transition: opacity 0.15s ease;
}

.safety-dismiss-btn:hover {
  opacity: 1;
}

.chat-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.chat-back-btn {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  border: 1px solid var(--border-color);
  background: #ffffff;
  color: #334155;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.chat-back-btn:hover {
  background: #f1f5f9;
  color: var(--primary);
  border-color: #cbd5e1;
}

.chat-partner-avatar {
  position: relative;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #0d9488 0%, #0284c7 100%);
  color: #ffffff;
  font-size: 0.92rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 6px rgba(13, 148, 136, 0.25);
  flex-shrink: 0;
}

.avatar-dot {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 9px;
  height: 9px;
  border-radius: 50%;
  border: 2px solid #ffffff;
}

.avatar-online-dot {
  background-color: #22c55e;
}

.avatar-offline-dot {
  background-color: #94a3b8;
}

.chat-header-meta {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.partner-name-row {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.partner-name {
  font-size: 0.98rem;
  font-weight: 700;
  color: #0f172a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.2;
}

.status-badge {
  font-size: 0.68rem;
  font-weight: 600;
  border-radius: 9999px;
  padding: 1px 7px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.status-badge.online {
  background: #ecfdf5;
  color: #059669;
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.status-badge.offline {
  background: #f1f5f9;
  color: #64748b;
}

.status-pulse {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 6px rgba(16, 185, 129, 0.6);
}

.chat-post-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.72rem;
  color: var(--primary);
  background: var(--primary-light);
  border: 1px solid rgba(13, 148, 136, 0.2);
  border-radius: 9999px;
  padding: 1px 8px;
  margin-top: 3px;
  cursor: pointer;
  max-width: 190px;
  transition: all 0.15s ease;
}

.chat-post-chip:hover {
  background: #ccfbf1;
  border-color: var(--primary);
}

.chat-post-chip.static {
  cursor: default;
  color: #64748b;
  background: #f1f5f9;
  border-color: #e2e8f0;
}

.chat-post-chip span {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chat-header-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.chat-action-btn {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  border: 1px solid var(--border-color);
  background: #ffffff;
  color: #64748b;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.chat-action-btn:hover {
  color: var(--primary);
  border-color: var(--primary);
  background: var(--primary-light);
}

.chat-action-btn.report-btn:hover {
  color: #ef4444;
  border-color: #fca5a5;
  background: #fef2f2;
}

/* Messages Stream */
.messages-stream {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 16px 14px 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  scroll-behavior: smooth;
}

/* Post Reference Banner */
.chat-post-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #ffffff;
  border: 1px solid rgba(13, 148, 136, 0.25);
  border-radius: 14px;
  padding: 12px 14px;
  margin: 4px 0 14px 0;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(13, 148, 136, 0.08);
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.chat-post-banner:hover {
  background: var(--primary-light);
  border-color: var(--primary);
  transform: translateY(-1px);
}

.banner-icon-badge {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: var(--primary-light);
  color: var(--primary);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.banner-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.banner-label {
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--primary);
}

.banner-title {
  font-size: 0.88rem;
  font-weight: 700;
  color: #0f172a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.25;
}

.banner-view-action {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--primary);
  flex-shrink: 0;
}

/* Date Divider */
.date-divider {
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 10px 0 4px 0;
}

.date-divider span {
  font-size: 0.7rem;
  font-weight: 600;
  color: #64748b;
  background: #e2e8f0;
  padding: 3px 10px;
  border-radius: 9999px;
  letter-spacing: 0.02em;
}

/* Empty State */
.empty-chat-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 30px 16px;
  margin: auto 0;
}

.empty-chat-badge {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: var(--primary-light);
  color: var(--primary);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 14px;
  box-shadow: 0 4px 12px var(--primary-glow);
}

.empty-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 4px;
}

.empty-subtitle {
  font-size: 0.82rem;
  color: #64748b;
  margin-bottom: 20px;
  max-width: 280px;
}

.quick-prompts-label {
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #94a3b8;
  margin-bottom: 10px;
}

.quick-prompts-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
  max-width: 320px;
}

.quick-prompt-btn {
  background: #ffffff;
  border: 1px solid var(--border-color);
  border-radius: 14px;
  padding: 9px 14px;
  font-size: 0.84rem;
  color: #334155;
  text-align: left;
  cursor: pointer;
  transition: all 0.15s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03);
}

.quick-prompt-btn:hover {
  background: var(--primary-light);
  border-color: var(--primary);
  color: var(--primary-hover);
  transform: translateY(-1px);
  box-shadow: 0 3px 8px var(--primary-glow);
}

/* Rows & Bubbles */
.message-row {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  width: 100%;
}

.message-row.me {
  justify-content: flex-end;
}

.message-row.them {
  justify-content: flex-start;
}

.msg-avatar {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: #cbd5e1;
  color: #334155;
  font-size: 0.72rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-bottom: 2px;
}

.message-bubble-col {
  display: flex;
  flex-direction: column;
  max-width: min(78%, 520px);
}

.message-row.me .message-bubble-col {
  align-items: flex-end;
}

.message-row.them .message-bubble-col {
  align-items: flex-start;
}

.message-bubble {
  padding: 9px 14px;
  border-radius: 18px;
  position: relative;
  word-break: break-word;
}

.message-row.me .message-bubble {
  background: linear-gradient(135deg, var(--primary) 0%, #0f766e 100%);
  color: #ffffff;
  border-bottom-right-radius: 4px;
  box-shadow: 0 2px 8px var(--primary-glow);
}

.message-row.them .message-bubble {
  background: #ffffff;
  color: #0f172a;
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-bottom-left-radius: 4px;
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.04);
}

.bubble-text {
  font-size: 0.92rem;
  line-height: 1.45;
  margin: 0;
}

.bubble-meta {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 4px;
  margin-top: 4px;
}

.bubble-time {
  font-size: 0.68rem;
  opacity: 0.75;
}

.delivery-icon {
  opacity: 0.85;
}

.delivery-icon.seen {
  color: #a7f3d0;
  opacity: 1;
}

.delivery-icon.sent {
  color: rgba(255, 255, 255, 0.65);
}

.seen-receipt-text {
  font-size: 0.68rem;
  color: #059669;
  font-weight: 600;
  margin-top: 3px;
  display: flex;
  align-items: center;
  gap: 3px;
  padding-right: 2px;
}

/* Input Bar */
.input-bar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  margin-bottom: var(--bottom-nav-height);
  background: rgba(255, 255, 255, 0.96);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-top: 1px solid var(--border-color);
  box-shadow: 0 -2px 10px rgba(15, 23, 42, 0.03);
  z-index: 10;
}

.input-wrapper {
  flex: 1;
  position: relative;
}

.chat-input {
  width: 100%;
  border-radius: 9999px;
  padding: 10px 18px;
  font-size: 0.92rem;
  background: #f8fafc;
  border: 1.5px solid var(--border-color);
  color: #0f172a;
  transition: all 0.15s ease;
  outline: none;
}

.chat-input:focus {
  background: #ffffff;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-glow);
}

.send-btn {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  border: none;
  background: linear-gradient(135deg, var(--primary) 0%, #0f766e 100%);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.15s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 2px 8px var(--primary-glow);
}

.send-btn:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 4px 12px var(--primary-glow);
}

.send-btn:active:not(:disabled) {
  transform: scale(0.96);
}

.send-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
  box-shadow: none;
}

/* Spinners */
.chat-spinner-large {
  width: 28px;
  height: 28px;
  border: 3px solid rgba(13, 148, 136, 0.2);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 10px auto;
}

.chat-spinner-sm {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #ffffff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.chat-loading-state {
  text-align: center;
  padding: 40px 10px;
  color: #64748b;
  font-size: 0.88rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
