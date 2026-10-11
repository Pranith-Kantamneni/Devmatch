const API_BASE = (import.meta.env?.VITE_API_URL || '') + '/api/v1'

function formatDetail(detail, fallback) {
  if (detail === undefined || detail === null || detail === '') return fallback
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    const parts = detail
      .map((d) => {
        if (typeof d === 'string') return d
        if (d && typeof d === 'object') {
          const loc = Array.isArray(d.loc) ? d.loc.slice(1).join('.') : ''
          const msg = d.msg || d.message || JSON.stringify(d)
          return loc ? `${loc}: ${msg}` : msg
        }
        return String(d)
      })
      .filter(Boolean)
    if (parts.length) return parts.join('; ')
    return fallback
  }
  if (typeof detail === 'object') {
    const msg = detail.msg || detail.message
    if (msg) return String(msg)
  }
  try {
    return JSON.stringify(detail)
  } catch {
    return fallback
  }
}

async function parseJsonSafe(response) {
  const contentType = response.headers.get('content-type')
  if (contentType && contentType.includes('application/json')) {
    try {
      return await response.json()
    } catch {
      return null
    }
  }
  return null
}

function buildError(data, status) {
  const fallback = `Request failed (${status})`
  const error = new Error(formatDetail(data?.detail, fallback))
  error.status = status
  error.detail = data?.detail
  return error
}

let authToken = localStorage.getItem('devmatch_token') || null
let refreshToken = localStorage.getItem('devmatch_refresh') || null
let refreshPromise = null

export function setToken(token) {
  authToken = token
  if (token) {
    localStorage.setItem('devmatch_token', token)
  } else {
    localStorage.removeItem('devmatch_token')
  }
}

export function setRefreshToken(token) {
  refreshToken = token
  if (token) {
    localStorage.setItem('devmatch_refresh', token)
  } else {
    localStorage.removeItem('devmatch_refresh')
  }
}

export function setTokens({ access_token, refresh_token }) {
  if (access_token) setToken(access_token)
  if (refresh_token !== undefined) setRefreshToken(refresh_token)
}

export function clearTokens() {
  setToken(null)
  setRefreshToken(null)
}

export function getToken() {
  return authToken
}

function unauthorized() {
  clearTokens()
  window.dispatchEvent(new Event('devmatch:unauthorized'))
}

/** Single-flight refresh: concurrent 401s share one rotation call. */
async function tryRefresh() {
  if (!refreshToken) return false
  if (!refreshPromise) {
    refreshPromise = (async () => {
      try {
        const url = new URL(`${API_BASE}/auth/refresh`, window.location.origin)
        const response = await fetch(url.pathname, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refreshToken }),
        })
        const data = await parseJsonSafe(response)
        if (!response.ok || !data?.access_token) return false
        setTokens(data)
        return true
      } catch {
        return false
      } finally {
        refreshPromise = null
      }
    })()
  }
  return refreshPromise
}

async function request(path, { method = 'GET', body, params, timeoutMs = 30000, _retried = false } = {}) {
  const url = new URL(API_BASE + path, window.location.origin)
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        if (Array.isArray(value)) {
          value.forEach((v) => url.searchParams.append(key, v))
        } else {
          url.searchParams.set(key, value)
        }
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

  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  let response
  try {
    response = await fetch(url.pathname + url.search, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    })
  } catch (err) {
    clearTimeout(timer)
    if (err?.name === 'AbortError') {
      const error = new Error('Request timed out. Please try again.')
      error.status = 0
      throw error
    }
    const error = new Error('Network error. Check your connection and try again.')
    error.status = 0
    throw error
  } finally {
    clearTimeout(timer)
  }

  const data = await parseJsonSafe(response)

  if (!response.ok) {
    // Expired access token? Rotate silently once, then retry the request.
    // Auth endpoints themselves never retry (avoid login loops).
    if (response.status === 401 && !path.startsWith('/auth/') && !_retried) {
      const ok = await tryRefresh()
      if (ok) {
        return request(path, { method, body, params, timeoutMs, _retried: true })
      }
    }
    if (response.status === 401) {
      unauthorized()
    }
    throw buildError(data, response.status)
  }

  return data
}

