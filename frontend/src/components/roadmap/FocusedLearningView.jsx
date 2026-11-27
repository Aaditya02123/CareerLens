import RoadmapResourceSection from './RoadmapResourceSection'

function hasAvailableEffort(item) {
  return (
    item?.effort_available === true &&
    Number.isFinite(item.minimum_hours) &&
    Number.isFinite(item.maximum_hours)
  )
}

function getStatusStyles(status) {
  if (status === 'missing') {
    return 'border-red-300/15 bg-red-300/[0.035] text-red-100/75'
  }

  return 'border-amber-300/15 bg-amber-300/[0.035] text-amber-100/75'
}

export default function FocusedLearningView({
  item,
  isUpdating,
  updateError,
  onProgressChange,
  resourceData,
  resourceLoading,
  resourceError,
  isResourcesExpanded,
  onToggleResources,
  onRetryResources,
  onBack,
}) {
  const effortAvailable = hasAvailableEffort(item)

  return (
    <section
      className="mt-6 rounded-2xl border border-[var(--cl-accent-soft)] bg-[var(--cl-surface)] p-5 sm:p-7"
      aria-labelledby="focused-learning-heading"
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--cl-accent)]">
            Focused learning
          </p>

          <h2
            id="focused-learning-heading"
            className="mt-2 text-2xl font-medium tracking-[-0.03em] text-[var(--cl-text)]"
          >
            {item.skill || 'Unnamed skill'}
          </h2>
        </div>

        <button
          type="button"
          onClick={onBack}
          className="rounded-lg border border-[var(--cl-border)] px-3 py-2 text-xs font-medium text-[var(--cl-text-soft)] transition hover:border-[var(--cl-accent)] hover:text-[var(--cl-text)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--cl-accent)]"
        >
          Back to roadmap
        </button>
      </div>

      <div className="mt-5 flex flex-wrap gap-2">
        <span className="rounded-full border border-[var(--cl-border)] px-2 py-1 text-[10px] uppercase tracking-[0.13em] text-[var(--cl-text-soft)]">
          {item.priority || 'unknown'} priority
        </span>

        <span
          className={[
            'rounded-full border px-2 py-1 text-[10px] uppercase tracking-[0.13em]',
            getStatusStyles(item.status),
          ].join(' ')}
        >
          {item.status || 'unknown'}
        </span>
      </div>

      <p className="mt-5 max-w-2xl text-sm leading-6 text-[var(--cl-text-soft)]">
        {item.reason || 'No reason was provided.'}
      </p>

      <div className="mt-6 rounded-xl border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-4">
        <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-[var(--cl-faint)]">
          Estimated effort
        </p>

        {effortAvailable ? (
          <p className="mt-2 text-lg font-medium text-[var(--cl-accent)]/90">
            {item.minimum_hours}–{item.maximum_hours} hours
          </p>
        ) : (
          <p className="mt-2 text-sm text-[var(--cl-muted)]">
            Estimate unavailable
          </p>
        )}
      </div>

      <div className="mt-6 rounded-xl border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-[var(--cl-faint)]">
              Current progress
            </p>
            <p className="mt-2 text-sm text-[var(--cl-text-soft)]">
              {item.progress_status === 'completed'
                ? 'Completed'
                : item.progress_status === 'in_progress'
                  ? 'In progress'
                  : item.progress_status === 'not_started'
                    ? 'Not started'
                    : 'Status unavailable'}
            </p>
          </div>

          <label className="sr-only" htmlFor={`focused-progress-${item.id}`}>
            Update progress for {item.skill || 'this skill'}
          </label>

          <select
            id={`focused-progress-${item.id}`}
            value={item.progress_status || ''}
            onChange={(event) =>
              onProgressChange(item.id, event.target.value)
            }
            disabled={isUpdating}
            className="min-w-[160px] rounded-lg border border-[var(--cl-border)] bg-[var(--cl-input-bg)] px-3 py-2 text-xs text-[var(--cl-text-soft)] outline-none transition focus:border-[var(--cl-accent)] disabled:cursor-not-allowed disabled:opacity-50"
          >
            <option value="not_started">Not started</option>
            <option value="in_progress">In progress</option>
            <option value="completed">Completed</option>
          </select>
        </div>

        {isUpdating && (
          <p className="mt-3 text-xs text-[var(--cl-faint)]">Saving progress...</p>
        )}

        {updateError && (
          <p className="mt-3 text-xs leading-5 text-red-200/75" role="alert">
            {updateError}
          </p>
        )}
      </div>

      {item.progress_status === 'completed' && (
        <p className="mt-4 rounded-xl border border-emerald-300/15 bg-emerald-300/[0.035] p-4 text-sm leading-6 text-emerald-100/75">
          This skill is complete. Return to the roadmap to see the next recommendation.
        </p>
      )}

      <RoadmapResourceSection
        resourceKey={`focused-${item.id}`}
        resourceData={resourceData}
        resourceLoading={resourceLoading}
        resourceError={resourceError}
        isExpanded={isResourcesExpanded}
        onToggle={onToggleResources}
        onRetry={onRetryResources}
      />
    </section>
  )
}
