function ActivityItem({ title, description, time, tone = 'neutral' }) {
  const toneClasses = {
    success: 'bg-[var(--cl-success-soft)] text-[var(--cl-success)]',
    warning: 'bg-[rgba(251,191,36,0.12)] text-[var(--cl-warning)]',
    neutral: 'bg-[var(--cl-accent-soft)] text-[var(--cl-accent)]',
  }

  return (
    <li className="flex gap-3">
      <span
        className={`mt-1 h-2.5 w-2.5 rounded-full ${toneClasses[tone]}`}
        aria-hidden="true"
      />
      <div className="min-w-0">
        <p className="text-sm font-medium text-[var(--cl-text)]">
          {title}
        </p>
        <p className="mt-1 text-sm leading-6 text-[var(--cl-muted)]">
          {description}
        </p>
        <p className="mt-1 text-xs text-[var(--cl-faint)]">{time}</p>
      </div>
    </li>
  )
}

export default ActivityItem