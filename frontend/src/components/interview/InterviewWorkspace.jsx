import { useCallback, useRef, useState } from 'react'

import {
  evaluateInterviewAnswer,
  fetchInterviewExecutionSession,
  fetchInterviewScorecard,
} from '../../services/api/interviewEvaluation'
import InterviewScorecard from './scorecard/InterviewScorecard'

function isValidSessionId(value) {
  return /^\d+$/.test(String(value).trim()) && Number(value) > 0
}

export default function InterviewWorkspace() {
  const [sessionIdInput, setSessionIdInput] = useState('')
  const [activeSessionId, setActiveSessionId] = useState(null)
  const [session, setSession] = useState(null)
  const [scorecard, setScorecard] = useState(null)
  const [sessionLoading, setSessionLoading] = useState(false)
  const [scorecardLoading, setScorecardLoading] = useState(false)
  const [sessionError, setSessionError] = useState('')
  const [scorecardError, setScorecardError] = useState('')
  const [validationError, setValidationError] = useState('')
  const [expandedId, setExpandedId] = useState(null)
  const [evaluatingAnswerId, setEvaluatingAnswerId] = useState(null)
  const [evaluationErrors, setEvaluationErrors] = useState({})
  const requestIdRef = useRef(0)

  const loadScorecard = useCallback(async (sessionId, requestId) => {
    setScorecardLoading(true)
    setScorecardError('')

    try {
      const response = await fetchInterviewScorecard(sessionId)
      if (requestId !== requestIdRef.current) return
      setScorecard(response)
    } catch (error) {
      if (requestId !== requestIdRef.current) return
      setScorecard(null)
      setScorecardError(
        error?.message || 'CareerLens could not load this scorecard.',
      )
    } finally {
      if (requestId === requestIdRef.current) {
        setScorecardLoading(false)
      }
    }
  }, [])

  const loadSession = useCallback(async (sessionId) => {
    const requestId = ++requestIdRef.current
    setActiveSessionId(sessionId)
    setSession(null)
    setScorecard(null)
    setSessionError('')
    setScorecardError('')
    setEvaluationErrors({})
    setExpandedId(null)
    setSessionLoading(true)
    setScorecardLoading(true)

    void loadScorecard(sessionId, requestId)

    try {
      const response = await fetchInterviewExecutionSession(sessionId)
      if (requestId !== requestIdRef.current) return
      setSession(response)
    } catch (error) {
      if (requestId !== requestIdRef.current) return
      setSession(null)
      setSessionError(
        error?.message || 'CareerLens could not load this interview session.',
      )
    } finally {
      if (requestId === requestIdRef.current) {
        setSessionLoading(false)
      }
    }
  }, [loadScorecard])

  function handleSubmit(event) {
    event.preventDefault()
    const normalizedId = sessionIdInput.trim()

    if (!isValidSessionId(normalizedId)) {
      setValidationError('Enter a valid positive interview session ID.')
      return
    }

    setValidationError('')
    void loadSession(Number(normalizedId))
  }

  function handleRetry() {
    if (activeSessionId) {
      void loadSession(activeSessionId)
    }
  }

  async function handleEvaluate(answerId) {
    if (!activeSessionId || evaluatingAnswerId) return

    const requestId = requestIdRef.current
    setEvaluatingAnswerId(answerId)
    setEvaluationErrors((current) => ({ ...current, [answerId]: '' }))

    try {
      await evaluateInterviewAnswer(activeSessionId, answerId)
      if (requestId !== requestIdRef.current) return
      await loadScorecard(activeSessionId, requestId)
    } catch (error) {
      if (requestId !== requestIdRef.current) return
      setEvaluationErrors((current) => ({
        ...current,
        [answerId]: error?.message || 'Evaluation could not be completed.',
      }))
    } finally {
      if (requestId === requestIdRef.current) {
        setEvaluatingAnswerId(null)
      }
    }
  }

  return (
    <div className="space-y-5">
      <section className="rounded-2xl border border-white/8 bg-[#111111] p-5 shadow-[var(--shadow-soft)] sm:p-7">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#d6b36a]">
              Interview practice
            </p>
            <h1 className="mt-2 text-2xl font-medium tracking-[-0.03em] text-white/90">
              Review your interview scorecard
            </h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-white/45">
              Enter an interview session ID to review rubric-grounded feedback
              and decide what to practice next.
            </p>
          </div>
          {activeSessionId && (
            <span className="rounded-full border border-white/10 px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.13em] text-white/45">
              Session {activeSessionId}
            </span>
          )}
        </div>

        <form className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-end" onSubmit={handleSubmit}>
          <div className="min-w-0 flex-1">
            <label
              htmlFor="interview-session-id"
              className="block text-[10px] font-semibold uppercase tracking-[0.16em] text-white/35"
            >
              Interview session ID
            </label>
            <input
              id="interview-session-id"
              inputMode="numeric"
              value={sessionIdInput}
              onChange={(event) => {
                setSessionIdInput(event.target.value)
                setValidationError('')
              }}
              placeholder="e.g. 12"
              aria-invalid={Boolean(validationError)}
              aria-describedby={validationError ? 'interview-session-error' : undefined}
              className="mt-2 w-full rounded-lg border border-white/10 bg-[#0b0b0b] px-3 py-2.5 text-sm text-white/75 outline-none transition focus:border-[#d6b36a]/60"
            />
            {validationError && (
              <p id="interview-session-error" className="mt-2 text-xs text-red-200/75" role="alert">
                {validationError}
              </p>
            )}
          </div>
          <button
            type="submit"
            className="rounded-lg bg-[#d6b36a] px-4 py-2.5 text-xs font-semibold text-[#17130b] transition hover:bg-[#e5c57c] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#f0d18b]/80"
          >
            Load scorecard
          </button>
        </form>
      </section>

      {sessionLoading || scorecardLoading ? (
        <div className="rounded-2xl border border-white/8 bg-[#111111] p-6" aria-label="Loading interview scorecard">
          <div className="h-5 w-2/5 animate-pulse rounded bg-white/[0.08]" />
          <div className="mt-4 h-24 animate-pulse rounded-xl bg-white/[0.04]" />
        </div>
      ) : sessionError || scorecardError ? (
        <section className="rounded-2xl border border-red-300/15 bg-red-300/[0.035] p-6" role="alert">
          <h2 className="text-base font-medium text-red-100/85">
            Scorecard unavailable
          </h2>
          <p className="mt-2 text-sm leading-6 text-red-100/65">
            {sessionError || scorecardError}
          </p>
          <button
            type="button"
            onClick={handleRetry}
            className="mt-4 rounded-lg border border-red-200/20 px-3 py-2 text-xs font-medium text-red-100/75 transition hover:bg-red-200/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-red-200/70"
          >
            Retry
          </button>
        </section>
      ) : scorecard && activeSessionId ? (
        <InterviewScorecard
          scorecard={scorecard}
          session={session}
          expandedId={expandedId}
          evaluatingAnswerId={evaluatingAnswerId}
          evaluationErrors={evaluationErrors}
          onToggleQuestion={setExpandedId}
          onEvaluateAnswer={handleEvaluate}
        />
      ) : (
        <section className="rounded-2xl border border-white/8 bg-[#111111] p-6">
          <p className="text-sm leading-6 text-white/45">
            Load an interview session to see its scorecard and candidate feedback.
          </p>
        </section>
      )}
    </div>
  )
}
