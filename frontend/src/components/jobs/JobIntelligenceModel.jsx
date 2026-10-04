import { useCallback, useEffect, useRef, useState } from 'react'

import { fetchSkillGap } from '../../services/api/skillGap'
import SkillGapSection from './SkillGapSection'

function formatScore(score) {
  if (typeof score !== 'number') return '—'
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

function SkillList({ title, skills, tone = 'normal' }) {
  if (!Array.isArray(skills) || skills.length === 0) return null

  const missing = tone === 'missing'

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
              missing
                ? 'border-white/7 bg-white/[0.025] text-white/50'
                : 'border-white/8 bg-white/[0.045] text-white/70',
            ].join(' ')}
          >
            {missing ? '⚠ ' : '✓ '}
            {skill}
          </span>
        ))}
      </div>
    </div>
  )
}

function normalizeEvidenceText(value) {
  return typeof value === 'string'
    ? value.replace(/\s+/g, ' ').trim().toLowerCase()
    : ''
}

function truncateExcerpt(value, maxLength = 240) {
  if (typeof value !== 'string') return ''

  const text = value.replace(/\s+/g, ' ').trim()

  if (text.length <= maxLength) return text

  const shortened = text.slice(0, maxLength)
  const boundary = shortened.lastIndexOf(' ')
  const safeText = boundary > 80 ? shortened.slice(0, boundary) : shortened

  return `${safeText.trim()}...`
}

function isRedundantExcerpt(sourceTitle, excerpt) {
  const normalizedTitle = normalizeEvidenceText(sourceTitle)
  const normalizedExcerpt = normalizeEvidenceText(excerpt)

  if (!normalizedExcerpt) return true
  if (!normalizedTitle) return false
  if (normalizedTitle === normalizedExcerpt) return true

  return (
    normalizedExcerpt.includes(normalizedTitle) &&
    normalizedExcerpt.length <= normalizedTitle.length + 24
  )
}

function formatSourceLabel(sourceType) {
  const labels = {
    skill: 'Technical skills',
    project: 'Project',
    experience: 'Experience',
    education: 'Education',
    certification: 'Certification',
  }

  return labels[sourceType] || sourceType || 'Resume evidence'
}

const SUPPORTING_SOURCE_ORDER = {
  experience: 0,
  project: 1,
  certification: 2,
  education: 3,
  skill: 4,
}

function getEvidenceStrength(item) {
  if (item?.strength === 'direct') return 'direct'
  if (item?.strength === 'supporting') return 'supporting'
  if (item?.source_type === 'skill') return 'direct'

  return 'supporting'
}

function groupEvidenceBySkill(evidence) {
  if (!Array.isArray(evidence)) return []

  const groups = new Map()

  evidence.forEach((item, index) => {
    if (!item || typeof item !== 'object') return

    const skill = typeof item.skill === 'string' ? item.skill.trim() : ''
    const normalizedSkill = normalizeEvidenceText(skill)
    const skillKey = normalizedSkill || `unknown-${index}`

    if (!groups.has(skillKey)) {
      groups.set(skillKey, {
        key: skillKey,
        skill: skill || 'Resume evidence',
        direct: [],
        supporting: [],
      })
    }

    const group = groups.get(skillKey)

    const sourceType =
      typeof item.source_type === 'string' ? item.source_type : ''

    const sourceTitle =
      typeof item.source_title === 'string'
        ? item.source_title.trim()
        : ''

    const excerpt =
      typeof item.excerpt === 'string'
        ? item.excerpt.trim()
        : ''

    const strength = getEvidenceStrength(item)

    const duplicate = [...group.direct, ...group.supporting].some(
      (existing) =>
        normalizeEvidenceText(existing.source_type) ===
          normalizeEvidenceText(sourceType) &&
        normalizeEvidenceText(existing.source_title) ===
          normalizeEvidenceText(sourceTitle) &&
        normalizeEvidenceText(existing.excerpt) ===
          normalizeEvidenceText(excerpt) &&
        existing.strength === strength,
    )

    if (duplicate) return

    const normalizedItem = {
      ...item,
      source_type: sourceType,
      source_title: sourceTitle,
      excerpt,
      strength,
      originalIndex: index,
    }

    if (strength === 'direct') {
      group.direct.push(normalizedItem)
    } else {
      group.supporting.push(normalizedItem)
    }
  })

  return Array.from(groups.values()).map((group) => ({
    ...group,
    supporting: [...group.supporting].sort((left, right) => {
      const leftPriority =
        SUPPORTING_SOURCE_ORDER[left.source_type] ?? 99

      const rightPriority =
        SUPPORTING_SOURCE_ORDER[right.source_type] ?? 99

      if (leftPriority !== rightPriority) {
        return leftPriority - rightPriority
      }

      return left.originalIndex - right.originalIndex
    }),
  }))
}

