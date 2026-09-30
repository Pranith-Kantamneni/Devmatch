const API_BASE = '/api/v1'

let authToken = localStorage.getItem('devmatch_token') || null

export function setToken(token) {
  authToken = token
  if (token) {
    localStorage.setItem('devmatch_token', token)
  } else {
    localStorage.removeItem('devmatch_token')
  }
}

export function getToken() {
  return authToken
}

async function request(path, { method = 'GET', body, params } = {}) {
  const url = new URL(API_BASE + path, window.location.origin)
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        url.searchParams.set(key, value)
      }
    })
  }

  const headers = {}
  if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
  }
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`
  }

  const response = await fetch(url.pathname + url.search, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  let data = null
  const contentType = response.headers.get('content-type')
  if (contentType && contentType.includes('application/json')) {
    data = await response.json()
  }

  if (!response.ok) {
    if (response.status === 401) {
      setToken(null)
      window.dispatchEvent(new Event('devmatch:unauthorized'))
    }
    const message = data?.detail || `Request failed (${response.status})`
    const error = new Error(message)
    error.status = response.status
    throw error
  }

  return data
}

export const api = {
  register: (payload) => request('/auth/register', { method: 'POST', body: payload }),
  login: (payload) => request('/auth/login', { method: 'POST', body: payload }),

  listUsers: (params) => request('/users/', { params }),
  getMe: () => request('/users/me'),

  getMyProfile: () => request('/profiles/me'),
  updateProfile: (payload) => request('/profiles/me', { method: 'PUT', body: payload }),
  getPublicProfile: (userId) => request(`/profiles/${userId}`),

  addSkill: (payload) => request('/profiles/me/skills', { method: 'POST', body: payload }),
  removeSkill: (skillId) => request(`/profiles/me/skills/${skillId}`, { method: 'DELETE' }),

  addProject: (payload) => request('/profiles/me/projects', { method: 'POST', body: payload }),
  removeProject: (projectId) => request(`/profiles/me/projects/${projectId}`, { method: 'DELETE' }),

  getRecommendations: (params) => request('/recommendations', { params }),

  listTeamProjects: (params) => request('/team-projects', { params }),
  getTeamProject: (id) => request(`/team-projects/${id}`),
  createTeamProject: (payload) => request('/team-projects', { method: 'POST', body: payload }),
  updateTeamProject: (id, payload) => request(`/team-projects/${id}`, { method: 'PUT', body: payload }),
  deleteTeamProject: (id) => request(`/team-projects/${id}`, { method: 'DELETE' }),
  addTeamSkill: (id, payload) => request(`/team-projects/${id}/skills`, { method: 'POST', body: payload }),
  removeTeamSkill: (id, skillId) => request(`/team-projects/${id}/skills/${skillId}`, { method: 'DELETE' }),
  getTeamRecommendations: (id, params) => request(`/team-projects/${id}/recommendations`, { params }),
  applyToTeam: (id, payload) => request(`/team-projects/${id}/apply`, { method: 'POST', body: payload }),
  listTeamApplications: (id) => request(`/team-projects/${id}/applications`),
  acceptApplication: (id, appId) => request(`/team-projects/${id}/applications/${appId}/accept`, { method: 'POST' }),
  rejectApplication: (id, appId) => request(`/team-projects/${id}/applications/${appId}/reject`, { method: 'POST' }),
  inviteToTeam: (id, payload) => request(`/team-projects/${id}/invite`, { method: 'POST', body: payload }),
  listMyApplications: () => request('/team-projects/me/applications'),
  listMyInvitations: () => request('/team-projects/me/invitations'),
  acceptInvitation: (invId) => request(`/team-projects/invitations/${invId}/accept`, { method: 'POST' }),
  rejectInvitation: (invId) => request(`/team-projects/invitations/${invId}/reject`, { method: 'POST' }),
  removeTeamMember: (id, userId) => request(`/team-projects/${id}/members/${userId}`, { method: 'DELETE' }),

  parseResume: async (file) => {
    const formData = new FormData()
    formData.append('file', file)

    const headers = {}
    if (authToken) {
      headers['Authorization'] = `Bearer ${authToken}`
    }

    const response = await fetch(`${API_BASE}/profiles/me/parse-resume`, {
      method: 'POST',
      headers,
      body: formData,
    })

    let data = null
    const contentType = response.headers.get('content-type')
    if (contentType && contentType.includes('application/json')) {
      data = await response.json()
    }

    if (!response.ok) {
      if (response.status === 401) {
        setToken(null)
        window.dispatchEvent(new Event('devmatch:unauthorized'))
      }
      const message = data?.detail || `Request failed (${response.status})`
      const error = new Error(message)
      error.status = response.status
      throw error
    }

    return data
  },
}
