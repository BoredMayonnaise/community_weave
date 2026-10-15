<template>
  <div class="profile-view">
    <div v-if="!state.user" class="card empty-card">
      <LockKeyhole class="empty-icon" :size="40" />
      <h3>Neighbor Profile</h3>
      <p>Sign in to manage your posts, profile, and neighborhood settings.</p>
      <button class="btn btn-primary" style="margin-top: 16px" @click="openAuth">
        Sign In / Register
      </button>
    </div>

    <div v-else>
      <!-- User Card -->
      <div class="card user-card">
        <div class="user-card-top">
          <div class="avatar-circle">
            {{ (state.user.profile?.display_name || state.user.username)[0].toUpperCase() }}
          </div>
          <div class="user-info">
            <h3 class="user-name">{{ state.user.profile?.display_name || state.user.username }}</h3>
            <span class="user-handle">@{{ state.user.username }}</span>
            <span class="user-neighborhood"><MapPin class="inline-icon" :size="14" />{{ state.user.profile?.neighborhood || 'No neighborhood set' }}</span>
          </div>
        </div>

        <div class="user-stats-row">
          <div class="stat-pill">
            <span class="stat-num">{{ myPosts.length }}</span>
            <span class="stat-label">Total</span>
          </div>
          <div class="stat-pill">
            <span class="stat-num stat-active">{{ activeCount }}</span>
            <span class="stat-label">Active</span>
          </div>
          <div class="stat-pill">
            <span class="stat-num stat-closed">{{ closedCount }}</span>
            <span class="stat-label">Resolved</span>
          </div>
        </div>
      </div>

      <!-- Quick Edit Neighborhood & Display Name -->
      <div class="card edit-card">
        <div class="edit-card-header">
          <h4 style="font-size: 0.95rem">Edit Profile & Neighborhood</h4>
          <button
            type="button"
            class="locate-badge-btn"
            @click="autoLocateNeighborhood"
            :disabled="locating"
            title="Auto-detect from GPS"
          >
            <LocateFixed :size="12" />
            <span>{{ locating ? 'Locating...' : 'Use My GPS' }}</span>
          </button>
        </div>
        <div style="display: flex; flex-direction: column; gap: 10px; margin-top: 10px;">
          <div>
            <label class="form-label" style="font-size: 0.76rem; margin-bottom: 4px; display: block; color: var(--text-muted);">Display Name</label>
            <input
              v-model="editDisplayName"
              class="form-input"
              placeholder="e.g. Maria Santos"
            />
          </div>
          <div>
            <label class="form-label" style="font-size: 0.76rem; margin-bottom: 4px; display: block; color: var(--text-muted);">Barangay / Neighborhood</label>
            <input
              v-model="editNeighborhood"
              class="form-input"
              placeholder="e.g. Brgy. Zone 15, Cadiz or Downtown"
            />
          </div>
          <button class="btn btn-primary btn-block" style="margin-top: 2px;" :disabled="savingProfile" @click="saveProfile">
            {{ savingProfile ? 'Saving...' : 'Save Changes' }}
          </button>
        </div>
      </div>

      <!-- My Posts -->
      <div class="my-posts-section">
        <h3 class="section-title">My Posts</h3>

        <div v-if="loadingPosts" class="state-msg">Loading your posts...</div>

        <div v-else-if="myPosts.length === 0" class="card empty-card" style="padding: 24px">
          <p>You haven't posted any requests or offers yet.</p>
          <button class="btn btn-secondary" style="margin-top: 10px" @click="goToCreate">
            + Create First Post
          </button>
        </div>

        <div v-else class="posts-list">
          <div v-for="post in myPosts" :key="post.id" class="card my-post-card">
            <div class="post-top">
              <span :class="['badge', post.type === 'offer' ? 'badge-offer' : 'badge-request']">
                <component :is="post.type === 'offer' ? Gift : HandHelping" class="inline-icon" :size="12" />
                {{ post.type === 'offer' ? 'Offer' : 'Request' }}
              </span>
              <span :class="['badge', post.status === 'open' ? 'badge-offer' : 'badge-closed']">
                {{ post.status === 'open' ? 'Active' : 'Closed' }}
              </span>
            </div>

            <h4 class="post-title" @click="openPost(post)">{{ post.title }}</h4>

            <div class="my-post-loc">
              <MapPin class="loc-pin" :size="12" />
              <span class="loc-main">{{ post.neighborhood }}</span>
              <span v-if="post.address && post.address !== post.neighborhood" class="loc-sub">
                • {{ post.address }}
              </span>
            </div>

            <div class="post-actions">
              <button
                v-if="post.status === 'open'"
                class="btn-text"
                @click="togglePostStatus(post, 'closed')"
              >
                Mark Closed
              </button>
              <button
                v-else
                class="btn-text text-primary"
                @click="togglePostStatus(post, 'open')"
              >
                Reopen Post
              </button>
              <button class="btn-text text-danger" @click="deletePost(post)">Delete</button>
              <button class="btn-text" @click="openPost(post)">View <ArrowRight class="inline-icon-end" :size="14" /></button>
            </div>
          </div>
        </div>
      </div>

      <!-- Security & Privacy Settings -->
      <div class="card security-card">
        <div class="security-card-header" @click="showSecuritySection = !showSecuritySection">
          <div class="security-header-title">
            <ShieldCheck class="inline-icon" :size="16" />
            <span>Security & Privacy</span>
          </div>
          <button type="button" class="btn-text">
            {{ showSecuritySection ? 'Hide' : 'Manage' }}
          </button>
        </div>

        <div v-if="showSecuritySection" class="security-card-body">
          <!-- Change Password -->
          <div class="security-subblock">
            <h5 class="subblock-title">Change Password</h5>
            <div v-if="passwordSuccess" class="success-box">{{ passwordSuccess }}</div>
            <div v-if="passwordError" class="error-box">{{ passwordError }}</div>
            <div class="password-form">
              <input
                v-model="oldPassword"
                type="password"
                autocomplete="current-password"
                class="form-input"
                placeholder="Current password"
              />
              <input
                v-model="newPassword"
                type="password"
                autocomplete="new-password"
                class="form-input"
                placeholder="New password (min 8 chars)"
              />
              <button
                class="btn btn-secondary btn-block"
                :disabled="savingPassword || !oldPassword || !newPassword"
                @click="handleChangePassword"
              >
                {{ savingPassword ? 'Updating...' : 'Update Password' }}
              </button>
            </div>
          </div>

          <!-- Delete Account -->
          <div class="security-subblock danger-zone">
            <h5 class="subblock-title text-danger">Delete Account & Data</h5>
            <p class="danger-desc">
              Permanently remove your account, profile, listings, and messages. This action cannot be undone.
            </p>
            <div v-if="!showDeleteConfirm">
              <button class="btn btn-outline-danger btn-block" @click="showDeleteConfirm = true">
                Delete My Account
              </button>
            </div>
            <div v-else class="delete-confirm-box">
              <label class="form-label" style="font-size: 0.78rem">Confirm password to delete:</label>
              <input
                v-model="deleteConfirmPassword"
                type="password"
                class="form-input"
                placeholder="Enter your password"
              />
              <div class="delete-btn-row">
                <button class="btn btn-secondary" style="flex: 1" @click="showDeleteConfirm = false">Cancel</button>
                <button
                  class="btn btn-danger"
                  style="flex: 1"
                  :disabled="deletingAccount || !deleteConfirmPassword"
                  @click="handleDeleteAccount"
                >
                  {{ deletingAccount ? 'Deleting...' : 'Permanently Delete' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Sign Out -->
      <button class="btn btn-secondary btn-block logout-btn" @click="logout">
        Sign Out
      </button>
    </div>

    <!-- App Version & Updates Card -->
    <div class="card update-card" style="margin-top: 16px;">
      <div class="update-card-header" style="display: flex; align-items: center; justify-content: space-between;">
        <div style="display: flex; align-items: center; gap: 8px;">
          <Smartphone class="inline-icon" :size="16" />
          <span style="font-weight: 600; font-size: 0.92rem;">App Version & Updates</span>
        </div>
        <span class="badge" style="font-size: 0.72rem; background: rgba(13, 148, 136, 0.12); color: var(--primary); font-weight: 600;">
          Installed: {{ APP_VERSION }}
        </span>
      </div>

      <p style="margin-top: 10px; font-size: 0.8rem; color: var(--text-muted); line-height: 1.4;">
        Community Weave native app for connecting and sharing with your neighbors.
      </p>

      <div style="margin-top: 10px; display: flex; flex-direction: column; gap: 8px;">
        <div style="display: flex; gap: 8px; align-items: center;">
          <button class="btn btn-secondary" style="font-size: 0.8rem; flex: 1;" :disabled="checkingUpdate" @click="checkForAppUpdates">
            <RefreshCw :size="13" :class="['inline-icon', { 'spin-icon': checkingUpdate }]" />
            <span>{{ checkingUpdate ? 'Checking GitHub...' : 'Check for Updates' }}</span>
          </button>
          <a
            v-if="latestRelease"
            :href="latestApkUrl || latestRelease.html_url"
            target="_blank"
            class="btn btn-primary"
            style="font-size: 0.8rem; text-decoration: none; display: inline-flex; align-items: center; gap: 5px; white-space: nowrap;"
          >
            <Download :size="13" />
            <span>Download {{ latestRelease.tag_name }}</span>
          </a>
        </div>
        <a
          href="/install.html"
          target="_blank"
          class="btn btn-secondary"
          style="font-size: 0.8rem; text-decoration: none; display: flex; align-items: center; justify-content: center; gap: 6px; background: rgba(13, 148, 136, 0.08); border-color: rgba(13, 148, 136, 0.25); color: var(--primary); font-weight: 600;"
        >
          <Smartphone :size="14" />
          <span>Install Guide & Direct Downloads (APK & iOS)</span>
        </a>
      </div>

      <div v-if="updateStatusMsg" :class="['state-msg', updateAvailable ? 'text-success' : 'text-muted']" style="font-size: 0.78rem; margin-top: 8px; padding: 6px 10px; border-radius: 6px; background: rgba(0,0,0,0.03);">
        {{ updateStatusMsg }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import {
  LockKeyhole, MapPin, ArrowRight, Gift, HandHelping, LocateFixed, ShieldCheck,
  Smartphone, RefreshCw, Download
} from 'lucide-vue-next'
import { state } from '../state.js'
import { api } from '../api.js'
import { geo } from '../geo.js'

const editDisplayName = ref('')
const editNeighborhood = ref('')
const savingProfile = ref(false)
const locating = ref(false)
const myPosts = ref([])
const loadingPosts = ref(false)

const APP_VERSION = 'v1.0.7'
const checkingUpdate = ref(false)
const updateStatusMsg = ref('')
const updateAvailable = ref(false)
const latestRelease = ref(null)
const latestApkUrl = ref('')

async function checkForAppUpdates() {
  checkingUpdate.value = true
  updateStatusMsg.value = ''
  updateAvailable.value = false
  latestRelease.value = null
  latestApkUrl.value = ''
  try {
    const res = await fetch('https://api.github.com/repos/BoredMayonnaise/community_weave/releases/latest', {
      headers: { 'Accept': 'application/vnd.github.v3+json' },
      signal: AbortSignal.timeout(8000)
    })
    if (!res.ok) {
      throw new Error(`GitHub API returned status ${res.status}`)
    }
    const data = await res.json()
    latestRelease.value = data
    const apkAsset = data.assets?.find(a => a.name.endsWith('.apk'))
    if (apkAsset) {
      latestApkUrl.value = apkAsset.browser_download_url
    }
    if (data.tag_name && data.tag_name !== APP_VERSION) {
      updateAvailable.value = true
      updateStatusMsg.value = `New release ${data.tag_name} is available!`
    } else {
      updateAvailable.value = false
      updateStatusMsg.value = `You are on the latest version (${APP_VERSION}).`
    }
  } catch (err) {
    updateStatusMsg.value = `Could not check updates: ${err.message}`
  } finally {
    checkingUpdate.value = false
  }
}

const showSecuritySection = ref(false)
const oldPassword = ref('')
const newPassword = ref('')
const savingPassword = ref(false)
const passwordSuccess = ref('')
const passwordError = ref('')

const showDeleteConfirm = ref(false)
const deleteConfirmPassword = ref('')
const deletingAccount = ref(false)

const activeCount = computed(() => myPosts.value.filter(p => p.status === 'open').length)
const closedCount = computed(() => myPosts.value.filter(p => p.status === 'closed').length)

async function autoLocateNeighborhood() {
  locating.value = true
  try {
    const loc = await geo.locateUser()
    editNeighborhood.value = loc.neighborhood
    const updated = await api.updateProfile({
      neighborhood: loc.neighborhood,
      address: loc.address,
      latitude: loc.latitude,
      longitude: loc.longitude
    })
    state.user = updated
    localStorage.setItem('cw_user', JSON.stringify(updated))
    state.showToast(`Updated to ${loc.neighborhood}!`)
  } catch (err) {
    state.showToast(err.message || 'Could not detect location')
  } finally {
    locating.value = false
  }
}

function openAuth() {
  state.showAuthModal = true
}

function openPost(post) {
  state.selectedPost = post
  state.currentTab = 'feed'
}

function goToCreate() {
  state.currentTab = 'create'
}

function logout() {
  api.logout().catch(() => {})
  state.logout()
}

async function handleChangePassword() {
  if (!oldPassword.value || !newPassword.value) return
  savingPassword.value = true
  passwordSuccess.value = ''
  passwordError.value = ''
  try {
    const res = await api.changePassword({
      old_password: oldPassword.value,
      new_password: newPassword.value
    })
    if (res.token) {
      state.token = res.token
      localStorage.setItem('cw_token', res.token)
    }
    passwordSuccess.value = 'Password updated successfully!'
    oldPassword.value = ''
    newPassword.value = ''
    state.showToast('Password changed successfully!')
  } catch (err) {
    passwordError.value = err.message || 'Failed to change password'
  } finally {
    savingPassword.value = false
  }
}

async function handleDeleteAccount() {
  if (!deleteConfirmPassword.value) return
  deletingAccount.value = true
  try {
    await api.deleteAccount({ password: deleteConfirmPassword.value })
    state.logout()
    state.showToast('Account permanently deleted.')
  } catch (err) {
    state.showToast(err.message || 'Failed to delete account')
  } finally {
    deletingAccount.value = false
  }
}

async function saveProfile() {
  savingProfile.value = true
  try {
    const payload = {}
    if (editNeighborhood.value.trim()) payload.neighborhood = editNeighborhood.value.trim()
    if (editDisplayName.value.trim()) payload.display_name = editDisplayName.value.trim()
    const updated = await api.updateProfile(payload)
    state.user = updated
    localStorage.setItem('cw_user', JSON.stringify(updated))
    state.showToast('Profile updated successfully!')
  } catch (err) {
    state.showToast(err.message || 'Failed to update')
  } finally {
    savingProfile.value = false
  }
}

async function fetchMyPosts() {
  if (!state.user) return
  loadingPosts.value = true
  try {
    myPosts.value = await api.getPosts({ author: state.user.username, status: 'all' })
  } catch (err) {
    // Ignore error
  } finally {
    loadingPosts.value = false
  }
}

async function togglePostStatus(post, newStatus) {
  try {
    const updated = await api.updatePost(post.id, { status: newStatus })
    post.status = updated.status
    state.showToast(`Post marked as ${newStatus}`)
  } catch (err) {
    state.showToast(err.message || 'Action failed')
  }
}

async function deletePost(post) {
  if (!confirm('Are you sure you want to delete this post?')) return
  try {
    await api.deletePost(post.id)
    myPosts.value = myPosts.value.filter(p => p.id !== post.id)
    state.showToast('Post deleted.')
  } catch (err) {
    state.showToast(err.message || 'Could not delete post')
  }
}

onMounted(() => {
  if (state.user) {
    editDisplayName.value = state.user.profile?.display_name || state.user.username || ''
    editNeighborhood.value = state.user.profile?.neighborhood || ''
    fetchMyPosts()
  }
})

watch(() => state.user, (u) => {
  if (u) {
    editDisplayName.value = u.profile?.display_name || u.username || ''
    editNeighborhood.value = u.profile?.neighborhood || ''
    fetchMyPosts()
  }
})
</script>

<style scoped>
.empty-card {
  text-align: center;
  padding: 40px 20px;
}

.user-card {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 18px;
  background: #ffffff;
  border: 1px solid rgba(226, 232, 240, 0.9);
  box-shadow: var(--shadow-sm);
}

.user-card-top {
  display: flex;
  align-items: center;
  gap: 14px;
}

.user-stats-row {
  display: flex;
  gap: 8px;
  border-top: 1px solid #f1f5f9;
  padding-top: 14px;
}

.stat-pill {
  flex: 1;
  background: #f8fafc;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 8px 6px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-num {
  font-size: 1.15rem;
  font-weight: 800;
  color: #0f172a;
  line-height: 1.1;
}

.stat-num.stat-active {
  color: var(--primary);
}

.stat-num.stat-closed {
  color: #64748b;
}

.stat-label {
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #94a3b8;
  margin-top: 3px;
}

.avatar-circle {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary) 0%, #14b8a6 100%);
  color: #ffffff;
  font-size: 1.5rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px var(--primary-glow);
}

.user-name {
  font-size: 1.15rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.015em;
}

.user-handle {
  display: block;
  font-size: 0.8rem;
  color: #94a3b8;
}

.user-neighborhood {
  display: block;
  font-size: 0.82rem;
  color: var(--primary);
  font-weight: 600;
  margin-top: 3px;
}

.edit-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
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

.form-row {
  display: flex;
  gap: 8px;
}

.my-posts-section {
  margin-top: 20px;
}

.section-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 12px;
}

.my-post-card {
  padding: 12px 14px;
}

.post-top {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}

.post-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #1e293b;
  cursor: pointer;
  margin-bottom: 6px;
}

