import { useState } from 'react'
import { Sparkles } from 'lucide-react'
import { fetchModelAnswerComparison } from '../../../services/api/interviewProctoring'
import ModelAnswerModal from '../ModelAnswerModal'

function scoreLabel(score) {
  return Number.isFinite(Number(score))
    ? `${Number(score).toFixed(2)} / 5`
    : 'Not available'
}

function MetaBadge({ children }) {
  return (
    <span className="rounded-full border border-[var(--cl-border)] px-2 py-1 text-[10px] uppercase tracking-[0.12em] text-[var(--cl-muted)]">
      {children}
    </span>
  )
}

export default function QuestionEvaluationCard({
  evaluation,
  pendingAnswer,
  isExpanded,
  isEvaluating,
  error,
  onToggle,
  onEvaluate,
}) {
  const [modelModalOpen, setModelModalOpen] = useState(false)
  const [modelData, setModelData] = useState(null)
  const [modelLoading, setModelLoading] = useState(false)

  const handleOpenModelAnswer = async () => {
    if (!evaluation?.session_id || !evaluation?.answer_id) return
    setModelLoading(true)
    try {
      const data = await fetchModelAnswerComparison(
        evaluation.session_id,
        evaluation.answer_id
      )
      setModelData(data)
      setModelModalOpen(true)
    } catch {
      // ignore
    } finally {
      setModelLoading(false)
    }
  }

  const question = evaluation?.question || 'Question text is unavailable.'
  const answer = evaluation?.answer || pendingAnswer?.answer || ''
  const titleId = `interview-question-${evaluation?.answer_id || pendingAnswer?.id}`
  const isPending = !evaluation

  return (
    <article className="rounded-2xl border border-[var(--cl-border)] bg-[var(--cl-surface)]">
      <div className="p-5 sm:p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex flex-wrap gap-2">
              <MetaBadge>
                {evaluation?.is_follow_up ? 'Adaptive follow-up' : 'Interview answer'}
              </MetaBadge>
              {evaluation?.question_category && (
                <MetaBadge>{evaluation.question_category}</MetaBadge>
              )}
              {evaluation?.difficulty && <MetaBadge>{evaluation.difficulty}</MetaBadge>}
            </div>
            <h4 id={titleId} className="mt-3 text-base font-medium leading-6 text-[var(--cl-text)]">
              {question}
            </h4>
            {evaluation?.competency_reference && (
              <p className="mt-2 text-xs text-[var(--cl-muted)]">
                Competency: {evaluation.competency_reference}
              </p>
            )}
            {evaluation?.is_follow_up && evaluation.parent_question && (
              <p className="mt-3 rounded-lg border border-[var(--cl-accent-soft)] bg-[var(--cl-accent-soft)] p-3 text-xs leading-5 text-[var(--cl-accent)]/75">
                Follow-up to: {evaluation.parent_question}
              </p>
            )}
          </div>

          <div className="flex shrink-0 items-center gap-2">
            {evaluation && (
              <button
                type="button"
                onClick={handleOpenModelAnswer}
                disabled={modelLoading}
                className="flex items-center gap-1 rounded-lg border border-[var(--cl-accent)]/30 bg-[var(--cl-accent)]/10 px-2.5 py-2 text-xs font-medium text-[var(--cl-accent)] transition hover:bg-[var(--cl-accent)]/20"
              >
                <Sparkles className="h-3.5 w-3.5" />
                <span>{modelLoading ? 'Loading...' : 'Exemplar Answer'}</span>
              </button>
            )}
            <span className="text-sm font-medium text-[var(--cl-accent)]/85">
              {evaluation ? scoreLabel(evaluation.weighted_score) : 'Pending'}
            </span>
            <button
              type="button"
              onClick={onToggle}
              aria-expanded={isExpanded}
              aria-controls={`${titleId}-details`}
              aria-label={`${isExpanded ? 'Collapse' : 'Expand'} evaluation for question`}
              className="rounded-lg border border-[var(--cl-border)] px-3 py-2 text-xs text-[var(--cl-text-soft)] transition hover:border-[var(--cl-accent)]/50 hover:text-[var(--cl-text)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--cl-accent)]"
            >
              {isExpanded ? 'Hide details' : 'View details'}
            </button>
          </div>
        </div>

        <div className="mt-5 border-t border-[var(--cl-border)] pt-4">
          <p className="text-[10px] font-semibold uppercase tracking-[0.15em] text-[var(--cl-faint)]">
            Candidate answer
          </p>
          <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-[var(--cl-text-soft)]">
            {answer || 'The submitted answer is unavailable.'}
          </p>
        </div>

        {isPending && (
          <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[var(--cl-accent-soft)] bg-[var(--cl-accent-soft)] p-4">
            <p className="text-xs leading-5 text-[var(--cl-accent)]">
              This answer is awaiting evaluation. Scores are not inferred from missing data.
            </p>
            <button
              type="button"
              onClick={onEvaluate}
              disabled={isEvaluating}
              className="rounded-lg bg-[var(--cl-accent)] px-3 py-2 text-xs font-semibold text-[var(--cl-accent-contrast)] transition hover:bg-[var(--cl-accent-hover)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--cl-accent)]/80 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isEvaluating ? 'Evaluating...' : 'Evaluate answer'}
            </button>
          </div>
        )}

        {error && (
          <div className="mt-4 rounded-xl border border-[var(--cl-danger)]/30 bg-[var(--cl-danger-soft)] p-4" role="alert">
            <p className="text-xs leading-5 text-[var(--cl-danger)]">{error}</p>
            <button
              type="button"
              onClick={onEvaluate}
              disabled={isEvaluating}
              className="mt-3 rounded-lg border border-[var(--cl-danger)]/40 px-3 py-2 text-xs text-[var(--cl-danger)] transition hover:bg-[var(--cl-danger-soft)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--cl-danger)] disabled:opacity-50"
            >
              Retry evaluation
            </button>
          </div>
        )}
      </div>

      <div
        id={`${titleId}-details`}
        hidden={!isExpanded || !evaluation}
        className="border-t border-[var(--cl-border)] bg-white/[0.015] p-5 sm:p-6"
      >
        {evaluation && (
          <div className="space-y-6">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.15em] text-[var(--cl-accent)]">
                Criterion feedback
              </p>
              <div className="mt-3 space-y-3">
                {(Array.isArray(evaluation.criteria) ? evaluation.criteria : []).map(
                  (criterion) => (
                    <div key={criterion.id || criterion.criterion_id} className="rounded-xl border border-[var(--cl-border)] bg-[var(--cl-input-bg)] p-4">
                      <div className="flex flex-wrap items-baseline justify-between gap-2">
                        <h5 className="text-sm font-medium text-[var(--cl-text)]">
                          {criterion.criterion_name || 'Criterion'}
                        </h5>
                        <span className="text-xs font-medium text-[var(--cl-accent)]/80">
                          {criterion.score ?? '—'} / 5
                        </span>
                      </div>
                      <p className="mt-2 text-sm leading-6 text-[var(--cl-text-soft)]">
                        {criterion.explanation || 'No explanation was provided.'}
                      </p>
                      {Array.isArray(criterion.evidence_excerpts) && criterion.evidence_excerpts.length > 0 && (
                        <div className="mt-3 rounded-lg border-l-2 border-[var(--cl-accent)] bg-[var(--cl-accent)]/[0.04] px-3 py-2">
                          <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[var(--cl-accent)]/75">
                            Evidence from your answer
                          </p>
                          {criterion.evidence_excerpts.map((excerpt) => (
                            <p key={excerpt} className="mt-1 text-xs italic leading-5 text-[var(--cl-accent)]/75">
                              “{excerpt}”
                            </p>
                          ))}
                        </div>
                      )}
                      <p className="mt-3 text-xs leading-5 text-[var(--cl-muted)]">
                        <span className="font-medium text-[var(--cl-text-soft)]">Improve:</span>{' '}
                        {criterion.improvement_suggestion || 'No suggestion was provided.'}
                      </p>
                    </div>
                  ),
                )}
              </div>
            </div>

            <FeedbackList title="Strengths" items={evaluation.strengths} tone="positive" />
            <FeedbackList title="Areas to improve" items={evaluation.improvement_areas} />
            <FeedbackList title="Actionable suggestions" items={evaluation.actionable_feedback} />
          </div>
        )}
      </div>

      {modelModalOpen && modelData && (
        <ModelAnswerModal
          sessionId={evaluation?.session_id}
          modelData={modelData}
          onClose={() => setModelModalOpen(false)}
        />
      )}
    </article>
  )
}

function FeedbackList({ title, items, tone = 'neutral' }) {
  const safeItems = Array.isArray(items) ? items.filter(Boolean) : []

  if (safeItems.length === 0) return null

  return (
    <div>
      <p className="text-[10px] font-semibold uppercase tracking-[0.15em] text-[var(--cl-accent)]">
        {title}
      </p>
      <ul className="mt-3 space-y-2">
        {safeItems.map((item) => (
          <li
            key={item}
            className={`rounded-lg border p-3 text-sm leading-6 ${tone === 'positive' ? 'border-emerald-300/15 bg-emerald-300/[0.035] text-emerald-100/75' : 'border-[var(--cl-border)] bg-[var(--cl-surface-muted)] text-[var(--cl-text-soft)]'}`}
          >
            {item}
          </li>
        ))}
      </ul>
    </div>
  )
}
