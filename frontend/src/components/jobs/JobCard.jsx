function formatScore(score) {
  if (typeof score !== 'number') {
    return null
  }

  return `${Math.round(score * 100)}%`
}

function MatchIndicator({ score }) {
  const percentage = Math.round((score || 0) * 100)

  return (
    <div className="flex items-center gap-3">
      <div className="h-2 w-20 overflow-hidden rounded-full border border-[var(--cl-border)] bg-[var(--cl-surface-muted)]">
        <div
          className="h-full rounded-full bg-[var(--cl-accent)] transition-all"
          style={{ width: `${percentage}%` }}
        />
      </div>

      <span className="text-sm font-semibold text-[var(--cl-accent)]">
        {percentage}%
      </span>
    </div>
  )
}

function SkillChip({ children, muted = false }) {
  return (
    <span
      className={[
        'rounded-md border px-2.5 py-1 text-[11px] font-medium',
        muted
          ? 'border-[var(--cl-border)] bg-[var(--cl-surface-muted)] text-[var(--cl-muted)]'
          : 'border-[var(--cl-border-strong)] bg-[var(--cl-surface-soft)] text-[var(--cl-text-soft)]',
      ].join(' ')}
    >
      {children}
    </span>
  )
}

export default function JobCard({
  job,
  recommendation,
  onSelect,
}) {
  const matchScore = recommendation?.hybrid_score ?? null
  const matchedSkills =
    recommendation?.matched_required_skills ?? []
  const missingSkills =
    recommendation?.missing_required_skills ?? []

  return (
    <article className="group rounded-2xl border border-[var(--cl-border)] bg-[var(--cl-surface)] p-5 shadow-xs transition duration-200 hover:-translate-y-0.5 hover:border-[var(--cl-border-strong)] hover:bg-[var(--cl-card-hover)]">
      <div className="flex flex-col gap-5">
        <div className="flex items-start justify-between gap-5">
          <div className="min-w-0">
            <div className="mb-2 flex flex-wrap items-center gap-2">
              {recommendation?.rank && (
                <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--cl-accent)]">
                  #{recommendation.rank} for you
                </span>
              )}

              {job.source && (
                <span className="rounded-full border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] px-2.5 py-0.5 text-[10px] font-medium text-[var(--cl-muted)]">
                  {job.source}
                </span>
              )}
            </div>

            <h3 className="truncate text-lg font-semibold tracking-[-0.02em] text-[var(--cl-text)]">
              {job.title}
            </h3>

            <p className="mt-1 text-sm text-[var(--cl-muted)]">
              {job.company || 'Company not specified'}
              {job.location ? ` · ${job.location}` : ''}
            </p>
          </div>

          {matchScore !== null && (
            <div className="shrink-0 text-right">
              <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-[var(--cl-faint)]">
                Match
              </div>

              <MatchIndicator score={matchScore} />
            </div>
          )}
        </div>

        {(matchedSkills.length > 0 ||
          missingSkills.length > 0) && (
          <div className="space-y-3">
            {matchedSkills.length > 0 && (
              <div>
                <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-[var(--cl-faint)]">
                  Matched skills
                </p>

                <div className="flex flex-wrap gap-2">
                  {matchedSkills.slice(0, 6).map((skill) => (
                    <SkillChip key={`matched-${skill}`}>
                      ✓ {skill}
                    </SkillChip>
                  ))}
                </div>
              </div>
            )}

            {missingSkills.length > 0 && (
              <div>
                <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-[var(--cl-faint)]">
                  Skill gap
                </p>

                <div className="flex flex-wrap gap-2">
                  {missingSkills.slice(0, 5).map((skill) => (
                    <SkillChip
                      key={`missing-${skill}`}
                      muted
                    >
                      {skill}
                    </SkillChip>
                  ))}

                  {missingSkills.length > 5 && (
                    <span className="px-1 py-1 text-[11px] text-[var(--cl-muted)]">
                      +{missingSkills.length - 5} more
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        <div className="flex items-center justify-between border-t border-[var(--cl-border)] pt-4">
          <div className="flex gap-5 text-xs text-[var(--cl-muted)]">
            {recommendation?.semantic_score !== undefined && (
              <span>
                Semantic{' '}
                <strong className="font-semibold text-[var(--cl-text-soft)]">
                  {formatScore(
                    recommendation.semantic_score
                  )}
                </strong>
              </span>
            )}

            {recommendation?.required_skill_score !==
              undefined && (
              <span>
                Skills{' '}
                <strong className="font-semibold text-[var(--cl-text-soft)]">
                  {formatScore(
                    recommendation.required_skill_score
                  )}
                </strong>
              </span>
            )}
          </div>

          <button
            type="button"
            onClick={() => onSelect?.(job)}
            className="text-xs font-semibold text-[var(--cl-accent)] transition hover:underline group-hover:translate-x-0.5"
          >
            View intelligence →
          </button>
        </div>
      </div>
    </article>
  )
}
