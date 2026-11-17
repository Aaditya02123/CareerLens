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
    return 'border-emerald-300/20 bg-emerald-300/[0.06] text-emerald-100/80'
  }

  if (status === 'partial') {
    return 'border-[#d6b36a]/30 bg-[#d6b36a]/[0.06] text-[#f0d18b]'
  }

  return 'border-white/10 bg-white/[0.025] text-white/55'
}

export default function ScorecardStatus({ scorecardStatus, sessionStatus }) {
  return (
    <div className="flex flex-wrap gap-2" aria-label="Interview status">
      <span
        className={`rounded-full border px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.13em] ${getStatusStyles(scorecardStatus)}`}
      >
        {getStatusLabel(scorecardStatus)}
      </span>

      <span className="rounded-full border border-white/10 bg-white/[0.02] px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.13em] text-white/50">
        {SESSION_STATUS_LABELS[sessionStatus] || 'Session status unavailable'}
      </span>
    </div>
  )
}
