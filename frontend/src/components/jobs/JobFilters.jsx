export default function JobFilters({
  search,
  location,
  experienceLevel,
  source,
  onSearchChange,
  onLocationChange,
  onExperienceChange,
  onSourceChange,
  onClear,
}) {
  const hasFilters =
    search ||
    location ||
    experienceLevel ||
    source

  return (
    <div className="rounded-2xl border border-[var(--cl-border)] bg-[var(--cl-surface)] px-5 py-5 shadow-xs">
      <div className="flex flex-col gap-3 xl:flex-row xl:items-center">
        <div className="relative flex-1">
          <span className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-sm text-[var(--cl-muted)]">
            ⌕
          </span>

          <input
            type="text"
            value={search}
            onChange={(event) =>
              onSearchChange(event.target.value)
            }
            placeholder="Search job titles..."
            className="h-11 w-full rounded-xl border border-[var(--cl-border)] bg-[var(--cl-input-bg)] pl-10 pr-4 text-sm text-[var(--cl-text)] outline-none transition placeholder:text-[var(--cl-faint)] focus:border-[var(--cl-accent)]"
          />
        </div>

        <div className="relative flex-1 xl:max-w-[220px]">
          <span className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-sm text-[var(--cl-muted)]">
            ◇
          </span>

          <input
            type="text"
            value={location}
            onChange={(event) =>
              onLocationChange(event.target.value)
            }
            placeholder="Location"
            className="h-11 w-full rounded-xl border border-[var(--cl-border)] bg-[var(--cl-input-bg)] pl-10 pr-4 text-sm text-[var(--cl-text)] outline-none transition placeholder:text-[var(--cl-faint)] focus:border-[var(--cl-accent)]"
          />
        </div>

        <select
          value={experienceLevel}
          onChange={(event) =>
            onExperienceChange(event.target.value)
          }
          className="h-11 rounded-xl border border-[var(--cl-border)] bg-[var(--cl-input-bg)] px-4 text-sm text-[var(--cl-text)] outline-none transition focus:border-[var(--cl-accent)] xl:w-[190px]"
        >
          <option value="">Experience level</option>
          <option value="internship">Internship</option>
          <option value="entry">Entry level</option>
          <option value="junior">Junior</option>
          <option value="mid">Mid level</option>
          <option value="senior">Senior</option>
        </select>

        <input
          type="text"
          value={source}
          onChange={(event) =>
            onSourceChange(event.target.value)
          }
          placeholder="Source"
          className="h-11 rounded-xl border border-[var(--cl-border)] bg-[var(--cl-input-bg)] px-4 text-sm text-[var(--cl-text)] outline-none transition placeholder:text-[var(--cl-faint)] focus:border-[var(--cl-accent)] xl:w-[160px]"
        />

        {hasFilters && (
          <button
            type="button"
            onClick={onClear}
            className="h-11 rounded-xl border border-[var(--cl-border)] px-4 text-sm font-medium text-[var(--cl-muted)] transition hover:border-[var(--cl-border-strong)] hover:bg-[var(--cl-surface-soft)] hover:text-[var(--cl-text)]"
          >
            Clear
          </button>
        )}
      </div>
    </div>
  )
}
