const API_BASE_URL = 'http://127.0.0.1:8000'

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
      'CareerLens could not complete this job request.'

    throw new Error(message)
  }

  return body
}

export async function fetchJobs({
  title = '',
  location = '',
  experienceLevel = '',
  source = '',
  limit = 50,
  offset = 0,
} = {}) {
  const params = new URLSearchParams()

  if (title.trim()) {
    params.set('title', title.trim())
  }

  if (location.trim()) {
    params.set('location', location.trim())
  }

  if (experienceLevel) {
    params.set('experience_level', experienceLevel)
  }

  if (source.trim()) {
    params.set('source', source.trim())
  }

  params.set('limit', String(limit))
  params.set('offset', String(offset))

  const response = await fetch(
    `${API_BASE_URL}/jobs?${params.toString()}`
  )

  return readJsonResponse(response)
}

export async function fetchJob(jobId) {
  if (!jobId) {
    throw new Error('A job ID is required.')
  }

  const response = await fetch(
    `${API_BASE_URL}/jobs/${encodeURIComponent(jobId)}`
  )

  return readJsonResponse(response)
}

export async function fetchJobRecommendations(
  resumeId,
  limit = 10
) {
  if (!resumeId) {
    throw new Error('A resume ID is required for recommendations.')
  }

  const response = await fetch(
    `${API_BASE_URL}/recommendations/resumes/${encodeURIComponent(
      resumeId
    )}?limit=${encodeURIComponent(limit)}`
  )

  return readJsonResponse(response)
}

export async function fetchRankedJobs(resumeId, limit = 10) {
  if (!resumeId) {
    throw new Error('A resume ID is required for ranking.')
  }

  const response = await fetch(
    `${API_BASE_URL}/matching/resumes/${encodeURIComponent(
      resumeId
    )}/jobs?limit=${encodeURIComponent(limit)}`
  )

  return readJsonResponse(response)
}

export async function fetchMatchExplanation(
  resumeId,
  jobId
) {
  if (!resumeId) {
    throw new Error('A resume ID is required for match explanation.')
  }

  if (!jobId) {
    throw new Error('A job ID is required for match explanation.')
  }

  const response = await fetch(
    `${API_BASE_URL}/matching/resumes/${encodeURIComponent(
      resumeId
    )}/jobs/${encodeURIComponent(jobId)}/explanation`
  )

  return readJsonResponse(response)
}