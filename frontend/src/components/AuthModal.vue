<template>
  <div class="modal-overlay" @click.self="close">
    <div class="modal-sheet">
      <div class="modal-header">
        <h3 class="modal-title">{{ isRegister ? 'Join Community Weave' : 'Sign In' }}</h3>
        <button class="close-btn" @click="close">&times;</button>
      </div>

      <p class="modal-desc">
        {{ isRegister ? 'Connect with your neighbors to share tools, help, and goods.' : 'Welcome back! Sign in to chat and post.' }}
      </p>

      <div v-if="error" class="error-box">{{ error }}</div>

      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label class="form-label">Username</label>
          <input v-model="form.username" class="form-input" required autocomplete="username" placeholder="e.g. alex24" />
        </div>

        <div v-if="isRegister" class="form-group">
          <label class="form-label">Display Name</label>
          <input v-model="form.display_name" class="form-input" placeholder="e.g. Alex Rivera" />
        </div>

        <div v-if="isRegister" class="form-group">
          <label class="form-label">Neighborhood / Area</label>
          <input v-model="form.neighborhood" class="form-input" placeholder="e.g. Downtown, Oakridge" />
        </div>

        <div class="form-group">
          <label class="form-label">Password</label>
          <input type="password" v-model="form.password" class="form-input" required autocomplete="current-password" placeholder="••••••••" />
        </div>

        <button type="submit" class="btn btn-primary btn-block" :disabled="loading">
          {{ loading ? 'Please wait...' : (isRegister ? 'Create Account' : 'Sign In') }}
        </button>
      </form>

      <div class="modal-footer">
        <button type="button" class="switch-btn" @click="toggleMode">
          {{ isRegister ? 'Already have an account? Sign In' : 'Need an account? Sign Up' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { state } from '../state.js'
import { api } from '../api.js'

const isRegister = ref(false)
const loading = ref(false)
const error = ref('')

const form = reactive({
  username: '',
  password: '',
  display_name: '',
  neighborhood: '',
})

function close() {
  state.showAuthModal = false
  error.value = ''
}

function toggleMode() {
  isRegister.value = !isRegister.value
  error.value = ''
}

async function handleSubmit() {
  loading.value = true
  error.value = ''
  try {
    let res
    if (isRegister.value) {
      res = await api.register(form)
    } else {
      res = await api.login({ username: form.username, password: form.password })
    }
    state.setAuth(res.token, res.user)
    state.showToast(`Welcome ${res.user.profile?.display_name || res.user.username}!`)
    close()
  } catch (err) {
    error.value = err.message || 'Authentication failed'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(4px);
  z-index: 100;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

@media (min-width: 480px) {
  .modal-overlay {
    align-items: center;
  }
}

.modal-sheet {
  width: 100%;
  max-width: 440px;
  background: #ffffff;
  border-radius: 24px 24px 0 0;
  padding: 24px 20px 32px 20px;
  animation: slideUp 0.25s ease-out;
}

@media (min-width: 480px) {
  .modal-sheet {
    border-radius: 20px;
  }
}

@keyframes slideUp {
  from { transform: translateY(100%); }
  to { transform: translateY(0); }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #94a3b8;
  cursor: pointer;
  padding: 4px;
}

.modal-desc {
  font-size: 0.88rem;
  color: #64748b;
  margin-bottom: 16px;
  line-height: 1.4;
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

.modal-footer {
  margin-top: 16px;
  text-align: center;
}

.switch-btn {
  background: none;
  border: none;
  color: #0284c7;
  font-weight: 600;
  font-size: 0.88rem;
  cursor: pointer;
}
</style>
