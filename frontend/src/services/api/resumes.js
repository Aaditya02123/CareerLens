import { getAuthHeaders, getStoredUser } from './auth'

const API_BASE_URL = 'http://127.0.0.1:8000'

export const CAREERLENS_DEV_USER_ID = 3

async function readJsonResponse(response) {
  let body = null

  try {
    body = await response.json()
  } catch {
    body = null
  }

  if (!response.ok) {
    const message =
      body?.detail ||
      'CareerLens could not complete this resume request.'

    throw new Error(message)
  }

  return body
}

export async function fetchUserResumes(
  userId = null,
) {
  const storedUser = getStoredUser()
  const activeUserId = storedUser?.id || userId || CAREERLENS_DEV_USER_ID

  const authHeaders = getAuthHeaders()
  const response = authHeaders
    ? await fetch(
        `${API_BASE_URL}/users/${activeUserId}/resumes`,
        {
          headers: authHeaders,
        },
      )
    : await fetch(
        `${API_BASE_URL}/users/${activeUserId}/resumes`,
      )

  return readJsonResponse(response)
}

export async function fetchResumeAnalysis(storedFilename) {
  if (!storedFilename) {
    throw new Error('A stored resume filename is required.')
  }

  const authHeaders = getAuthHeaders()
  const response = authHeaders
    ? await fetch(
        `${API_BASE_URL}/resume/${encodeURIComponent(
          storedFilename,
        )}/analysis`,
        {
          headers: authHeaders,
        },
      )
    : await fetch(
        `${API_BASE_URL}/resume/${encodeURIComponent(
          storedFilename,
        )}/analysis`,
      )

  return readJsonResponse(response)
}

export async function uploadResume(
  file,
  userId = null,
) {
  if (!file) {
    throw new Error('Please select a resume file before uploading.')
  }

  const storedUser = getStoredUser()
  const activeUserId = storedUser?.id || userId || CAREERLENS_DEV_USER_ID

  const formData = new FormData()
  formData.append('file', file)

  const authHeaders = getAuthHeaders()
  const response = await fetch(
    `${API_BASE_URL}/resume?user_id=${encodeURIComponent(
      activeUserId,
    )}`,
    {
      method: 'POST',
      headers: {
        ...(authHeaders || {}),
      },
      body: formData,
    },
  )

  return readJsonResponse(response)
}
