const PROGRESS_LABELS = {
  not_started: 'Not started',
  in_progress: 'In progress',
  completed: 'Completed',
}

function getProgressStyles(progressStatus) {
  if (progressStatus === 'completed') {
    return 'border-emerald-300/25 bg-emerald-300/[0.06] text-emerald-100/80'
  }

  if (progressStatus === 'in_progress') {
    return 'border-[#d6b36a]/35 bg-[#d6b36a]/[0.07] text-[#f0d18b]'
  }

  if (progressStatus === 'not_started') {
    return 'border-white/10 bg-white/[0.025] text-white/55'
  }

  return 'border-white/10 bg-white/[0.015] text-white/40'
}

function getProgressLabel(progressStatus) {
  return PROGRESS_LABELS[progressStatus] || 'Status unavailable'
}

function getEffortLabel(item) {
  if (
    item?.effort_available === true &&
    Number.isFinite(item.minimum_hours) &&
    Number.isFinite(item.maximum_hours)
  ) {
    return `${item.minimum_hours}–${item.maximum_hours} hours`
  }

  return 'Estimate unavailable'
}

export default function LearningJourneyTimeline({ items }) {
  const safeItems = Array.isArray(items) ? items : []

  return (
    <section
      className="mb-5 rounded-2xl border border-white/8 bg-[#111111] p-5"
      aria-labelledby="learning-journey-heading"
    >
      <div>
        <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#d6b36a]">
          Learning journey
        </p>

        <h3
          id="learning-journey-heading"
          className="mt-2 text-lg font-medium text-white/90"
        >
          Your roadmap path
        </h3>

        <p className="mt-2 text-sm leading-6 text-white/45">
          This overview follows the roadmap order. Search, sorting, and
          progress filters below change the detailed list without changing
          the journey sequence.
        </p>
      </div>

      {safeItems.length === 0 ? (
        <p className="mt-5 rounded-xl border border-white/8 bg-white/[0.02] p-4 text-sm leading-6 text-white/45">
          Your learning journey will appear here when roadmap skills are available.
        </p>
      ) : (
        <ol className="mt-6 space-y-0">
          {safeItems.map((item, index) => {
            const progressStatus = item?.progress_status
            const progressLabel = getProgressLabel(progressStatus)
            const isLast = index === safeItems.length - 1

            return (
              <li
                key={item?.id ?? `${item?.skill || 'skill'}-${index}`}
                className="relative flex gap-4"
              >
                <div className="flex w-5 shrink-0 flex-col items-center">
                  <span
                    className={[
                      'mt-1 flex h-5 w-5 items-center justify-center rounded-full border text-[10px] font-semibold',
                      getProgressStyles(progressStatus),
                    ].join(' ')}
                    aria-label={`${item?.skill || 'Skill'}: ${progressLabel}`}
                  >
                    {progressStatus === 'completed' ? '✓' : index + 1}
                  </span>

                  {!isLast && (
                    <span
                      className="mt-1 min-h-12 w-px flex-1 bg-white/10"
                      aria-hidden="true"
                    />
                  )}
                </div>

                <div className="min-w-0 flex-1 pb-6">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <h4 className="break-words text-sm font-medium text-white/85">
                        {item?.skill || 'Unnamed skill'}
                      </h4>

                      <div className="mt-2 flex flex-wrap gap-2 text-[10px] uppercase tracking-[0.12em]">
                        <span
                          className={[
                            'rounded-full border px-2 py-1',
                            getProgressStyles(progressStatus),
                          ].join(' ')}
                        >
                          {progressLabel}
                        </span>

                        <span className="rounded-full border border-white/10 px-2 py-1 text-white/45">
                          {item?.priority || 'unknown'} priority
                        </span>

                        <span className="rounded-full border border-white/10 px-2 py-1 text-white/45">
                          {item?.status || 'unknown'} gap
                        </span>
                      </div>
                    </div>

                    <span className="text-xs text-white/40">
                      {getEffortLabel(item)}
                    </span>
                  </div>
                </div>
              </li>
            )
          })}
        </ol>
      )}
    </section>
  )
}
