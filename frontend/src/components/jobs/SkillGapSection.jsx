function GapItem({ item, status }) {
  const statusStyles = {
    matched: 'border-emerald-300/15 bg-emerald-300/[0.035]',
    partial: 'border-amber-300/15 bg-amber-300/[0.035]',
    missing: 'border-red-300/15 bg-red-300/[0.035]',
  }

  return (
    <article
      className={[
        'rounded-xl border p-4',
        statusStyles[status] || 'border-[var(--cl-border)] bg-[var(--cl-surface-muted)]',
      ].join(' ')}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <h4 className="min-w-0 break-words text-sm font-medium text-[var(--cl-text)]">
          {item.skill}
        </h4>

        <span className="rounded-full border border-[var(--cl-border)] px-2 py-1 text-[10px] uppercase tracking-[0.13em] text-[var(--cl-muted)]">
          {item.priority} priority
        </span>
      </div>

      <p className="mt-2 text-xs leading-5 text-[var(--cl-muted)]">
        {item.reason}
      </p>
    </article>
  )
}

function GapCategory({ title, items, status }) {
  if (!Array.isArray(items) || items.length === 0) {
    return null
  }

  return (
    <section>
      <h3 className="text-[10px] font-semibold uppercase tracking-[0.17em] text-[var(--cl-faint)]">
        {title}
      </h3>

      <div className="mt-3 space-y-2">
        {items.map((item, index) => (
          <GapItem
            key={`${status}-${item.skill}-${index}`}
            item={item}
            status={status}
          />
        ))}
      </div>
    </section>
  )
}

function SummaryPill({ value, label, tone }) {
  const toneStyles = {
    matched: 'border-emerald-300/15 text-emerald-100/70',
    partial: 'border-amber-300/15 text-amber-100/70',
    missing: 'border-red-300/15 text-red-100/70',
  }

  return (
    <span
      className={[
        'rounded-full border px-2.5 py-1 text-[10px] uppercase tracking-[0.12em]',
        toneStyles[tone],
      ].join(' ')}
    >
      {value} {label}
    </span>
  )
}

export default function SkillGapSection({
  data,
  loading = false,
  error = '',
  onRetry,
}) {
  return (
    <section
      className="rounded-xl border border-[var(--cl-accent-soft)] bg-[var(--cl-accent-soft)] p-5"
      aria-labelledby="skill-gap-analysis-heading"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--cl-accent)]">
            Skill gap analysis
          </p>

          <h3
            id="skill-gap-analysis-heading"
            className="mt-2 text-xl font-medium tracking-[-0.02em] text-[var(--cl-text)]"
          >
            Required-skill coverage
          </h3>
        </div>

        {!loading && !error && data && (
          <span className="text-xs text-[var(--cl-faint)]">
            {data.total_required_skills || 0} required skills
          </span>
        )}
      </div>

      {loading ? (
        <div
          className="mt-5 space-y-2"
          aria-live="polite"
          aria-label="Loading skill gap analysis"
        >
          <div className="h-3 animate-pulse rounded bg-[var(--cl-surface-muted)]" />
          <div className="h-3 w-10/12 animate-pulse rounded bg-[var(--cl-surface-muted)]" />
          <div className="h-16 animate-pulse rounded-xl bg-[var(--cl-surface-soft)]" />
        </div>
      ) : error ? (
        <div
          className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"
          role="alert"
        >
          <div>
            <p className="text-sm text-[var(--cl-text-soft)]">
              Unable to load skill-gap analysis.
            </p>

            <p className="mt-1 text-xs leading-5 text-[var(--cl-faint)]">
              {error}
            </p>
          </div>

          <button
            type="button"
            onClick={onRetry}
            className="shrink-0 rounded-lg border border-[var(--cl-accent-soft)] px-3 py-2 text-xs font-medium text-[var(--cl-accent)]/80 transition hover:bg-[var(--cl-accent)]/10 hover:text-[var(--cl-accent)]"
          >
            Retry
          </button>
        </div>
      ) : !data ? (
        <p className="mt-4 text-sm leading-6 text-[var(--cl-muted)]">
          Skill-gap analysis is not available for this match.
        </p>
      ) : (
        <>
          <div className="mt-4 flex flex-wrap items-center gap-2">
            <SummaryPill
              value={data.matched_count || 0}
              label="matched"
              tone="matched"
            />

            <SummaryPill
              value={data.partial_count || 0}
              label="partial"
              tone="partial"
            />

            <SummaryPill
              value={data.missing_count || 0}
              label="missing"
              tone="missing"
            />
          </div>

          <div className="mt-6 space-y-5">
            <GapCategory
              title="Matched"
              items={data.matched}
              status="matched"
            />

            <GapCategory
              title="Partial"
              items={data.partial}
              status="partial"
            />

            <GapCategory
              title="Missing"
              items={data.missing}
              status="missing"
            />

            {(!data.matched || data.matched.length === 0) &&
              (!data.partial || data.partial.length === 0) &&
              (!data.missing || data.missing.length === 0) && (
                <p className="text-sm leading-6 text-[var(--cl-muted)]">
                  No required skills were returned for this job.
                </p>
              )}
          </div>
        </>
      )}
    </section>
  )
}