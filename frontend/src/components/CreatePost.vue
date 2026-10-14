<template>
  <div class="create-view">
    <div v-if="!state.user" class="card empty-card">
      <div class="empty-icon">🔐</div>
      <h3>Sign in to Post</h3>
      <p>You need to be signed in to post requests or offers to your neighborhood.</p>
      <button class="btn btn-primary" style="margin-top: 16px" @click="openAuth">
        Sign In / Register
      </button>
    </div>

    <div v-else class="card form-card">
      <h2 class="page-title">New Post</h2>
      <p class="page-subtitle">Share what you need or what you have to offer.</p>

      <div v-if="error" class="error-box">{{ error }}</div>

      <form @submit.prevent="submitPost">
        <!-- Post Type Selector -->
        <div class="form-group">
          <label class="form-label">Post Type</label>
          <div class="type-selector">
            <button
              type="button"
              :class="['type-option', { active: form.type === 'request' }]"
              @click="form.type = 'request'"
            >
              🙋 Request (Need help)
            </button>
            <button
              type="button"
              :class="['type-option', { active: form.type === 'offer' }]"
              @click="form.type = 'offer'"
            >
              🎁 Offer (Can share)
            </button>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">Title</label>
          <input
            v-model="form.title"
            class="form-input"
            required
            placeholder="e.g. Need ladder for 2 hours, or Extra lemons from garden"
          />
        </div>

        <div class="form-row">
          <div class="form-group" style="flex: 1">
            <label class="form-label">Category</label>
            <select v-model="form.category" class="form-select">
              <option value="Tools">Tools</option>
              <option value="Food">Food</option>
              <option value="Goods">Goods</option>
              <option value="Skills">Skills</option>
              <option value="Help">Help</option>
              <option value="Other">Other</option>
            </select>
          </div>

          <div class="form-group" style="flex: 1">
            <label class="form-label">Neighborhood</label>
            <input
              v-model="form.neighborhood"
              class="form-input"
              required
              placeholder="e.g. Downtown"
            />
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">Description & Details</label>
          <textarea
            v-model="form.description"
            class="form-textarea"
            rows="4"
            required
            placeholder="Provide timing, pickup location, or any details neighbors should know..."
          ></textarea>
        </div>

        <button type="submit" class="btn btn-primary btn-block" :disabled="submitting">
          {{ submitting ? 'Publishing...' : 'Publish Post' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { state } from '../state.js'
import { api } from '../api.js'

const submitting = ref(false)
const error = ref('')

const form = reactive({
  type: 'request',
  title: '',
  category: 'Tools',
  neighborhood: '',
  description: '',
})

function openAuth() {
  state.showAuthModal = true
}

onMounted(() => {
  if (state.user && state.user.profile?.neighborhood) {
    form.neighborhood = state.user.profile.neighborhood
  }
})

async function submitPost() {
  submitting.value = true
  error.value = ''
  try {
    const post = await api.createPost(form)
    state.showToast('Post published successfully!')
    // Reset form
    form.title = ''
    form.description = ''
    // Switch to feed and view newly created post
    state.selectedPost = post
    state.currentTab = 'feed'
  } catch (err) {
    error.value = err.message || 'Failed to create post'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.page-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
}

.page-subtitle {
  font-size: 0.88rem;
  color: #64748b;
  margin-bottom: 16px;
}

.type-selector {
  display: flex;
  gap: 8px;
}

.type-option {
  flex: 1;
  padding: 10px;
  border: 1px solid var(--border-color);
  background: #f8fafc;
  color: #475569;
  border-radius: var(--radius-sm);
  font-weight: 600;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.15s ease;
}

.type-option.active {
  border-color: var(--primary);
  background: #e0f2fe;
  color: var(--primary);
}

.form-row {
  display: flex;
  gap: 12px;
}

.error-box {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #b91c1c;
  padding: 10px;
  border-radius: 8px;
  font-size: 0.85rem;
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
</style>
