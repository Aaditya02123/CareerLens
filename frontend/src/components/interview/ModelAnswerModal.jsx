import { useState } from 'react'
import {
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  BookOpen,
  X,
  Gauge,
  Flame,
  Check,
} from 'lucide-react'
import { syncInterviewGapsToRoadmap } from '../../services/api/interviewProctoring'

export default function ModelAnswerModal({
  sessionId,
  modelData,
  onClose,
  onRoadmapSynced,
}) {
  const [syncing, setSyncing] = useState(false)
  const [synced, setSynced] = useState(false)
  const [syncMessage, setSyncMessage] = useState('')

  if (!modelData) return null

  const {
    question_text,
    target_competency,
    candidate_answer,
    model_answer,
    missing_critical_nuances = [],
    key_strengths_demonstrated = [],
    delivery_metrics,
  } = modelData

  const handleSyncRoadmap = async () => {
    if (!sessionId || syncing || synced) return
    setSyncing(true)
    setSyncMessage('')

    try {
      const result = await syncInterviewGapsToRoadmap(sessionId)
      setSynced(true)
      setSyncMessage(
        `Added ${result.added_count} target skill milestones to your Learning Roadmap!`
      )
      if (onRoadmapSynced) onRoadmapSynced(result)
    } catch (err) {
      setSyncMessage(err?.message || 'Failed to sync with roadmap.')
    } finally {
      setSyncing(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="relative flex max-h-[90vh] w-full max-w-4xl flex-col overflow-hidden rounded-2xl border border-[var(--cl-border)] bg-[var(--cl-surface)] shadow-2xl">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-[var(--cl-border)] p-5">
          <div className="flex items-center gap-2.5">
            <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-[var(--cl-accent)]/15 text-[var(--cl-accent)]">
              <Sparkles className="h-4 w-4" />
            </span>
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-[var(--cl-accent)]">
                Exemplar Answer Coaching & Gap Analysis
              </p>
              <h2 className="text-base font-medium text-[var(--cl-text)]">
                {target_competency}
              </h2>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-2 text-[var(--cl-muted)] hover:bg-[var(--cl-surface-muted)] hover:text-[var(--cl-text)] transition"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Question Banner */}
          <div className="rounded-xl border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-4">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-[var(--cl-faint)]">
              Question Asked
            </span>
            <p className="mt-1 text-sm font-medium text-[var(--cl-text)]">
              "{question_text}"
            </p>
          </div>

          {/* Delivery & Pacing Telemetry */}
          {delivery_metrics && (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <div className="rounded-xl border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-3">
                <div className="flex items-center gap-1.5 text-xs text-[var(--cl-muted)]">
                  <Gauge className="h-3.5 w-3.5 text-sky-400" />
                  <span>Speaking Rate</span>
                </div>
                <p className="mt-1 text-lg font-semibold text-[var(--cl-text)]">
                  {delivery_metrics.wpm}{' '}
                  <span className="text-xs font-normal text-[var(--cl-muted)]">WPM</span>
                </p>
                <p className="text-[10px] text-[var(--cl-faint)]">{delivery_metrics.pacing_rating}</p>
              </div>

              <div className="rounded-xl border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-3">
                <div className="flex items-center gap-1.5 text-xs text-[var(--cl-muted)]">
                  <Flame className="h-3.5 w-3.5 text-amber-400" />
                  <span>Filler Words</span>
                </div>
                <p className="mt-1 text-lg font-semibold text-[var(--cl-text)]">
                  {delivery_metrics.filler_word_count}
                </p>
                <p className="text-[10px] text-[var(--cl-faint)]">
                  {delivery_metrics.filler_words_detected?.length
                    ? `Detected: "${delivery_metrics.filler_words_detected.slice(0, 3).join(', ')}"`
                    : 'Clean delivery'}
                </p>
              </div>

              <div className="rounded-xl border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-3">
                <div className="flex items-center gap-1.5 text-xs text-[var(--cl-muted)]">
                  <BookOpen className="h-3.5 w-3.5 text-indigo-400" />
                  <span>Word Count</span>
                </div>
                <p className="mt-1 text-lg font-semibold text-[var(--cl-text)]">
                  {delivery_metrics.word_count}
                </p>
                <p className="text-[10px] text-[var(--cl-faint)]">Total response words</p>
              </div>

              <div className="rounded-xl border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-3">
                <div className="flex items-center gap-1.5 text-xs text-[var(--cl-muted)]">
                  <Sparkles className="h-3.5 w-3.5 text-emerald-400" />
                  <span>Clarity Score</span>
                </div>
                <p className="mt-1 text-lg font-semibold text-emerald-400">
                  {delivery_metrics.clarity_score}
                  <span className="text-xs font-normal text-[var(--cl-muted)]">/10</span>
                </p>
                <p className="text-[10px] text-[var(--cl-faint)]">Structure & diction</p>
              </div>
            </div>
          )}

          {/* Two-Column Comparison: Candidate vs Exemplar */}
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            {/* Candidate Answer */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-[var(--cl-muted)]">
                  What You Said
                </span>
                <span className="text-[10px] text-[var(--cl-faint)]">Your Transcript</span>
              </div>
              <div className="rounded-xl border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-4 text-xs leading-6 text-[var(--cl-text-soft)] max-h-60 overflow-y-auto">
                {candidate_answer || (
                  <span className="italic text-[var(--cl-faint)]">No transcript recorded for this turn.</span>
                )}
              </div>
            </div>

            {/* Exemplar Model Answer */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-[var(--cl-accent)]">
                  Exemplar STAR Answer
                </span>
                <span className="rounded-full bg-[var(--cl-accent)]/15 px-2 py-0.5 text-[9px] font-semibold text-[var(--cl-accent)]">
                  Staff-Level Benchmark
                </span>
              </div>
              <div className="rounded-xl border border-[var(--cl-accent)]/30 bg-[var(--cl-accent)]/[0.04] p-4 text-xs leading-6 text-[var(--cl-text)] max-h-60 overflow-y-auto whitespace-pre-line">
                {model_answer}
              </div>
            </div>
          </div>

          {/* Delta & Missing Nuances */}
          <div className="space-y-3">
            <h3 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-amber-400">
              <AlertTriangle className="h-4 w-4" />
              Exact Missing Nuances & Edge Cases
            </h3>
            <div className="space-y-2">
              {missing_critical_nuances.map((nuance, index) => (
                <div
                  key={index}
                  className="flex items-start gap-2.5 rounded-xl border border-amber-500/15 bg-amber-500/5 p-3 text-xs leading-5 text-[var(--cl-text-soft)]"
                >
                  <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-400" />
                  <span>{nuance}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Demonstrated Strengths */}
          {key_strengths_demonstrated.length > 0 && (
            <div className="space-y-3">
              <h3 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-emerald-400">
                <CheckCircle2 className="h-4 w-4" />
                Demonstrated Strengths in Your Answer
              </h3>
              <div className="space-y-2">
                {key_strengths_demonstrated.map((strength, index) => (
                  <div
                    key={index}
                    className="flex items-start gap-2.5 rounded-xl border border-emerald-500/15 bg-emerald-500/5 p-3 text-xs leading-5 text-[var(--cl-text-soft)]"
                  >
                    <Check className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-400" />
                    <span>{strength}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer with 1-Click Roadmap Action */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-5">
          <div>
            {syncMessage ? (
              <p className="text-xs font-medium text-emerald-400">{syncMessage}</p>
            ) : (
              <p className="text-xs text-[var(--cl-muted)]">
                Push weaknesses directly into your CareerLens personalized learning path.
              </p>
            )}
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={handleSyncRoadmap}
              disabled={syncing || synced}
              className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold shadow-sm transition ${
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

            <button
              type="button"
              onClick={onClose}
              className="rounded-xl border border-[var(--cl-border)] px-4 py-2 text-xs font-medium text-[var(--cl-muted)] hover:bg-[var(--cl-surface)] transition"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
