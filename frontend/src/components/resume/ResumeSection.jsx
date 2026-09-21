const SECTION_EYEBROWS = {
  profile: 'Profile',
  summary: 'Professional context',
  skills: 'Capabilities',
  education: 'Academic background',
  experience: 'Career history',
  projects: 'Proof of work',
  certifications: 'Credentials',
  training: 'Learning',
  achievements: 'Recognition',
  awards: 'Recognition',
  research: 'Research',
  publications: 'Publications',
  volunteering: 'Community',
  leadership: 'Leadership',
  interests: 'Interests',
  languages: 'Languages',
  custom: 'Additional information',
}

function getEyebrow(section) {
  return (
    SECTION_EYEBROWS[section?.canonical_type] ||
    'Resume section'
  )
}

function cleanDisplayText(value) {
  if (typeof value !== 'string') {
    return value
  }

  return value
    .replace(/\s+,/g, ',')
    .replace(/\s*–\s*/g, ' – ')
    .replace(/\s*—\s*/g, ' — ')
    .replace(/\s+-\s+/g, ' – ')
    .replace(/\s{2,}/g, ' ')
    .trim()
}

function splitExpectedGraduation(value) {
  if (typeof value !== 'string') {
    return {
      title: value,
      expectedGraduation: null,
    }
  }

  const match = value.match(
    /^(.+?)\s*(Expected\s+.+)$/i,
  )

  if (!match) {
    return {
      title: value,
      expectedGraduation: null,
    }
  }

  return {
    title: match[1].trim(),
    expectedGraduation: match[2].trim(),
  }
}

function formatDateRange(item) {
  if (!item) {
    return null
  }

  if (item.start_date && item.end_date) {
    return `${cleanDisplayText(
      item.start_date,
    )} – ${cleanDisplayText(item.end_date)}`
  }

  return (
    cleanDisplayText(
      item.start_date || item.end_date,
    ) || null
  )
}

function normalizeEntry(item) {
  if (typeof item === 'string') {
    return {
      title: null,
      metadata: [],
      details: [cleanDisplayText(item)],
      url: null,
    }
  }

  if (!item || typeof item !== 'object') {
    return {
      title: null,
      metadata: [],
      details: [],
      url: null,
    }
  }

  const metadata = []
  const details = []

  let title =
    item.title ||
    item.role ||
    item.institution ||
    null

  const expectedFromTitle =
    splitExpectedGraduation(title)

  title = expectedFromTitle.title

  if (expectedFromTitle.expectedGraduation) {
    metadata.push(
      expectedFromTitle.expectedGraduation,
    )
  }

  if (item.organization) {
    metadata.push(
      cleanDisplayText(item.organization),
    )
  }

  if (item.location) {
    metadata.push(
      cleanDisplayText(item.location),
    )
  }

  const dateRange = formatDateRange(item)

  if (dateRange) {
    metadata.push(dateRange)
  }

  if (item.degree) {
    metadata.push(
      cleanDisplayText(item.degree),
    )
  }

  if (item.field_of_study) {
    metadata.push(
      cleanDisplayText(item.field_of_study),
    )
  }

  if (
    item.expected_graduation &&
    !expectedFromTitle.expectedGraduation
  ) {
    metadata.push(
      `Expected ${cleanDisplayText(
        item.expected_graduation,
      )}`,
    )
  }

  if (item.gpa) {
    metadata.push(
      `GPA ${cleanDisplayText(item.gpa)}`,
    )
  }

  if (
    Array.isArray(item.technologies) &&
    item.technologies.length > 0
  ) {
    metadata.push(
      item.technologies
        .filter(Boolean)
        .map(cleanDisplayText)
        .join(' · '),
    )
  }

  if (item.issuer) {
    metadata.push(
      cleanDisplayText(item.issuer),
    )
  }

  if (item.credential_type) {
    metadata.push(
      item.credential_type
        .charAt(0)
        .toUpperCase() +
        item.credential_type.slice(1),
    )
  }

  if (
    Array.isArray(item.coursework) &&
    item.coursework.length > 0
  ) {
    details.push(
      `Relevant coursework: ${item.coursework
        .filter(Boolean)
        .map(cleanDisplayText)
        .join(', ')}`,
    )
  }

  if (Array.isArray(item.description)) {
    details.push(
      ...item.description
        .filter(Boolean)
        .map(cleanDisplayText),
    )
  }

  if (Array.isArray(item.content)) {
    details.push(
      ...item.content
        .filter(Boolean)
        .map(cleanDisplayText),
    )
  }

  return {
    title: cleanDisplayText(title),
    metadata: metadata
      .filter(Boolean)
      .map(cleanDisplayText),
    details,
    url: item.url
      ? cleanDisplayText(item.url)
      : null,
  }
}

