const STATUS_CONTENT = {
  not_configured: {
    label: 'Using defaults',
    description:
      'Save your preferences to compare this projection with your own availability.',
    className: 'border-white/10 bg-white/[0.025] text-white/65',
  },
  no_estimate: {
    label: 'Estimate unavailable',
    description:
      'Some remaining skills do not have a reliable effort estimate yet.',
    className: 'border-white/10 bg-white/[0.025] text-white/65',
  },
  completed: {
    label: 'Roadmap complete',
    description: 'There is no remaining estimated learning work in this roadmap.',
    className: 'border-emerald-300/20 bg-emerald-300/[0.045] text-emerald-100/80',
  },
  no_target_date: {
    label: 'No target date',
    description:
      'Add a target date to see whether the projected effort fits your timeline.',
    className: 'border-amber-300/20 bg-amber-300/[0.04] text-amber-100/80',
  },
  on_track: {
    label: 'On track',
    description:
      'The projected maximum effort fits before your target completion date.',
    className: 'border-emerald-300/20 bg-emerald-300/[0.045] text-emerald-100/80',
  },
  at_risk: {
    label: 'At risk',
    description:
      'The projected maximum effort extends beyond your target completion date.',
    className: 'border-amber-300/20 bg-amber-300/[0.04] text-amber-100/80',
  },
}
function formatDate(value) {
  if (!value) return 'Not set'

  const date = new Date(`${value}T00:00:00`)

  if (Number.isNaN(date.getTime())) return 'Date unavailable'

  return new Intl.DateTimeFormat(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(date)
}

function SummaryMetric({ label, value }) {
  return (
    <div className="rounded-xl border border-white/8 bg-white/[0.025] p-3">
      <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-white/35">
        {label}
      </p>
      <p className="mt-2 text-lg font-medium text-white/85">{value}</p>
    </div>
  )
}

export default function RoadmapScheduleSummary({
  schedule,
  loading,
  error,
  onRetry,
}) {
  if (loading) {
    return (
      <section
        className="mb-5 rounded-2xl border border-white/8 bg-[#111111] p-5"
        aria-labelledby="roadmap-schedule-heading"
        aria-busy="true"
      >
        <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#d6b36a]">
          Personalized schedule
        </p>
        <h3
          id="roadmap-schedule-heading"
          className="mt-2 text-lg font-medium text-white/90"
        >
          Loading schedule
        </h3>
        <div
          className="mt-5 h-24 animate-pulse rounded-xl bg-white/[0.04]"
          aria-label="Loading roadmap schedule"
        />
      </section>
    )
  }

  if (error) {
    return (
      <section
        className="mb-5 rounded-2xl border border-red-300/15 bg-red-300/[0.035] p-5"
        aria-labelledby="roadmap-schedule-heading"
        role="alert"
      >
        <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-red-200/75">
          Personalized schedule
        </p>
        <h3
          id="roadmap-schedule-heading"
          className="mt-2 text-lg font-medium text-red-100/90"
        >
          Schedule temporarily unavailable
        </h3>
        <p className="mt-2 text-sm leading-6 text-red-100/60">{error}</p>
        <button
          type="button"
          onClick={onRetry}
          className="mt-4 rounded-lg border border-red-200/20 px-3 py-2 text-xs font-medium text-red-100/75 transition hover:bg-red-200/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-red-200/70"
        >
          Retry schedule
        </button>
      </section>
    )
  }

  if (!schedule) {
    return null
  }

  const status = STATUS_CONTENT[schedule.schedule_status] || {
    label: 'Status unavailable',
    description:
      'The backend returned an unrecognized schedule status. Review the roadmap estimates directly.',
    className: 'border-white/10 bg-white/[0.025] text-white/65',
  }
  const hasRemainingEffort =
    Number.isFinite(schedule.remaining_minimum_hours) &&
    Number.isFinite(schedule.remaining_maximum_hours) &&
    (schedule.remaining_minimum_hours > 0 ||
      schedule.remaining_maximum_hours > 0)

  return (
    <section
      className="mb-5 rounded-2xl border border-white/8 bg-[#111111] p-5"
      aria-labelledby="roadmap-schedule-heading"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#d6b36a]">
            Personalized schedule
          </p>
          <h3
            id="roadmap-schedule-heading"
            className="mt-2 text-lg font-medium text-white/90"
          >
            Your learning projection
          </h3>
        </div>

        <span
          className={`rounded-full border px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.13em] ${status.className}`}
        >
          {status.label}
        </span>
      </div>

      <p className="mt-3 max-w-2xl text-sm leading-6 text-white/50">
        {status.description}
      </p>

      <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <SummaryMetric
          label="Weekly availability"
          value={`${schedule.weekly_hours || 0} hrs`}
        />
        <SummaryMetric
          label="Remaining effort"
          value={
            hasRemainingEffort
              ? `${schedule.remaining_minimum_hours}–${schedule.remaining_maximum_hours} hrs`
              : '0 hrs'
          }
        />
        <SummaryMetric
          label="Estimated duration"
          value={
            hasRemainingEffort
              ? `${schedule.estimated_minimum_weeks}–${schedule.estimated_maximum_weeks} wks`
              : 'Complete'
          }
        />
        <SummaryMetric
          label="Pace"
          value={schedule.pace || 'Unavailable'}
        />
      </div>

      <div className="mt-4 flex flex-wrap gap-x-5 gap-y-2 text-xs text-white/40">
        <span>
          Preferences: {schedule.configured ? 'saved' : 'default values'}
        </span>
        <span>
          Target date: {formatDate(schedule.target_completion_date)}
        </span>
      </div>

      <p className="mt-4 text-xs leading-5 text-white/35">
        This is an indicative projection based on available weekly hours,
        not a guaranteed completion time.
      </p>
    </section>
  )
}
