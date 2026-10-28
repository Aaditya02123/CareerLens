import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react'

import { fetchJobs } from '../../services/api/jobs'
import { fetchUserResumes } from '../../services/api/resumes'
import {
  fetchLearningRoadmap,
  updateLearningRoadmapProgress,
} from '../../services/api/learningRoadmap'

const PROGRESS_OPTIONS = [
  {
    value: 'not_started',
    label: 'Not started',
  },
  {
    value: 'in_progress',
    label: 'In progress',
  },
  {
    value: 'completed',
    label: 'Completed',
  },
]

function sortResumesNewestFirst(resumes) {
  return [...resumes].sort((first, second) => {
    const firstTime = new Date(
      first.created_at || 0,
    ).getTime()

    const secondTime = new Date(
      second.created_at || 0,
    ).getTime()

    if (secondTime !== firstTime) {
      return secondTime - firstTime
    }

    return (second.id || 0) - (first.id || 0)
  })
}

function getProgressLabel(progressStatus) {
  return (
    PROGRESS_OPTIONS.find(
      (option) => option.value === progressStatus,
    )?.label || progressStatus
  )
}

function getStatusStyles(status) {
  if (status === 'missing') {
    return 'border-red-300/15 bg-red-300/[0.035] text-red-100/75'
  }

  return 'border-amber-300/15 bg-amber-300/[0.035] text-amber-100/75'
}

function RoadmapItem({
  item,
  isUpdating,
  updateError,
  onProgressChange,
}) {
  return (
    <article className="rounded-2xl border border-white/8 bg-[#111111] p-5">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="break-words text-base font-medium text-white/90">
              {item.skill}
            </h3>

            <span
              className={[
                'rounded-full border px-2 py-1 text-[10px] uppercase tracking-[0.13em]',
                getStatusStyles(item.status),
              ].join(' ')}
            >
              {item.status}
            </span>

            <span className="rounded-full border border-white/10 px-2 py-1 text-[10px] uppercase tracking-[0.13em] text-white/45">
              {item.priority} priority
            </span>
          </div>

          <p className="mt-3 text-sm leading-6 text-white/50">
            {item.reason}
          </p>
        </div>

        <div className="shrink-0">
          <label
            htmlFor={`roadmap-progress-${item.id}`}
            className="block text-[10px] font-semibold uppercase tracking-[0.16em] text-white/35"
          >
            Progress
          </label>

          <select
            id={`roadmap-progress-${item.id}`}
            value={item.progress_status}
            onChange={(event) =>
              onProgressChange(
                item.id,
                event.target.value,
              )
            }
            disabled={isUpdating}
            className="mt-2 min-w-[150px] rounded-lg border border-white/10 bg-[#0b0b0b] px-3 py-2 text-xs text-white/75 outline-none transition focus:border-[#d6b36a]/60 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {PROGRESS_OPTIONS.map((option) => (
              <option
                key={option.value}
                value={option.value}
              >
                {option.label}
              </option>
            ))}
          </select>

          <p className="mt-2 text-right text-[11px] text-white/30">
            {isUpdating
              ? 'Saving...'
              : getProgressLabel(item.progress_status)}
          </p>
        </div>
      </div>

      {updateError && (
        <p
          className="mt-3 text-xs leading-5 text-red-200/75"
          role="alert"
        >
          {updateError}
        </p>
      )}
    </article>
  )
}

