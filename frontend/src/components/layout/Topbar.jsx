function getStatusView(status) {
  if (status === 'healthy') {
    return {
      label: 'System operational',
      tone: 'text-[var(--cl-success)]',
      dot: 'bg-[var(--cl-success)]',
    }
  }

  if (status === 'loading') {
    return {
      label: 'Checking backend',
      tone: 'text-[var(--cl-muted)]',
      dot: 'bg-[var(--cl-warning)]',
    }
  }

  return {
    label: 'Backend unavailable',
    tone: 'text-[var(--cl-muted)]',
    dot: 'bg-[var(--cl-danger)]',
  }
}

function Topbar({ title, description, backendStatus }) {
  const statusView = getStatusView(backendStatus)

  return (
    <header className="border-b border-[var(--cl-border)] bg-[var(--cl-bg)]/80 px-4 py-4 backdrop-blur-xl sm:px-6 lg:px-8">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[var(--cl-faint)]">
            CareerLens
          </p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight text-[var(--cl-text)]">
            {title}
          </h1>
          <p className="mt-1 text-sm text-[var(--cl-muted)]">
            {description}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 rounded-full border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] px-3 py-2">
            <span
              className={`h-2 w-2 rounded-full ${statusView.dot}`}
              aria-hidden="true"
            />
            <span className={`text-xs font-medium ${statusView.tone}`}>
              {statusView.label}
            </span>
          </div>

          <div
            className="grid h-10 w-10 place-items-center rounded-full border border-[var(--cl-border-strong)] bg-[var(--cl-surface)] text-sm font-semibold text-[var(--cl-text)]"
            aria-label="User profile placeholder"
            role="img"
          >
            A
          </div>
        </div>
      </div>
    </header>
  )
}

export default Topbar