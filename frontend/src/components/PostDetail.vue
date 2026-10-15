<template>
  <div class="detail-view">
    <div class="top-bar">
      <button class="back-btn" @click="closeDetail">
        <ArrowLeft class="inline-icon" :size="16" /> Back to Feed
      </button>
      <button class="report-link" @click="openReportModal">
        <TriangleAlert class="inline-icon" :size="14" /> Report
      </button>
    </div>

    <!-- Report Modal -->
    <ReportModal
      v-if="showReportModal"
      :post="post"
      @close="showReportModal = false"
    />

    <!-- Main Detail Card -->
    <div class="card detail-card">
      <!-- Badges Row -->
      <div class="badge-row">
        <span :class="['badge', post.type === 'offer' ? 'badge-offer' : 'badge-request']">
          <component :is="post.type === 'offer' ? Gift : HandHelping" class="inline-icon" :size="12" />
          {{ post.type === 'offer' ? 'Offer' : 'Request' }}
        </span>
        <span class="badge badge-category">
          <component :is="getCategoryIcon(post.category)" :size="11" class="inline-icon" />
          {{ post.category }}
        </span>
        <span :class="['badge', post.status === 'open' ? 'badge-active' : 'badge-closed']">
          {{ post.status === 'open' ? 'Active' : 'Closed' }}
        </span>
      </div>

      <h2 class="post-title">{{ post.title }}</h2>

      <!-- Author Profile Card -->
      <div class="author-card">
        <div class="author-avatar">
          {{ (post.author_display_name || 'N').charAt(0).toUpperCase() }}
        </div>
        <div class="author-info">
          <div class="author-name-row">
            <span class="author-name">{{ post.author_display_name }}</span>
            <span v-if="post.author_username" class="author-handle">@{{ post.author_username }}</span>
          </div>
          <div class="author-meta-sub">
            <span class="author-area">
              <MapPin :size="12" class="inline-icon loc-icon" />
              {{ post.neighborhood || 'Local Neighbor' }}
            </span>
            <span class="meta-dot">•</span>
            <span class="post-time-meta">
              <Clock :size="11" class="inline-icon" />
              {{ formatRelativeTime(post.created_at) }}
            </span>
          </div>
        </div>
      </div>

      <!-- Description Body -->
      <div class="description-section">
        <h4 class="section-label">Details</h4>
        <p class="description-body">{{ post.description }}</p>
      </div>

      <!-- Prominent Privacy-Safe Location Card -->
      <div class="location-box">
        <div class="loc-icon-bubble">
          <MapPin :size="18" />
        </div>
        <div class="loc-box-text">
          <div class="loc-box-title">{{ post.neighborhood || 'Local Area' }}</div>
          <div v-if="post.address && post.address !== post.neighborhood" class="loc-box-subtitle">
            Near {{ post.address }}
          </div>
          <div class="loc-safety-subtext">
            <span>Approximate ~400m area for neighbor privacy</span>
          </div>
        </div>
        <div v-if="post.latitude && post.longitude" class="loc-radius-badge" title="Approximate ~400m area for user privacy">
          <ShieldCheck :size="12" />
          <span>Approx. Area</span>
        </div>
      </div>

      <!-- Actions Section -->
      <div class="actions-section">
        <!-- If Author -->
        <div v-if="isAuthor" class="author-actions">
          <button
            v-if="post.status === 'open'"
            class="btn btn-secondary btn-block"
            @click="closePost"
            :disabled="actionLoading"
          >
            <CheckCircle2 class="inline-icon" :size="16" /> Mark as Resolved / Close
          </button>
          <div v-else class="status-notice">
            This post is marked as closed.
          </div>
        </div>

        <!-- If Neighbor (Not Author) -->
        <div v-else class="respond-actions">
          <div v-if="!state.user" class="login-prompt">
            <p>Sign in to contact {{ post.author_display_name }} directly.</p>
            <button class="btn btn-primary btn-block" style="margin-top: 10px" @click="openAuth">
              Sign In to Respond
            </button>
          </div>

          <div v-else-if="post.status === 'open'" class="message-composer">
            <label class="form-label composer-label">
              <MessageCircle :size="14" class="inline-icon" />
              <span>Send a direct message to {{ post.author_display_name }}:</span>
            </label>

            <!-- Quick Suggestion Reply Chips -->
            <div class="quick-replies-row">
              <button
                v-for="(reply, idx) in quickReplies"
                :key="idx"
                type="button"
                class="quick-reply-chip"
                @click="applyQuickReply(reply)"
              >
                {{ reply }}
              </button>
            </div>

            <textarea
              v-model="responseMessage"
              class="form-textarea message-input"
              placeholder="Type your message here..."
              rows="3"
            ></textarea>

            <button
              class="btn btn-primary btn-block send-btn"
              :disabled="actionLoading || !responseMessage.trim()"
              @click="respondToPost"
            >
              <Send v-if="!actionLoading" class="inline-icon" :size="15" />
              <span>{{ actionLoading ? 'Sending...' : 'Send Message & Open Chat' }}</span>
            </button>
          </div>

          <div v-else class="status-notice">
            This post has been resolved and is closed.
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import {
  ArrowLeft, TriangleAlert, Gift, HandHelping, MapPin, CheckCircle2,
  MessageCircle, ShieldCheck, Clock, Send, Wrench, Utensils,
  Package, Sparkles, Layers
} from 'lucide-vue-next'
import { state } from '../state.js'
import { api } from '../api.js'
import ReportModal from './ReportModal.vue'