export default function RoadmapWorkspace() {
  const [resume, setResume] = useState(null)
  const [jobs, setJobs] = useState([])
  const [selectedJobId, setSelectedJobId] = useState('')

  const [resumeLoading, setResumeLoading] = useState(true)
  const [jobsLoading, setJobsLoading] = useState(true)
  const [resumeError, setResumeError] = useState('')
  const [jobsError, setJobsError] = useState('')

  const [roadmap, setRoadmap] = useState(null)
  const [roadmapLoading, setRoadmapLoading] = useState(false)
  const [roadmapError, setRoadmapError] = useState('')
  const [roadmapRetryKey, setRoadmapRetryKey] = useState(0)

  const [updatingItems, setUpdatingItems] = useState({})
  const [progressErrors, setProgressErrors] = useState({})

  const roadmapRequestIdRef = useRef(0)
  const progressRequestIdsRef = useRef(new Map())
  const selectedJobIdRef = useRef('')

  selectedJobIdRef.current = selectedJobId

  const selectedJob = useMemo(() => {
    return (
      jobs.find(
        (job) => String(job.id) === selectedJobId,
      ) || null
    )
  }, [jobs, selectedJobId])

  const invalidateRoadmap = useCallback(() => {
    roadmapRequestIdRef.current += 1
    setRoadmap(null)
    setRoadmapError('')
    setRoadmapLoading(false)
    setUpdatingItems({})
    setProgressErrors({})
  }, [])

  const loadResume = useCallback(async () => {
    setResumeLoading(true)
    setResumeError('')

    try {
      const resumes = await fetchUserResumes()
      const orderedResumes = sortResumesNewestFirst(
        Array.isArray(resumes) ? resumes : [],
      )

      setResume(orderedResumes[0] || null)
    } catch (error) {
      setResume(null)
      setResumeError(
        error?.message ||
          'CareerLens could not load your resume.',
      )
    } finally {
      setResumeLoading(false)
    }
  }, [])

  const loadJobs = useCallback(async () => {
    setJobsLoading(true)
    setJobsError('')

    try {
      const jobList = await fetchJobs({
        limit: 50,
      })

      const nextJobs = Array.isArray(jobList)
        ? jobList
        : []

      const currentSelectedJobId =
        selectedJobIdRef.current

      if (
        currentSelectedJobId &&
        !nextJobs.some(
          (job) =>
            String(job.id) === currentSelectedJobId,
        )
      ) {
        invalidateRoadmap()
        setSelectedJobId('')
      }

      setJobs(nextJobs)
    } catch (error) {
      setJobs([])
      invalidateRoadmap()
      setSelectedJobId('')

      setJobsError(
        error?.message ||
          'CareerLens could not load available jobs.',
      )
    } finally {
      setJobsLoading(false)
    }
  }, [invalidateRoadmap])

  useEffect(() => {
    void loadResume()
    void loadJobs()
  }, [loadJobs, loadResume])

  useEffect(() => {
    const requestId = ++roadmapRequestIdRef.current

    setRoadmap(null)
    setRoadmapError('')
    setUpdatingItems({})
    setProgressErrors({})

    if (!resume?.id || !selectedJob?.id) {
      setRoadmapLoading(false)
      return
    }

    setRoadmapLoading(true)

    fetchLearningRoadmap(
      resume.id,
      selectedJob.id,
    )
      .then((response) => {
        if (
          requestId !== roadmapRequestIdRef.current
        ) {
          return
        }

        setRoadmap(response)
      })
      .catch((error) => {
        if (
          requestId !== roadmapRequestIdRef.current
        ) {
          return
        }

        setRoadmapError(
          error?.message ||
            'CareerLens could not load this learning roadmap.',
        )
      })
      .finally(() => {
        if (
          requestId === roadmapRequestIdRef.current
        ) {
          setRoadmapLoading(false)
        }
      })
  }, [
    resume,
    selectedJob,
    roadmapRetryKey,
  ])

  function handleJobChange(event) {
    invalidateRoadmap()
    setSelectedJobId(event.target.value)
  }

  function handleRetryRoadmap() {
    setRoadmapRetryKey((current) => current + 1)
  }

  async function handleProgressChange(
    itemId,
    nextStatus,
  ) {
    const roadmapRequestIdAtRequest =
      roadmapRequestIdRef.current

    const nextRequestId =
      (progressRequestIdsRef.current.get(itemId) ||
        0) + 1

    progressRequestIdsRef.current.set(
      itemId,
      nextRequestId,
    )

    const isCurrentProgressRequest = () =>
      progressRequestIdsRef.current.get(itemId) ===
        nextRequestId &&
      roadmapRequestIdRef.current ===
        roadmapRequestIdAtRequest

    setUpdatingItems((current) => ({
      ...current,
      [itemId]: true,
    }))

    setProgressErrors((current) => ({
      ...current,
      [itemId]: '',
    }))

    try {
      const updatedItem =
        await updateLearningRoadmapProgress(
          itemId,
          nextStatus,
        )

      if (!isCurrentProgressRequest()) {
        return
      }

      setRoadmap((current) => {
        if (!current) {
          return current
        }

        return {
          ...current,
          roadmap: current.roadmap.map((item) =>
            item.id === updatedItem.id
              ? {
                  ...item,
                  progress_status:
                    updatedItem.progress_status,
                }
              : item,
          ),
        }
      })
    } catch (error) {
      if (!isCurrentProgressRequest()) {
        return
      }

      setProgressErrors((current) => ({
        ...current,
        [itemId]:
          error?.message ||
          'Progress could not be updated. Please try again.',
      }))
    } finally {
      if (!isCurrentProgressRequest()) {
        setUpdatingItems((current) => {
            const next = { ...current }
            delete next[itemId]
            return next
        })
      }
    }
  }

  const roadmapItems = Array.isArray(
    roadmap?.roadmap,
  )
    ? roadmap.roadmap
    : []

  const hasResume = Boolean(resume)
  const hasJobs = jobs.length > 0

  return (
    <section className="min-h-full bg-[#0a0a0a] text-white">
      <div className="mx-auto max-w-[1100px] px-6 py-7 lg:px-8">
        <header className="mb-7">
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.22em] text-[#d6b36a]">
            Learning intelligence
          </p>

          <h1 className="text-3xl font-medium tracking-[-0.035em]">
            Learning roadmap
          </h1>

          <p className="mt-2 max-w-2xl text-sm leading-6 text-white/45">
            Turn the remaining skill gaps for a target role
            into a focused, trackable learning plan.
          </p>
        </header>

        <section className="rounded-2xl border border-white/8 bg-[#111111] p-5">
          <div className="grid gap-5 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#d6b36a]">
                Resume context
              </p>

              {resumeLoading ? (
                <div
                  className="mt-3 h-10 animate-pulse rounded-lg bg-white/[0.06]"
                  aria-label="Loading resume"
                />
              ) : resumeError ? (
                <div className="mt-3" role="alert">
                  <p className="text-sm text-red-200/75">
                    {resumeError}
                  </p>

                  <button
                    type="button"
                    onClick={loadResume}
                    className="mt-3 rounded-lg border border-white/10 px-3 py-2 text-xs text-white/65 transition hover:border-[#d6b36a]/40 hover:text-white"
                  >
                    Try again
                  </button>
                </div>
              ) : !hasResume ? (
                <p className="mt-3 text-sm leading-6 text-white/45">
                  Upload a resume before creating a
                  personalized roadmap.
                </p>
              ) : (
                <p className="mt-3 truncate text-sm text-white/75">
                  {resume.original_filename ||
                    'Latest resume'}
                </p>
              )}
            </div>

            <div>
              <label
                htmlFor="roadmap-target-job"
                className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#d6b36a]"
              >
                Target job
              </label>

              {jobsLoading ? (
                <div
                  className="mt-3 h-10 animate-pulse rounded-lg bg-white/[0.06]"
                  aria-label="Loading jobs"
                />
              ) : jobsError ? (
                <div className="mt-3" role="alert">
                  <p className="text-sm text-red-200/75">
                    {jobsError}
                  </p>

                  <button
                    type="button"
                    onClick={loadJobs}
                    className="mt-3 rounded-lg border border-white/10 px-3 py-2 text-xs text-white/65 transition hover:border-[#d6b36a]/40 hover:text-white"
                  >
                    Try again
                  </button>
                </div>
              ) : !hasJobs ? (
                <p className="mt-3 text-sm leading-6 text-white/45">
                  No jobs are available to use as a target.
                </p>
              ) : (
                <select
                  id="roadmap-target-job"
                  value={selectedJobId}
                  onChange={handleJobChange}
                  className="mt-3 w-full rounded-lg border border-white/10 bg-[#0b0b0b] px-3 py-2.5 text-sm text-white/75 outline-none transition focus:border-[#d6b36a]/60"
                >
                  <option value="">
                    Select a target job
                  </option>

                  {jobs.map((job) => (
                    <option
                      key={job.id}
                      value={job.id}
                    >
                      {job.title || 'Untitled role'}
                      {job.company
                        ? ` — ${job.company}`
                        : ''}
                    </option>
                  ))}
                </select>
              )}
            </div>
          </div>
        </section>

        {!resumeLoading && !hasResume && (
          <section className="mt-6 rounded-2xl border border-[#d6b36a]/15 bg-[#d6b36a]/[0.035] p-6">
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#d6b36a]">
              Resume required
            </p>

            <h2 className="mt-2 text-lg font-medium">
              Upload a resume to unlock your roadmap.
            </h2>

            <p className="mt-2 text-sm leading-6 text-white/45">
              CareerLens uses the latest analyzed resume to
              identify skills that need attention for a
              selected job.
            </p>
          </section>
        )}

        {!jobsLoading && hasResume && hasJobs && !selectedJob && (
          <section className="mt-6 rounded-2xl border border-white/8 bg-[#111111] p-6">
            <p className="text-sm font-medium text-white/75">
              Choose a target job to view your roadmap.
            </p>

            <p className="mt-2 text-sm leading-6 text-white/40">
              Select a role above and CareerLens will load
              the persisted learning plan for that match.
            </p>
          </section>
        )}

        {selectedJob && (
          <section
            className="mt-6"
            aria-live="polite"
            aria-busy={roadmapLoading}
          >
            <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-white/30">
                  Target roadmap
                </p>

                <h2 className="mt-1 text-xl font-medium tracking-[-0.025em]">
                  {selectedJob.title ||
                    'Selected opportunity'}
                </h2>
              </div>

              {roadmap && (
                <span className="text-xs text-white/35">
                  {roadmap.total_items} skill
                  {roadmap.total_items === 1
                    ? ''
                    : 's'} to work on
                </span>
              )}
            </div>

            {roadmapLoading ? (
              <div
                className="space-y-3"
                aria-label="Loading learning roadmap"
              >
                {[1, 2].map((item) => (
                  <div
                    key={item}
                    className="h-32 animate-pulse rounded-2xl border border-white/6 bg-white/[0.025]"
                  />
                ))}
              </div>
            ) : roadmapError ? (
              <div
                className="rounded-2xl border border-red-300/15 bg-red-300/[0.035] p-6"
                role="alert"
              >
                <p className="text-sm text-red-100/80">
                  Unable to load this learning roadmap.
                </p>

                <p className="mt-2 text-xs leading-5 text-red-100/55">
                  {roadmapError}
                </p>

                <button
                  type="button"
                  onClick={handleRetryRoadmap}
                  className="mt-4 rounded-lg border border-red-200/20 px-3 py-2 text-xs font-medium text-red-100/75 transition hover:bg-red-200/10"
                >
                  Retry
                </button>
              </div>
            ) : roadmapItems.length === 0 ? (
              <div className="rounded-2xl border border-emerald-300/15 bg-emerald-300/[0.035] p-6">
                <p className="text-sm font-medium text-emerald-100/80">
                  No learning gaps are currently listed.
                </p>

                <p className="mt-2 text-sm leading-6 text-white/40">
                  Keep building evidence for the skills you
                  already match and revisit this roadmap as
                  your target changes.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {roadmapItems.map((item) => (
                  <RoadmapItem
                    key={item.id}
                    item={item}
                    isUpdating={Boolean(
                      updatingItems[item.id],
                    )}
                    updateError={
                      progressErrors[item.id] || ''
                    }
                    onProgressChange={
                      handleProgressChange
                    }
                  />
                ))}
              </div>
            )}
          </section>
        )}
      </div>
    </section>
  )
}