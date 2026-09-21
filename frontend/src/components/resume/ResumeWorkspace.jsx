import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from 'react'
import {
  CAREERLENS_DEV_USER_ID,
  fetchResumeAnalysis,
  fetchUserResumes,
  uploadResume,
} from '../../services/api/resumes'
import ResumeEmptyState from './ResumeEmptyState'
import ResumeSection from './ResumeSection'
import ResumeSummary from './ResumeSummary'
import ResumeUpload from './ResumeUpload'
import SkillGroup from './SkillGroup'

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

    return second.id - first.id
  })
}

function groupCategorizedSkills(categorizedSkills) {
  const skills = Array.isArray(
    categorizedSkills?.skills,
  )
    ? categorizedSkills.skills
    : []

  return skills.reduce((groups, skill) => {
    const category = skill.category || 'Other'

    if (!groups[category]) {
      groups[category] = []
    }

    if (
      skill.name &&
      !groups[category].includes(skill.name)
    ) {
      groups[category].push(skill.name)
    }

    return groups
  }, {})
}

function isSupportedResumeFile(file) {
  if (!file) {
    return false
  }

  const filename = file.name.toLowerCase()

  return (
    filename.endsWith('.pdf') ||
    filename.endsWith('.docx')
  )
}

function createLegacySection(
  canonicalType,
  title,
  items,
) {
  if (!Array.isArray(items) || items.length === 0) {
    return null
  }

  return {
    canonical_type: canonicalType,
    title,
    entries: items.map((item) => ({
      title: null,
      content: [item],
      raw_text: item,
    })),
    raw_content: items,
  }
}

function buildSectionViews(structuredResume) {
  if (!structuredResume) {
    return []
  }

  const typedEntries = {
    education:
      structuredResume.education_entries || [],
    experience:
      structuredResume.experience_entries || [],
    projects:
      structuredResume.project_entries || [],
    certifications:
      structuredResume.credential_entries || [],
  }

  const sections = Array.isArray(
    structuredResume.sections,
  )
    ? structuredResume.sections
    : []

  if (sections.length > 0) {
    return sections
      .map((section) => {
        const canonicalType =
          section.canonical_type || 'custom'

        const specializedItems =
          typedEntries[canonicalType]

        if (
          Array.isArray(specializedItems) &&
          specializedItems.length > 0
        ) {
          return {
            section,
            items: specializedItems,
          }
        }

        if (
          Array.isArray(section.entries) &&
          section.entries.length > 0
        ) {
          return {
            section,
            items: section.entries,
          }
        }

        if (
          Array.isArray(section.raw_content) &&
          section.raw_content.length > 0
        ) {
          return {
            section,
            items: section.raw_content,
          }
        }

        return null
      })
      .filter(Boolean)
  }

  const fallbackSections = [
    createLegacySection(
      'summary',
      'Summary',
      structuredResume.summary
        ? [structuredResume.summary]
        : [],
    ),
    createLegacySection(
      'skills',
      'Skills',
      structuredResume.skills,
    ),
    createLegacySection(
      'experience',
      'Experience',
      structuredResume.experience,
    ),
    createLegacySection(
      'education',
      'Education',
      structuredResume.education,
    ),
    createLegacySection(
      'projects',
      'Projects',
      structuredResume.projects,
    ),
    createLegacySection(
      'certifications',
      'Certifications',
      structuredResume.certifications,
    ),
  ]

  return fallbackSections
    .filter(Boolean)
    .map((section) => ({
      section,
      items: section.entries,
    }))
}

function getVisibleSectionViews(sectionViews) {
  return sectionViews.filter(
    ({ section }) =>
      section?.canonical_type !== 'skills',
  )
}

