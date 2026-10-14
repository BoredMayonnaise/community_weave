import { state } from './state.js'

const BASE_URL = '/api'

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

  const res = await fetch(`${BASE_URL}${endpoint}`, options)

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
    throw new Error(errorMsg)
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
}
