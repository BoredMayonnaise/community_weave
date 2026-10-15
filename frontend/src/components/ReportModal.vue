<template>
  <div class="modal-overlay" @click.self="close">
    <div class="report-sheet">
      <!-- Modal Header -->
      <div class="report-header">
        <div class="report-badge-icon">
          <ShieldAlert :size="20" />
        </div>
        <div class="report-header-text">
          <h3 class="report-title">Report Content</h3>
          <p class="report-subtitle">
            Help keep our neighborhood safe. Why are you reporting this
            <span v-if="targetAuthor">post by <strong>{{ targetAuthor }}</strong></span>
            <span v-else>post</span>?
          </p>
        </div>
        <button class="close-btn" @click="close" title="Close report modal">
          <X :size="18" />
        </button>
      </div>

      <!-- Error notice if API fails -->
      <div v-if="errorMessage" class="report-error-banner">
        <AlertCircle :size="16" class="error-icon" />
        <span>{{ errorMessage }}</span>
      </div>

      <!-- Report Form -->
      <form @submit.prevent="handleSubmit" class="report-form">
        <!-- Preset Reason Options -->
        <div class="options-list">
          <label
            v-for="opt in reportReasons"
            :key="opt.id"
            :class="['option-card', { selected: selectedReason === opt.id }]"
          >
            <input
              type="radio"
              name="reportReason"
              :value="opt.id"
              v-model="selectedReason"
              class="sr-only"
            />
            <div class="radio-indicator">
              <span v-if="selectedReason === opt.id" class="radio-dot"></span>
            </div>
            <div class="option-content">
              <div class="option-label">{{ opt.label }}</div>
              <div class="option-desc">{{ opt.desc }}</div>
            </div>
          </label>
        </div>

        <!-- Specific Details Input (Automatic for 'other' or toggled for others) -->
        <div v-if="selectedReason === 'other' || showCustomDetails" class="specific-details-section">
          <div class="details-header-row">
            <label class="details-label">
              {{ selectedReason === 'other' ? 'Specific reason / details *' : 'Additional details (optional)' }}
            </label>
            <span class="char-count" :class="{ 'char-limit': customDetails.length > 380 }">
              {{ 400 - customDetails.length }} left
            </span>
          </div>
          <textarea
            ref="textareaRef"
            v-model="customDetails"
            maxlength="400"
            rows="3"
            class="form-textarea details-textarea"
            :placeholder="selectedReason === 'other'
              ? 'Please describe specifically what is wrong with this user or post...'
              : 'Add any specific notes or context for community moderators...'"
            :required="selectedReason === 'other'"
          ></textarea>
        </div>

        <!-- Optional toggle for extra notes if not 'other' -->
        <div v-else-if="selectedReason" class="toggle-details-row">
          <button
            type="button"
            class="toggle-details-btn"
            @click="showCustomDetails = true"
          >
            + Add specific details with this user
          </button>
        </div>

        <!-- Action Buttons -->
        <div class="report-actions">
          <button
            type="button"
            class="btn btn-secondary cancel-btn"
            @click="close"
            :disabled="submitting"
          >
            Cancel
          </button>
          <button
            type="submit"
            class="btn btn-danger submit-btn"
            :disabled="submitting || !canSubmit"
          >
            <TriangleAlert v-if="!submitting" :size="15" />
            <span>{{ submitting ? 'Submitting...' : 'Submit Report' }}</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { ShieldAlert, TriangleAlert, AlertCircle, X } from 'lucide-vue-next'
import { state } from '../state.js'
import { api } from '../api.js'

