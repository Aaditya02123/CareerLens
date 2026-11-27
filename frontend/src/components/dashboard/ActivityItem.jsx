function ActivityItem({ title, description, time, tone = 'neutral', category }) {
  const dotClasses = {
    success: 'bg-[var(--cl-success)]',
    warning: 'bg-[var(--cl-warning)]',
    neutral: 'bg-[var(--cl-accent)]',
  }

  return (
    <li className="flex gap-3">
      <span
        className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${dotClasses[tone] || dotClasses.neutral}`}
        aria-hidden="true"
      />
      <div className="min-w-0 flex-1">
        <div className="flex items-center justify-between gap-2">
          <p className="text-sm font-medium text-[var(--cl-text)]">
            {title}
          </p>
          <span className="shrink-0 text-[11px] text-[var(--cl-faint)]">{time}</span>
        </div>
        <p className="mt-0.5 text-xs leading-5 text-[var(--cl-muted)]">
          {description}
        </p>
        {category && (
          <span className="mt-1.5 inline-block rounded-full border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] px-2 py-0.5 text-[10px] font-medium text-[var(--cl-muted)]">
            {category}
          </span>
        )}
      </div>
    </li>
  )
}

export default ActivityItem
