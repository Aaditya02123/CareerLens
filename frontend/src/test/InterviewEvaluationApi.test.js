import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  evaluateInterviewAnswer,
  fetchInterviewAnswerEvaluation,
  fetchInterviewExecutionSession,
  fetchInterviewScorecard,
} from '../services/api/interviewEvaluation'

afterEach(() => {
  vi.restoreAllMocks()
})

describe('interview evaluation API service', () => {
  it('loads the execution session and scorecard using encoded IDs', async () => {
    const body = { session_id: 7, status: 'partial' }
    vi.stubGlobal(
      'fetch',
      vi.fn()
        .mockResolvedValueOnce(
          new Response(JSON.stringify(body), { status: 200 }),
        )
        .mockResolvedValueOnce(
          new Response(JSON.stringify(body), { status: 200 }),
        ),
    )

    await expect(fetchInterviewExecutionSession(7)).resolves.toEqual(body)
    await expect(fetchInterviewScorecard(7)).resolves.toEqual(body)

    expect(fetch).toHaveBeenNthCalledWith(
      1,
      'http://127.0.0.1:8000/interview-preparation/sessions/7',
    )
    expect(fetch).toHaveBeenNthCalledWith(
      2,
      'http://127.0.0.1:8000/interview-preparation/sessions/7/scorecard',
    )
  })

  it('triggers evaluation and retrieves an individual evaluation', async () => {
    const body = { answer_id: 3, weighted_score: 4 }
    vi.stubGlobal(
      'fetch',
      vi.fn()
        .mockResolvedValueOnce(
          new Response(JSON.stringify(body), { status: 200 }),
        )
        .mockResolvedValueOnce(
          new Response(JSON.stringify(body), { status: 200 }),
        ),
    )

    await expect(evaluateInterviewAnswer(7, 3)).resolves.toEqual(body)
    await expect(fetchInterviewAnswerEvaluation(7, 3)).resolves.toEqual(body)

    expect(fetch).toHaveBeenNthCalledWith(
      1,
      'http://127.0.0.1:8000/interview-preparation/sessions/7/answers/3/evaluate',
      { method: 'POST' },
    )
    expect(fetch).toHaveBeenNthCalledWith(
      2,
      'http://127.0.0.1:8000/interview-preparation/sessions/7/answers/3/evaluation',
    )
  })

  it('surfaces backend detail and rejects invalid IDs', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: 'Scorecard not found.' }), {
          status: 404,
        }),
      ),
    )

    await expect(fetchInterviewScorecard(7)).rejects.toThrow(
      'Scorecard not found.',
    )
    await expect(fetchInterviewScorecard(0)).rejects.toThrow(
      'A valid interview session ID is required.',
    )
    await expect(evaluateInterviewAnswer(7, 0)).rejects.toThrow(
      'A valid interview answer ID is required.',
    )
  })
})
