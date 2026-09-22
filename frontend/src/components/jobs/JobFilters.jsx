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
    <div className="border-b border-white/8 bg-[#101010] px-5 py-5">
      <div className="flex flex-col gap-3 xl:flex-row xl:items-center">
        <div className="relative flex-1">
          <span className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-sm text-white/35">
            ⌕
          </span>

          <input
            type="text"
            value={search}
            onChange={(event) =>
              onSearchChange(event.target.value)
            }
            placeholder="Search job titles..."
            className="h-11 w-full rounded-xl border border-white/8 bg-white/[0.035] pl-10 pr-4 text-sm text-white outline-none transition placeholder:text-white/30 focus:border-[#d6b36a]/50 focus:bg-white/[0.05]"
          />
        </div>

        <div className="relative flex-1 xl:max-w-[220px]">
          <span className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-sm text-white/35">
            ◇
          </span>

          <input
            type="text"
            value={location}
            onChange={(event) =>
              onLocationChange(event.target.value)
            }
            placeholder="Location"
            className="h-11 w-full rounded-xl border border-white/8 bg-white/[0.035] pl-10 pr-4 text-sm text-white outline-none transition placeholder:text-white/30 focus:border-[#d6b36a]/50 focus:bg-white/[0.05]"
          />
        </div>

        <select
          value={experienceLevel}
          onChange={(event) =>
            onExperienceChange(event.target.value)
          }
          className="h-11 rounded-xl border border-white/8 bg-[#151515] px-4 text-sm text-white/70 outline-none transition focus:border-[#d6b36a]/50 xl:w-[190px]"
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
          className="h-11 rounded-xl border border-white/8 bg-white/[0.035] px-4 text-sm text-white outline-none transition placeholder:text-white/30 focus:border-[#d6b36a]/50 focus:bg-white/[0.05] xl:w-[160px]"
        />

        {hasFilters && (
          <button
            type="button"
            onClick={onClear}
            className="h-11 rounded-xl border border-white/8 px-4 text-sm text-white/55 transition hover:border-white/15 hover:bg-white/[0.04] hover:text-white"
          >
            Clear
          </button>
        )}
      </div>
    </div>
  )
}