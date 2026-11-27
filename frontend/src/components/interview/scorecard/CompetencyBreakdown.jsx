function scoreWidth(score) {
  if (!Number.isFinite(Number(score))) return '0%'
  return `${Math.max(0, Math.min(Number(score) / 5 * 100, 100))}%`
}

export default function CompetencyBreakdown({ competencies }) {
  const safeCompetencies = Array.isArray(competencies) ? competencies : []

  return (
    <section
      className="rounded-2xl border border-[var(--cl-border)] bg-[var(--cl-surface)] p-5 sm:p-6"
      aria-labelledby="competency-breakdown-heading"
    >
      <div>
        <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--cl-accent)]">
          Competency breakdown
        </p>
        <h3
          id="competency-breakdown-heading"
          className="mt-2 text-lg font-medium text-[var(--cl-text)]"
        >
          Where your answers are strongest
        </h3>
      </div>

      {safeCompetencies.length === 0 ? (
        <p className="mt-5 rounded-xl border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-4 text-sm leading-6 text-[var(--cl-muted)]">
          Competency scores will appear after answers are evaluated.
        </p>
      ) : (
        <div className="mt-5 space-y-5">
          {safeCompetencies.map((competency) => {
            const hasScore = Number.isFinite(Number(competency?.score))
            const scoreLabel = hasScore
              ? `${Number(competency.score).toFixed(2)} / 5`
              : 'Not available'

            return (
              <div key={competency?.competency_reference || scoreLabel}>
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <div>
                    <h4 className="text-sm font-medium text-[var(--cl-text)]">
                      {competency?.competency_reference || 'Unnamed competency'}
                    </h4>
                    <p className="mt-1 text-xs text-[var(--cl-faint)]">
                      {competency?.evaluated_answer_count ?? 0} answer
                      {competency?.evaluated_answer_count === 1 ? '' : 's'}
                      {' · '}
                      {competency?.competency_weight_percent ?? '—'}% weight
                    </p>
                  </div>
                  <span className="text-sm font-medium text-[var(--cl-accent)]/85">
                    {scoreLabel}
                  </span>
                </div>

                <div
                  className="mt-3 h-2 overflow-hidden rounded-full bg-[var(--cl-border)]"
                  role="progressbar"
                  aria-label={`${competency?.competency_reference || 'Competency'} score`}
                  aria-valuemin="0"
                  aria-valuemax="5"
                  aria-valuenow={hasScore ? Number(competency.score) : 0}
                >
                  <div
                    className="h-full rounded-full bg-[var(--cl-accent)] transition-[width]"
                    style={{ width: scoreWidth(competency?.score) }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      )}
    </section>
  )
}
