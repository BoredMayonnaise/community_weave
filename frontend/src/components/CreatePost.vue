<template>
  <div class="create-view">
    <div v-if="!state.user" class="card empty-card">
      <LockKeyhole class="empty-icon" :size="40" />
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
              :class="['type-option', { 'request-active active': form.type === 'request' }]"
              @click="form.type = 'request'"
            >
              <HandHelping class="inline-icon" :size="16" /> Request (Need help)
            </button>
            <button
              type="button"
              :class="['type-option', { 'offer-active active': form.type === 'offer' }]"
              @click="form.type = 'offer'"
            >
              <Gift class="inline-icon" :size="16" /> Offer (Can share)
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
            <div class="label-with-btn">
              <label class="form-label" style="margin-bottom: 0">Barangay / Neighborhood</label>
              <button
                type="button"
                class="locate-badge-btn"
                @click="autoLocate"
                :disabled="locating"
                title="Auto-detect from GPS"
              >
                <LocateFixed :size="12" />
                <span>{{ locating ? 'Locating...' : 'Locate Me' }}</span>
              </button>
            </div>
            <input
              v-model="form.neighborhood"
              class="form-input"
              required
              placeholder="e.g. Brgy. Zone 15, Cadiz or Downtown"
              list="neighborhood-options"
            />
            <datalist id="neighborhood-options">
              <option v-for="n in neighborhoods" :key="n" :value="n" />
            </datalist>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">Approximate Address or Pickup Spot <span class="optional-label">(Optional)</span></label>
          <input
            v-model="form.address"
            class="form-input"
            placeholder="e.g. Rizal St. or Near City Hall"
          />
          <div class="geo-safety-box">
            <ShieldCheck :size="15" class="geo-safety-icon" />
            <div class="geo-safety-text">
              <strong>Privacy Protection:</strong> Your exact doorstep is never shared publicly. Neighbors only see a safe approximate ~400m area on the map.
            </div>
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
import { LockKeyhole, HandHelping, Gift, LocateFixed, ShieldCheck } from 'lucide-vue-next'
import { state } from '../state.js'
import { api } from '../api.js'
import { geo } from '../geo.js'

const submitting = ref(false)
const locating = ref(false)
const error = ref('')
const neighborhoods = ref(['Downtown', 'North Hills', 'Riverside', 'West End', 'Oakridge'])

const form = reactive({
  type: 'request',
  title: '',
  category: 'Tools',
  neighborhood: '',
  address: '',
  latitude: null,
  longitude: null,
  description: '',
})

function openAuth() {
  state.showAuthModal = true
}

async function autoLocate() {
  locating.value = true
  try {
    const loc = await geo.locateUser()
    form.neighborhood = loc.neighborhood
    form.address = loc.address
    form.latitude = loc.latitude
    form.longitude = loc.longitude
    if (loc.neighborhood && !neighborhoods.value.includes(loc.neighborhood)) {
      neighborhoods.value.push(loc.neighborhood)
    }
    state.showToast(`Detected location: ${loc.neighborhood}`)
  } catch (err) {
    state.showToast(err.message || 'Could not detect location')
  } finally {
    locating.value = false
  }
}

onMounted(() => {
  if (state.user && state.user.profile?.neighborhood) {
    form.neighborhood = state.user.profile.neighborhood
  }
  api.getNeighborhoods().then(res => { if (res?.length) neighborhoods.value = res }).catch(() => {})
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
    form.address = ''
    form.latitude = null
    form.longitude = null
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
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
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
  border-width: 1.5px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.type-option.request-active {
  border-color: #3b82f6;
  background: #eff6ff;
  color: #1d4ed8;
}

.type-option.offer-active {
  border-color: #10b981;
  background: #ecfdf5;
  color: #047857;
}

/* flex `gap` already spaces these out; drop the inline-text margin */
.type-option .inline-icon {
  margin-right: 0;
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

.label-with-btn {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.locate-badge-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: var(--primary-light);
  border: 1px solid rgba(13, 148, 136, 0.3);
  color: var(--primary);
  border-radius: 9999px;
  padding: 2px 8px;
  font-size: 0.72rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.locate-badge-btn:hover:not(:disabled) {
  background: #ccfbf1;
  border-color: var(--primary);
}

.locate-badge-btn:disabled {
  opacity: 0.6;
  cursor: wait;
}

.optional-label {
  font-weight: 400;
  font-size: 0.75rem;
  color: #94a3b8;
}

.geo-safety-box {
  margin-top: 8px;
  display: flex;
  align-items: flex-start;
  gap: 8px;
  background: #f0fdfa;
  border: 1px solid rgba(13, 148, 136, 0.25);
  border-radius: 8px;
  padding: 8px 10px;
}

.geo-safety-icon {
  color: #0d9488;
  flex-shrink: 0;
  margin-top: 2px;
}

.geo-safety-text {
  font-size: 0.74rem;
  color: #134e4a;
  line-height: 1.4;
}

.geo-safety-text strong {
  font-weight: 700;
  color: #0f766e;
}
</style>
