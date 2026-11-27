import { useEffect, useRef, useState } from 'react'
import { LogIn, LogOut, ShieldCheck } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

function SunIcon({ className }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2" />
      <path d="M12 20v2" />
      <path d="m4.93 4.93 1.41 1.41" />
      <path d="m17.66 17.66 1.41 1.41" />
      <path d="M2 12h2" />
      <path d="M20 12h2" />
      <path d="m6.34 17.66-1.41 1.41" />
      <path d="m19.07 4.93-1.41 1.41" />
    </svg>
  )
}

function MoonIcon({ className }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" />
    </svg>
  )
}

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

function Topbar({
  title,
  description,
  backendStatus,
  theme = 'dark',
  onToggleTheme,
}) {
  const statusView = getStatusView(backendStatus)
  const { user, isAuthenticated, logout, openAuthModal } = useAuth()
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const menuRef = useRef(null)

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setDropdownOpen(false)
      }
    }
    if (dropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [dropdownOpen])

  const initial = user?.name
    ? user.name.charAt(0).toUpperCase()
    : user?.email
      ? user.email.charAt(0).toUpperCase()
      : 'A'

  return (
    <header className="border-b border-[var(--cl-border)] bg-[var(--cl-bg)]/80 px-4 py-4 backdrop-blur-xl transition-colors duration-200 sm:px-6 lg:px-8">
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
          {onToggleTheme && (
            <button
              type="button"
              onClick={onToggleTheme}
              aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
              title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
              className="flex items-center gap-2 rounded-full border border-[var(--cl-border)] bg-[var(--cl-surface)] px-3 py-2 text-xs font-medium text-[var(--cl-text)] shadow-xs transition hover:border-[var(--cl-border-strong)] hover:bg-[var(--cl-surface-soft)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--cl-accent)]"
            >
              {theme === 'dark' ? (
                <>
                  <SunIcon className="h-4 w-4 text-[var(--cl-accent)]" />
                  <span className="text-xs font-medium text-[var(--cl-text-soft)]">Light</span>
                </>
              ) : (
                <>
                  <MoonIcon className="h-4 w-4 text-[var(--cl-accent)]" />
                  <span className="text-xs font-medium text-[var(--cl-text-soft)]">Dark</span>
                </>
              )}
            </button>
          )}

          <div className="flex items-center gap-2 rounded-full border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] px-3 py-2">
            <span
              className={`h-2 w-2 rounded-full ${statusView.dot}`}
              aria-hidden="true"
            />
            <span className={`text-xs font-medium ${statusView.tone}`}>
              {statusView.label}
            </span>
          </div>

          {isAuthenticated ? (
            <div className="relative" ref={menuRef}>
              <button
                type="button"
                onClick={() => setDropdownOpen(!dropdownOpen)}
                aria-expanded={dropdownOpen}
                aria-haspopup="true"
                aria-label={`User menu for ${user?.name || user?.email}`}
                className="flex items-center gap-2 rounded-full border border-[var(--cl-border-strong)] bg-[var(--cl-surface)] p-1 pr-3 text-left transition hover:border-[var(--cl-accent)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--cl-accent)]"
              >
                <div
                  className="grid h-8 w-8 place-items-center rounded-full bg-[var(--cl-accent)] text-xs font-semibold text-[var(--cl-accent-contrast)]"
                  aria-label="User profile placeholder"
                  role="img"
                >
                  {initial}
                </div>
                <div className="hidden sm:block">
                  <span className="block truncate text-xs font-semibold text-[var(--cl-text)]">
                    {user?.name || 'User'}
                  </span>
                </div>
              </button>

              {dropdownOpen && (
                <div
                  className="absolute right-0 mt-2 w-56 rounded-[var(--radius-md)] border border-[var(--cl-border-strong)] bg-[var(--cl-surface)] p-2 shadow-[var(--shadow-soft)] z-50 animate-in fade-in zoom-in-95 duration-150"
                  role="menu"
                >
                  <div className="border-b border-[var(--cl-border)] px-3 py-2">
                    <p className="truncate text-xs font-semibold text-[var(--cl-text)]">
                      {user?.name}
                    </p>
                    <p className="truncate text-[11px] text-[var(--cl-muted)]">
                      {user?.email}
                    </p>
                    <div className="mt-1.5 flex items-center gap-1 text-[10px] text-[var(--cl-success)]">
                      <ShieldCheck className="h-3 w-3" />
                      <span>Authenticated Session</span>
                    </div>
                  </div>

                  <div className="pt-1">
                    <button
                      type="button"
                      role="menuitem"
                      onClick={() => {
                        logout()
                        setDropdownOpen(false)
                      }}
                      className="flex w-full items-center gap-2 rounded-[var(--radius-sm)] px-3 py-2 text-xs font-medium text-[var(--cl-danger)] transition hover:bg-[var(--cl-danger-soft)]"
                    >
                      <LogOut className="h-3.5 w-3.5" />
                      <span>Sign Out</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <button
              type="button"
              onClick={() => openAuthModal('login')}
              className="flex items-center gap-1.5 rounded-full bg-[var(--cl-accent)] px-3.5 py-1.5 text-xs font-semibold text-[var(--cl-accent-contrast)] shadow-xs transition hover:bg-[var(--cl-accent-hover)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--cl-accent)]"
            >
              <LogIn className="h-3.5 w-3.5" />
              <span>Sign In</span>
            </button>
          )}
        </div>
      </div>
    </header>
  )
}

export default Topbar
