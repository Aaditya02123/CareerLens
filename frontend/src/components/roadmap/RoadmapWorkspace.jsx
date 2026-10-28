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
  { value: 'not_started', label: 'Not started' },
  { value: 'in_progress', label: 'In progress' },
  { value: 'completed', label: 'Completed' },
]

const ROADMAP_FILTERS = [
  { value: 'all', label: 'All' },
  { value: 'not_started', label: 'Not started' },
  { value: 'in_progress', label: 'In progress' },
  { value: 'completed', label: 'Completed' },
]

const SORT_OPTIONS = [
  { value: 'default', label: 'Default order' },
  { value: 'skill_asc', label: 'Skill name A–Z' },
  { value: 'priority', label: 'Priority' },
  { value: 'progress', label: 'Progress status' },
]

const PRIORITY_ORDER = {
  high: 0,
  medium: 1,
  low: 2,
}

const PROGRESS_ORDER = {
  not_started: 0,
  in_progress: 1,
  completed: 2,
}

function sortResumesNewestFirst(resumes) {
  return [...resumes].sort((first, second) => {
    const firstTime = new Date(first.created_at || 0).getTime()
    const secondTime = new Date(second.created_at || 0).getTime()

    if (secondTime !== firstTime) {
      return secondTime - firstTime
    }

    return (second.id || 0) - (first.id || 0)
  })
}

function isKnownProgressStatus(progressStatus) {
  return PROGRESS_OPTIONS.some(
    (option) => option.value === progressStatus,
  )
}

function getProgressLabel(progressStatus) {
  return (
    PROGRESS_OPTIONS.find(
      (option) => option.value === progressStatus,
    )?.label || 'Status unavailable'
  )
}

function getFilterLabel(filterValue) {
  return (
    ROADMAP_FILTERS.find(
      (filter) => filter.value === filterValue,
    )?.label || 'selected'
  )
}

function getStatusStyles(status) {
  if (status === 'missing') {
    return 'border-red-300/15 bg-red-300/[0.035] text-red-100/75'
  }

  return 'border-amber-300/15 bg-amber-300/[0.035] text-amber-100/75'
}

function getProgressSummary(items) {
  const safeItems = Array.isArray(items) ? items : []
  const total = safeItems.length

  const completed = safeItems.filter(
    (item) => item?.progress_status === 'completed',
  ).length

  const inProgress = safeItems.filter(
    (item) => item?.progress_status === 'in_progress',
  ).length

  const notStarted = safeItems.filter(
    (item) => item?.progress_status === 'not_started',
  ).length

  const completionPercentage =
    total === 0
      ? 0
      : Math.round((completed / total) * 100)

  return {
    total,
    completed,
    inProgress,
    notStarted,
    completionPercentage,
  }
}

function getProgressFilterCounts(items) {
  const safeItems = Array.isArray(items) ? items : []

  return {
    all: safeItems.length,
    not_started: safeItems.filter(
      (item) => item?.progress_status === 'not_started',
    ).length,
    in_progress: safeItems.filter(
      (item) => item?.progress_status === 'in_progress',
    ).length,
    completed: safeItems.filter(
      (item) => item?.progress_status === 'completed',
    ).length,
  }
}

function SummaryMetric({ label, value }) {
  return (
    <div className="rounded-xl border border-white/8 bg-white/[0.025] p-3">
      <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-white/35">
        {label}
      </p>

      <p className="mt-2 text-xl font-medium text-white/85">
        {value}
      </p>
    </div>
  )
}

function RoadmapProgressSummary({ summary }) {
  return (
    <section
      className="mb-5 rounded-2xl border border-[#d6b36a]/15 bg-[#d6b36a]/[0.035] p-5"
      aria-labelledby="roadmap-progress-summary-heading"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#d6b36a]">
            Progress overview
          </p>

          <h3
            id="roadmap-progress-summary-heading"
            className="mt-2 text-lg font-medium text-white/90"
          >
            Learning roadmap progress
          </h3>
        </div>

        <span className="text-sm font-medium text-[#e5c57c]/85">
          {summary.completionPercentage}% complete
        </span>
      </div>

      <div className="mt-5">
        <div
          className="h-2 overflow-hidden rounded-full bg-white/10"
          role="progressbar"
          aria-label="Roadmap completion progress"
          aria-valuemin="0"
          aria-valuemax="100"
          aria-valuenow={summary.completionPercentage}
        >
          <div
            className="h-full rounded-full bg-[#d6b36a] transition-[width]"
            style={{
              width: `${summary.completionPercentage}%`,
            }}
          />
        </div>

        <p className="mt-2 text-xs text-white/40">
          {summary.completed} of {summary.total} skill
          {summary.total === 1 ? '' : 's'} completed
        </p>
      </div>

      <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <SummaryMetric
          label="Total skills"
          value={summary.total}
        />

        <SummaryMetric
          label="Completed"
          value={summary.completed}
        />

        <SummaryMetric
          label="In progress"
          value={summary.inProgress}
        />

        <SummaryMetric
          label="Not started"
          value={summary.notStarted}
        />
      </div>

      {summary.total === 0 && (
        <p className="mt-4 text-sm leading-6 text-white/45">
          There are no roadmap items to track for this job yet.
        </p>
      )}
    </section>
  )
}

