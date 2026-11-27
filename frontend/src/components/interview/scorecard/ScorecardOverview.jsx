import ScorecardStatus from './ScorecardStatus'

function Metric({ label, value }) {
  return (
    <div className="rounded-xl border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-3">
      <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[var(--cl-faint)]">
        {label}
      </p>
      <p className="mt-2 text-xl font-medium text-[var(--cl-text)]">{value}</p>
    </div>
  )
}

export default function ScorecardOverview({ scorecard, session }) {
  const overallScore = scorecard?.overall_score
  const hasScore =
    overallScore !== null &&
    overallScore !== undefined &&
    Number.isFinite(Number(overallScore))
  const competencyCount = Array.isArray(scorecard?.competency_scores)
    ? scorecard.competency_scores.length
    : 0
  const pendingCount = Array.isArray(scorecard?.pending_answer_ids)
    ? scorecard.pending_answer_ids.length
    : 0

  return (
    <section
      className="rounded-2xl border border-[var(--cl-accent-soft)] bg-[var(--cl-surface)] p-5 shadow-[var(--shadow-soft)] sm:p-7"
      aria-labelledby="interview-scorecard-heading"
    >
      <div className="flex flex-wrap items-start justify-between gap-5">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--cl-accent)]">
            Interview scorecard
          </p>
          <h2
            id="interview-scorecard-heading"
            className="mt-2 text-2xl font-medium tracking-[-0.03em] text-[var(--cl-text)]"
          >
            Your interview feedback
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-[var(--cl-muted)]">
            Scores and feedback are advisory, grounded in the persisted
            interview rubric, and intended to help you improve future answers.
          </p>
        </div>

        <ScorecardStatus
          scorecardStatus={scorecard?.status}
          sessionStatus={session?.status}
        />
      </div>

      <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-[var(--cl-accent-soft)] bg-[var(--cl-accent-soft)] p-4 sm:col-span-2 lg:col-span-1">
          <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[var(--cl-accent)]/75">
            Overall score
          </p>
          {hasScore ? (
            <p className="mt-2 text-3xl font-semibold text-[var(--cl-accent)]">
              {Number(overallScore).toFixed(2)}
              <span className="ml-1 text-sm font-normal text-[var(--cl-muted)]">
                / 5
              </span>
            </p>
          ) : (
            <p className="mt-3 text-sm text-[var(--cl-muted)]">Not available yet</p>
          )}
          {scorecard?.status === 'partial' && (
            <p className="mt-2 text-xs leading-5 text-[var(--cl-accent)]/70">
              Provisional score from the answers evaluated so far.
            </p>
          )}
        </div>

        <Metric
          label="Answers evaluated"
          value={scorecard?.evaluated_answer_count ?? 0}
        />
        <Metric label="Awaiting evaluation" value={pendingCount} />
        <Metric label="Competencies assessed" value={competencyCount} />
      </div>

      {scorecard?.status === 'pending' && (
        <p className="mt-5 rounded-xl border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-4 text-sm leading-6 text-[var(--cl-muted)]">
          Evaluation has not started. Choose an answer below to begin an
          explicit evaluation.
        </p>
      )}
    </section>
  )
}