.my-post-loc {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.75rem;
  color: #64748b;
  margin-bottom: 10px;
}

.my-post-loc .loc-pin {
  color: var(--primary);
  flex-shrink: 0;
}

.my-post-loc .loc-main {
  font-weight: 600;
  color: #334155;
}

.my-post-loc .loc-sub {
  color: #64748b;
  font-weight: 400;
}

.post-actions {
  display: flex;
  justify-content: flex-end;
  gap: 14px;
  border-top: 1px solid #f1f5f9;
  padding-top: 8px;
}

.btn-text {
  background: none;
  border: none;
  font-size: 0.82rem;
  font-weight: 600;
  color: #64748b;
  cursor: pointer;
}

.text-danger {
  color: #dc2626;
}

.text-primary {
  color: var(--primary);
}

.logout-btn {
  margin-top: 24px;
  color: #dc2626;
}

.state-msg {
  text-align: center;
  padding: 20px;
  color: #94a3b8;
}

/* Security & Privacy Card */
.security-card {
  margin-top: 16px;
  padding: 16px;
  border: 1px solid #e2e8f0;
}

.security-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
}

.security-header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.95rem;
  font-weight: 700;
  color: #1e293b;
}

.security-header-title .inline-icon {
  color: var(--primary);
}

.security-card-body {
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid #f1f5f9;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.security-subblock {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.subblock-title {
  font-size: 0.88rem;
  font-weight: 700;
  color: #334155;
  margin: 0;
}

.password-form {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.danger-zone {
  padding-top: 12px;
  border-top: 1px dashed #fecdd3;
}

.danger-desc {
  font-size: 0.78rem;
  color: #64748b;
  line-height: 1.4;
  margin: 0 0 4px 0;
}

.delete-confirm-box {
  background: #fff1f2;
  border: 1px solid #fecdd3;
  border-radius: 8px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.delete-btn-row {
  display: flex;
  gap: 8px;
}

.btn-outline-danger {
  background: transparent;
  border: 1px solid #fca5a5;
  color: #dc2626;
  font-size: 0.82rem;
  font-weight: 600;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-outline-danger:hover {
  background: #fef2f2;
  border-color: #dc2626;
}

.success-box {
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  color: #047857;
  font-size: 0.78rem;
  padding: 6px 10px;
  border-radius: 6px;
}
</style>
