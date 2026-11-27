import { useState } from 'react'
import { Sparkles, Check } from 'lucide-react'
import { syncInterviewGapsToRoadmap } from '../../../services/api/interviewProctoring'

function FeedbackColumn({ title, items, tone }) {
  const safeItems = Array.isArray(items) ? items.filter(Boolean) : []

  return (
    <div className="rounded-xl border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-4">
      <h4 className="text-sm font-medium text-[var(--cl-text)]">{title}</h4>
      {safeItems.length === 0 ? (
        <p className="mt-3 text-sm leading-6 text-[var(--cl-muted)]">
          No {tone} recorded yet.
        </p>
      ) : (
        <ul className="mt-3 space-y-2">
          {safeItems.map((item) => (
            <li key={item} className="text-sm leading-6 text-[var(--cl-text-soft)]">
              <span className="mr-2 text-[var(--cl-accent)]" aria-hidden="true">•</span>
              {item}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default function InterviewFeedbackSection({
  scorecard,
  actionableFeedback,
}) {
  const [syncing, setSyncing] = useState(false)
  const [synced, setSynced] = useState(false)
  const [syncMsg, setSyncMsg] = useState('')

  const handleSyncRoadmap = async () => {
    if (!scorecard?.session_id || syncing || synced) return
    setSyncing(true)
    setSyncMsg('')

    try {
      const res = await syncInterviewGapsToRoadmap(scorecard.session_id)
      setSynced(true)
      setSyncMsg(`Added ${res.added_count} targeted gaps to your roadmap!`)
    } catch (err) {
      setSyncMsg(err?.message || 'Sync failed.')
    } finally {
      setSyncing(false)
    }
  }

  return (
    <section
      className="rounded-2xl border border-[var(--cl-border)] bg-[var(--cl-surface)] p-5 sm:p-6"
      aria-labelledby="interview-feedback-heading"
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--cl-accent)]">
            Candidate feedback & action
          </p>
          <h3
            id="interview-feedback-heading"
            className="mt-2 text-lg font-medium text-[var(--cl-text)]"
          >
            Keep building from the evidence
          </h3>
          <p className="mt-2 text-sm leading-6 text-[var(--cl-muted)]">
            These notes reflect submitted answers and rubric evaluations.
          </p>
        </div>

        {scorecard?.session_id && (
          <div className="flex flex-col items-end gap-1">
            <button
              type="button"
              onClick={handleSyncRoadmap}
              disabled={syncing || synced}
              className={`flex items-center gap-1.5 rounded-xl px-3.5 py-2 text-xs font-semibold shadow-sm transition ${
                synced
                  ? 'bg-emerald-500 text-white cursor-default'
                  : 'bg-[var(--cl-accent)] text-[var(--cl-accent-contrast)] hover:opacity-95'
              }`}
            >
              {synced ? (
                <>
                  <Check className="h-3.5 w-3.5" />
                  Synced to Roadmap
                </>
              ) : syncing ? (
                'Syncing...'
              ) : (
                <>
                  <Sparkles className="h-3.5 w-3.5" />
                  Add Weaknesses to My Roadmap
                </>
              )}
            </button>
            {syncMsg && <span className="text-[10px] text-emerald-400 font-medium">{syncMsg}</span>}
          </div>
        )}
      </div>

      <div className="mt-5 grid gap-3 lg:grid-cols-3">
        <FeedbackColumn title="Strengths" items={scorecard?.strengths} tone="strengths" />
        <FeedbackColumn title="Areas to improve" items={scorecard?.improvement_areas} tone="improvement areas" />
        <FeedbackColumn
          title="Next practice focus"
          items={actionableFeedback}
          tone="practice suggestions"
        />
      </div>
    </section>
  )
}