const post = computed(() => state.selectedPost || {})
const isAuthor = computed(() => {
  return state.user && state.user.username === post.value.author_username
})

const actionLoading = ref(false)
const responseMessage = ref('')
const showReportModal = ref(false)

function getCategoryIcon(cat) {
  switch (cat) {
    case 'Tools': return Wrench
    case 'Food': return Utensils
    case 'Goods': return Package
    case 'Skills': return Sparkles
    case 'Help': return HandHelping
    default: return Layers
  }
}

function formatRelativeTime(iso) {
  if (!iso) return ''
  const date = new Date(iso)
  const now = new Date()
  const diffSec = Math.floor((now - date) / 1000)
  if (diffSec < 45) return 'Just now'
  const diffMin = Math.floor(diffSec / 60)
  if (diffMin < 60) return `${diffMin}m ago`
  const diffHour = Math.floor(diffMin / 60)
  if (diffHour < 24) return `${diffHour}h ago`
  const diffDay = Math.floor(diffHour / 24)
  if (diffDay === 1) return 'Yesterday'
  if (diffDay < 7) return `${diffDay}d ago`
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}

const quickReplies = computed(() => {
  if (post.value.type === 'offer') {
    return [
      'Hi! Is this still available?',
      "I'd love to pick this up!",
      'What time works best for you?'
    ]
  } else {
    return [
      'Hi! I can help with this!',
      'I have one you can borrow!',
      'Where can I drop this off?'
    ]
  }
})

function applyQuickReply(text) {
  responseMessage.value = text
}

function closeDetail() {
  state.selectedPost = null
}

function openAuth() {
  state.showAuthModal = true
}

function openReportModal() {
  if (!state.user) {
    state.showAuthModal = true
    return
  }
  showReportModal.value = true
}

async function closePost() {
  actionLoading.value = true
  try {
    const updated = await api.updatePost(post.value.id, { status: 'closed' })
    state.selectedPost = updated
    state.showToast('Post marked as closed.')
  } catch (err) {
    state.showToast(err.message || 'Could not close post')
  } finally {
    actionLoading.value = false
  }
}

async function respondToPost() {
  if (!responseMessage.value.trim()) return
  actionLoading.value = true
  try {
    const conv = await api.startConversation(post.value.id, responseMessage.value.trim())
    state.showToast('Message sent!')
    state.selectedPost = null
    state.activeConversationId = conv.id
    state.currentTab = 'messages'
  } catch (err) {
    state.showToast(err.message || 'Failed to send message')
  } finally {
    actionLoading.value = false
  }
}
</script>

<style scoped>
.detail-view {
  display: flex;
  flex-direction: column;
  padding-top: 14px;
}

.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #ffffff;
  border: 1px solid var(--border-color);
  font-size: 0.85rem;
  font-weight: 600;
  color: #334155;
  cursor: pointer;
  padding: 6px 14px;
  border-radius: 9999px;
  transition: all 0.15s ease;
  box-shadow: var(--shadow-sm);
}

.back-btn:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
  color: var(--primary);
  transform: translateY(-0.5px);
}