function EvidenceSource({ item, skill, supporting = false }) {
  const sourceTitle =
    item.source_title || formatSourceLabel(item.source_type)

  const normalizedSkill = normalizeEvidenceText(skill)
  const normalizedExcerpt = normalizeEvidenceText(item.excerpt)

  const excerptIsSameAsSkill =
    normalizedExcerpt &&
    normalizedSkill &&
    normalizedExcerpt === normalizedSkill

  const showExcerpt =
    !excerptIsSameAsSkill &&
    !isRedundantExcerpt(sourceTitle, item.excerpt)

  const excerpt = truncateExcerpt(item.excerpt)

  return (
    <article
      className={[
        'rounded-lg border p-3',
        supporting
          ? 'border-white/7 bg-white/[0.02]'
          : 'border-[#d6b36a]/12 bg-[#d6b36a]/[0.025]',
      ].join(' ')}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-medium leading-5 text-white/75">
            {sourceTitle}
          </p>

          <p className="mt-1 text-[10px] uppercase tracking-[0.14em] text-white/30">
            {formatSourceLabel(item.source_type)}
          </p>
        </div>

        {!supporting && (
          <span className="shrink-0 rounded-full border border-[#d6b36a]/15 px-2 py-1 text-[9px] uppercase tracking-[0.14em] text-[#e5c57c]/75">
            Direct
          </span>
        )}
      </div>

      {showExcerpt && excerpt && (
        <p className="mt-2 text-sm leading-6 text-white/50">
          {excerpt}
        </p>
      )}
    </article>
  )
}

function EvidenceGroup({ group }) {
  return (
    <section className="rounded-xl border border-white/7 bg-white/[0.02] p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="min-w-0">
          <h4 className="text-base font-medium text-white">
            {group.skill}
          </h4>

          <div className="mt-1 flex flex-wrap items-center gap-2">
            {group.direct.length > 0 && (
              <span className="text-[10px] uppercase tracking-[0.14em] text-[#d6b36a]/70">
                Direct evidence
              </span>
            )}

            {group.direct.length > 0 && group.supporting.length > 0 && (
              <span className="text-[10px] text-white/20">·</span>
            )}

            {group.supporting.length > 0 && (
              <span className="text-[10px] uppercase tracking-[0.14em] text-white/30">
                {group.supporting.length} supporting{' '}
                {group.supporting.length === 1 ? 'source' : 'sources'}
              </span>
            )}
          </div>
        </div>

        {group.direct.length > 0 && (
          <span className="rounded-full border border-[#d6b36a]/15 px-2 py-1 text-[10px] uppercase tracking-[0.13em] text-[#e5c57c]">
            Direct
          </span>
        )}
      </div>

      {group.direct.length > 0 && (
        <div className="mt-4 space-y-2">
          {group.direct.map((item, index) => (
            <EvidenceSource
              key={`direct-${item.source_type}-${item.source_title}-${index}`}
              item={item}
              skill={group.skill}
            />
          ))}
        </div>
      )}

      {group.supporting.length > 0 && (
        <div className="mt-4">
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-white/30">
            Supporting evidence
          </p>

          <div className="space-y-2">
            {group.supporting.map((item, index) => (
              <EvidenceSource
                key={`supporting-${item.source_type}-${item.source_title}-${index}`}
                item={item}
                skill={group.skill}
                supporting
              />
            ))}
          </div>
        </div>
      )}
    </section>
  )
}

