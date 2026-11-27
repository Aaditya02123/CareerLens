import { getAuthHeaders } from './auth'

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
      'CareerLens could not complete this request.'

    throw new Error(message)
  }

  return body
}

export async function recordProctoringEvent(
  sessionId,
  eventType,
  severity = 'medium',
  details = {}
) {
  if (!sessionId) return null

  try {
    const response = await fetch(
      `${API_BASE_URL}/interview-preparation/sessions/${encodeURIComponent(
        sessionId
      )}/proctoring-events`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify({
          event_type: eventType,
          severity,
          details,
        }),
      }
    )

    return readJsonResponse(response)
  } catch {
    // Non-blocking telemetry failure should never crash the interview
    return null
  }
}

export async function fetchProctoringSummary(sessionId) {
  if (!sessionId) {
    throw new Error('Interview session ID is required.')
  }

  const response = await fetch(
    `${API_BASE_URL}/interview-preparation/sessions/${encodeURIComponent(
      sessionId
    )}/proctoring-summary`,
    {
      headers: {
        ...getAuthHeaders(),
      },
    }
  )

  return readJsonResponse(response)
}

export async function fetchModelAnswerComparison(
  sessionId,
  answerId,
  durationSeconds = null
) {
  if (!sessionId || !answerId) {
    throw new Error('Session ID and Answer ID are required.')
  }

  const query = durationSeconds ? `?duration_seconds=${encodeURIComponent(durationSeconds)}` : ''

  const response = await fetch(
    `${API_BASE_URL}/interview-preparation/sessions/${encodeURIComponent(
      sessionId
    )}/answers/${encodeURIComponent(answerId)}/model-answer${query}`,
    {
      method: 'POST',
      headers: {
        ...getAuthHeaders(),
      },
    }
  )

  return readJsonResponse(response)
}

export async function syncInterviewGapsToRoadmap(sessionId) {
  if (!sessionId) {
    throw new Error('Interview session ID is required.')
  }

  const response = await fetch(
    `${API_BASE_URL}/interview-preparation/sessions/${encodeURIComponent(
      sessionId
    )}/sync-roadmap`,
    {
      method: 'POST',
      headers: {
        ...getAuthHeaders(),
      },
    }
  )

  return readJsonResponse(response)
}

export async function submitInterviewAnswer(
  sessionId,
  questionId,
  questionOrder,
  answerText
) {
  if (!sessionId || !questionId) {
    throw new Error('Session ID and Question ID are required.')
  }

  const response = await fetch(
    `${API_BASE_URL}/interview-preparation/sessions/${encodeURIComponent(
      sessionId
    )}/answers`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
      },
      body: JSON.stringify({
        session_question_id: questionId,
        question_order: questionOrder,
        answer: answerText,
      }),
    }
  )

  return readJsonResponse(response)
}

export async function checkNetworkLatency() {
  const start = performance.now()
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
      cache: 'no-store',
    })
    if (!response.ok) throw new Error('Health check failed')
    const elapsed = Math.round(performance.now() - start)
    return { success: true, latencyMs: elapsed }
  } catch {
    return { success: false, latencyMs: 999 }
  }
}
