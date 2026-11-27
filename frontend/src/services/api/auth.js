const API_BASE_URL = 'http://127.0.0.1:8000'

export const TOKEN_STORAGE_KEY = 'careerlens_auth_token'
export const USER_STORAGE_KEY = 'careerlens_auth_user'

export function getStoredToken() {
  try {
    return localStorage.getItem(TOKEN_STORAGE_KEY) || null
  } catch {
    return null
  }
}

export function setStoredToken(token) {
  try {
    if (token) {
      localStorage.setItem(TOKEN_STORAGE_KEY, token)
    } else {
      localStorage.removeItem(TOKEN_STORAGE_KEY)
    }
  } catch {
    // Ignore storage errors in restricted contexts
  }
}

export function getStoredUser() {
  try {
    const raw = localStorage.getItem(USER_STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function setStoredUser(user) {
  try {
    if (user) {
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user))
    } else {
      localStorage.removeItem(USER_STORAGE_KEY)
    }
  } catch {
    // Ignore storage errors in restricted contexts
  }
}

export function clearStoredAuth() {
  try {
    localStorage.removeItem(TOKEN_STORAGE_KEY)
    localStorage.removeItem(USER_STORAGE_KEY)
  } catch {
    // Ignore storage errors in restricted contexts
  }
}

export function getAuthHeaders(customToken = null) {
  const token = customToken || getStoredToken()
  if (!token) return null
  return {
    Authorization: `Bearer ${token}`,
  }
}

async function readJsonResponse(response, fallbackMessage) {
  let body = null
  try {
    body = await response.json()
  } catch {
    body = null
  }

  if (!response.ok) {
    const detail = body?.detail
    const message =
      typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map((d) => d.msg || JSON.stringify(d)).join(', ')
          : fallbackMessage || `Request failed with status ${response.status}`
    throw new Error(message)
  }

  return body
}

export async function registerUser({ email, name, password }) {
  if (!email?.trim()) throw new Error('Email address is required.')
  if (!name?.trim()) throw new Error('Full name is required.')
  if (!password || password.length < 12) {
    throw new Error('Password must contain at least 12 characters.')
  }

  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email: email.trim().toLowerCase(),
      name: name.trim(),
      password,
    }),
  })

  return readJsonResponse(response, 'CareerLens could not create your account.')
}

export async function loginUser({ email, password }) {
  if (!email?.trim()) throw new Error('Email address is required.')
  if (!password) throw new Error('Password is required.')

  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email: email.trim().toLowerCase(),
      password,
    }),
  })

  return readJsonResponse(response, 'CareerLens could not log you in.')
}

export async function fetchCurrentUser(token = null) {
  const authToken = token || getStoredToken()
  if (!authToken) {
    throw new Error('No authentication token available.')
  }

  const response = await fetch(`${API_BASE_URL}/auth/me`, {
    headers: {
      Authorization: `Bearer ${authToken}`,
    },
  })

  return readJsonResponse(response, 'Could not verify authentication session.')
}