function AiSection({
  aiExplanation,
  aiLoading,
  aiError,
  onRetryAi,
}) {
  return (
    <section className="rounded-xl border border-sky-300/15 bg-sky-300/[0.035] p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-sky-200/75">
            Grounded AI interpretation
          </p>

          <h3 className="mt-2 text-lg font-medium tracking-[-0.02em] text-white">
            Why it fits
          </h3>
        </div>

        <span className="rounded-full border border-sky-200/15 px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-sky-100/50">
          Supplementary
        </span>
      </div>

      <p className="mt-3 text-xs leading-5 text-sky-100/45">
        This interpretation is based on the deterministic match and resume
        evidence shown below.
      </p>

      {aiLoading ? (
        <div
          className="mt-4 space-y-2"
          aria-live="polite"
          aria-label="Loading AI interpretation"
        >
          <div className="h-3 animate-pulse rounded bg-white/[0.08]" />
          <div className="h-3 w-11/12 animate-pulse rounded bg-white/[0.08]" />
        </div>
      ) : aiError ? (
        <div
          className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"
          role="alert"
        >
          <p className="text-sm leading-6 text-white/50">
            {aiError}
          </p>

          <button
            type="button"
            onClick={onRetryAi}
            className="shrink-0 rounded-lg border border-sky-200/20 px-3 py-2 text-xs font-medium text-sky-100/75 transition hover:bg-sky-200/10 hover:text-white"
          >
            Retry
          </button>
        </div>
      ) : aiExplanation?.why_it_fits ? (
        <p className="mt-4 text-sm leading-7 text-white/65">
          {aiExplanation.why_it_fits}
        </p>
      ) : null}
    </section>
  )
}

