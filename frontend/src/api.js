import { Capacitor } from '@capacitor/core'
import { state } from './state.js'

export const DEFAULT_LIVE_API_URL = 'https://communityweave.duckdns.org/api'

export function getApiBaseUrl() {
  const custom = localStorage.getItem('cw_server_url')
  if (custom && custom.trim()) {
    return custom.trim().replace(/\/+$/, '')
  }

  const envUrl = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL
  if (envUrl && envUrl.trim()) {
    return envUrl.trim().replace(/\/+$/, '')
  }

  if (Capacitor.isNativePlatform()) {
    return DEFAULT_LIVE_API_URL
  }

  return '/api'
}

export function setApiBaseUrl(url) {
  if (!url || !url.trim()) {
    localStorage.removeItem('cw_server_url')
  } else {
    localStorage.setItem('cw_server_url', url.trim())
  }
}

export async function apiRequest(endpoint, method = 'GET', data = null) {
  const headers = {}

  if (state.token) {
    headers['Authorization'] = `Token ${state.token}`
  }

  const options = {
    method,
    headers,
  }

  if (data !== null) {
    headers['Content-Type'] = 'application/json'
    options.body = JSON.stringify(data)
  }

  // Timeout + catch so a dead backend surfaces as a toast instead of a spinner that never stops.
  const baseUrl = getApiBaseUrl()
  const res = await fetch(`${baseUrl}${endpoint}`, { ...options, signal: AbortSignal.timeout(10000) })
    .catch(() => { throw new Error(`Backend unreachable at ${baseUrl}. Is the server online?`) })

  if (res.status === 204) {
    return null
  }

  let json = null
  try {
    json = await res.json()
  } catch (err) {
    // Non-JSON response
  }

  if (!res.ok) {
    const errorMsg = json?.detail || (typeof json === 'object' ? Object.values(json).flat().join(', ') : 'Request failed')
    const err = new Error(errorMsg)
    err.status = res.status
    throw err
  }

  return json
}

export const api = {
  // Auth
  register: (payload) => apiRequest('/auth/register/', 'POST', payload),
  login: (payload) => apiRequest('/auth/login/', 'POST', payload),
  logout: () => apiRequest('/auth/logout/', 'POST'),
  getMe: () => apiRequest('/auth/me/'),
  updateProfile: (payload) => apiRequest('/auth/me/', 'PATCH', payload),
  changePassword: (payload) => apiRequest('/auth/change-password/', 'POST', payload),
  deleteAccount: (payload) => apiRequest('/auth/delete-account/', 'POST', payload),
  ping: () => apiRequest('/auth/ping/', 'POST'),

  // Posts
  getPosts: (params = {}) => {
    const qs = new URLSearchParams(params).toString()
    return apiRequest(`/posts/${qs ? '?' + qs : ''}`)
  },
  getPost: (id) => apiRequest(`/posts/${id}/`),
  createPost: (data) => apiRequest('/posts/', 'POST', data),
  updatePost: (id, data) => apiRequest(`/posts/${id}/`, 'PATCH', data),
  deletePost: (id) => apiRequest(`/posts/${id}/`, 'DELETE'),

  // Conversations & Messages
  getConversations: () => apiRequest('/conversations/'),
  startConversation: (postId, message) => apiRequest('/conversations/', 'POST', { post_id: postId, message }),
  getMessages: (conversationId) => apiRequest(`/conversations/${conversationId}/messages/`),
  sendMessage: (conversationId, text) => apiRequest(`/conversations/${conversationId}/messages/`, 'POST', { text }),

  // Reports
  reportPost: (postId, reason) => apiRequest('/reports/', 'POST', { post_id: postId, reason }),

  // Neighborhoods
  getNeighborhoods: () => apiRequest('/neighborhoods/'),
}
