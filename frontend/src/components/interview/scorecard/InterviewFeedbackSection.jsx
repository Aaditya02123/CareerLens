function FeedbackColumn({ title, items, tone }) {
  const safeItems = Array.isArray(items) ? items.filter(Boolean) : []

  return (
    <div className="rounded-xl border border-white/8 bg-white/[0.02] p-4">
      <h4 className="text-sm font-medium text-white/80">{title}</h4>
      {safeItems.length === 0 ? (
        <p className="mt-3 text-sm leading-6 text-white/40">
          No {tone} recorded yet.
        </p>
      ) : (
        <ul className="mt-3 space-y-2">
          {safeItems.map((item) => (
            <li key={item} className="text-sm leading-6 text-white/55">
              <span className="mr-2 text-[#d6b36a]" aria-hidden="true">•</span>
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
  return (
    <section
      className="rounded-2xl border border-white/8 bg-[#111111] p-5 sm:p-6"
      aria-labelledby="interview-feedback-heading"
    >
      <div>
        <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#d6b36a]">
          Candidate feedback
        </p>
        <h3
          id="interview-feedback-heading"
          className="mt-2 text-lg font-medium text-white/90"
        >
          Keep building from the evidence
        </h3>
        <p className="mt-2 text-sm leading-6 text-white/45">
          These notes reflect the submitted answers and rubric feedback. They
          are practice guidance, not a hiring decision.
        </p>
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
