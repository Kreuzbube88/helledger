import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const TOKEN_KEY = 'helledger_token'

function _isTokenExpired(token) {
  try {
    const b64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')
    const { exp } = JSON.parse(atob(b64))
    return typeof exp === 'number' && exp * 1000 < Date.now()
  } catch {
    return true
  }
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY))
  const user = ref(null)

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  function setToken(newToken, remember = true) {
    token.value = newToken
    if (newToken) {
      if (remember) {
        localStorage.setItem(TOKEN_KEY, newToken)
        sessionStorage.removeItem(TOKEN_KEY)
      } else {
        sessionStorage.setItem(TOKEN_KEY, newToken)
        localStorage.removeItem(TOKEN_KEY)
      }
    } else {
      localStorage.removeItem(TOKEN_KEY)
      sessionStorage.removeItem(TOKEN_KEY)
    }
  }

  function getToken() {
    return localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY)
  }

  async function login(email, password, remember = true) {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ email, password }),
    })
    if (!res.ok) {
      const err = await res.json()
      throw err
    }
    const { access_token } = await res.json()
    setToken(access_token, remember)
    await fetchUser()
  }

  async function register(name, email, password, language = 'de') {
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ name, email, password, language }),
    })
    if (!res.ok) {
      const err = await res.json()
      throw err
    }
    const { access_token } = await res.json()
    setToken(access_token, true)
    await fetchUser()
  }

  async function fetchUser() {
    let t = getToken()
    if (!t) return
    let res = await fetch('/api/auth/me', {
      headers: { Authorization: `Bearer ${t}` },
      credentials: 'include',
    })
    if (res.status === 401 && _isTokenExpired(t)) {
      // Token expired — try refreshing before giving up
      const refreshRes = await fetch('/api/auth/refresh', {
        method: 'POST',
        credentials: 'include',
      })
      if (refreshRes.ok) {
        const data = await refreshRes.json()
        setToken(data.access_token)
        t = data.access_token
        res = await fetch('/api/auth/me', {
          headers: { Authorization: `Bearer ${t}` },
          credentials: 'include',
        })
      }
    }
    if (res.ok) user.value = await res.json()
    else { setToken(null); user.value = null }
  }

  function logout() {
    setToken(null)
    user.value = null
  }

  return { token, user, isAuthenticated, isAdmin, setToken, login, register, fetchUser, logout }
})
