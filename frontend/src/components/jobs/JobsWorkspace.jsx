import { useCallback, useEffect, useMemo, useState } from 'react'

import {
  fetchJobRecommendations,
  fetchJobs,
  fetchMatchExplanation,
} from '../../services/api/jobs'
import { fetchUserResumes } from '../../services/api/resumes'

import JobCard from './JobCard'
import JobFilters from './JobFilters'
import JobIntelligenceModel from './JobIntelligenceModel'

function getLatestResume(resumes) {
  if (!Array.isArray(resumes) || resumes.length === 0) {
    return null
  }

  return [...resumes].sort(
    (a, b) =>
      new Date(b.created_at) - new Date(a.created_at)
  )[0]
}

function matchesClientFilters(job, filters) {
  const title = job.title?.toLowerCase() || ''
  const location = job.location?.toLowerCase() || ''
  const source = job.source?.toLowerCase() || ''

  const search = filters.search.trim().toLowerCase()
  const locationQuery =
    filters.location.trim().toLowerCase()
  const sourceQuery =
    filters.source.trim().toLowerCase()

  if (search && !title.includes(search)) {
    return false
  }

  if (
    locationQuery &&
    !location.includes(locationQuery)
  ) {
    return false
  }

  if (
    filters.experienceLevel &&
    job.experience_level?.toLowerCase() !==
      filters.experienceLevel.toLowerCase()
  ) {
    return false
  }

  if (sourceQuery && !source.includes(sourceQuery)) {
    return false
  }

  return true
}

