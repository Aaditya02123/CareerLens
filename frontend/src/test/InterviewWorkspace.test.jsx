import { cleanup, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import InterviewWorkspace from '../components/interview/InterviewWorkspace'
import {
  evaluateInterviewAnswer,
  fetchInterviewExecutionSession,
  fetchInterviewScorecard,
} from '../services/api/interviewEvaluation'

vi.mock('../services/api/interviewEvaluation', () => ({
  evaluateInterviewAnswer: vi.fn(),
  fetchInterviewExecutionSession: vi.fn(),
  fetchInterviewScorecard: vi.fn(),
}))

const session = {
  id: 7,
  status: 'completed',
  answers: [
    { id: 101, answer: 'I validate input before persistence.' },
    { id: 102, answer: 'I would add a failure-path test.' },
  ],
}

const evaluatedAnswer = {
  id: 1,
  session_id: 7,
  answer_id: 101,
  question_id: 11,
  question: 'How would you design a reliable Python API?',
  answer: 'I validate input before persistence.',
  question_category: 'technical',
  difficulty: 'medium',
  question_order: 1,
  conversation_order: 1,
  is_follow_up: false,
  parent_question_id: null,
  parent_question: null,
  parent_answer: null,
  competency_reference: 'Backend design',
  weighted_score: 4.2,
  strengths: ['Clear validation boundary.'],
  improvement_areas: ['Explain one trade-off.'],
  actionable_feedback: ['Connect the choice to a failure case.'],
  evaluation_status: 'complete',
  provider_name: 'FakeProvider',
  criteria: [
    {
      id: 1,
      criterion_id: 'correctness',
      criterion_name: 'Technical correctness',
      score: 4,
      explanation: 'The answer names a concrete validation step.',
      evidence_excerpts: ['validate input before persistence'],
      improvement_suggestion: 'Explain how invalid input is reported.',
    },
  ],
}

function scorecard(overrides = {}) {
  return {
    session_id: 7,
    status: 'partial',
    overall_score: 4.2,
    evaluated_answer_count: 1,
    pending_answer_ids: [102],
    competency_scores: [
      {
        competency_reference: 'Backend design',
        competency_weight_percent: 100,
        evaluated_answer_count: 1,
        score: 4.2,
      },
    ],
    answer_evaluations: [evaluatedAnswer],
    strengths: ['Clear validation boundary.'],
    improvement_areas: ['Explain one trade-off.'],
    ...overrides,
  }
}

async function loadWorkspace(response = scorecard()) {
  fetchInterviewExecutionSession.mockResolvedValue(session)
  fetchInterviewScorecard.mockResolvedValue(response)
  const user = userEvent.setup()
  render(<InterviewWorkspace />)
  await user.type(screen.getByLabelText('Interview session ID'), '7')
  await user.click(screen.getByRole('button', { name: 'Load scorecard' }))
  await screen.findByRole('heading', { name: 'Your interview feedback' })
  return user
}

beforeEach(() => {
  vi.clearAllMocks()
  evaluateInterviewAnswer.mockResolvedValue(evaluatedAnswer)
})

afterEach(() => {
  cleanup()
})

describe('InterviewWorkspace', () => {
  it('renders backend scores, competency breakdown, and exact evidence', async () => {
    const user = await loadWorkspace()

    expect(screen.getByText('4.20')).toBeInTheDocument()
    expect(screen.getByText('Backend design')).toBeInTheDocument()
    expect(screen.getByText('Partially evaluated')).toBeInTheDocument()
    expect(screen.getByText('How would you design a reliable Python API?')).toBeInTheDocument()

    const questionCard = screen
      .getByText('How would you design a reliable Python API?')
      .closest('article')
    await user.click(
      within(questionCard).getByRole('button', {
        name: 'Expand evaluation for question',
      }),
    )
    await waitFor(() => {
      expect(
        within(questionCard).getAllByText(/validate input before persistence/).length,
      ).toBeGreaterThan(1)
    })
    expect(
      within(questionCard).getByText('Explain how invalid input is reported.'),
    ).toBeInTheDocument()
    expect(within(questionCard).getByText('Clear validation boundary.')).toBeInTheDocument()
  })

  it('explicitly evaluates a pending answer and refreshes the scorecard', async () => {
    const user = await loadWorkspace()
    fetchInterviewScorecard.mockResolvedValueOnce(
      scorecard({
        status: 'complete',
        evaluated_answer_count: 2,
        pending_answer_ids: [],
        answer_evaluations: [evaluatedAnswer],
      }),
    )

    await user.click(screen.getByRole('button', { name: 'Evaluate answer' }))

    await waitFor(() => {
      expect(evaluateInterviewAnswer).toHaveBeenCalledWith(7, 102)
      expect(fetchInterviewScorecard).toHaveBeenCalledTimes(2)
    })
  })

  it('keeps the submitted session when an evaluation request fails', async () => {
    const user = await loadWorkspace()
    evaluateInterviewAnswer.mockRejectedValueOnce(
      new Error('Provider temporarily unavailable.'),
    )

    await user.click(screen.getByRole('button', { name: 'Evaluate answer' }))
    expect(
      await screen.findByText('Provider temporarily unavailable.'),
    ).toBeInTheDocument()
    expect(screen.getByText('How would you design a reliable Python API?')).toBeInTheDocument()
  })

  it('does not let a stale session response replace the active session', async () => {
    const requests = new Map()
    fetchInterviewExecutionSession.mockImplementation(
      (sessionId) =>
        new Promise((resolve) => requests.set(`session-${sessionId}`, resolve)),
    )
    fetchInterviewScorecard.mockImplementation(
      (sessionId) =>
        Promise.resolve(scorecard({ session_id: Number(sessionId) })),
    )

    const user = userEvent.setup()
    render(<InterviewWorkspace />)
    const input = screen.getByLabelText('Interview session ID')
    await user.type(input, '7')
    await user.click(screen.getByRole('button', { name: 'Load scorecard' }))
    await user.clear(input)
    await user.type(input, '8')
    await user.click(screen.getByRole('button', { name: 'Load scorecard' }))

    requests.get('session-7')(session)
    await Promise.resolve()
    expect(screen.queryByText('Session 7')).not.toBeInTheDocument()

    requests.get('session-8')({ ...session, id: 8 })
    expect(await screen.findByText('Session 8')).toBeInTheDocument()
  })

  it('shows an honest empty state for a pending scorecard', async () => {
    await loadWorkspace({
      session_id: 7,
      status: 'pending',
      overall_score: null,
      evaluated_answer_count: 0,
      pending_answer_ids: [],
      competency_scores: [],
      answer_evaluations: [],
      strengths: [],
      improvement_areas: [],
    })

    expect(screen.getByText('Not available yet')).toBeInTheDocument()
    expect(screen.getByText(/Evaluation has not started\./)).toBeInTheDocument()
    expect(screen.getByText('No submitted answers are available for evaluation yet.')).toBeInTheDocument()
  })
})
