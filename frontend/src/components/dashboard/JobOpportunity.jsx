function JobOpportunity({
  role,
  company,
  location,
  match,
  matchedSkills,
  missingSkill,
}) {
  return (
    <article className="group border-b border-[var(--cl-border)] py-5 last:border-b-0">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <h3 className="text-base font-semibold text-[var(--cl-text)]">
            {role}
          </h3>
          <p className="mt-1 text-sm text-[var(--cl-muted)]">
            {company} · {location}
          </p>

          <div className="mt-4 flex flex-wrap gap-2">
            {matchedSkills.map((skill) => (
              <span
                key={skill}
                className="rounded-full border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] px-2.5 py-1 text-xs text-[var(--cl-text-soft)]"
              >
                {skill}
              </span>
            ))}
          </div>

          <p className="mt-3 text-xs text-[var(--cl-muted)]">
            Missing focus:{' '}
            <span className="font-medium text-[var(--cl-warning)]">
              {missingSkill}
            </span>
          </p>
        </div>

        <div className="flex items-center gap-3 sm:flex-col sm:items-end">
          <div className="text-right">
            <p className="text-2xl font-semibold text-[var(--cl-text)]">
              {match}%
            </p>
            <p className="text-xs uppercase tracking-[0.18em] text-[var(--cl-faint)]">
              Match
            </p>
          </div>

          <div
            className="h-1.5 w-24 overflow-hidden rounded-full bg-[var(--cl-surface-muted)]"
            aria-hidden="true"
          >
            <div
              className="h-full rounded-full bg-[var(--cl-accent)] transition-all group-hover:bg-[var(--cl-success)]"
              style={{ width: `${match}%` }}
            />
          </div>
        </div>
      </div>
    </article>
  )
}

export default JobOpportunity