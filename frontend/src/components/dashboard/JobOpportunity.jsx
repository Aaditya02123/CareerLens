function JobOpportunity({
  role,
  company,
  location,
  match,
  matchedSkills = [],
  missingSkill,
  tier,
  onSelect,
}) {
  return (
    <article className="group border-b border-[var(--cl-border)] py-5 last:border-b-0">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-base font-semibold text-[var(--cl-text)] group-hover:text-[var(--cl-accent)] transition">
              {role}
            </h3>
            {tier && (
              <span className="rounded-full border border-[var(--cl-accent)]/30 bg-[var(--cl-accent-soft)] px-2.5 py-0.5 text-[10px] font-semibold tracking-wide text-[var(--cl-accent)]">
                {tier}
              </span>
            )}
          </div>

          <p className="mt-1 text-sm text-[var(--cl-muted)]">
            {company} · {location}
          </p>

          <div className="mt-3 flex flex-wrap gap-1.5">
            {matchedSkills.map((skill) => (
              <span
                key={skill}
                className="rounded-md border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] px-2 py-0.5 text-xs text-[var(--cl-text-soft)]"
              >
                {skill}
              </span>
            ))}
          </div>

          {missingSkill && (
            <p className="mt-3 text-xs text-[var(--cl-muted)]">
              Missing focus:{' '}
              <span className="font-semibold text-[var(--cl-warning)]">
                {missingSkill}
              </span>
            </p>
          )}
        </div>

        <div className="flex items-center justify-between gap-4 sm:flex-col sm:items-end">
          <div className="text-right">
            <p className="text-2xl font-bold tracking-tight text-[var(--cl-text)]">
              {match}%
            </p>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--cl-faint)]">
              Match
            </p>
          </div>

          <div
            className="h-2 w-24 overflow-hidden rounded-full bg-[var(--cl-surface-muted)] border border-[var(--cl-border)]"
            aria-hidden="true"
          >
            <div
              className="h-full rounded-full bg-[var(--cl-accent)] transition-all group-hover:bg-[var(--cl-success)]"
              style={{ width: `${match}%` }}
            />
          </div>

          {onSelect && (
            <button
              type="button"
              onClick={onSelect}
              className="mt-1 rounded-md border border-[var(--cl-border)] bg-[var(--cl-surface-soft)] px-2.5 py-1 text-xs font-medium text-[var(--cl-text-soft)] transition hover:border-[var(--cl-accent)]/50 hover:bg-[var(--cl-accent-soft)] hover:text-[var(--cl-accent)]"
            >
              View in Jobs →
            </button>
          )}
        </div>
      </div>
    </article>
  )
}

export default JobOpportunity