.report-link {
  background: none;
  border: none;
  font-size: 0.8rem;
  font-weight: 500;
  color: #94a3b8;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 10px;
  border-radius: 8px;
  transition: all 0.15s ease;
}

.report-link:hover {
  color: #ef4444;
  background: #fef2f2;
}

.detail-card {
  padding: 22px;
  background: #ffffff;
  border: 1px solid rgba(226, 232, 240, 0.9);
  box-shadow: var(--shadow-sm);
}

.badge-row {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 14px;
  flex-wrap: wrap;
}

.badge-active {
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  color: #047857;
}

.post-title {
  font-size: 1.4rem;
  font-weight: 800;
  letter-spacing: -0.025em;
  color: #0f172a;
  margin-bottom: 16px;
  line-height: 1.3;
}

/* Author Card */
.author-card {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #f8fafc;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 12px 14px;
  margin-bottom: 20px;
}

.author-avatar {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: linear-gradient(135deg, #0d9488 0%, #0284c7 100%);
  color: #ffffff;
  font-size: 1.15rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(13, 148, 136, 0.25);
  flex-shrink: 0;
}

.author-info {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.author-name-row {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.author-name {
  font-size: 0.95rem;
  font-weight: 700;
  color: #1e293b;
}

.author-handle {
  font-size: 0.78rem;
  color: #94a3b8;
}

.author-meta-sub {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.76rem;
  color: #64748b;
  flex-wrap: wrap;
}

.author-area {
  color: var(--primary);
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 3px;
}

.loc-icon {
  margin-top: -1px;
}

.meta-dot {
  color: #cbd5e1;
}

.post-time-meta {
  color: #94a3b8;
  display: inline-flex;
  align-items: center;
  gap: 3px;
}

/* Description Section */
.description-section {
  margin-bottom: 22px;
}

.section-label {
  font-size: 0.8rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #94a3b8;
  margin-bottom: 8px;
}

.description-body {
  font-size: 0.95rem;
  line-height: 1.65;
  color: #334155;
  white-space: pre-wrap;
  background: #ffffff;
  border-left: 3px solid var(--primary);
  padding: 8px 0 8px 14px;
}

/* Location Box */
.location-box {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 12px 14px;
  margin-bottom: 22px;
}

.loc-icon-bubble {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: var(--primary-light);
  color: var(--primary);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.loc-box-text {
  flex: 1;
  min-width: 0;
}

.loc-box-title {
  font-weight: 700;
  font-size: 0.95rem;
  color: #1e293b;
  line-height: 1.3;
}

.loc-box-subtitle {
  font-size: 0.82rem;
  color: #64748b;
  margin-top: 2px;
}

.loc-safety-subtext {
  font-size: 0.72rem;
  color: #0d9488;
  margin-top: 4px;
  line-height: 1.3;
}

.loc-radius-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: #f0fdfa;
  border: 1px solid rgba(13, 148, 136, 0.3);
  color: #0f766e;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 9999px;
  white-space: nowrap;
}

/* Actions Section */
.actions-section {
  border-top: 1px solid #f1f5f9;
  padding-top: 18px;
}

.composer-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.82rem;
  font-weight: 600;
  color: #475569;
  margin-bottom: 8px;
}

.quick-replies-row {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  margin-bottom: 10px;
  padding-bottom: 4px;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}

.quick-replies-row::-webkit-scrollbar {
  display: none;
}

.quick-reply-chip {
  background: #f8fafc;
  border: 1px solid var(--border-color);
  color: #475569;
  font-size: 0.75rem;
  font-weight: 500;
  padding: 5px 10px;
  border-radius: 9999px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s ease;
}

.quick-reply-chip:hover {
  background: var(--primary-light);
  border-color: rgba(13, 148, 136, 0.35);
  color: var(--primary);
}

.quick-reply-chip:active {
  transform: scale(0.96);
}

.message-input {
  font-size: 0.9rem;
  border-radius: 12px;
  padding: 10px 12px;
}

.send-btn {
  margin-top: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.status-notice {
  text-align: center;
  font-size: 0.88rem;
  color: #64748b;
  padding: 14px;
  background: #f8fafc;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-color);
}

.login-prompt {
  text-align: center;
  padding: 18px;
  background: #f8fafc;
  border-radius: var(--radius-sm);
  font-size: 0.9rem;
  color: #475569;
  border: 1px solid var(--border-color);
}
</style>
