<template>
  <div class="detail-view">
    <div class="top-bar">
      <button class="back-btn" @click="closeDetail">
        ← Back
      </button>
      <button class="report-link" @click="toggleReport">
        ⚠️ Report
      </button>
    </div>

    <!-- Report Box (if toggled) -->
    <div v-if="showReportBox" class="card report-box">
      <h4 style="margin-bottom: 6px; font-size: 0.95rem">Report this post</h4>
      <textarea
        v-model="reportReason"
        class="form-textarea"
        placeholder="Why are you reporting this post? (e.g. spam, inappropriate)"
        rows="2"
      ></textarea>
      <div style="display: flex; gap: 8px; margin-top: 8px">
        <button class="btn btn-secondary" style="flex: 1" @click="showReportBox = false">Cancel</button>
        <button class="btn btn-danger" style="flex: 1" :disabled="submittingReport" @click="submitReport">
          {{ submittingReport ? 'Sending...' : 'Submit Report' }}
        </button>
      </div>
    </div>

    <!-- Main Detail Card -->
    <div class="card detail-card">
      <div class="badge-row">
        <span :class="['badge', post.type === 'offer' ? 'badge-offer' : 'badge-request']">
          {{ post.type === 'offer' ? '🎁 Offer' : '🙋 Request' }}
        </span>
        <span class="badge badge-category">{{ post.category }}</span>
        <span v-if="post.status === 'closed'" class="badge badge-closed">Closed</span>
      </div>

      <h2 class="post-title">{{ post.title }}</h2>

      <div class="meta-row">
        <span>📍 {{ post.neighborhood }}</span>
        <span>•</span>
        <span>Posted by <strong>{{ post.author_display_name }}</strong></span>
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
            ✓ Mark as Resolved / Close
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
              {{ actionLoading ? 'Sending...' : '💬 Send Message & Open Chat' }}
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
import { state } from '../state.js'
import { api } from '../api.js'

const post = computed(() => state.selectedPost || {})
const isAuthor = computed(() => {
  return state.user && state.user.username === post.value.author_username
})

const actionLoading = ref(false)
const responseMessage = ref('')
const showReportBox = ref(false)
const reportReason = ref('')
const submittingReport = ref(false)

function closeDetail() {
  state.selectedPost = null
}

function openAuth() {
  state.showAuthModal = true
}

function toggleReport() {
  if (!state.user) {
    state.showAuthModal = true
    return
  }
  showReportBox.value = !showReportBox.value
}

async function submitReport() {
  if (!reportReason.value.trim()) return
  submittingReport.value = true
  try {
    await api.reportPost(post.value.id, reportReason.value.trim())
    state.showToast('Thank you. Post reported for review.')
    showReportBox.value = false
    reportReason.value = ''
  } catch (err) {
    state.showToast(err.message || 'Failed to submit report')
  } finally {
    submittingReport.value = false
  }
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
}

.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.back-btn {
  background: none;
  border: none;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--primary);
  cursor: pointer;
  padding: 6px 0;
}

.report-link {
  background: none;
  border: none;
  font-size: 0.8rem;
  color: #94a3b8;
  cursor: pointer;
}

.report-box {
  background: #fff1f2;
  border-color: #fecdd3;
  margin-bottom: 14px;
}

.badge-row {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 10px;
}

.post-title {
  font-size: 1.35rem;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 8px;
  line-height: 1.3;
}

.meta-row {
  display: flex;
  gap: 8px;
  font-size: 0.85rem;
  color: #64748b;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f1f5f9;
}

.description-body {
  font-size: 0.95rem;
  line-height: 1.6;
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
