<template>
  <div class="detail-view">
    <div class="top-bar">
      <button class="back-btn" @click="closeDetail">
        <ArrowLeft class="inline-icon" :size="16" /> Back
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
      <div class="badge-row">
        <span :class="['badge', post.type === 'offer' ? 'badge-offer' : 'badge-request']">
          <component :is="post.type === 'offer' ? Gift : HandHelping" class="inline-icon" :size="12" />
          {{ post.type === 'offer' ? 'Offer' : 'Request' }}
        </span>
        <span class="badge badge-category">{{ post.category }}</span>
        <span v-if="post.status === 'closed'" class="badge badge-closed">Closed</span>
      </div>

      <h2 class="post-title">{{ post.title }}</h2>

      <div class="meta-row">
        <span class="meta-item author-meta">
          <span class="detail-avatar-dot">{{ (post.author_display_name || 'N').charAt(0).toUpperCase() }}</span>
          <span>Posted by <strong>{{ post.author_display_name }}</strong></span>
        </span>
        <span v-if="post.created_at" class="meta-divider">•</span>
        <span v-if="post.created_at" class="meta-item date-meta">
          {{ formatDate(post.created_at) }}
        </span>
      </div>

      <!-- Prominent Location Card -->
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

      <div class="description-body">
        <p>{{ post.description }}</p>
      </div>

      <!-- Actions -->
      <div class="actions-section">
        <!-- If Author -->
        <div v-if="isAuthor" class="author-actions">
          <button
            v-if="post.status === 'open'"
            class="btn btn-secondary btn-block"
            @click="closePost"
            :disabled="actionLoading"
          >
            <Check class="inline-icon" :size="16" /> Mark as Resolved / Close
          </button>
          <p v-else class="status-notice">This post is marked as closed.</p>
        </div>

        <!-- If Neighbor (Not Author) -->
        <div v-else class="respond-actions">
          <div v-if="!state.user" class="login-prompt">
            <p>Sign in to contact {{ post.author_display_name }} directly.</p>
            <button class="btn btn-primary btn-block" style="margin-top: 8px" @click="openAuth">
              Sign In to Respond
            </button>
          </div>

          <div v-else-if="post.status === 'open'" class="message-composer">
            <label class="form-label">Send a direct message:</label>
            <textarea
              v-model="responseMessage"
              class="form-textarea"
              placeholder="Hi! I can help with this..."
              rows="3"
            ></textarea>
            <button
              class="btn btn-primary btn-block"
              style="margin-top: 8px"
              :disabled="actionLoading || !responseMessage.trim()"
              @click="respondToPost"
            >
              <MessageCircle v-if="!actionLoading" class="inline-icon" :size="16" />
              {{ actionLoading ? 'Sending...' : 'Send Message & Open Chat' }}
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
  ArrowLeft, TriangleAlert, Gift, HandHelping, MapPin, Check, MessageCircle, ShieldCheck
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

function formatDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
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
  padding: 20px;
  background: #ffffff;
  border: 1px solid rgba(226, 232, 240, 0.9);
  box-shadow: var(--shadow-sm);
}

.badge-row {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 12px;
}

.post-title {
  font-size: 1.35rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: #0f172a;
  margin-bottom: 10px;
  line-height: 1.3;
}

.meta-row {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 0.85rem;
  color: #64748b;
  margin-bottom: 18px;
  padding-bottom: 14px;
  border-bottom: 1px solid #f1f5f9;
  flex-wrap: wrap;
}

.meta-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.meta-divider {
  color: #cbd5e1;
}

.author-meta {
  color: #334155;
}

.date-meta {
  color: #94a3b8;
  font-size: 0.8rem;
}

.location-box {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 12px 14px;
  margin-bottom: 18px;
}

.loc-icon-bubble {
  width: 36px;
  height: 36px;
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

.detail-avatar-dot {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: linear-gradient(135deg, #0d9488 0%, #0284c7 100%);
  color: #ffffff;
  font-size: 0.7rem;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.description-body {
  font-size: 0.95rem;
  line-height: 1.65;
  color: #334155;
  white-space: pre-wrap;
  margin-bottom: 24px;
}

.actions-section {
  border-top: 1px solid #f1f5f9;
  padding-top: 16px;
}

.status-notice {
  text-align: center;
  font-size: 0.9rem;
  color: #64748b;
  padding: 12px;
  background: #f8fafc;
  border-radius: var(--radius-sm);
}

.login-prompt {
  text-align: center;
  padding: 16px;
  background: #f8fafc;
  border-radius: var(--radius-sm);
  font-size: 0.9rem;
  color: #475569;
}
</style>
