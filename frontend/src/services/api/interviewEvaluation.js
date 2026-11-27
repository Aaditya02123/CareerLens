import { getAuthHeaders } from './auth'

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

function validateSessionId(sessionId) {
  if (!sessionId || !Number.isInteger(Number(sessionId)) || Number(sessionId) < 1) {
    throw new Error('A valid interview session ID is required.')
  }
}

function validateAnswerId(answerId) {
  if (!answerId || !Number.isInteger(Number(answerId)) || Number(answerId) < 1) {
    throw new Error('A valid interview answer ID is required.')
  }
}

export async function fetchInterviewExecutionSession(sessionId) {
  validateSessionId(sessionId)
  const authHeaders = getAuthHeaders()

  const response = authHeaders
    ? await fetch(
        `${API_BASE_URL}/interview-preparation/sessions/${encodeURIComponent(sessionId)}`,
        { headers: authHeaders },
      )
    : await fetch(
        `${API_BASE_URL}/interview-preparation/sessions/${encodeURIComponent(sessionId)}`,
      )

  return readJsonResponse(
    response,
    'CareerLens could not load the interview session.',
  )
}

export async function fetchInterviewScorecard(sessionId) {
  validateSessionId(sessionId)
  const authHeaders = getAuthHeaders()

  const response = authHeaders
    ? await fetch(
        `${API_BASE_URL}/interview-preparation/sessions/${encodeURIComponent(sessionId)}/scorecard`,
        { headers: authHeaders },
      )
    : await fetch(
        `${API_BASE_URL}/interview-preparation/sessions/${encodeURIComponent(sessionId)}/scorecard`,
      )

  return readJsonResponse(
    response,
    'CareerLens could not load the interview scorecard.',
  )
}

export async function fetchInterviewAnswerEvaluation(
  sessionId,
  answerId,
) {
  validateSessionId(sessionId)
  validateAnswerId(answerId)
  const authHeaders = getAuthHeaders()

  const response = authHeaders
    ? await fetch(
        `${API_BASE_URL}/interview-preparation/sessions/${encodeURIComponent(sessionId)}/answers/${encodeURIComponent(answerId)}/evaluation`,
        { headers: authHeaders },
      )
    : await fetch(
        `${API_BASE_URL}/interview-preparation/sessions/${encodeURIComponent(sessionId)}/answers/${encodeURIComponent(answerId)}/evaluation`,
      )

  return readJsonResponse(
    response,
    'CareerLens could not load this answer evaluation.',
  )
}

export async function evaluateInterviewAnswer(sessionId, answerId) {
  validateSessionId(sessionId)
  validateAnswerId(answerId)
  const authHeaders = getAuthHeaders()

  const options = {
    method: 'POST',
    ...(authHeaders ? { headers: authHeaders } : {}),
  }

  const response = await fetch(
    `${API_BASE_URL}/interview-preparation/sessions/${encodeURIComponent(
      sessionId,
    )}/answers/${encodeURIComponent(answerId)}/evaluate`,
    options,
  )

  return readJsonResponse(
    response,
    'CareerLens could not evaluate this interview answer.',
  )
}
