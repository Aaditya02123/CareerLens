function formatResourceType(resourceType) {
  return String(resourceType || 'resource').replaceAll('_', ' ')
}

export default function RoadmapResourceSection({
  resourceKey,
  resourceData,
  resourceLoading,
  resourceError,
  isExpanded,
  onToggle,
  onRetry,
}) {
  const resourceSectionId = `roadmap-resources-${resourceKey}`
  const resources = Array.isArray(resourceData?.resources)
    ? resourceData.resources
    : []

  return (
    <div className="mt-5 border-t border-white/8 pt-4">
      <button
        type="button"
        aria-expanded={isExpanded}
        aria-controls={resourceSectionId}
        onClick={onToggle}
        className="flex w-full items-center justify-between gap-3 text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-[#d6b36a]/70"
      >
        <span className="text-[10px] font-semibold uppercase tracking-[0.16em] text-[#d6b36a]">
          Learning resources
        </span>

        <span className="text-xs text-white/40">
          {isExpanded ? 'Hide resources' : 'Explore resources'}
        </span>
      </button>

      <div
        id={resourceSectionId}
        className="mt-4"
        aria-live="polite"
        hidden={!isExpanded}
      >
        {resourceLoading ? (
          <div
            className="rounded-xl border border-white/8 bg-white/[0.025] p-4"
            aria-label="Loading learning resources"
          >
            <div className="h-4 w-2/3 animate-pulse rounded bg-white/[0.08]" />
            <div className="mt-3 h-3 w-1/3 animate-pulse rounded bg-white/[0.06]" />
          </div>
        ) : resourceError ? (
          <div
            className="rounded-xl border border-red-300/15 bg-red-300/[0.035] p-4"
            role="alert"
          >
            <p className="text-xs leading-5 text-red-100/70">
              Learning resources are temporarily unavailable.
            </p>

            <p className="mt-1 text-[11px] leading-5 text-red-100/45">
              {resourceError}
            </p>

            <button
              type="button"
              onClick={onRetry}
              className="mt-3 rounded-lg border border-red-200/20 px-3 py-2 text-xs font-medium text-red-100/75 transition hover:bg-red-200/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-red-200/70"
            >
              Retry
            </button>
          </div>
        ) : resources.length === 0 ? (
          <div className="rounded-xl border border-white/8 bg-white/[0.02] p-4">
            <p className="text-xs leading-5 text-white/50">
              No curated learning resources are currently available for this skill.
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {resources.map((resource) => (
              <article
                key={resource.id}
                className="rounded-xl border border-white/8 bg-white/[0.02] p-4"
              >
                <a
                  href={resource.url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-sm font-medium text-[#e5c57c]/90 underline-offset-4 hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-[#d6b36a]/70"
                >
                  {resource.title || 'Learning resource'}
                </a>

                <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-white/40">
                  <span>{resource.provider || 'Unknown provider'}</span>
                  <span>{formatResourceType(resource.resource_type)}</span>
                  <span>{resource.level || 'Level unavailable'}</span>
                </div>
              </article>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
