import { reactive } from 'vue'

const savedToken = localStorage.getItem('cw_token') || ''
// Corrupt JSON here throws during module load and blanks the whole app
let savedUser = null
try { savedUser = JSON.parse(localStorage.getItem('cw_user')) } catch {}

export const state = reactive({
  token: savedToken,
  user: savedUser,
  currentTab: 'feed', // 'feed' | 'create' | 'messages' | 'profile'
  selectedPost: null,
  activeConversationId: null,
  showAuthModal: false,
  toast: null,
  unreadMessagesCount: 0,
  chatNotification: null,
  chatNotificationTimer: null,

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
    this.unreadMessagesCount = 0
    this.dismissChatNotification()
    this.showToast('Logged out')
  },

  showToast(msg) {
    this.toast = msg
    setTimeout(() => {
      if (this.toast === msg) this.toast = null
    }, 3000)
  },

  showChatNotification(notif) {
    if (this.chatNotificationTimer) {
      clearTimeout(this.chatNotificationTimer)
    }
    this.chatNotification = notif
    this.chatNotificationTimer = setTimeout(() => {
      this.chatNotification = null
    }, 5500)
  },

  dismissChatNotification() {
    if (this.chatNotificationTimer) {
      clearTimeout(this.chatNotificationTimer)
    }
    this.chatNotification = null
  }
})
