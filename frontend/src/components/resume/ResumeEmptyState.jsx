import ResumeUpload from './ResumeUpload'

function ResumeEmptyState({
  selectedFile,
  isUploading,
  uploadError,
  uploadMessage,
  onFileChange,
  onUpload,
}) {
  const intelligenceAreas = [
    {
      label: '01',
      title: 'Profile',
      description: 'Identity and career summary',
    },
    {
      label: '02',
      title: 'Skills',
      description: 'Normalized technical capabilities',
    },
    {
      label: '03',
      title: 'Experience',
      description: 'Roles, organizations, and evidence',
    },
    {
      label: '04',
      title: 'Projects',
      description: 'Technical proof of work',
    },
    {
      label: '05',
      title: 'Education',
      description: 'Academic background',
    },
    {
      label: '06',
      title: 'More',
      description: 'Custom resume sections',
    },
  ]

  return (
    <section className="grid gap-6 xl:grid-cols-[1.12fr_0.88fr]">
      <div className="relative overflow-hidden rounded-[var(--radius-lg)] border border-[var(--cl-border-strong)] bg-[linear-gradient(145deg,var(--cl-surface),#0d151f)] p-6 shadow-[var(--shadow-soft)] sm:p-8">
        <div className="pointer-events-none absolute -right-20 -top-20 h-56 w-56 rounded-full border border-[var(--cl-border)] opacity-40" />
        <div className="pointer-events-none absolute -bottom-28 -left-16 h-64 w-64 rounded-full border border-[var(--cl-border)] opacity-30" />

        <div className="relative">
          <div className="flex items-center gap-3">
            <span className="h-2 w-2 rounded-full bg-[var(--cl-accent)]" />
            <p className="text-sm font-semibold uppercase tracking-[0.22em] text-[var(--cl-accent)]">
              Resume Intelligence
            </p>
          </div>

          <h2 className="mt-5 max-w-3xl text-4xl font-semibold tracking-tight text-[var(--cl-text)] sm:text-5xl">
            Turn one resume into a career intelligence layer.
          </h2>

          <p className="mt-5 max-w-2xl text-base leading-7 text-[var(--cl-muted)]">
            CareerLens reads your resume as structured evidence rather than
            treating it as a static document. That structure becomes the
            foundation for matching, skill gaps, roadmaps, applications, and
            interview preparation.
          </p>

          <div className="mt-8 grid gap-px overflow-hidden rounded-[var(--radius-lg)] border border-[var(--cl-border)] bg-[var(--cl-border)] sm:grid-cols-2">
            {intelligenceAreas.map((item) => (
              <div
                key={item.label}
                className="bg-[var(--cl-surface-muted)] p-4 transition hover:bg-[var(--cl-surface)]"
              >
                <div className="flex items-start gap-3">
                  <span className="font-mono text-xs text-[var(--cl-accent)]">
                    {item.label}
                  </span>

                  <div>
                    <p className="text-sm font-semibold text-[var(--cl-text)]">
                      {item.title}
                    </p>
                    <p className="mt-1 text-xs leading-5 text-[var(--cl-muted)]">
                      {item.description}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <p className="mt-6 text-xs leading-5 text-[var(--cl-faint)]">
            PDF and DOCX resumes are currently supported.
          </p>
        </div>
      </div>

      <ResumeUpload
        inputId="resume-file-empty"
        selectedFile={selectedFile}
        isUploading={isUploading}
        uploadError={uploadError}
        uploadMessage={uploadMessage}
        onFileChange={onFileChange}
        onUpload={onUpload}
      />
    </section>
  )
}

export default ResumeEmptyState