export default function JobIntelligenceModel({
  job,
  explanation,
  loading,
  error,
  aiExplanation,
  aiLoading,
  aiError,
  onRetryAi,
  onClose,
}) {
  const closeButtonRef = useRef(null)
  const closeHandlerRef = useRef(onClose)
  const skillGapRequestIdRef = useRef(0)

  const [skillGap, setSkillGap] = useState(null)
  const [skillGapLoading, setSkillGapLoading] = useState(false)
  const [skillGapError, setSkillGapError] = useState('')

  const jobId = job?.id
  const resumeId = explanation?.resume_id

  useEffect(() => {
    closeHandlerRef.current = onClose
  }, [onClose])

  const loadSkillGap = useCallback(
    async (requestResumeId, requestJobId, requestId) => {
      try {
        const result = await fetchSkillGap(
          requestResumeId,
          requestJobId,
        )

        if (requestId !== skillGapRequestIdRef.current) {
          return
        }

        setSkillGap(result)
      } catch (requestError) {
        if (requestId !== skillGapRequestIdRef.current) {
          return
        }

        setSkillGapError(
          requestError?.message ||
            'CareerLens could not load skill-gap analysis.',
        )
      } finally {
        if (requestId === skillGapRequestIdRef.current) {
          setSkillGapLoading(false)
        }
      }
    },
    [],
  )

  useEffect(() => {
    const requestId = ++skillGapRequestIdRef.current

    if (!jobId || !resumeId) {
      setSkillGap(null)
      setSkillGapLoading(false)
      setSkillGapError('')
      return undefined
    }

    setSkillGap(null)
    setSkillGapLoading(true)
    setSkillGapError('')

    void loadSkillGap(
      resumeId,
      jobId,
      requestId,
    )

    return () => {
      skillGapRequestIdRef.current += 1
    }
  }, [jobId, resumeId, loadSkillGap])

  const handleRetrySkillGap = useCallback(() => {
    if (!jobId || !resumeId) {
      return
    }

    const requestId = ++skillGapRequestIdRef.current

    setSkillGap(null)
    setSkillGapLoading(true)
    setSkillGapError('')

    void loadSkillGap(
      resumeId,
      jobId,
      requestId,
    )
  }, [jobId, resumeId, loadSkillGap])

  useEffect(() => {
    if (!jobId) return undefined

    const previousActiveElement = document.activeElement

    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        closeHandlerRef.current?.()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    document.body.style.overflow = 'hidden'
    closeButtonRef.current?.focus()

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = ''

      if (previousActiveElement instanceof HTMLElement) {
        previousActiveElement.focus()
      }
    }
  }, [jobId])

  if (!job) return null

  const dialogTitleId = `job-intelligence-title-${job.id}`
  const evidenceGroups = groupEvidenceBySkill(explanation?.evidence)

  return (
    <div className="fixed inset-0 z-50 bg-black/65">
      <button
        type="button"
        className="absolute inset-0 h-full w-full cursor-default"
        aria-label="Close job intelligence"
        onClick={onClose}
      />

      <aside
        role="dialog"
        aria-modal="true"
        aria-labelledby={dialogTitleId}
        className="cl-scrollbar relative ml-auto flex h-full w-full flex-col overflow-y-auto border-l border-white/10 bg-[#0d131c] shadow-2xl lg:max-w-[680px]"
      >
        <header className="sticky top-0 z-10 border-b border-white/8 bg-[#0d131c]/95 px-5 py-5 backdrop-blur-xl sm:px-7">
          <div className="flex items-start justify-between gap-5">
            <div className="min-w-0">
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#d6b36a]">
                Job intelligence
              </p>

              <h2
                id={dialogTitleId}
                className="mt-2 truncate text-2xl font-medium tracking-[-0.03em] text-white"
              >
                {job.title}
              </h2>

              <p className="mt-1 text-sm text-white/45">
                {job.company || 'Company not specified'}
                {job.location ? ` · ${job.location}` : ''}
              </p>

              <div className="mt-3 flex flex-wrap items-center gap-2">
                {job.source && (
                  <span className="rounded-full border border-white/8 px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-white/45">
                    {job.source}
                  </span>
                )}

                {job.source_url && (
                  <a
                    href={job.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-xs font-medium text-[#d6b36a] underline-offset-4 hover:underline"
                  >
                    Open original job →
                  </a>
                )}
              </div>
            </div>

            <button
              ref={closeButtonRef}
              type="button"
              onClick={onClose}
              className="shrink-0 rounded-lg px-2 py-1 text-xl text-white/45 transition hover:bg-white/5 hover:text-white"
              aria-label="Close job intelligence"
            >
              ×
            </button>
          </div>
        </header>

        <div className="space-y-7 px-5 py-6 sm:px-7">
          {loading ? (
            <div
              className="space-y-4"
              aria-live="polite"
              aria-label="Loading match intelligence"
            >
              <div className="h-28 animate-pulse rounded-xl bg-white/[0.035]" />
              <div className="h-36 animate-pulse rounded-xl bg-white/[0.035]" />
              <div className="h-48 animate-pulse rounded-xl bg-white/[0.035]" />
            </div>
          ) : error ? (
            <div
              className="rounded-xl border border-red-400/15 bg-red-400/[0.04] p-5"
              role="alert"
            >
              <p className="text-sm font-medium text-red-100">
                Could not load match intelligence.
              </p>

              <p className="mt-2 text-sm leading-6 text-red-100/55">
                {error}
              </p>
            </div>
          ) : explanation ? (
            <>
              <section>
                <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-white/35">
                  Match intelligence
                </p>

                <h3 className="mt-2 text-xl font-medium tracking-[-0.02em] text-white">
                  {explanation.match_level
                    ? `${explanation.match_level} alignment`
                    : 'Your match breakdown'}
                </h3>

                <div className="mt-4 grid gap-3 sm:grid-cols-2">
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
                    label="Preferred skills"
                    score={explanation.preferred_skill_score}
                  />

                  <ScoreCard
                    label="Semantic alignment"
                    score={explanation.semantic_score}
                  />
                </div>
              </section>

              <AiSection
                aiExplanation={aiExplanation}
                aiLoading={aiLoading}
                aiError={aiError}
                onRetryAi={onRetryAi}
              />

              <SkillGapSection
                data={skillGap}
                loading={skillGapLoading}
                error={skillGapError}
                onRetry={handleRetrySkillGap}
              />

              <SkillList
                title="Matched preferred skills"
                skills={explanation.matched_preferred_skills}
              />

              <section>
                <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#d6b36a]">
                  Resume evidence
                </p>

                <h3 className="mt-2 text-xl font-medium tracking-[-0.02em] text-white">
                  What in your resume supports this match
                </h3>

                <p className="mt-2 text-xs leading-5 text-white/35">
                  Evidence is grouped by skill, with direct resume evidence
                  separated from supporting project and experience evidence.
                </p>

                <div className="mt-5 space-y-3">
                  {evidenceGroups.length > 0 ? (
                    evidenceGroups.map((group) => (
                      <EvidenceGroup
                        key={group.key}
                        group={group}
                      />
                    ))
                  ) : (
                    <div className="rounded-xl border border-dashed border-white/10 bg-white/[0.02] px-4 py-5 text-sm leading-6 text-white/40">
                      No resume evidence was returned for the matched skills.
                    </div>
                  )}
                </div>
              </section>

              <section className="rounded-xl border border-white/8 bg-white/[0.02] p-5">
                <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-white/35">
                  Next step
                </p>

                {aiExplanation?.next_step ? (
                  <p className="mt-3 text-sm leading-6 text-white/60">
                    {aiExplanation.next_step}
                  </p>
                ) : aiError ? (
                  <p className="mt-3 text-sm leading-6 text-white/40">
                    The structured next step is temporarily unavailable.
                  </p>
                ) : null}
              </section>

              <section>
                <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-white/35">
                  Job description
                </p>

                <p className="mt-3 text-sm leading-6 text-white/50">
                  {job.description || 'No job description was provided.'}
                </p>
              </section>
            </>
          ) : null}
        </div>
      </aside>
    </div>
  )
}