import { getAuthHeaders, getStoredUser } from './auth'

const API_BASE_URL = 'http://127.0.0.1:8000'

const ALLOWED_PROGRESS_STATUSES = new Set([
  'not_started',
  'in_progress',
  'completed',
])

async function readJsonResponse(response, fallbackMessage) {
  let body = null

  try {
    body = await response.json()
  } catch {
    body = null
  }

  if (!response.ok) {
    const message = body?.detail || fallbackMessage
    throw new Error(message)
  }

  return body
}

export async function fetchLearningRoadmap(resumeId, jobId) {
  if (!resumeId) {
    throw new Error('A resume ID is required for the learning roadmap.')
  }

  if (!jobId) {
    throw new Error('A job ID is required for the learning roadmap.')
  }

  const authHeaders = getAuthHeaders()
  const response = authHeaders
    ? await fetch(
        `${API_BASE_URL}/roadmaps/resumes/${encodeURIComponent(
          resumeId,
        )}/jobs/${encodeURIComponent(jobId)}`,
        {
          headers: authHeaders,
        },
      )
    : await fetch(
        `${API_BASE_URL}/roadmaps/resumes/${encodeURIComponent(
          resumeId,
        )}/jobs/${encodeURIComponent(jobId)}`,
      )

  return readJsonResponse(
    response,
    'CareerLens could not load the learning roadmap.',
  )
}

export async function fetchRoadmapSchedule(resumeId, jobId) {
  if (!resumeId) {
    throw new Error('A resume ID is required for the roadmap schedule.')
  }

  if (!jobId) {
    throw new Error('A job ID is required for the roadmap schedule.')
  }

  const authHeaders = getAuthHeaders()
  const response = authHeaders
    ? await fetch(
        `${API_BASE_URL}/roadmaps/resumes/${encodeURIComponent(
          resumeId,
        )}/jobs/${encodeURIComponent(jobId)}/schedule`,
        {
          headers: authHeaders,
        },
      )
    : await fetch(
        `${API_BASE_URL}/roadmaps/resumes/${encodeURIComponent(
          resumeId,
        )}/jobs/${encodeURIComponent(jobId)}/schedule`,
      )

  return readJsonResponse(
    response,
    'CareerLens could not load the roadmap schedule.',
  )
}

export async function updateLearningRoadmapProgress(
  itemId,
  progressStatus,
) {
  if (!itemId) {
    throw new Error(
      'A roadmap item ID is required to update progress.',
    )
  }

  if (!ALLOWED_PROGRESS_STATUSES.has(progressStatus)) {
    throw new Error(
      'Progress status must be not_started, in_progress, or completed.',
    )
  }

  const authHeaders = getAuthHeaders()
  const response = await fetch(
    `${API_BASE_URL}/roadmaps/items/${encodeURIComponent(
      itemId,
    )}/progress`,
    {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...(authHeaders || {}),
      },
      body: JSON.stringify({
        progress_status: progressStatus,
      }),
    },
  )

  return readJsonResponse(
    response,
    'CareerLens could not update learning roadmap progress.',
  )
}

export async function fetchLearningResources(skill, userId = null) {
  if (!skill || !String(skill).trim()) {
    throw new Error(
      'A skill is required to load learning resources.',
    )
  }

  const storedUser = getStoredUser()
  const activeUserId = storedUser?.id || userId || null

  const resourcePath = activeUserId
    ? `/users/${encodeURIComponent(
        activeUserId,
      )}/learning-resources/${encodeURIComponent(skill)}`
    : `/learning-resources/${encodeURIComponent(skill)}`

  const authHeaders = getAuthHeaders()
  const response = authHeaders
    ? await fetch(`${API_BASE_URL}${resourcePath}`, {
        headers: authHeaders,
      })
    : await fetch(`${API_BASE_URL}${resourcePath}`)

  return readJsonResponse(
    response,
    'CareerLens could not load learning resources.',
  )
}