const props = defineProps({
  post: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['close', 'reported'])

const reportReasons = [
  {
    id: 'spam',
    label: 'Spam or advertising',
    desc: 'Unwanted promotions, commercial ads, repetitive posts, or links.'
  },
  {
    id: 'inappropriate',
    label: 'Inappropriate or offensive',
    desc: 'Disrespectful language, harassment, hate speech, or nudity.'
  },
  {
    id: 'scam',
    label: 'Scam, fraud, or fake listing',
    desc: 'Suspicious requests, deception, payment fraud, or fake profiles.'
  },
  {
    id: 'safety',
    label: 'Safety concern or dangerous item',
    desc: 'Hazardous materials, weapons, illegal goods, or immediate risks.'
  },
  {
    id: 'other',
    label: 'Other reason',
    desc: 'Specify your own custom details regarding this user or post.'
  }
]

const selectedReason = ref('spam')
const customDetails = ref('')
const showCustomDetails = ref(false)
const submitting = ref(false)
const errorMessage = ref('')
const textareaRef = ref(null)

const targetAuthor = computed(() => {
  return props.post?.author_display_name || props.post?.author_username || ''
})

const canSubmit = computed(() => {
  if (!selectedReason.value) return false
  if (selectedReason.value === 'other') {
    return customDetails.value.trim().length > 0
  }
  return true
})

// Auto-focus textarea when 'other' is selected
watch(selectedReason, (newVal) => {
  errorMessage.value = ''
  if (newVal === 'other') {
    nextTick(() => {
      textareaRef.value?.focus()
    })
  }
})

function close() {
  emit('close')
}

async function handleSubmit() {
  if (!canSubmit.value || submitting.value) return
  submitting.value = true
  errorMessage.value = ''

  try {
    const matched = reportReasons.find(r => r.id === selectedReason.value)
    let finalReason = matched ? matched.label : selectedReason.value

    if (selectedReason.value === 'other') {
      finalReason = customDetails.value.trim()
        ? `Other: ${customDetails.value.trim()}`
        : 'Other'
    } else if (customDetails.value.trim()) {
      finalReason = `${matched.label} - ${customDetails.value.trim()}`
    }

    await api.reportPost(props.post.id, finalReason)
    state.showToast('Thank you. Post reported for community review.')
    emit('reported', props.post.id)
    close()
  } catch (err) {
    errorMessage.value = err.message || 'Failed to submit report. Please try again.'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.65);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  z-index: 9999;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding: 0;
}

@media (min-width: 520px) {
  .modal-overlay {
    align-items: center;
    padding: 20px;
  }
}

.report-sheet {
  width: 100%;
  max-width: 480px;
  background: #ffffff;
  border-radius: 24px 24px 0 0;
  padding: 22px 20px 28px 20px;
  box-shadow: 0 -10px 40px rgba(0, 0, 0, 0.2);
  animation: modalSlideUp 0.24s cubic-bezier(0.16, 1, 0.3, 1);
  max-height: 90vh;
  overflow-y: auto;
}

@media (min-width: 520px) {
  .report-sheet {
    border-radius: 20px;
    box-shadow: 0 20px 50px rgba(15, 23, 42, 0.25);
    animation: modalPopIn 0.22s cubic-bezier(0.16, 1, 0.3, 1);
  }
}

@keyframes modalSlideUp {
  from { transform: translateY(100%); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

@keyframes modalPopIn {
  from { transform: scale(0.95); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

.report-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 16px;
  position: relative;
}

.report-badge-icon {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: #fee2e2;
  color: #ef4444;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.report-header-text {
  flex: 1;
  min-width: 0;
}

.report-title {
  font-size: 1.15rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 2px 0;
}

.report-subtitle {
  font-size: 0.82rem;
  color: #64748b;
  margin: 0;
  line-height: 1.35;
}

.close-btn {
  background: none;
  border: none;
  color: #94a3b8;
  padding: 4px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}

.close-btn:hover {
  background: #f1f5f9;
  color: #334155;
}

.report-error-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #b91c1c;
  padding: 10px 12px;
  border-radius: 10px;
  font-size: 0.82rem;
  margin-bottom: 14px;
}

.error-icon {
  flex-shrink: 0;
}

.report-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.options-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.option-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 11px 14px;
  border-radius: 12px;
  border: 1.5px solid #e2e8f0;
  background: #f8fafc;
  cursor: pointer;
  transition: all 0.15s ease;
  user-select: none;
}

.option-card:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
}

.option-card.selected {
  background: #fff1f2;
  border-color: #f43f5e;
  box-shadow: 0 2px 8px rgba(244, 63, 94, 0.12);
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  border: 0;
}

.radio-indicator {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid #cbd5e1;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 2px;
  flex-shrink: 0;
  transition: all 0.15s ease;
}

.option-card.selected .radio-indicator {
  border-color: #f43f5e;
}

.radio-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #f43f5e;
}

.option-content {
  flex: 1;
}

.option-label {
  font-size: 0.88rem;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 2px;
}

.option-card.selected .option-label {
  color: #9f1239;
}

.option-desc {
  font-size: 0.75rem;
  color: #64748b;
  line-height: 1.3;
}

.option-card.selected .option-desc {
  color: #be123c;
}

.toggle-details-row {
  text-align: left;
}

.toggle-details-btn {
  background: none;
  border: none;
  color: #0d9488;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  padding: 4px 0;
  transition: color 0.15s ease;
}

.toggle-details-btn:hover {
  color: #0f766e;
  text-decoration: underline;
}

.specific-details-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
  animation: fadeIn 0.18s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

.details-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.details-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: #334155;
}

.char-count {
  font-size: 0.72rem;
  color: #94a3b8;
}

.char-limit {
  color: #ef4444;
  font-weight: 600;
}

.details-textarea {
  width: 100%;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1.5px solid #cbd5e1;
  font-size: 0.84rem;
  line-height: 1.4;
  resize: vertical;
  background: #ffffff;
  transition: border-color 0.15s ease;
}

.details-textarea:focus {
  outline: none;
  border-color: #f43f5e;
  box-shadow: 0 0 0 3px rgba(244, 63, 94, 0.12);
}

.report-actions {
  display: flex;
  gap: 10px;
  margin-top: 6px;
}

.cancel-btn {
  flex: 1;
  padding: 10px;
  font-size: 0.88rem;
  border-radius: 10px;
}

.submit-btn {
  flex: 1.4;
  padding: 10px;
  font-size: 0.88rem;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  background: #ef4444;
  border-color: #ef4444;
  color: #ffffff;
}

.submit-btn:hover:not(:disabled) {
  background: #dc2626;
  border-color: #dc2626;
}

.submit-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
</style>
