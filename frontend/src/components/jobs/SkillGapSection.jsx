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
        statusStyles[status] || 'border-white/8 bg-white/[0.02]',
      ].join(' ')}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <h4 className="min-w-0 break-words text-sm font-medium text-white/80">
          {item.skill}
        </h4>

        <span className="rounded-full border border-white/10 px-2 py-1 text-[10px] uppercase tracking-[0.13em] text-white/45">
          {item.priority} priority
        </span>
      </div>

      <p className="mt-2 text-xs leading-5 text-white/50">
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
      <h3 className="text-[10px] font-semibold uppercase tracking-[0.17em] text-white/35">
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
      className="rounded-xl border border-[#d6b36a]/12 bg-[#d6b36a]/[0.025] p-5"
      aria-labelledby="skill-gap-analysis-heading"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#d6b36a]">
            Skill gap analysis
          </p>

          <h3
            id="skill-gap-analysis-heading"
            className="mt-2 text-xl font-medium tracking-[-0.02em] text-white"
          >
            Required-skill coverage
          </h3>
        </div>

        {!loading && !error && data && (
          <span className="text-xs text-white/35">
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
          <div className="h-3 animate-pulse rounded bg-white/[0.08]" />
          <div className="h-3 w-10/12 animate-pulse rounded bg-white/[0.08]" />
          <div className="h-16 animate-pulse rounded-xl bg-white/[0.05]" />
        </div>
      ) : error ? (
        <div
          className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"
          role="alert"
        >
          <div>
            <p className="text-sm text-white/55">
              Unable to load skill-gap analysis.
            </p>

            <p className="mt-1 text-xs leading-5 text-white/35">
              {error}
            </p>
          </div>

          <button
            type="button"
            onClick={onRetry}
            className="shrink-0 rounded-lg border border-[#d6b36a]/20 px-3 py-2 text-xs font-medium text-[#e5c57c]/80 transition hover:bg-[#d6b36a]/10 hover:text-[#e5c57c]"
          >
            Retry
          </button>
        </div>
      ) : !data ? (
        <p className="mt-4 text-sm leading-6 text-white/40">
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
                <p className="text-sm leading-6 text-white/40">
                  No required skills were returned for this job.
                </p>
              )}
          </div>
        </>
      )}
    </section>
  )
}