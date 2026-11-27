const STATUS_LABELS = {
  pending: 'Evaluation pending',
  partial: 'Partially evaluated',
  complete: 'Evaluation complete',
}

const SESSION_STATUS_LABELS = {
  created: 'Interview created',
  in_progress: 'Interview in progress',
  completed: 'Interview completed',
}

function getStatusLabel(status) {
  return STATUS_LABELS[status] || 'Evaluation status unavailable'
}

function getStatusStyles(status) {
  if (status === 'complete') {
    return 'border-[var(--cl-success)]/30 bg-[var(--cl-success-soft)] text-[var(--cl-success)]'
  }

  if (status === 'partial') {
    return 'border-[var(--cl-accent)]/30 bg-[var(--cl-accent-soft)] text-[var(--cl-accent)]'
  }

  return 'border-[var(--cl-border)] bg-[var(--cl-surface-muted)] text-[var(--cl-text-soft)]'
}

export default function ScorecardStatus({ scorecardStatus, sessionStatus }) {
  return (
    <div className="flex flex-wrap gap-2" aria-label="Interview status">
      <span
        className={`rounded-full border px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.13em] ${getStatusStyles(scorecardStatus)}`}
      >
        {getStatusLabel(scorecardStatus)}
      </span>

      <span className="rounded-full border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.13em] text-[var(--cl-muted)]">
        {SESSION_STATUS_LABELS[sessionStatus] || 'Session status unavailable'}
      </span>
    </div>
  )
}
