import QuestionEvaluationCard from './QuestionEvaluationCard'

function getPendingAnswers(session, evaluations, pendingAnswerIds) {
  const safeAnswers = Array.isArray(session?.answers) ? session.answers : []
  const evaluatedIds = new Set(
    (Array.isArray(evaluations) ? evaluations : []).map(
      (evaluation) => evaluation.answer_id,
    ),
  )
  const pendingIds = Array.isArray(pendingAnswerIds) ? pendingAnswerIds : []

  return safeAnswers.filter(
    (answer) =>
      pendingIds.includes(answer.id) && !evaluatedIds.has(answer.id),
  )
}

export default function QuestionEvaluationList({
  session,
  scorecard,
  expandedId,
  evaluatingAnswerId,
  evaluationErrors,
  onToggle,
  onEvaluate,
}) {
  const evaluations = Array.isArray(scorecard?.answer_evaluations)
    ? [...scorecard.answer_evaluations].sort(
        (first, second) =>
          Number(first.conversation_order ?? first.question_order ?? 0) -
          Number(second.conversation_order ?? second.question_order ?? 0),
      )
    : []
  const pendingAnswers = getPendingAnswers(
    session,
    evaluations,
    scorecard?.pending_answer_ids,
  )

  return (
    <section aria-labelledby="question-evaluations-heading">
      <div>
        <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#d6b36a]">
          Question review
        </p>
        <h3
          id="question-evaluations-heading"
          className="mt-2 text-lg font-medium text-white/90"
        >
          Question-by-question evaluation
        </h3>
      </div>

      {evaluations.length === 0 && pendingAnswers.length === 0 ? (
        <div className="mt-5 rounded-xl border border-white/8 bg-white/[0.02] p-5">
          <p className="text-sm leading-6 text-white/45">
            No submitted answers are available for evaluation yet.
          </p>
        </div>
      ) : (
        <div className="mt-5 space-y-3">
          {evaluations.map((evaluation) => (
            <QuestionEvaluationCard
              key={evaluation.answer_id}
              evaluation={evaluation}
              isExpanded={expandedId === `evaluation-${evaluation.answer_id}`}
              isEvaluating={evaluatingAnswerId === evaluation.answer_id}
              error={evaluationErrors?.[evaluation.answer_id]}
              onToggle={() => onToggle(`evaluation-${evaluation.answer_id}`)}
              onEvaluate={() => onEvaluate(evaluation.answer_id)}
            />
          ))}

          {pendingAnswers.map((answer) => (
            <QuestionEvaluationCard
              key={answer.id}
              pendingAnswer={answer}
              isExpanded={expandedId === `pending-${answer.id}`}
              isEvaluating={evaluatingAnswerId === answer.id}
              error={evaluationErrors?.[answer.id]}
              onToggle={() => onToggle(`pending-${answer.id}`)}
              onEvaluate={() => onEvaluate(answer.id)}
            />
          ))}
        </div>
      )}
    </section>
  )
}
