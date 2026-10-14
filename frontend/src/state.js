import { reactive } from 'vue'

const savedToken = localStorage.getItem('cw_token') || ''
const savedUser = localStorage.getItem('cw_user') ? JSON.parse(localStorage.getItem('cw_user')) : null

export const state = reactive({
  token: savedToken,
  user: savedUser,
  currentTab: 'feed', // 'feed' | 'create' | 'messages' | 'profile'
  selectedPost: null,
  activeConversationId: null,
  showAuthModal: false,
  toast: null,

  setAuth(token, user) {
    this.token = token
    this.user = user
    if (token) {
      localStorage.setItem('cw_token', token)
      localStorage.setItem('cw_user', JSON.stringify(user))
    } else {
      localStorage.removeItem('cw_token')
      localStorage.removeItem('cw_user')
    }
  },

  logout() {
    this.setAuth('', null)
    this.currentTab = 'feed'
    this.selectedPost = null
    this.activeConversationId = null
    this.showToast('Logged out')
  },

  showToast(msg) {
    this.toast = msg
    setTimeout(() => {
      if (this.toast === msg) this.toast = null
    }, 3000)
  }
})