export const api = {
  register: (payload) => request('/auth/register', { method: 'POST', body: payload }),
  login: (payload) => request('/auth/login', { method: 'POST', body: payload }),
  refresh: (payload) => request('/auth/refresh', { method: 'POST', body: payload }),
  logout: (payload) => request('/auth/logout', { method: 'POST', body: payload }),

  getOAuthProviders: () => request('/auth/oauth/providers'),
  getOAuthLoginUrl: (provider) => request(`/auth/oauth/${provider}/login`),
  completeOAuthLogin: (provider, params) =>
    request(`/auth/oauth/${provider}/callback`, { params }),

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
  listJoinedTeams: () => request('/team-projects/me/teams'),
  getTeamProject: (id) => request(`/team-projects/${id}`),
  createTeamProject: (payload) => request('/team-projects', { method: 'POST', body: payload }),
  updateTeamProject: (id, payload) => request(`/team-projects/${id}`, { method: 'PUT', body: payload }),
  deleteTeamProject: (id) => request(`/team-projects/${id}`, { method: 'DELETE' }),
  addTeamSkill: (id, payload) => request(`/team-projects/${id}/skills`, { method: 'POST', body: payload }),
  removeTeamSkill: (id, skillId) => request(`/team-projects/${id}/skills/${skillId}`, { method: 'DELETE' }),
  getTeamRecommendations: (id, params) => request(`/team-projects/${id}/recommendations`, { params }),
  getTeamSkillGaps: (id) => request(`/team-projects/${id}/skill-gaps`),
  listTeamMessages: (id, params) => request(`/team-projects/${id}/messages`, { params }),
  postTeamMessage: (id, payload) => request(`/team-projects/${id}/messages`, { method: 'POST', body: payload }),
  listApplicationMessages: (id, appId, params) =>
    request(`/team-projects/${id}/applications/${appId}/messages`, { params }),
  postApplicationMessage: (id, appId, payload) =>
    request(`/team-projects/${id}/applications/${appId}/messages`, { method: 'POST', body: payload }),

  listPolls: (id) => request(`/team-projects/${id}/polls`),
  createPoll: (id, payload) => request(`/team-projects/${id}/polls`, { method: 'POST', body: payload }),
  votePoll: (id, pollId, payload) => request(`/team-projects/${id}/polls/${pollId}/vote`, { method: 'POST', body: payload }),
  closePoll: (id, pollId) => request(`/team-projects/${id}/polls/${pollId}/close`, { method: 'POST' }),

  chatOverview: () => request('/chat/overview'),
  chatStatus: (userId) => request(`/chat/with/${userId}`),
  requestChat: (payload) => request('/chat/requests', { method: 'POST', body: payload }),
  acceptChat: (convoId) => request(`/chat/requests/${convoId}/accept`, { method: 'POST' }),
  rejectChat: (convoId) => request(`/chat/requests/${convoId}/reject`, { method: 'POST' }),
  listDMMessages: (convoId, params) => request(`/chat/conversations/${convoId}/messages`, { params }),
  postDMMessage: (convoId, payload) => request(`/chat/conversations/${convoId}/messages`, { method: 'POST', body: payload }),

  listColleges: (params) => request('/meta/colleges', { params }),
  listBranches: () => request('/meta/branches'),
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

    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), 120000)
    let response
    try {
      response = await fetch(`${API_BASE}/profiles/me/parse-resume`, {
        method: 'POST',
        headers,
        body: formData,
        signal: controller.signal,
      })
    } catch (err) {
      clearTimeout(timer)
      const error = new Error(
        err?.name === 'AbortError'
          ? 'Resume parsing timed out. Try a smaller file.'
          : 'Network error. Check your connection and try again.'
      )
      error.status = 0
      throw error
    } finally {
      clearTimeout(timer)
    }

    const data = await parseJsonSafe(response)

    if (!response.ok) {
      if (response.status === 401) {
        // Multipart uploads aren't retried automatically; rotate the
        // session so the user's next attempt still works.
        const ok = await tryRefresh()
        if (!ok) unauthorized()
      }
      throw buildError(data, response.status)
    }

    return data
  },
}
