import { getAuthHeaders, getStoredUser } from './auth'

const API_BASE_URL = 'http://127.0.0.1:8000'

export const CAREERLENS_DEV_USER_ID = 3

async function readJsonResponse(response, fallbackMessage) {
  let body = null

  try {
    body = await response.json()
  } catch {
    body = null
  }

  if (!response.ok) {
    throw new Error(body?.detail || fallbackMessage)
  }

  return body
}

export async function fetchLearningPreferences(userId = null) {
  const storedUser = getStoredUser()
  const activeUserId = storedUser?.id || userId || CAREERLENS_DEV_USER_ID

  const authHeaders = getAuthHeaders()
  const response = authHeaders
    ? await fetch(
        `${API_BASE_URL}/users/${encodeURIComponent(activeUserId)}/learning-preferences`,
        {
          headers: authHeaders,
        },
      )
    : await fetch(
        `${API_BASE_URL}/users/${encodeURIComponent(activeUserId)}/learning-preferences`,
      )

  return readJsonResponse(
    response,
    'CareerLens could not load learning preferences.',
  )
}

export async function saveLearningPreferences(userId = null, payload = {}) {
  const storedUser = getStoredUser()
  const activeUserId = storedUser?.id || userId || CAREERLENS_DEV_USER_ID

  const authHeaders = getAuthHeaders()
  const headers = {
    'Content-Type': 'application/json',
    ...(authHeaders || {}),
  }

  const response = await fetch(
    `${API_BASE_URL}/users/${encodeURIComponent(
      activeUserId,
    )}/learning-preferences`,
    {
      method: 'PUT',
      headers,
      body: JSON.stringify(payload),
    },
  )

  return readJsonResponse(
    response,
    'CareerLens could not save learning preferences.',
  )
}