export default function JobsWorkspace() {
  const [jobs, setJobs] = useState([])
  const [recommendations, setRecommendations] =
    useState([])

  const [resume, setResume] = useState(null)

  const [loading, setLoading] = useState(true)
  const [recommendationsLoading, setRecommendationsLoading] =
    useState(false)

  const [error, setError] = useState('')

  const [filters, setFilters] = useState({
    search: '',
    location: '',
    experienceLevel: '',
    source: '',
  })

  const [selectedJob, setSelectedJob] = useState(null)
  const [matchExplanation, setMatchExplanation] = useState(null)
  const [matchExplanationLoading, setMatchExplanationLoading] = useState(false)
  const [matchExplanationError, setMatchExplanationError] = useState('')

  const loadJobs = useCallback(async () => {
    setLoading(true)
    setError('')

    try {
      const resumes = await fetchUserResumes()
      const latestResume = getLatestResume(resumes)

      setResume(latestResume)

      const jobList = await fetchJobs({
        limit: 50,
      })

      setJobs(jobList)

      if (latestResume?.id) {
        setRecommendationsLoading(true)

        try {
          const recommendationResponse =
            await fetchJobRecommendations(
              latestResume.id,
              10
            )

          setRecommendations(
            recommendationResponse?.recommendations || []
          )
        } finally {
          setRecommendationsLoading(false)
        }
      } else {
        setRecommendations([])
      }
    } catch (requestError) {
      setError(
        requestError?.message ||
          'CareerLens could not load job intelligence.'
      )
    } finally {
      setLoading(false)
    }
  }, [])
  const handleSelectJob = async (job) => {
    setSelectedJob(job)
    setMatchExplanation(null)
    setMatchExplanationError('')

    if (!resume?.id || !job?.id) {
      return
    }

    setMatchExplanationLoading(true)

    try {
      const explanation = await fetchMatchExplanation(
        resume.id,
        job.id
      )

      setMatchExplanation(explanation)
    } catch (requestError) {
      setMatchExplanationError(
        requestError?.message ||
          'CareerLens could not load match intelligence.'
      )
    } finally {
      setMatchExplanationLoading(false)
    }
  }

  useEffect(() => {
    loadJobs()
  }, [loadJobs])

  const recommendationByJobId = useMemo(() => {
    return new Map(
      recommendations.map((recommendation) => [
        recommendation.job_id,
        recommendation,
      ])
    )
  }, [recommendations])

  const filteredJobs = useMemo(() => {
    return jobs.filter((job) =>
      matchesClientFilters(job, filters)
    )
  }, [jobs, filters])

  const recommendedJobs = useMemo(() => {
    return recommendations
      .map((recommendation) => {
        const job = jobs.find(
          (item) => item.id === recommendation.job_id
        )

        if (!job) {
          return null
        }

        return {
          job,
          recommendation,
        }
      })
      .filter(Boolean)
      .filter(({ job }) =>
        matchesClientFilters(job, filters)
      )
  }, [recommendations, jobs, filters])

  const handleClearFilters = () => {
    setFilters({
      search: '',
      location: '',
      experienceLevel: '',
      source: '',
    })
  }

  const updateFilter = (key, value) => {
    setFilters((current) => ({
      ...current,
      [key]: value,
    }))
  }

  const recommendationCount =
    recommendedJobs.length

  const hasJobs = filteredJobs.length > 0

  return (
    <section className="min-h-full bg-[#0a0a0a] text-white">
      <div className="mx-auto max-w-[1500px] px-6 py-7 lg:px-8">
        <header className="mb-7">
          <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-end">
            <div>
              <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.22em] text-[#d6b36a]">
                Career intelligence
              </p>

              <h1 className="text-3xl font-medium tracking-[-0.035em] text-white">
                Jobs
              </h1>

              <p className="mt-2 max-w-2xl text-sm leading-6 text-white/45">
                Discover opportunities, understand your
                match, and see the skills that could move
                you closer to the role.
              </p>
            </div>

            <div className="flex items-center gap-3">
              {resume && (
                <div className="rounded-xl border border-white/8 bg-white/[0.025] px-4 py-2.5">
                  <p className="text-[9px] font-semibold uppercase tracking-[0.16em] text-white/30">
                    Matching resume
                  </p>

                  <p className="mt-1 max-w-[220px] truncate text-xs text-white/65">
                    {resume.original_filename}
                  </p>
                </div>
              )}

              <button
                type="button"
                onClick={loadJobs}
                disabled={loading}
                className="rounded-xl border border-white/8 px-4 py-2.5 text-xs font-medium text-white/60 transition hover:border-white/15 hover:bg-white/[0.04] hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
              >
                {loading ? 'Refreshing...' : 'Refresh'}
              </button>
            </div>
          </div>
        </header>

        <JobFilters
          search={filters.search}
          location={filters.location}
          experienceLevel={filters.experienceLevel}
          source={filters.source}
          onSearchChange={(value) =>
            updateFilter('search', value)
          }
          onLocationChange={(value) =>
            updateFilter('location', value)
          }
          onExperienceChange={(value) =>
            updateFilter('experienceLevel', value)
          }
          onSourceChange={(value) =>
            updateFilter('source', value)
          }
          onClear={handleClearFilters}
        />

        {error && (
          <div className="mt-5 rounded-2xl border border-red-400/15 bg-red-400/[0.04] px-5 py-4">
            <p className="text-sm text-red-200/80">
              {error}
            </p>

            <button
              type="button"
              onClick={loadJobs}
              className="mt-3 text-xs font-medium text-red-200 underline underline-offset-4"
            >
              Try again
            </button>
          </div>
        )}

        {!loading && !error && !resume && (
          <div className="mt-5 rounded-2xl border border-[#d6b36a]/15 bg-[#d6b36a]/[0.035] p-6">
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#d6b36a]">
              Resume required for personalization
            </p>

            <h2 className="mt-2 text-lg font-medium text-white">
              Upload a resume to unlock your match intelligence.
            </h2>

            <p className="mt-2 max-w-xl text-sm leading-6 text-white/45">
              CareerLens can still show available jobs, but
              personalized recommendations require an analyzed
              resume.
            </p>
          </div>
        )}

        <div className="mt-7 grid gap-7 xl:grid-cols-[minmax(0,1fr)_320px]">
          <main>
            <div className="mb-4 flex items-end justify-between">
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-white/30">
                  For you
                </p>

                <h2 className="mt-1 text-xl font-medium tracking-[-0.025em]">
                  Personalized opportunities
                </h2>
              </div>

              <span className="text-xs text-white/30">
                {recommendationsLoading
                  ? 'Calculating matches...'
                  : `${recommendationCount} matched`}
              </span>
            </div>

            {recommendationsLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((item) => (
                  <div
                    key={item}
                    className="h-[230px] animate-pulse rounded-2xl border border-white/6 bg-white/[0.025]"
                  />
                ))}
              </div>
            ) : recommendedJobs.length > 0 ? (
              <div className="space-y-3">
                {recommendedJobs.map(
                  ({ job, recommendation }) => (
                    <JobCard
                      key={job.id}
                      job={job}
                      recommendation={recommendation}
                      onSelect={handleSelectJob}
                    />
                  )
                )}
              </div>
            ) : (
              <div className="rounded-2xl border border-white/8 bg-[#111111] p-8">
                <p className="text-sm font-medium text-white/75">
                  No personalized matches found.
                </p>

                <p className="mt-2 text-sm leading-6 text-white/40">
                  Once your resume has an analysis and jobs
                  are available, CareerLens will calculate
                  personalized matches here.
                </p>
              </div>
            )}

            <div className="mb-4 mt-10 flex items-end justify-between">
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-white/30">
                  Discovery
                </p>

                <h2 className="mt-1 text-xl font-medium tracking-[-0.025em]">
                  All opportunities
                </h2>
              </div>

              <span className="text-xs text-white/30">
                {filteredJobs.length} results
              </span>
            </div>

            {!loading && !hasJobs ? (
              <div className="rounded-2xl border border-white/8 bg-[#111111] p-8">
                <p className="text-sm font-medium text-white/75">
                  No jobs match these filters.
                </p>

                <button
                  type="button"
                  onClick={handleClearFilters}
                  className="mt-3 text-xs text-[#d6b36a]"
                >
                  Clear filters
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                {filteredJobs.map((job) => (
                  <JobCard
                    key={`discovery-${job.id}`}
                    job={job}
                    recommendation={recommendationByJobId.get(
                      job.id
                    )}
                    onSelect={handleSelectJob}
                  />
                ))}
              </div>
            )}
          </main>

          <aside className="hidden xl:block">
            <div className="sticky top-6 rounded-2xl border border-white/8 bg-[#101010] p-5">
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#d6b36a]">
                Intelligence
              </p>

              <h3 className="mt-2 text-lg font-medium tracking-[-0.02em]">
                What CareerLens looks at
              </h3>

              <div className="mt-5 space-y-4">
                <div className="border-b border-white/7 pb-4">
                  <p className="text-sm text-white/75">
                    Required skills
                  </p>

                  <p className="mt-1 text-xs leading-5 text-white/35">
                    How much of the role's required skill set
                    appears in your resume.
                  </p>
                </div>

                <div className="border-b border-white/7 pb-4">
                  <p className="text-sm text-white/75">
                    Semantic alignment
                  </p>

                  <p className="mt-1 text-xs leading-5 text-white/35">
                    Similarity between your resume and the
                    job's description.
                  </p>
                </div>

                <div>
                  <p className="text-sm text-white/75">
                    Skill gap
                  </p>

                  <p className="mt-1 text-xs leading-5 text-white/35">
                    Required skills detected in the job but
                    not in your resume.
                  </p>
                </div>
              </div>
            </div>
          </aside>
        </div>

        <JobIntelligenceModel
          job={selectedJob}
          explanation={matchExplanation}
          loading={matchExplanationLoading}
          error={matchExplanationError}
          onClose={() => {
            setSelectedJob(null)
            setMatchExplanation(null)
            setMatchExplanationError('')
          }}
        />
      </div>
    </section>
  )
}