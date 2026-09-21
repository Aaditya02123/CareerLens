function formatFileSize(size) {
  if (!size) {
    return 'Size unavailable'
  }

  if (size < 1024 * 1024) {
    return `${Math.max(1, Math.round(size / 1024))} KB`
  }

  return `${(size / (1024 * 1024)).toFixed(1)} MB`
}

function ResumeUpload({
  selectedFile,
  isUploading,
  uploadError,
  uploadMessage,
  onFileChange,
  onUpload,
  inputId = 'resume-file',
  title = 'Upload resume',
  description = 'Choose a PDF or DOCX resume to begin building your CareerLens profile.',
}) {
  return (
    <section className="rounded-[var(--radius-lg)] border border-[var(--cl-border)] bg-[var(--cl-surface)] p-6 shadow-[var(--shadow-soft)]">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--cl-faint)]">
          Resume source
        </p>

        <h2 className="mt-2 text-2xl font-semibold tracking-tight text-[var(--cl-text)]">
          {title}
        </h2>

        <p className="mt-3 text-sm leading-6 text-[var(--cl-muted)]">
          {description}
        </p>
      </div>

      <div className="mt-6">
        <label
          htmlFor={inputId}
          className="group block cursor-pointer rounded-[var(--radius-lg)] border border-dashed border-[var(--cl-border-strong)] bg-[var(--cl-surface-muted)] p-5 transition hover:border-[var(--cl-accent)] hover:bg-[var(--cl-surface)]"
        >
          <div className="flex items-start justify-between gap-4">
            <div>
              <span className="block text-sm font-medium text-[var(--cl-text)]">
                Select resume file
              </span>

              <span className="mt-1 block text-sm text-[var(--cl-muted)]">
                PDF or DOCX only
              </span>
            </div>

            <span className="rounded-full border border-[var(--cl-border)] px-2.5 py-1 text-[10px] uppercase tracking-[0.14em] text-[var(--cl-faint)] transition group-hover:border-[var(--cl-accent)] group-hover:text-[var(--cl-accent)]">
              Browse
            </span>
          </div>

          <input
            id={inputId}
            type="file"
            accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            className="mt-5 block w-full cursor-pointer text-sm text-[var(--cl-muted)] file:mr-4 file:rounded-[var(--radius-sm)] file:border-0 file:bg-[var(--cl-accent-soft)] file:px-4 file:py-2 file:text-sm file:font-medium file:text-[var(--cl-accent)]"
            onChange={(event) =>
              onFileChange(event.target.files?.[0])
            }
            disabled={isUploading}
          />
        </label>
      </div>

      {selectedFile ? (
        <div className="mt-4 rounded-[var(--radius-md)] border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-4">
          <div className="flex items-start gap-3">
            <div className="mt-0.5 h-8 w-8 shrink-0 rounded-[var(--radius-sm)] border border-[var(--cl-border)] bg-[var(--cl-surface)] text-center text-xs leading-8 text-[var(--cl-accent)]">
              CV
            </div>

            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-[var(--cl-text)]">
                {selectedFile.name}
              </p>

              <p className="mt-1 text-xs text-[var(--cl-muted)]">
                {selectedFile.type || 'Document'} ·{' '}
                {formatFileSize(selectedFile.size)}
              </p>
            </div>
          </div>
        </div>
      ) : null}

      <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:items-center">
        <button
          type="button"
          onClick={onUpload}
          disabled={!selectedFile || isUploading}
          className="rounded-[var(--radius-md)] border border-[var(--cl-accent)]/50 bg-[var(--cl-accent-soft)] px-4 py-2.5 text-sm font-semibold text-[var(--cl-accent)] transition hover:border-[var(--cl-accent)] hover:bg-[var(--cl-accent)]/15 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isUploading ? 'Analyzing...' : 'Upload resume'}
        </button>

        <p className="text-xs leading-5 text-[var(--cl-muted)]">
          CareerLens validates the file before storing it.
        </p>
      </div>

      <div
        aria-live="polite"
        className="mt-4"
      >
        {uploadError ? (
          <p className="rounded-[var(--radius-md)] border border-[rgba(248,113,113,0.32)] bg-[rgba(248,113,113,0.08)] px-4 py-3 text-sm leading-6 text-[var(--cl-text-soft)]">
            {uploadError}
          </p>
        ) : null}

        {uploadMessage ? (
          <p className="rounded-[var(--radius-md)] border border-[rgba(74,222,128,0.24)] bg-[var(--cl-success-soft)] px-4 py-3 text-sm leading-6 text-[var(--cl-text-soft)]">
            {uploadMessage}
          </p>
        ) : null}
      </div>
    </section>
  )
}

export default ResumeUpload