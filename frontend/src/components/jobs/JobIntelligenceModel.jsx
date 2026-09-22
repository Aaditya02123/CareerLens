function formatScore(score) {
  if (typeof score !== 'number') {
    return '—'
  }

  return `${Math.round(score * 100)}%`
}

function ScoreCard({ label, score, accent = false }) {
  return (
    <div className="rounded-xl border border-white/7 bg-white/[0.025] p-4">
      <p className="text-[9px] font-semibold uppercase tracking-[0.16em] text-white/30">
        {label}
      </p>

      <p
        className={[
          'mt-2 text-xl font-medium',
          accent ? 'text-[#e5c57c]' : 'text-white',
        ].join(' ')}
      >
        {formatScore(score)}
      </p>
    </div>
  )
}

function SkillList({
  title,
  skills,
  tone = 'normal',
}) {
  if (!Array.isArray(skills) || skills.length === 0) {
    return null
  }

  const isMissing = tone === 'missing'

  return (
    <div>
      <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-white/30">
        {title}
      </p>

      <div className="flex flex-wrap gap-2">
        {skills.map((skill) => (
          <span
            key={`${title}-${skill}`}
            className={[
              'rounded-md border px-2.5 py-1 text-[11px]',
              isMissing
                ? 'border-white/7 bg-white/[0.025] text-white/50'
                : 'border-white/8 bg-white/[0.045] text-white/70',
            ].join(' ')}
          >
            {isMissing ? '⚠ ' : '✓ '}
            {skill}
          </span>
        ))}
      </div>
    </div>
  )
}

export default function JobIntelligenceModal({
  job,
  explanation,
  loading,
  error,
  onClose,
}) {
  if (!job) {
    return null
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/75 p-4 backdrop-blur-sm lg:items-center">
      <div className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-2xl border border-white/10 bg-[#121212] p-6 shadow-2xl">
        <div className="flex items-start justify-between gap-5">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#d6b36a]">
              Match intelligence
            </p>

            <h2 className="mt-2 text-2xl font-medium tracking-[-0.03em] text-white">
              {job.title}
            </h2>

            <p className="mt-1 text-sm text-white/45">
              {job.company || 'Company not specified'}
              {job.location ? ` · ${job.location}` : ''}
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="rounded-lg px-2 py-1 text-xl text-white/35 transition hover:bg-white/5 hover:text-white"
            aria-label="Close match intelligence"
          >
            ×
          </button>
        </div>

        {loading ? (
          <div className="mt-7 space-y-4">
            <div className="h-24 animate-pulse rounded-xl bg-white/[0.035]" />
            <div className="h-28 animate-pulse rounded-xl bg-white/[0.035]" />
            <div className="h-36 animate-pulse rounded-xl bg-white/[0.035]" />
          </div>
        ) : error ? (
          <div className="mt-7 rounded-xl border border-red-400/15 bg-red-400/[0.04] p-5">
            <p className="text-sm font-medium text-red-100">
              Could not load match intelligence.
            </p>

            <p className="mt-2 text-sm leading-6 text-red-100/55">
              {error}
            </p>
          </div>
        ) : explanation ? (
          <div className="mt-7 space-y-7">
            <section>
              <div className="grid gap-3 sm:grid-cols-3">
                <ScoreCard
                  label="Overall match"
                  score={explanation.hybrid_score}
                  accent
                />

                <ScoreCard
                  label="Required skills"
                  score={explanation.required_skill_score}
                />

                <ScoreCard
                  label="Semantic alignment"
                  score={explanation.semantic_score}
                />
              </div>
            </section>

            <section className="rounded-xl border border-[#d6b36a]/10 bg-[#d6b36a]/[0.025] p-5">
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#d6b36a]">
                Why this role matches
              </p>

              <h3 className="mt-2 text-xl font-medium tracking-[-0.02em] text-white">
                {explanation.match_level
                  ? `${explanation.match_level} alignment`
                  : 'Your match breakdown'}
              </h3>

              <p className="mt-3 text-sm leading-6 text-white/50">
                CareerLens found{' '}
                <span className="text-white/80">
                  {explanation.matched_required_skills?.length || 0}
                </span>{' '}
                matching required skills and{' '}
                <span className="text-white/80">
                  {explanation.missing_required_skills?.length || 0}
                </span>{' '}
                required skill gaps in the current resume analysis.
              </p>
            </section>

            <section className="grid gap-6 sm:grid-cols-2">
              <SkillList
                title="Matched required skills"
                skills={explanation.matched_required_skills}
              />

              <SkillList
                title="Missing required skills"
                skills={explanation.missing_required_skills}
                tone="missing"
              />
            </section>

            <SkillList
              title="Matched preferred skills"
              skills={explanation.matched_preferred_skills}
            />

            {Array.isArray(explanation.primary_factors) &&
              explanation.primary_factors.length > 0 && (
                <section>
                  <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-white/30">
                    Primary matching factors
                  </p>

                  <div className="mt-3 space-y-2">
                    {explanation.primary_factors.map(
                      (factor, index) => (
                        <div
                          key={`${factor}-${index}`}
                          className="rounded-lg border border-white/7 bg-white/[0.02] px-4 py-3 text-sm leading-6 text-white/60"
                        >
                          {factor}
                        </div>
                      )
                    )}
                  </div>
                </section>
              )}
              
              {Array.isArray(explanation.evidence) &&
                explanation.evidence.length > 0 && (
                    <section>
                    <div>
                        <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#d6b36a]">
                        Resume evidence
                        </p>

                        <h3 className="mt-2 text-xl font-medium tracking-[-0.02em] text-white">
                        What in your resume supports this match
                        </h3>

                        <p className="mt-2 max-w-2xl text-sm leading-6 text-white/45">
                        CareerLens found the following evidence in your
                        resume analysis for the skills matched to this role.
                        </p>
                    </div>

                    <div className="mt-5 space-y-3">
                        {explanation.evidence.map((item, index) => (
                        <article
                            key={`${item.skill}-${item.source_type}-${item.source_title}-${index}`}
                            className="rounded-xl border border-white/7 bg-white/[0.02] p-4"
                        >
                            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                            <div>
                                <div className="flex flex-wrap items-center gap-2">
                                <span className="rounded-md border border-[#d6b36a]/15 bg-[#d6b36a]/[0.04] px-2 py-1 text-[11px] font-medium text-[#e5c57c]">
                                    {item.skill}
                                </span>

                                <span className="text-[10px] uppercase tracking-[0.14em] text-white/30">
                                    {item.source_type}
                                </span>
                                </div>

                                <p className="mt-2 text-sm font-medium text-white/75">
                                {item.source_title}
                                </p>
                            </div>

                            <span className="text-[10px] uppercase tracking-[0.14em] text-white/25">
                                {item.strength} evidence
                            </span>
                            </div>

                            <p className="mt-3 text-sm leading-6 text-white/50">
                            {item.excerpt}
                            </p>
                        </article>
                        ))}
                    </div>
                    </section>
                )}

            <section>
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-white/30">
                Job description
              </p>

              <p className="mt-3 text-sm leading-6 text-white/50">
                {job.description ||
                  'No job description was provided.'}
              </p>
            </section>

            {job.source_url && (
              <div className="flex justify-end border-t border-white/7 pt-5">
                <a
                  href={job.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="rounded-xl bg-[#d6b36a] px-4 py-2.5 text-xs font-semibold text-[#17130b] transition hover:bg-[#e3c27e]"
                >
                  Open original job →
                </a>
              </div>
            )}
          </div>
        ) : null}
      </div>
    </div>
  )
}