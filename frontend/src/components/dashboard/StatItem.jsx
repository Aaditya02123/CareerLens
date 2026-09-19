function StatItem({ label, value, detail, trend }) {
  return (
    <article className="rounded-[var(--radius-lg)] border border-[var(--cl-border)] bg-[var(--cl-surface)] p-5 transition hover:border-[var(--cl-border-strong)]">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm text-[var(--cl-muted)]">{label}</p>
          <p className="mt-3 text-3xl font-semibold tracking-tight text-[var(--cl-text)]">
            {value}
          </p>
        </div>
        <span className="rounded-full border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] px-2.5 py-1 text-xs font-medium text-[var(--cl-accent)]">
          {trend}
        </span>
      </div>
      <p className="mt-4 text-sm leading-6 text-[var(--cl-muted)]">
        {detail}
      </p>
    </article>
  )
}

export default StatItem