function RoadmapProgressFilters({
  selectedFilter,
  filterCounts,
  onFilterChange,
}) {
  return (
    <div
      className="mb-5 flex flex-wrap gap-2"
      role="group"
      aria-label="Filter roadmap items by progress"
    >
      {ROADMAP_FILTERS.map((filter) => {
        const isSelected =
          selectedFilter === filter.value

        return (
          <button
            key={filter.value}
            type="button"
            aria-pressed={isSelected}
            onClick={() =>
              onFilterChange(filter.value)
            }
            className={[
              'rounded-full border px-3 py-2 text-xs font-medium transition',
              isSelected
                ? 'border-[#d6b36a]/50 bg-[#d6b36a]/12 text-[#f0d18b]'
                : 'border-white/10 bg-white/[0.02] text-white/50 hover:border-white/20 hover:text-white/80',
            ].join(' ')}
          >
            {filter.label}
            <span
              className={
                isSelected
                  ? 'ml-2 text-[#f0d18b]/80'
                  : 'ml-2 text-white/30'
              }
            >
              {filterCounts[filter.value]}
            </span>
          </button>
        )
      })}
    </div>
  )
}

function RoadmapSearchAndSort({
  searchQuery,
  sortOption,
  onSearchChange,
  onSortChange,
}) {
  return (
    <div className="mb-5 grid gap-3 md:grid-cols-[minmax(0,1fr)_220px]">
      <div>
        <label
          htmlFor="roadmap-search"
          className="block text-[10px] font-semibold uppercase tracking-[0.16em] text-white/35"
        >
          Search skills
        </label>

        <input
          id="roadmap-search"
          type="search"
          value={searchQuery}
          onChange={(event) =>
            onSearchChange(event.target.value)
          }
          placeholder="Search by skill name"
          className="mt-2 w-full rounded-lg border border-white/10 bg-[#0b0b0b] px-3 py-2.5 text-sm text-white/75 outline-none placeholder:text-white/25 focus:border-[#d6b36a]/60"
        />
      </div>

      <div>
        <label
          htmlFor="roadmap-sort"
          className="block text-[10px] font-semibold uppercase tracking-[0.16em] text-white/35"
        >
          Sort roadmap
        </label>

        <select
          id="roadmap-sort"
          value={sortOption}
          onChange={(event) =>
            onSortChange(event.target.value)
          }
          className="mt-2 w-full rounded-lg border border-white/10 bg-[#0b0b0b] px-3 py-2.5 text-sm text-white/75 outline-none focus:border-[#d6b36a]/60"
        >
          {SORT_OPTIONS.map((option) => (
            <option
              key={option.value}
              value={option.value}
            >
              {option.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  )
}

function RoadmapItem({
  item,
  isUpdating,
  updateError,
  onProgressChange,
}) {
  const hasKnownStatus = isKnownProgressStatus(
    item.progress_status,
  )

  return (
    <article className="rounded-2xl border border-white/8 bg-[#111111] p-5">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="break-words text-base font-medium text-white/90">
              {item.skill || 'Unnamed skill'}
            </h3>

            <span
              className={[
                'rounded-full border px-2 py-1 text-[10px] uppercase tracking-[0.13em]',
                getStatusStyles(item.status),
              ].join(' ')}
            >
              {item.status || 'unknown'}
            </span>

            <span className="rounded-full border border-white/10 px-2 py-1 text-[10px] uppercase tracking-[0.13em] text-white/45">
              {item.priority || 'unknown'} priority
            </span>
          </div>

          <p className="mt-3 text-sm leading-6 text-white/50">
            {item.reason || 'No reason was provided.'}
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
            value={
              hasKnownStatus
                ? item.progress_status
                : ''
            }
            onChange={(event) =>
              onProgressChange(
                item.id,
                event.target.value,
              )
            }
            disabled={isUpdating}
            className="mt-2 min-w-[150px] rounded-lg border border-white/10 bg-[#0b0b0b] px-3 py-2 text-xs text-white/75 outline-none transition focus:border-[#d6b36a]/60 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {!hasKnownStatus && (
              <option value="" disabled>
                Status unavailable
              </option>
            )}

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

  const [selectedFilter, setSelectedFilter] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [sortOption, setSortOption] = useState('default')
  const [updatingItems, setUpdatingItems] = useState({})
  const [progressErrors, setProgressErrors] = useState({})

  const roadmapRequestIdRef = useRef(0)
  const progressRequestIdsRef = useRef(new Map())
  const selectedJobIdRef = useRef('')

  selectedJobIdRef.current = selectedJobId

  const selectedJob = useMemo(
    () =>
      jobs.find(
        (job) => String(job.id) === selectedJobId,
      ) || null,
    [jobs, selectedJobId],
  )

  const roadmapItems = Array.isArray(roadmap?.roadmap)
    ? roadmap.roadmap
    : []

  const progressSummary = useMemo(
    () => getProgressSummary(roadmapItems),
    [roadmapItems],
  )

  const progressFilterCounts = useMemo(
    () => getProgressFilterCounts(roadmapItems),
    [roadmapItems],
  )

  const filteredAndSortedRoadmapItems = useMemo(() => {
    const normalizedQuery = searchQuery
      .trim()
      .toLowerCase()

    const matchingItems = roadmapItems.filter((item) => {
      const matchesProgressFilter =
        selectedFilter === 'all' ||
        item?.progress_status === selectedFilter

      const skillName = String(
        item?.skill || '',
      ).toLowerCase()

      const matchesSearch =
        !normalizedQuery ||
        skillName.includes(normalizedQuery)

      return matchesProgressFilter && matchesSearch
    })

    if (sortOption === 'default') {
      return matchingItems
    }

    const indexedItems = matchingItems.map(
      (item, index) => ({
        item,
        index,
      }),
    )

    indexedItems.sort((first, second) => {
      if (sortOption === 'skill_asc') {
        const firstSkill = String(
          first.item?.skill || '',
        ).toLowerCase()
        const secondSkill = String(
          second.item?.skill || '',
        ).toLowerCase()

        if (firstSkill !== secondSkill) {
          if (!firstSkill) {
            return 1
          }

          if (!secondSkill) {
            return -1
          }

          return firstSkill.localeCompare(secondSkill)
        }
      }

      if (sortOption === 'priority') {
        const firstPriority =
          PRIORITY_ORDER[first.item?.priority] ?? 99
        const secondPriority =
          PRIORITY_ORDER[second.item?.priority] ?? 99

        if (firstPriority !== secondPriority) {
          return firstPriority - secondPriority
        }
      }

      if (sortOption === 'progress') {
        const firstProgress =
          PROGRESS_ORDER[
            first.item?.progress_status
          ] ?? 99
        const secondProgress =
          PROGRESS_ORDER[
            second.item?.progress_status
          ] ?? 99

        if (firstProgress !== secondProgress) {
          return firstProgress - secondProgress
        }
      }

      return first.index - second.index
    })

    return indexedItems.map(({ item }) => item)
  }, [
    roadmapItems,
    searchQuery,
    selectedFilter,
    sortOption,
  ])

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
      const jobList = await fetchJobs({ limit: 50 })
      const nextJobs = Array.isArray(jobList) ? jobList : []
      const currentSelectedJobId =
        selectedJobIdRef.current

      if (
        currentSelectedJobId &&
        !nextJobs.some(
          (job) => String(job.id) === currentSelectedJobId,
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
    setSelectedFilter('all')
    setSearchQuery('')
    setSortOption('default')
    setUpdatingItems({})
    setProgressErrors({})

    if (!resume?.id || !selectedJob?.id) {
      setRoadmapLoading(false)
      return
    }

    setRoadmapLoading(true)

    fetchLearningRoadmap(resume.id, selectedJob.id)
      .then((response) => {
        if (requestId !== roadmapRequestIdRef.current) {
          return
        }

        setRoadmap(response)
      })
      .catch((error) => {
        if (requestId !== roadmapRequestIdRef.current) {
          return
        }

        setRoadmapError(
          error?.message ||
            'CareerLens could not load this learning roadmap.',
        )
      })
      .finally(() => {
        if (requestId === roadmapRequestIdRef.current) {
          setRoadmapLoading(false)
        }
      })
  }, [resume, selectedJob, roadmapRetryKey])

  function handleJobChange(event) {
    invalidateRoadmap()
    setSelectedFilter('all')
    setSearchQuery('')
    setSortOption('default')
    setSelectedJobId(event.target.value)
  }

  function handleRetryRoadmap() {
    setRoadmapRetryKey((current) => current + 1)
  }

  async function handleProgressChange(itemId, nextStatus) {
    const roadmapRequestIdAtRequest =
      roadmapRequestIdRef.current

    const nextRequestId =
      (progressRequestIdsRef.current.get(itemId) || 0) + 1

    progressRequestIdsRef.current.set(itemId, nextRequestId)

    const isCurrentProgressRequest = () =>
      progressRequestIdsRef.current.get(itemId) ===
        nextRequestId &&
      roadmapRequestIdRef.current === roadmapRequestIdAtRequest

    setUpdatingItems((current) => ({
      ...current,
      [itemId]: true,
    }))

    setProgressErrors((current) => ({
      ...current,
      [itemId]: '',
    }))

    try {
      const updatedItem = await updateLearningRoadmapProgress(
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
            String(item.id) === String(updatedItem.id)
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
      if (isCurrentProgressRequest()) {
        setUpdatingItems((current) => {
          const next = { ...current }
          delete next[itemId]
          return next
        })
      }
    }
  }

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
                  {resume.original_filename || 'Latest resume'}
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
                  <option value="">Select a target job</option>

                  {jobs.map((job) => (
                    <option key={job.id} value={job.id}>
                      {job.title || 'Untitled role'}
                      {job.company ? ` — ${job.company}` : ''}
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
              identify skills that need attention for a selected
              job.
            </p>
          </section>
        )}

        {!jobsLoading && hasResume && hasJobs && !selectedJob && (
          <section className="mt-6 rounded-2xl border border-white/8 bg-[#111111] p-6">
            <p className="text-sm font-medium text-white/75">
              Choose a target job to view your roadmap.
            </p>

            <p className="mt-2 text-sm leading-6 text-white/40">
              Select a role above and CareerLens will load the
              persisted learning plan for that match.
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
                  {selectedJob.title || 'Selected opportunity'}
                </h2>
              </div>

              {roadmap && (
                <span className="text-xs text-white/35">
                  {roadmap.total_items} skill
                  {roadmap.total_items === 1 ? '' : 's'} to work on
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
                    className="h-32 rounded-2xl border border-white/6 bg-white/[0.025] animate-pulse"
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
            ) : roadmap ? (
              <>
                <RoadmapProgressSummary
                  summary={progressSummary}
                />

                <RoadmapProgressFilters
                  selectedFilter={selectedFilter}
                  filterCounts={progressFilterCounts}
                  onFilterChange={setSelectedFilter}
                />

                <RoadmapSearchAndSort
                  searchQuery={searchQuery}
                  sortOption={sortOption}
                  onSearchChange={setSearchQuery}
                  onSortChange={setSortOption}
                />

                {roadmapItems.length === 0 ? (
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
                ) : filteredAndSortedRoadmapItems.length === 0 ? (
                  <div className="rounded-2xl border border-white/8 bg-[#111111] p-6">
                    <p className="text-sm font-medium text-white/75">
                      No roadmap items match the current search and filters.
                    </p>

                    <p className="mt-2 text-sm leading-6 text-white/40">
                      Try another skill name or reset the active
                      filter and search.
                    </p>

                    <div className="mt-4 flex flex-wrap gap-2">
                      <button
                        type="button"
                        onClick={() => setSearchQuery('')}
                        className="rounded-lg border border-[#d6b36a]/25 px-3 py-2 text-xs font-medium text-[#e5c57c]/85 transition hover:bg-[#d6b36a]/10"
                      >
                        Clear search
                      </button>

                      <button
                        type="button"
                        onClick={() => setSelectedFilter('all')}
                        className="rounded-lg border border-white/10 px-3 py-2 text-xs font-medium text-white/60 transition hover:border-white/20 hover:text-white/85"
                      >
                        Show all skills
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {filteredAndSortedRoadmapItems.map(
                      (item) => (
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
                      ),
                    )}
                  </div>
                )}
              </>
            ) : null}
          </section>
        )}
      </div>
    </section>
  )
}