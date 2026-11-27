import { useCallback, useRef, useState } from 'react'
import { Video, BarChart3, Sparkles } from 'lucide-react'

import {
  evaluateInterviewAnswer,
  fetchInterviewExecutionSession,
  fetchInterviewScorecard,
} from '../../services/api/interviewEvaluation'
import InterviewScorecard from './scorecard/InterviewScorecard'
import HardwareCheckScreen from './HardwareCheckScreen'
import LiveInterviewRoom from './LiveInterviewRoom'

function isValidSessionId(value) {
  return /^\d+$/.test(String(value).trim()) && Number(value) > 0
}

export default function InterviewWorkspace() {
  const [workspaceTab, setWorkspaceTab] = useState('review') // 'review' | 'take'
  const [interviewStage, setInterviewStage] = useState('setup') // 'setup' | 'check' | 'room'
  const [interviewMode, setInterviewMode] = useState('practice')
  const [liveStream, setLiveStream] = useState(null)

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

  function handleStartLiveTake(event) {
    event.preventDefault()
    const normalizedId = sessionIdInput.trim()

    if (!isValidSessionId(normalizedId)) {
      setValidationError('Enter a valid positive interview session ID.')
      return
    }

    setValidationError('')
    const numId = Number(normalizedId)
    void loadSession(numId).then(() => {
      setInterviewStage('check')
    })
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

  const handleHardwarePassed = ({ mode, stream }) => {
    setInterviewMode(mode)
    setLiveStream(stream)
    setInterviewStage('room')
  }

  const handleInterviewFinished = (finishedSessionId) => {
    setInterviewStage('setup')
    setWorkspaceTab('review')
    if (finishedSessionId) {
      void loadSession(finishedSessionId)
    }
  }

  return (
    <div className="space-y-6">
      {/* Workspace Header with Mode Switcher */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[var(--cl-border)] pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-[var(--cl-accent)]/15 text-[var(--cl-accent)]">
              <Sparkles className="h-3.5 w-3.5" />
            </span>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--cl-accent)]">
              AI Interview Intelligence
            </p>
          </div>
          <h1 className="mt-1 text-2xl font-medium tracking-[-0.03em] text-[var(--cl-text)]">
            Berri MasterMind & Proctor Verification
          </h1>
        </div>

        {/* View Switcher Tabs */}
        <div className="flex rounded-xl border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-1">
          <button
            type="button"
            onClick={() => setWorkspaceTab('review')}
            className={`flex items-center gap-1.5 rounded-lg px-3.5 py-1.5 text-xs font-medium transition ${
              workspaceTab === 'review'
                ? 'bg-[var(--cl-surface)] text-[var(--cl-text)] shadow-sm'
                : 'text-[var(--cl-muted)] hover:text-[var(--cl-text)]'
            }`}
          >
            <BarChart3 className="h-3.5 w-3.5" />
            Scorecard & Integrity Audit
          </button>

          <button
            type="button"
            onClick={() => {
              setWorkspaceTab('take')
              if (!interviewStage || interviewStage === 'setup') {
                setInterviewStage('setup')
              }
            }}
            className={`flex items-center gap-1.5 rounded-lg px-3.5 py-1.5 text-xs font-medium transition ${
              workspaceTab === 'take'
                ? 'bg-[var(--cl-surface)] text-[var(--cl-text)] shadow-sm'
                : 'text-[var(--cl-muted)] hover:text-[var(--cl-text)]'
            }`}
          >
            <Video className="h-3.5 w-3.5" />
            Live AI Interview Room
          </button>
        </div>
      </div>

      {/* Mode A: Take Live AI Interview Flow */}
      {workspaceTab === 'take' && (
        <div className="space-y-6">
          {interviewStage === 'setup' && (
            <section className="rounded-2xl border border-[var(--cl-border)] bg-[var(--cl-surface)] p-6 shadow-[var(--shadow-soft)] max-w-xl mx-auto space-y-4">
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--cl-accent)]">
                  Live Voice & Face Interview
                </p>
                <h2 className="mt-1 text-lg font-medium text-[var(--cl-text)]">
                  Launch an Interactive Interview Session
                </h2>
                <p className="mt-1 text-xs text-[var(--cl-muted)] leading-5">
                  Enter your prepared interview session ID to begin the pre-flight hardware check and start your session with the AI interviewer.
                </p>
              </div>

              <form onSubmit={handleStartLiveTake} className="space-y-4 pt-2">
                <div>
                  <label
                    htmlFor="live-session-id"
                    className="block text-[10px] font-semibold uppercase tracking-[0.16em] text-[var(--cl-faint)]"
                  >
                    Session ID
                  </label>
                  <input
                    id="live-session-id"
                    inputMode="numeric"
                    value={sessionIdInput}
                    onChange={(event) => {
                      setSessionIdInput(event.target.value)
                      setValidationError('')
                    }}
                    placeholder="e.g. 10"
                    className="mt-1.5 w-full rounded-xl border border-[var(--cl-border)] bg-[var(--cl-input-bg)] px-3.5 py-2.5 text-sm text-[var(--cl-text)] outline-none transition focus:border-[var(--cl-accent)]"
                  />
                  {validationError && (
                    <p className="mt-1.5 text-xs text-[var(--cl-danger)]">{validationError}</p>
                  )}
                </div>

                <button
                  type="submit"
                  disabled={sessionLoading}
                  className="w-full flex items-center justify-center gap-2 rounded-xl bg-[var(--cl-accent)] py-2.5 text-xs font-semibold text-[var(--cl-accent-contrast)] shadow-md hover:opacity-95 transition"
                >
                  <Video className="h-3.5 w-3.5" />
                  {sessionLoading ? 'Loading Session...' : 'Start Hardware Check & Interview'}
                </button>
              </form>
            </section>
          )}

          {interviewStage === 'check' && (
            <HardwareCheckScreen
              session={session}
              onProceed={handleHardwarePassed}
              onCancel={() => setInterviewStage('setup')}
            />
          )}

          {interviewStage === 'room' && (
            <LiveInterviewRoom
              session={session}
              mode={interviewMode}
              stream={liveStream}
              onFinish={handleInterviewFinished}
              onExit={() => setInterviewStage('setup')}
            />
          )}
        </div>
      )}

      {/* Mode B: Scorecard & Audit Review Flow */}
      {workspaceTab === 'review' && (
        <div className="space-y-5">
          <section className="rounded-2xl border border-[var(--cl-border)] bg-[var(--cl-surface)] p-5 shadow-[var(--shadow-soft)] sm:p-7">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--cl-accent)]">
                  Interview practice
                </p>
                <h1 className="mt-2 text-2xl font-medium tracking-[-0.03em] text-[var(--cl-text)]">
                  Review your interview scorecard
                </h1>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-[var(--cl-muted)]">
                  Enter an interview session ID to review rubric-grounded feedback
                  and decide what to practice next.
                </p>
              </div>
              {activeSessionId && (
                <span className="rounded-full border border-[var(--cl-border)] px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.13em] text-[var(--cl-muted)]">
                  Session {activeSessionId}
                </span>
              )}
            </div>

            <form className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-end" onSubmit={handleSubmit}>
              <div className="min-w-0 flex-1">
                <label
                  htmlFor="interview-session-id"
                  className="block text-[10px] font-semibold uppercase tracking-[0.16em] text-[var(--cl-faint)]"
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
                  className="mt-2 w-full rounded-lg border border-[var(--cl-border)] bg-[var(--cl-input-bg)] px-3 py-2.5 text-sm text-[var(--cl-text-soft)] outline-none transition focus:border-[var(--cl-accent)]"
                />
                {validationError && (
                  <p id="interview-session-error" className="mt-2 text-xs text-[var(--cl-danger)]" role="alert">
                    {validationError}
                  </p>
                )}
              </div>
              <button
                type="submit"
                className="rounded-lg bg-[var(--cl-accent)] px-4 py-2.5 text-xs font-semibold text-[var(--cl-accent-contrast)] transition hover:bg-[var(--cl-accent-hover)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--cl-accent)]/80"
              >
                Load scorecard
              </button>
            </form>
          </section>

          {sessionLoading || scorecardLoading ? (
            <div className="rounded-2xl border border-[var(--cl-border)] bg-[var(--cl-surface)] p-6" aria-label="Loading interview scorecard">
              <div className="h-5 w-2/5 animate-pulse rounded bg-[var(--cl-surface-muted)]" />
              <div className="mt-4 h-24 animate-pulse rounded-xl bg-[var(--cl-surface-soft)]" />
            </div>
          ) : sessionError || scorecardError ? (
            <section className="rounded-2xl border border-[var(--cl-danger)]/30 bg-[var(--cl-danger-soft)] p-6" role="alert">
              <h2 className="text-base font-medium text-[var(--cl-danger)]">
                Scorecard unavailable
              </h2>
              <p className="mt-2 text-sm leading-6 text-[var(--cl-text-soft)]">
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
            <section className="rounded-2xl border border-[var(--cl-border)] bg-[var(--cl-surface)] p-6">
              <p className="text-sm leading-6 text-[var(--cl-muted)]">
                Load an interview session to see its scorecard and candidate feedback.
              </p>
            </section>
          )}
        </div>
      )}
    </div>
  )
}

