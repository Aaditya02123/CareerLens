function StatItem({ label, value, detail, trend }) {
  return (
    <article className="group rounded-[var(--radius-lg)] border border-[var(--cl-border)] bg-[var(--cl-surface)] p-5 shadow-xs transition hover:border-[var(--cl-border-strong)] hover:bg-[var(--cl-surface-soft)]">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--cl-muted)]">
            {label}
          </p>
          <p className="mt-2 text-3xl font-semibold tracking-tight text-[var(--cl-text)]">
            {value}
          </p>
        </div>
        {trend && (
          <span className="shrink-0 rounded-full border border-[var(--cl-accent)]/30 bg-[var(--cl-accent-soft)] px-2.5 py-1 text-xs font-medium text-[var(--cl-accent)]">
            {trend}
          </span>
        )}
      </div>
      <p className="mt-3 text-xs leading-5 text-[var(--cl-muted)]">
        {detail}
      </p>
    </article>
  )
}

export default StatItem
