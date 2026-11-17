import CompetencyBreakdown from './CompetencyBreakdown'
import InterviewFeedbackSection from './InterviewFeedbackSection'
import QuestionEvaluationList from './QuestionEvaluationList'
import ScorecardOverview from './ScorecardOverview'

export default function InterviewScorecard({
  scorecard,
  session,
  expandedId,
  evaluatingAnswerId,
  evaluationErrors,
  onToggleQuestion,
  onEvaluateAnswer,
}) {
  const actionableFeedback = Array.from(
    new Set(
      (Array.isArray(scorecard?.answer_evaluations)
        ? scorecard.answer_evaluations
        : []
      ).flatMap((evaluation) =>
        Array.isArray(evaluation?.actionable_feedback)
          ? evaluation.actionable_feedback
          : [],
      ),
    ),
  )

  return (
    <div className="space-y-5">
      <ScorecardOverview scorecard={scorecard} session={session} />

      <div className="grid gap-5 xl:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)]">
        <CompetencyBreakdown competencies={scorecard?.competency_scores} />
        <InterviewFeedbackSection
          scorecard={scorecard}
          actionableFeedback={actionableFeedback}
        />
      </div>

      <QuestionEvaluationList
        session={session}
        scorecard={scorecard}
        expandedId={expandedId}
        evaluatingAnswerId={evaluatingAnswerId}
        evaluationErrors={evaluationErrors}
        onToggle={onToggleQuestion}
        onEvaluate={onEvaluateAnswer}
      />
    </div>
  )
}
