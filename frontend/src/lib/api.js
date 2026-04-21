const API_BASE = '/api'
const TOKEN_KEY = 'helledger_token'

async function _request(method, path, body, retry = true) {
  const token = localStorage.getItem(TOKEN_KEY)
  const headers = { 'Content-Type': 'application/json' }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    credentials: 'include',
    body: body != null ? JSON.stringify(body) : undefined,
  })

  if (res.status === 401 && retry) {
    const ok = await _tryRefresh()
    if (ok) return _request(method, path, body, false)
  }
  return res
}

async function _tryRefresh() {
  try {
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      credentials: 'include',
    })
    if (!res.ok) return false
    const data = await res.json()
    if (!data.access_token) return false
    localStorage.setItem(TOKEN_KEY, data.access_token)
    return true
  } catch {
    return false
  }
}

export function useApi() {
  return {
    get: (path) => _request('GET', path, null),
    post: (path, body) => _request('POST', path, body),
    patch: (path, body) => _request('PATCH', path, body),
    delete: (path) => _request('DELETE', path, null),
    upload: (path, formData) => {
      const token = localStorage.getItem(TOKEN_KEY)
      const headers = {}
      if (token) headers['Authorization'] = `Bearer ${token}`
      return fetch(`${API_BASE}${path}`, {
        method: 'POST',
        headers,
        credentials: 'include',
        body: formData,
      })
    },
  }
}
