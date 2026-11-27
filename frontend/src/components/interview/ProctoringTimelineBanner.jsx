import { useEffect, useState } from 'react'
import {
  ShieldAlert,
  ShieldCheck,
  Clock,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'
import { fetchProctoringSummary } from '../../services/api/interviewProctoring'

export default function ProctoringTimelineBanner({ sessionId }) {
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(false)
  const [expanded, setExpanded] = useState(false)

  useEffect(() => {
    if (!sessionId) return

    let isMounted = true
    setLoading(true)

    fetchProctoringSummary(sessionId)
      .then((data) => {
        if (isMounted) setSummary(data)
      })
      .catch(() => {})
      .finally(() => {
        if (isMounted) setLoading(false)
      })

    return () => {
      isMounted = false
    }
  }, [sessionId])

  if (loading || !summary) return null

  const {
    integrity_score,
    status,
    total_events,
    timeline = [],
  } = summary

  const isClean = status === 'clean'
  const isFlagged = status === 'flagged'

  return (
    <div className="rounded-2xl border border-[var(--cl-border)] bg-[var(--cl-surface)] p-5 shadow-[var(--shadow-soft)] space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div
            className={`flex h-10 w-10 items-center justify-center rounded-xl ${
              isClean
                ? 'bg-emerald-500/15 text-emerald-400'
                : isFlagged
                ? 'bg-red-500/15 text-red-400'
                : 'bg-amber-500/15 text-amber-400'
            }`}
          >
            {isClean ? (
              <ShieldCheck className="h-5 w-5" />
            ) : (
              <ShieldAlert className="h-5 w-5" />
            )}
          </div>

          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-semibold uppercase tracking-[0.16em] text-[var(--cl-faint)]">
                Berri Proctor Verification
              </span>
              <span
                className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${
                  isClean
                    ? 'bg-emerald-500/10 text-emerald-400'
                    : isFlagged
                    ? 'bg-red-500/10 text-red-400'
                    : 'bg-amber-500/10 text-amber-400'
                }`}
              >
                {status.replace('_', ' ')}
              </span>
            </div>

            <h3 className="text-sm font-medium text-[var(--cl-text)] mt-0.5">
              Integrity Score: {integrity_score}/100{' '}
              <span className="text-xs font-normal text-[var(--cl-muted)]">
                ({total_events} telemetry {total_events === 1 ? 'event' : 'events'} logged)
              </span>
            </h3>
          </div>
        </div>

        {timeline.length > 0 && (
          <button
            type="button"
            onClick={() => setExpanded((prev) => !prev)}
            className="flex items-center gap-1.5 rounded-xl border border-[var(--cl-border)] px-3 py-1.5 text-xs font-medium text-[var(--cl-text-soft)] hover:bg-[var(--cl-surface-muted)] transition"
          >
            <span>{expanded ? 'Hide Audit Log' : 'View Integrity Audit Timeline'}</span>
            {expanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
          </button>
        )}
      </div>

      {/* Expanded Timeline */}
      {expanded && timeline.length > 0 && (
        <div className="border-t border-[var(--cl-border)] pt-4 space-y-3 animate-fade-in">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[var(--cl-muted)]">
            Chronological Telemetry Log
          </p>

          <div className="space-y-2 max-h-56 overflow-y-auto">
            {timeline.map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between rounded-xl border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] px-3.5 py-2.5 text-xs"
              >
                <div className="flex items-center gap-2.5">
                  <span
                    className={`h-2 w-2 rounded-full ${
                      item.severity === 'high'
                        ? 'bg-red-400'
                        : item.severity === 'medium'
                        ? 'bg-amber-400'
                        : 'bg-zinc-400'
                    }`}
                  />
                  <span className="font-medium text-[var(--cl-text)]">{item.label}</span>
                  {item.details?.duration_ms && (
                    <span className="text-[10px] text-[var(--cl-muted)] font-mono">
                      ({Math.round(item.details.duration_ms / 1000)}s away)
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-2 text-[10px] text-[var(--cl-faint)]">
                  <Clock className="h-3 w-3" />
                  <span>{new Date(item.timestamp).toLocaleTimeString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
