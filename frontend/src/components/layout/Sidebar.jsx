const navigationItems = [
  { label: 'Overview', icon: 'overview' },
  { label: 'Resume', icon: 'resume' },
  { label: 'Jobs', icon: 'jobs' },
  { label: 'Applications', icon: 'applications' },
  { label: 'Roadmap', icon: 'roadmap' },
  { label: 'Interviews', icon: 'interviews' },
]

function NavIcon({ type }) {
  const commonProps = {
    className: 'h-4 w-4',
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: '1.8',
    strokeLinecap: 'round',
    strokeLinejoin: 'round',
    'aria-hidden': 'true',
  }

  const paths = {
    overview: (
      <>
        <path d="M4 13h6V4H4z" />
        <path d="M14 20h6V4h-6z" />
        <path d="M4 20h6v-3H4z" />
      </>
    ),
    resume: (
      <>
        <path d="M7 3h7l4 4v14H7z" />
        <path d="M14 3v5h5" />
        <path d="M10 12h6" />
        <path d="M10 16h5" />
      </>
    ),
    jobs: (
      <>
        <path d="M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2" />
        <path d="M4 8h16v11H4z" />
        <path d="M9 13h6" />
      </>
    ),
    applications: (
      <>
        <path d="M5 5h14v14H5z" />
        <path d="m8 12 2.5 2.5L16 9" />
      </>
    ),
    roadmap: (
      <>
        <path d="M5 6h4" />
        <path d="M15 18h4" />
        <path d="M7 6c6 0 4 12 10 12" />
        <path d="M17 6a2 2 0 1 0 0.01 0" />
        <path d="M7 18a2 2 0 1 0 0.01 0" />
      </>
    ),
    interviews: (
      <>
        <path d="M5 6h14v9H8l-3 3z" />
        <path d="M9 10h6" />
        <path d="M9 13h4" />
      </>
    ),
  }

  return <svg {...commonProps}>{paths[type]}</svg>
}

function Sidebar({ activeSection, onNavigate }) {
  return (
    <aside className="border-b border-[var(--cl-border)] bg-[var(--cl-sidebar)]/95 lg:sticky lg:top-0 lg:flex lg:h-screen lg:w-[var(--sidebar-width)] lg:flex-col lg:border-b-0 lg:border-r">
      <div className="flex items-center justify-between px-4 py-4 sm:px-6 lg:block lg:px-6 lg:py-7">
        <button
          type="button"
          className="group flex items-center gap-3 text-left"
          onClick={() => onNavigate('Overview')}
          aria-label="Go to CareerLens overview"
        >
          <span className="grid h-10 w-10 place-items-center rounded-[var(--radius-md)] border border-[var(--cl-border-strong)] bg-[var(--cl-accent-soft)] text-sm font-semibold text-[var(--cl-accent)] transition group-hover:border-[var(--cl-accent)]">
            CL
          </span>
          <span>
            <span className="block text-base font-semibold tracking-tight text-[var(--cl-text)]">
              CareerLens
            </span>
            <span className="block text-[0.65rem] font-semibold uppercase tracking-[0.22em] text-[var(--cl-muted)]">
              Career Intelligence
            </span>
          </span>
        </button>

        <div className="hidden rounded-full border border-[var(--cl-border)] px-3 py-1 text-xs text-[var(--cl-muted)] sm:block lg:hidden">
          Workspace
        </div>
      </div>

      <nav
        className="cl-scrollbar flex gap-2 overflow-x-auto px-4 pb-4 sm:px-6 lg:flex-1 lg:flex-col lg:overflow-x-visible lg:px-4 lg:pb-0"
        aria-label="CareerLens sections"
      >
        <p className="hidden px-3 pt-2 text-[0.68rem] font-semibold uppercase tracking-[0.22em] text-[var(--cl-faint)] lg:block">
          Workspace
        </p>

        {navigationItems.map((item) => {
          const isActive = activeSection === item.label

          return (
            <button
              key={item.label}
              type="button"
              onClick={() => onNavigate(item.label)}
              className={[
                'flex shrink-0 items-center gap-3 rounded-[var(--radius-md)] border px-3 py-2.5 text-sm font-medium transition',
                'lg:w-full',
                isActive
                  ? 'border-[var(--cl-border-strong)] bg-[var(--cl-surface-soft)] text-[var(--cl-text)] shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]'
                  : 'border-transparent text-[var(--cl-muted)] hover:border-[var(--cl-border)] hover:bg-[var(--cl-surface-muted)] hover:text-[var(--cl-text-soft)]',
              ].join(' ')}
              aria-current={isActive ? 'page' : undefined}
            >
              <span
                className={[
                  'grid h-7 w-7 place-items-center rounded-lg border transition',
                  isActive
                    ? 'border-[var(--cl-accent)]/40 bg-[var(--cl-accent-soft)] text-[var(--cl-accent)]'
                    : 'border-[var(--cl-border)] text-[var(--cl-faint)]',
                ].join(' ')}
              >
                <NavIcon type={item.icon} />
              </span>
              <span>{item.label}</span>
            </button>
          )
        })}
      </nav>

      <div className="hidden border-t border-[var(--cl-border)] p-4 lg:block">
        <div className="rounded-[var(--radius-md)] border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-4">
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-[var(--cl-faint)]">
            Profile
          </p>
          <div className="mt-3 flex items-center gap-3">
            <div className="grid h-9 w-9 place-items-center rounded-full bg-[var(--cl-accent-soft)] text-xs font-semibold text-[var(--cl-accent)]">
              AD
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-[var(--cl-text)]">
                Your Profile
              </p>
              <p className="truncate text-xs text-[var(--cl-muted)]">
                Career Workspace
              </p>
            </div>
          </div>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar