function scoreLabel(score) {
  return Number.isFinite(Number(score))
    ? `${Number(score).toFixed(2)} / 5`
    : 'Not available'
}

function MetaBadge({ children }) {
  return (
    <span className="rounded-full border border-white/10 px-2 py-1 text-[10px] uppercase tracking-[0.12em] text-white/45">
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
  const question = evaluation?.question || 'Question text is unavailable.'
  const answer = evaluation?.answer || pendingAnswer?.answer || ''
  const titleId = `interview-question-${evaluation?.answer_id || pendingAnswer?.id}`
  const isPending = !evaluation

  return (
    <article className="rounded-2xl border border-white/8 bg-[#111111]">
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
            <h4 id={titleId} className="mt-3 text-base font-medium leading-6 text-white/85">
              {question}
            </h4>
            {evaluation?.competency_reference && (
              <p className="mt-2 text-xs text-white/40">
                Competency: {evaluation.competency_reference}
              </p>
            )}
            {evaluation?.is_follow_up && evaluation.parent_question && (
              <p className="mt-3 rounded-lg border border-[#d6b36a]/15 bg-[#d6b36a]/[0.035] p-3 text-xs leading-5 text-[#f0d18b]/75">
                Follow-up to: {evaluation.parent_question}
              </p>
            )}
          </div>

          <div className="flex shrink-0 items-center gap-3">
            <span className="text-sm font-medium text-[#e5c57c]/85">
              {evaluation ? scoreLabel(evaluation.weighted_score) : 'Pending'}
            </span>
            <button
              type="button"
              onClick={onToggle}
              aria-expanded={isExpanded}
              aria-controls={`${titleId}-details`}
              aria-label={`${isExpanded ? 'Collapse' : 'Expand'} evaluation for question`}
              className="rounded-lg border border-white/10 px-3 py-2 text-xs text-white/60 transition hover:border-[#d6b36a]/45 hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-[#d6b36a]/70"
            >
              {isExpanded ? 'Hide details' : 'View details'}
            </button>
          </div>
        </div>

        <div className="mt-5 border-t border-white/8 pt-4">
          <p className="text-[10px] font-semibold uppercase tracking-[0.15em] text-white/35">
            Candidate answer
          </p>
          <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-white/60">
            {answer || 'The submitted answer is unavailable.'}
          </p>
        </div>

        {isPending && (
          <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[#d6b36a]/15 bg-[#d6b36a]/[0.035] p-4">
            <p className="text-xs leading-5 text-[#f0d18b]/75">
              This answer is awaiting evaluation. Scores are not inferred from missing data.
            </p>
            <button
              type="button"
              onClick={onEvaluate}
              disabled={isEvaluating}
              className="rounded-lg bg-[#d6b36a] px-3 py-2 text-xs font-semibold text-[#17130b] transition hover:bg-[#e5c57c] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#f0d18b]/80 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isEvaluating ? 'Evaluating...' : 'Evaluate answer'}
            </button>
          </div>
        )}

        {error && (
          <div className="mt-4 rounded-xl border border-red-300/15 bg-red-300/[0.035] p-4" role="alert">
            <p className="text-xs leading-5 text-red-100/75">{error}</p>
            <button
              type="button"
              onClick={onEvaluate}
              disabled={isEvaluating}
              className="mt-3 rounded-lg border border-red-200/20 px-3 py-2 text-xs text-red-100/75 transition hover:bg-red-200/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-red-200/70 disabled:opacity-50"
            >
              Retry evaluation
            </button>
          </div>
        )}
      </div>

      <div
        id={`${titleId}-details`}
        hidden={!isExpanded || !evaluation}
        className="border-t border-white/8 bg-white/[0.015] p-5 sm:p-6"
      >
        {evaluation && (
          <div className="space-y-6">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.15em] text-[#d6b36a]">
                Criterion feedback
              </p>
              <div className="mt-3 space-y-3">
                {(Array.isArray(evaluation.criteria) ? evaluation.criteria : []).map(
                  (criterion) => (
                    <div key={criterion.id || criterion.criterion_id} className="rounded-xl border border-white/8 bg-[#0b0b0b] p-4">
                      <div className="flex flex-wrap items-baseline justify-between gap-2">
                        <h5 className="text-sm font-medium text-white/80">
                          {criterion.criterion_name || 'Criterion'}
                        </h5>
                        <span className="text-xs font-medium text-[#e5c57c]/80">
                          {criterion.score ?? '—'} / 5
                        </span>
                      </div>
                      <p className="mt-2 text-sm leading-6 text-white/55">
                        {criterion.explanation || 'No explanation was provided.'}
                      </p>
                      {Array.isArray(criterion.evidence_excerpts) && criterion.evidence_excerpts.length > 0 && (
                        <div className="mt-3 rounded-lg border-l-2 border-[#d6b36a]/60 bg-[#d6b36a]/[0.04] px-3 py-2">
                          <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[#d6b36a]/75">
                            Evidence from your answer
                          </p>
                          {criterion.evidence_excerpts.map((excerpt) => (
                            <p key={excerpt} className="mt-1 text-xs italic leading-5 text-[#f0d18b]/75">
                              “{excerpt}”
                            </p>
                          ))}
                        </div>
                      )}
                      <p className="mt-3 text-xs leading-5 text-white/45">
                        <span className="font-medium text-white/60">Improve:</span>{' '}
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
    </article>
  )
}

function FeedbackList({ title, items, tone = 'neutral' }) {
  const safeItems = Array.isArray(items) ? items.filter(Boolean) : []

  if (safeItems.length === 0) return null

  return (
    <div>
      <p className="text-[10px] font-semibold uppercase tracking-[0.15em] text-[#d6b36a]">
        {title}
      </p>
      <ul className="mt-3 space-y-2">
        {safeItems.map((item) => (
          <li
            key={item}
            className={`rounded-lg border p-3 text-sm leading-6 ${tone === 'positive' ? 'border-emerald-300/15 bg-emerald-300/[0.035] text-emerald-100/75' : 'border-white/8 bg-white/[0.02] text-white/55'}`}
          >
            {item}
          </li>
        ))}
      </ul>
    </div>
  )
}
