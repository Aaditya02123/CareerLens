function formatDate(value) {
  if (!value) {
    return 'Upload date unavailable'
  }

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return 'Upload date unavailable'
  }

  return new Intl.DateTimeFormat('en', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

function getReadableFileType(contentType) {
  if (contentType === 'application/pdf') {
    return 'PDF'
  }

  if (
    contentType ===
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  ) {
    return 'DOCX'
  }

  return contentType || 'Document'
}

function getMetricValue(value) {
  return Array.isArray(value) ? value.length : 0
}

function ResumeSummary({
  resume,
  hasAnalysis,
  structuredResume,
}) {
  const sectionCount = getMetricValue(
    structuredResume?.sections,
  )

  const skillCount = getMetricValue(
    structuredResume?.skills,
  )

  const projectCount = getMetricValue(
    structuredResume?.project_entries,
  )

  return (
    <aside className="rounded-[var(--radius-lg)] border border-[var(--cl-border)] bg-[var(--cl-surface)] p-6 shadow-[var(--shadow-soft)]">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--cl-faint)]">
            Current resume
          </p>

          <h2 className="mt-2 text-2xl font-semibold tracking-tight text-[var(--cl-text)]">
            {structuredResume?.name ||
              resume.original_filename}
          </h2>

          {structuredResume?.email ? (
            <p className="mt-1 break-all text-sm text-[var(--cl-muted)]">
              {structuredResume.email}
            </p>
          ) : null}
        </div>

        <span className="shrink-0 rounded-full border border-[var(--cl-border)] bg-[var(--cl-accent-soft)] px-3 py-1 text-xs font-medium text-[var(--cl-accent)]">
          {getReadableFileType(resume.content_type)}
        </span>
      </div>

      <div className="mt-5 rounded-[var(--radius-md)] border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-4">
        <p className="text-xs uppercase tracking-[0.18em] text-[var(--cl-faint)]">
          Uploaded
        </p>

        <p className="mt-2 text-sm font-medium text-[var(--cl-text-soft)]">
          {formatDate(resume.created_at)}
        </p>
      </div>

      <div className="mt-5 grid grid-cols-3 gap-2">
        <div className="rounded-[var(--radius-md)] border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-3">
          <p className="text-lg font-semibold text-[var(--cl-text)]">
            {skillCount}
          </p>
          <p className="mt-1 text-[10px] uppercase tracking-[0.14em] text-[var(--cl-faint)]">
            Skills
          </p>
        </div>

        <div className="rounded-[var(--radius-md)] border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-3">
          <p className="text-lg font-semibold text-[var(--cl-text)]">
            {projectCount}
          </p>
          <p className="mt-1 text-[10px] uppercase tracking-[0.14em] text-[var(--cl-faint)]">
            Projects
          </p>
        </div>

        <div className="rounded-[var(--radius-md)] border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-3">
          <p className="text-lg font-semibold text-[var(--cl-text)]">
            {sectionCount}
          </p>
          <p className="mt-1 text-[10px] uppercase tracking-[0.14em] text-[var(--cl-faint)]">
            Sections
          </p>
        </div>
      </div>

      <dl className="mt-5 grid gap-3 text-sm">
        <div className="flex items-center justify-between gap-4 border-t border-[var(--cl-border)] pt-3">
          <dt className="text-[var(--cl-muted)]">
            Analysis
          </dt>

          <dd className="font-medium text-[var(--cl-text)]">
            {hasAnalysis ? 'Available' : 'Not available'}
          </dd>
        </div>

        <div className="flex items-center justify-between gap-4 border-t border-[var(--cl-border)] pt-3">
          <dt className="text-[var(--cl-muted)]">
            Stored ID
          </dt>

          <dd className="max-w-[12rem] truncate font-mono text-xs text-[var(--cl-text-soft)]">
            {resume.stored_filename}
          </dd>
        </div>
      </dl>
    </aside>
  )
}

export default ResumeSummary