function EntryCard({ item, index }) {
  const entry = normalizeEntry(item)

  return (
    <article className="group rounded-[var(--radius-md)] border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-5 transition duration-200 hover:border-[var(--cl-border-strong)] hover:bg-[var(--cl-surface)]">
      <div className="flex gap-4">
        <div className="mt-1 hidden h-7 w-7 shrink-0 items-center justify-center rounded-full border border-[var(--cl-border)] bg-[var(--cl-surface)] font-mono text-[10px] text-[var(--cl-faint)] sm:flex">
          {String(index + 1).padStart(2, '0')}
        </div>

        <div className="min-w-0 flex-1">
          {entry.title ? (
            <h3 className="text-base font-semibold leading-6 text-[var(--cl-text)]">
              {entry.title}
            </h3>
          ) : null}

          {entry.metadata.length > 0 ? (
            <div className="mt-2 flex flex-wrap gap-x-2 gap-y-1 text-xs leading-5 text-[var(--cl-muted)]">
              {entry.metadata.map(
                (value, metadataIndex) => (
                  <span
                    key={`${value}-${metadataIndex}`}
                    className="inline-flex items-center"
                  >
                    {metadataIndex > 0 ? (
                      <span className="mr-2 text-[var(--cl-faint)]">
                        ·
                      </span>
                    ) : null}

                    {value}
                  </span>
                ),
              )}
            </div>
          ) : null}

          {entry.url ? (
            <a
              href={
                entry.url.startsWith('http')
                  ? entry.url
                  : `https://${entry.url}`
              }
              target="_blank"
              rel="noreferrer"
              className="mt-3 inline-flex max-w-full truncate text-xs font-medium text-[var(--cl-accent)] transition hover:opacity-80"
            >
              {entry.url}
            </a>
          ) : null}

          {entry.details.length > 0 ? (
            <div className="mt-4 space-y-2">
              {entry.details.map(
                (detail, detailIndex) => (
                  <p
                    key={`${detail}-${detailIndex}`}
                    className="text-sm leading-6 text-[var(--cl-text-soft)]"
                  >
                    {detail}
                  </p>
                ),
              )}
            </div>
          ) : null}
        </div>
      </div>
    </article>
  )
}

function ResumeSection({
  section,
  items = [],
}) {
  if (!section) {
    return null
  }

  const sectionType =
    section.canonical_type || 'custom'

  const sectionTitle =
    section.title || 'Resume section'

  const rawContent = Array.isArray(
    section.raw_content,
  )
    ? section.raw_content.filter(Boolean)
    : []

  const displayItems = Array.isArray(items)
    ? items
    : []

  if (
    displayItems.length === 0 &&
    rawContent.length === 0
  ) {
    return null
  }

  if (sectionType === 'summary') {
    const summaryText = rawContent
      .map(cleanDisplayText)
      .join(' ')
      .trim()

    if (!summaryText) {
      return null
    }

    return (
      <section className="rounded-[var(--radius-lg)] border border-[var(--cl-border)] bg-[var(--cl-surface)] p-6 shadow-[var(--shadow-soft)]">
        <div className="border-b border-[var(--cl-border)] pb-5">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--cl-accent)]">
            {getEyebrow(section)}
          </p>

          <h2 className="mt-2 text-2xl font-semibold tracking-tight text-[var(--cl-text)]">
            {cleanDisplayText(sectionTitle)}
          </h2>
        </div>

        <p className="mt-5 max-w-4xl text-sm leading-7 text-[var(--cl-text-soft)]">
          {summaryText}
        </p>
      </section>
    )
  }

  return (
    <section className="rounded-[var(--radius-lg)] border border-[var(--cl-border)] bg-[var(--cl-surface)] p-6 shadow-[var(--shadow-soft)]">
      <div className="flex flex-col gap-2 border-b border-[var(--cl-border)] pb-5 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--cl-faint)]">
            {getEyebrow(section)}
          </p>

          <h2 className="mt-2 text-2xl font-semibold tracking-tight text-[var(--cl-text)]">
            {cleanDisplayText(sectionTitle)}
          </h2>
        </div>

        <span className="text-xs text-[var(--cl-muted)]">
          {displayItems.length}{' '}
          {displayItems.length === 1
            ? 'entry'
            : 'entries'}
        </span>
      </div>

      <div className="mt-5 space-y-3">
        {displayItems.length > 0
          ? displayItems.map((item, index) => (
              <EntryCard
                key={`${sectionTitle}-${index}`}
                item={item}
                index={index}
              />
            ))
          : rawContent.map((content, index) => (
              <EntryCard
                key={`${sectionTitle}-raw-${index}`}
                item={content}
                index={index}
              />
            ))}
      </div>
    </section>
  )
}

export default ResumeSection