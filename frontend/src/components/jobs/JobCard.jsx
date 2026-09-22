function formatScore(score) {
  if (typeof score !== 'number') {
    return null
  }

  return `${Math.round(score * 100)}%`
}

function MatchIndicator({ score }) {
  const percentage = Math.round((score || 0) * 100)

  return (
    <div className="flex items-center gap-3">
      <div className="h-1.5 w-20 overflow-hidden rounded-full bg-white/8">
        <div
          className="h-full rounded-full bg-[#d6b36a] transition-all"
          style={{ width: `${percentage}%` }}
        />
      </div>

      <span className="text-sm font-medium text-[#e5c57c]">
        {percentage}%
      </span>
    </div>
  )
}

function SkillChip({ children, muted = false }) {
  return (
    <span
      className={[
        'rounded-md border px-2.5 py-1 text-[11px]',
        muted
          ? 'border-white/7 bg-white/[0.025] text-white/45'
          : 'border-white/8 bg-white/[0.045] text-white/65',
      ].join(' ')}
    >
      {children}
    </span>
  )
}

export default function JobCard({
  job,
  recommendation,
  onSelect,
}) {
  const matchScore = recommendation?.hybrid_score ?? null
  const matchedSkills =
    recommendation?.matched_required_skills ?? []
  const missingSkills =
    recommendation?.missing_required_skills ?? []

  return (
    <article className="group rounded-2xl border border-white/8 bg-[#111111] p-5 transition duration-200 hover:-translate-y-0.5 hover:border-white/14 hover:bg-[#141414]">
      <div className="flex flex-col gap-5">
        <div className="flex items-start justify-between gap-5">
          <div className="min-w-0">
            <div className="mb-2 flex flex-wrap items-center gap-2">
              {recommendation?.rank && (
                <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#d6b36a]">
                  #{recommendation.rank} for you
                </span>
              )}

              {job.source && (
                <span className="rounded-full border border-white/7 bg-white/[0.025] px-2 py-0.5 text-[10px] text-white/35">
                  {job.source}
                </span>
              )}
            </div>

            <h3 className="truncate text-lg font-medium tracking-[-0.02em] text-white">
              {job.title}
            </h3>

            <p className="mt-1 text-sm text-white/45">
              {job.company || 'Company not specified'}
              {job.location ? ` · ${job.location}` : ''}
            </p>
          </div>

          {matchScore !== null && (
            <div className="shrink-0 text-right">
              <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-white/30">
                Match
              </div>

              <MatchIndicator score={matchScore} />
            </div>
          )}
        </div>

        {(matchedSkills.length > 0 ||
          missingSkills.length > 0) && (
          <div className="space-y-3">
            {matchedSkills.length > 0 && (
              <div>
                <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-white/30">
                  Matched skills
                </p>

                <div className="flex flex-wrap gap-2">
                  {matchedSkills.slice(0, 6).map((skill) => (
                    <SkillChip key={`matched-${skill}`}>
                      ✓ {skill}
                    </SkillChip>
                  ))}
                </div>
              </div>
            )}

            {missingSkills.length > 0 && (
              <div>
                <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-white/30">
                  Skill gap
                </p>

                <div className="flex flex-wrap gap-2">
                  {missingSkills.slice(0, 5).map((skill) => (
                    <SkillChip
                      key={`missing-${skill}`}
                      muted
                    >
                      {skill}
                    </SkillChip>
                  ))}

                  {missingSkills.length > 5 && (
                    <span className="px-1 py-1 text-[11px] text-white/30">
                      +{missingSkills.length - 5} more
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        <div className="flex items-center justify-between border-t border-white/7 pt-4">
          <div className="flex gap-5 text-xs text-white/35">
            {recommendation?.semantic_score !== undefined && (
              <span>
                Semantic{' '}
                <strong className="font-medium text-white/55">
                  {formatScore(
                    recommendation.semantic_score
                  )}
                </strong>
              </span>
            )}

            {recommendation?.required_skill_score !==
              undefined && (
              <span>
                Skills{' '}
                <strong className="font-medium text-white/55">
                  {formatScore(
                    recommendation.required_skill_score
                  )}
                </strong>
              </span>
            )}
          </div>

          <button
            type="button"
            onClick={() => onSelect?.(job)}
            className="text-xs font-medium text-[#d6b36a] transition group-hover:translate-x-0.5"
          >
            View intelligence →
          </button>
        </div>
      </div>
    </article>
  )
}