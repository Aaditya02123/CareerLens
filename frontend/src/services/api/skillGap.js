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
      'CareerLens could not load the skill-gap analysis.'

    throw new Error(message)
  }

  return body
}

export async function fetchSkillGap(resumeId, jobId) {
  if (!resumeId) {
    throw new Error('A resume ID is required for skill-gap analysis.')
  }

  if (!jobId) {
    throw new Error('A job ID is required for skill-gap analysis.')
  }

  const response = await fetch(
    `${API_BASE_URL}/skill-gap/resumes/${encodeURIComponent(
      resumeId,
    )}/jobs/${encodeURIComponent(jobId)}`,
  )

  return readJsonResponse(response)
}