function ResumeWorkspace() {
  const [resumes, setResumes] = useState([])
  const [analysis, setAnalysis] = useState(null)
  const [selectedFile, setSelectedFile] = useState(null)

  const [isLoading, setIsLoading] = useState(true)
  const [isUploading, setIsUploading] = useState(false)

  const [loadError, setLoadError] = useState('')
  const [analysisError, setAnalysisError] =
    useState('')
  const [uploadError, setUploadError] = useState('')
  const [uploadMessage, setUploadMessage] =
    useState('')

  const currentResume = useMemo(() => {
    return sortResumesNewestFirst(resumes)[0] || null
  }, [resumes])

  const structuredResume =
    analysis?.structured_resume || null

  const skillGroups = useMemo(() => {
    const categorizedGroups =
      groupCategorizedSkills(
        analysis?.categorized_skills,
      )

    if (
      Object.keys(categorizedGroups).length > 0
    ) {
      return categorizedGroups
    }

    const flatSkills =
      structuredResume?.skills || []

    if (flatSkills.length === 0) {
      return {}
    }

    return {
      'Detected skills': flatSkills,
    }
  }, [analysis, structuredResume])

  const sectionViews = useMemo(() => {
    return buildSectionViews(structuredResume)
  }, [structuredResume])

  const visibleSectionViews = useMemo(() => {
    return getVisibleSectionViews(
      sectionViews,
    )
  }, [sectionViews])

  /*
   * Skills are rendered as their own visual section,
   * while the backend's skills section is excluded from
   * ResumeSection rendering. Count it once here so the
   * summary and detailed profile use the same number.
   */
  const displayedSectionCount = useMemo(() => {
    const contentSectionCount =
      visibleSectionViews.length

    const hasSkills =
      Object.keys(skillGroups).length > 0

    return (
      contentSectionCount +
      (hasSkills ? 1 : 0)
    )
  }, [
    visibleSectionViews,
    skillGroups,
  ])

  const loadResumeWorkspace =
    useCallback(async () => {
      setIsLoading(true)
      setLoadError('')
      setAnalysisError('')

      try {
        const userResumes =
          await fetchUserResumes(
            CAREERLENS_DEV_USER_ID,
          )

        const orderedResumes =
          sortResumesNewestFirst(
            Array.isArray(userResumes)
              ? userResumes
              : [],
          )

        setResumes(orderedResumes)

        const latestResume =
          orderedResumes[0]

        if (!latestResume) {
          setAnalysis(null)
          return
        }

        try {
          const resumeAnalysis =
            await fetchResumeAnalysis(
              latestResume.stored_filename,
            )

          setAnalysis(resumeAnalysis)
        } catch (error) {
          setAnalysis(null)
          setAnalysisError(
            error.message ||
              'CareerLens could not load the resume analysis yet.',
          )
        }
      } catch (error) {
        setResumes([])
        setAnalysis(null)

        setLoadError(
          error.message ||
            'CareerLens could not reach the resume workspace.',
        )
      } finally {
        setIsLoading(false)
      }
    }, [])

  useEffect(() => {
    loadResumeWorkspace()
  }, [loadResumeWorkspace])

  function handleFileChange(file) {
    setUploadError('')
    setUploadMessage('')

    if (!file) {
      setSelectedFile(null)
      return
    }

    if (!isSupportedResumeFile(file)) {
      setSelectedFile(null)
      setUploadError(
        'Please choose a PDF or DOCX resume.',
      )
      return
    }

    setSelectedFile(file)
  }

  async function handleUpload() {
    if (!selectedFile) {
      setUploadError(
        'Choose a resume file before uploading.',
      )
      return
    }

    setIsUploading(true)
    setUploadError('')
    setUploadMessage(
      'Uploading resume for analysis...',
    )

    try {
      await uploadResume(
        selectedFile,
        CAREERLENS_DEV_USER_ID,
      )

      setSelectedFile(null)
      setUploadMessage(
        'Resume uploaded. Refreshing intelligence...',
      )

      await loadResumeWorkspace()

      setUploadMessage(
        'Resume intelligence is ready.',
      )
    } catch (error) {
      setUploadError(
        error.message ||
          'The resume could not be uploaded.',
      )
      setUploadMessage('')
    } finally {
      setIsUploading(false)
    }
  }

  if (isLoading) {
    return (
      <section className="rounded-[var(--radius-lg)] border border-[var(--cl-border)] bg-[var(--cl-surface)] p-8 shadow-[var(--shadow-soft)]">
        <div className="flex items-center gap-3">
          <span className="h-2 w-2 animate-pulse rounded-full bg-[var(--cl-accent)]" />

          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[var(--cl-accent)]">
            Resume Intelligence
          </p>
        </div>

        <h2 className="mt-4 text-3xl font-semibold tracking-tight text-[var(--cl-text)]">
          Reading your resume workspace.
        </h2>

        <p className="mt-3 max-w-2xl text-sm leading-6 text-[var(--cl-muted)]">
          CareerLens is checking your uploaded resume and
          loading its structured analysis.
        </p>

        <div className="mt-8 grid gap-3 md:grid-cols-3">
          {[1, 2, 3].map((item) => (
            <div
              key={item}
              className="h-24 animate-pulse rounded-[var(--radius-md)] border border-[var(--cl-border)] bg-[var(--cl-surface-muted)]"
            />
          ))}
        </div>
      </section>
    )
  }

  if (loadError) {
    return (
      <section className="rounded-[var(--radius-lg)] border border-[var(--cl-border)] bg-[var(--cl-surface)] p-8 shadow-[var(--shadow-soft)]">
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[var(--cl-danger)]">
          Resume unavailable
        </p>

        <h2 className="mt-4 text-3xl font-semibold tracking-tight text-[var(--cl-text)]">
          CareerLens could not load your resume workspace.
        </h2>

        <p className="mt-3 max-w-2xl text-sm leading-6 text-[var(--cl-muted)]">
          {loadError}
        </p>

        <button
          type="button"
          onClick={loadResumeWorkspace}
          className="mt-6 rounded-[var(--radius-md)] border border-[var(--cl-border-strong)] bg-[var(--cl-surface-muted)] px-4 py-2.5 text-sm font-medium text-[var(--cl-text)] transition hover:border-[var(--cl-accent)]"
        >
          Try again
        </button>
      </section>
    )
  }

  if (!currentResume) {
    return (
      <ResumeEmptyState
        selectedFile={selectedFile}
        isUploading={isUploading}
        uploadError={uploadError}
        uploadMessage={uploadMessage}
        onFileChange={handleFileChange}
        onUpload={handleUpload}
      />
    )
  }

  return (
    <div className="space-y-8">
      <section className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <div className="relative overflow-hidden rounded-[var(--radius-lg)] border border-[var(--cl-border-strong)] bg-[linear-gradient(145deg,var(--cl-surface),#0f1722)] p-6 shadow-[var(--shadow-soft)] sm:p-8">
          <div className="pointer-events-none absolute -right-24 -top-24 h-64 w-64 rounded-full border border-[var(--cl-border)] opacity-40" />

          <div className="relative">
            <div className="flex items-center gap-3">
              <span className="h-2 w-2 rounded-full bg-[var(--cl-accent)]" />

              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[var(--cl-accent)]">
                Resume Intelligence
              </p>
            </div>

            <h1 className="mt-5 max-w-3xl text-4xl font-semibold tracking-tight text-[var(--cl-text)] sm:text-5xl">
              Your resume is now structured career evidence.
            </h1>

            <p className="mt-5 max-w-2xl text-base leading-7 text-[var(--cl-muted)]">
              CareerLens has transformed the uploaded document
              into structured information that can power the
              rest of your career intelligence workflow.
            </p>

            {analysisError ? (
              <div
                className="mt-6 rounded-[var(--radius-md)] border border-[rgba(251,191,36,0.3)] bg-[rgba(251,191,36,0.08)] p-4 text-sm leading-6 text-[var(--cl-text-soft)]"
                role="status"
              >
                {analysisError}
              </div>
            ) : null}
          </div>
        </div>

        <ResumeSummary
          resume={currentResume}
          hasAnalysis={Boolean(analysis)}
          structuredResume={structuredResume}
        />
      </section>

      <section className="grid gap-6 xl:grid-cols-[0.72fr_1.28fr]">
        <ResumeUpload
          inputId="resume-file-replace"
          selectedFile={selectedFile}
          isUploading={isUploading}
          uploadError={uploadError}
          uploadMessage={uploadMessage}
          onFileChange={handleFileChange}
          onUpload={handleUpload}
          title="Replace resume"
          description="Upload a newer PDF or DOCX. CareerLens will store it and refresh the analysis view."
        />

        <section className="rounded-[var(--radius-lg)] border border-[var(--cl-border)] bg-[var(--cl-surface)] p-6 shadow-[var(--shadow-soft)]">
          <div className="flex items-end justify-between gap-4 border-b border-[var(--cl-border)] pb-5">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--cl-faint)]">
                Candidate profile
              </p>

              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-[var(--cl-text)]">
                What CareerLens detected
              </h2>
            </div>

            {structuredResume ? (
              <span className="text-xs text-[var(--cl-muted)]">
                Structured data
              </span>
            ) : null}
          </div>

          {structuredResume ? (
            <div className="mt-5 grid gap-4 sm:grid-cols-2">
              <div className="rounded-[var(--radius-md)] border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-4">
                <p className="text-[10px] uppercase tracking-[0.18em] text-[var(--cl-faint)]">
                  Name
                </p>

                <p className="mt-2 text-lg font-semibold text-[var(--cl-text)]">
                  {structuredResume.name ||
                    'Not detected'}
                </p>
              </div>

              <div className="rounded-[var(--radius-md)] border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-4">
                <p className="text-[10px] uppercase tracking-[0.18em] text-[var(--cl-faint)]">
                  Email
                </p>

                <p className="mt-2 break-words text-sm font-semibold text-[var(--cl-text)]">
                  {structuredResume.email ||
                    'Not detected'}
                </p>
              </div>

              <div className="rounded-[var(--radius-md)] border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-4">
                <p className="text-[10px] uppercase tracking-[0.18em] text-[var(--cl-faint)]">
                  Sections
                </p>

                <p className="mt-2 text-lg font-semibold text-[var(--cl-text)]">
                  {displayedSectionCount}
                </p>
              </div>

              <div className="rounded-[var(--radius-md)] border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-4">
                <p className="text-[10px] uppercase tracking-[0.18em] text-[var(--cl-faint)]">
                  Projects
                </p>

                <p className="mt-2 text-lg font-semibold text-[var(--cl-text)]">
                  {structuredResume.project_entries
                    ?.length || 0}
                </p>
              </div>
            </div>
          ) : (
            <p className="mt-5 text-sm leading-6 text-[var(--cl-muted)]">
              Resume metadata is available, but structured
              analysis has not been loaded yet.
            </p>
          )}
        </section>
      </section>

      {Object.keys(skillGroups).length > 0 ? (
        <section className="rounded-[var(--radius-lg)] border border-[var(--cl-border)] bg-[var(--cl-surface)] p-6 shadow-[var(--shadow-soft)]">
          <div className="flex flex-col gap-2 border-b border-[var(--cl-border)] pb-5 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--cl-faint)]">
                Skills
              </p>

              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-[var(--cl-text)]">
                Capabilities CareerLens detected
              </h2>
            </div>

            <span className="text-xs text-[var(--cl-muted)]">
              {Object.values(skillGroups).flat().length}{' '}
              skills
            </span>
          </div>

          <div className="mt-6 grid gap-4 lg:grid-cols-2">
            {Object.entries(skillGroups).map(
              ([category, skills]) => (
                <SkillGroup
                  key={category}
                  category={category}
                  skills={skills}
                />
              ),
            )}
          </div>
        </section>
      ) : null}

      {structuredResume ? (
        <section className="space-y-6">
          <div className="flex items-end justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--cl-faint)]">
                Resume evidence
              </p>

              <h2 className="mt-2 text-3xl font-semibold tracking-tight text-[var(--cl-text)]">
                Your structured profile
              </h2>
            </div>

            <span className="hidden text-xs text-[var(--cl-muted)] sm:block">
              {displayedSectionCount}{' '}
              {displayedSectionCount === 1
                ? 'section'
                : 'sections'}
            </span>
          </div>

          <div className="space-y-6">
            {visibleSectionViews.map(
              ({ section, items }) => (
                <ResumeSection
                  key={`${section.title}-${section.canonical_type}`}
                  section={section}
                  items={items}
                />
              ),
            )}
          </div>
        </section>
      ) : null}

      <section className="rounded-[var(--radius-lg)] border border-[var(--cl-border)] bg-[var(--cl-surface)] p-6 shadow-[var(--shadow-soft)]">
        <div className="border-b border-[var(--cl-border)] pb-5">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--cl-faint)]">
            Intelligence pipeline
          </p>

          <h2 className="mt-2 text-2xl font-semibold tracking-tight text-[var(--cl-text)]">
            How this resume becomes useful
          </h2>
        </div>

        <div className="mt-6 grid gap-px overflow-hidden rounded-[var(--radius-lg)] border border-[var(--cl-border)] bg-[var(--cl-border)] md:grid-cols-3 lg:grid-cols-6">
          {[
            'Resume',
            'Skills',
            'Job matching',
            'Skill gaps',
            'Learning roadmap',
            'Interview preparation',
          ].map((step, index) => (
            <div
              key={step}
              className="bg-[var(--cl-surface-muted)] p-4"
            >
              <p className="font-mono text-[10px] text-[var(--cl-accent)]">
                {String(index + 1).padStart(2, '0')}
              </p>

              <p className="mt-3 text-sm font-medium leading-5 text-[var(--cl-text)]">
                {step}
              </p>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}

export default ResumeWorkspace