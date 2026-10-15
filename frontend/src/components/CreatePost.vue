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
      <p class="page-subtitle">Share what you need or what you have to offer with your neighbors.</p>

      <div v-if="error" class="error-box">{{ error }}</div>

      <form @submit.prevent="submitPost">
        <!-- Post Type Selector -->
        <div class="form-group">
          <label class="form-label">What would you like to post?</label>
          <div class="type-selector">
            <button
              type="button"
              :class="['type-option', { 'request-active active': form.type === 'request' }]"
              @click="form.type = 'request'"
            >
              <HandHelping class="inline-icon" :size="16" />
              <span>Request (Need Help)</span>
            </button>
            <button
              type="button"
              :class="['type-option', { 'offer-active active': form.type === 'offer' }]"
              @click="form.type = 'offer'"
            >
              <Gift class="inline-icon" :size="16" />
              <span>Offer (Can Share)</span>
            </button>
          </div>
        </div>

        <!-- Category Grid Selector -->
        <div class="form-group">
          <label class="form-label">Category</label>
          <div class="category-grid">
            <button
              v-for="cat in categoryList"
              :key="cat.name"
              type="button"
              :class="['cat-choice-btn', { active: form.category === cat.name }]"
              @click="form.category = cat.name"
            >
              <component :is="cat.icon" :size="15" class="cat-choice-icon" />
              <span>{{ cat.name }}</span>
            </button>
          </div>
        </div>

        <!-- Title -->
        <div class="form-group">
          <div class="label-with-hint">
            <label class="form-label">Title</label>
            <span class="char-count">{{ form.title.length }}/100</span>
          </div>
          <input
            v-model="form.title"
            maxlength="100"
            class="form-input"
            required
            :placeholder="form.type === 'request' ? 'e.g. Need ladder for 2 hours, or Looking for tutoring' : 'e.g. Extra lemons from garden, or Cordless drill to lend'"
          />
        </div>

        <!-- Neighborhood with GPS -->
        <div class="form-group">
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

        <!-- Approximate Address -->
        <div class="form-group">
          <label class="form-label">Approximate Landmark or Pickup Spot <span class="optional-label">(Optional)</span></label>
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

        <!-- Description -->
        <div class="form-group">
          <div class="label-with-hint">
            <label class="form-label">Description & Details</label>
            <span class="char-count">{{ form.description.length }}/1000</span>
          </div>
          <textarea
            v-model="form.description"
            maxlength="1000"
            class="form-textarea"
            rows="4"
            required
            placeholder="Provide timing, pickup location, or any details neighbors should know..."
          ></textarea>
        </div>

        <button type="submit" class="btn btn-primary btn-block publish-btn" :disabled="submitting">
          <Send v-if="!submitting" class="inline-icon" :size="15" />
          <span>{{ submitting ? 'Publishing...' : (form.type === 'offer' ? 'Publish Offer' : 'Publish Request') }}</span>
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import {
  LockKeyhole, HandHelping, Gift, LocateFixed, ShieldCheck,
  Wrench, Utensils, Package, Sparkles, Layers, Send
} from 'lucide-vue-next'
import { state } from '../state.js'
import { api } from '../api.js'
import { geo } from '../geo.js'

const submitting = ref(false)
const locating = ref(false)
const error = ref('')
const neighborhoods = ref([
  'Brgy. 171 Bagumbong, Caloocan',
  'Brgy. 177 Camarin, Caloocan',
  'Brgy. 170 Deparo, Caloocan',
  'Grace Park West, Caloocan',
  'Morning Breeze, Caloocan',
  'Brgy. UP Campus, Diliman, QC',
  'Brgy. Loyola Heights, QC',
  'Brgy. 400 Sampaloc, Manila',
  'Brgy. Poblacion, Makati',
  'Brgy. Kapitolyo, Pasig'
])

const categoryList = [
  { name: 'Tools', icon: Wrench },
  { name: 'Food', icon: Utensils },
  { name: 'Goods', icon: Package },
  { name: 'Skills', icon: Sparkles },
  { name: 'Help', icon: HandHelping },
  { name: 'Other', icon: Layers },
]

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
    if (state.user.profile.address) form.address = state.user.profile.address
    if (state.user.profile.latitude) form.latitude = state.user.profile.latitude
    if (state.user.profile.longitude) form.longitude = state.user.profile.longitude
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
  font-size: 1.3rem;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.02em;
}

.page-subtitle {
  font-size: 0.88rem;
  color: #64748b;
  margin-bottom: 18px;
}

.type-selector {
  display: flex;
  gap: 10px;
}

.type-option {
  flex: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 11px;
  border: 1.5px solid var(--border-color);
  background: #f8fafc;
  color: #475569;
  border-radius: var(--radius-sm);
  font-weight: 600;
  font-size: 0.86rem;
  cursor: pointer;
  transition: all 0.16s ease;
}

.type-option:hover {
  background: #f1f5f9;
}

.type-option.active {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
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

/* Category Grid */
.category-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.cat-choice-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 9px 8px;
  background: #f8fafc;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: #475569;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.cat-choice-btn:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
}

.cat-choice-btn.active {
  background: var(--primary-light);
  border-color: var(--primary);
  color: var(--primary);
  box-shadow: 0 2px 8px var(--primary-glow);
}

.cat-choice-icon {
  flex-shrink: 0;
}

.label-with-hint {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.label-with-btn {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.char-count {
  font-size: 0.72rem;
  color: #94a3b8;
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

.publish-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 0.92rem;
  padding: 12px;
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

@media (max-width: 480px) {
  .category-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
