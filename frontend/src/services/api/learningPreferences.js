const API_BASE_URL = 'http://127.0.0.1:8000'

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

export async function fetchLearningPreferences(userId) {
  if (!userId) {
    throw new Error('A user ID is required for learning preferences.')
  }

  const response = await fetch(
    `${API_BASE_URL}/users/${encodeURIComponent(
      userId,
    )}/learning-preferences`,
  )
  return readJsonResponse(
    response,
    'CareerLens could not load learning preferences.',
  )
}

export async function saveLearningPreferences(userId, payload) {
  if (!userId) {
    throw new Error('A user ID is required for learning preferences.')
  }

  const response = await fetch(
    `${API_BASE_URL}/users/${encodeURIComponent(
      userId,
    )}/learning-preferences`,
    {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    },
  )

  return readJsonResponse(
    response,
    'CareerLens could not save learning preferences.',
  )
}
