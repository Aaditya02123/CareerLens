function SkillGroup({ category, skills }) {
  const safeSkills = Array.isArray(skills)
    ? skills.filter(Boolean)
    : []

  if (safeSkills.length === 0) {
    return null
  }

  return (
    <article className="rounded-[var(--radius-md)] border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-5 transition hover:border-[var(--cl-border-strong)]">
      <div className="flex items-center justify-between gap-4">
        <h3 className="text-sm font-semibold text-[var(--cl-text)]">
          {category}
        </h3>

        <span className="font-mono text-[10px] text-[var(--cl-faint)]">
          {String(safeSkills.length).padStart(2, '0')}
        </span>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {safeSkills.map((skill) => (
          <span
            key={`${category}-${skill}`}
            className="rounded-full border border-[var(--cl-border)] bg-[var(--cl-surface)] px-3 py-1.5 text-xs font-medium text-[var(--cl-text-soft)] transition hover:border-[var(--cl-accent)] hover:text-[var(--cl-accent)]"
          >
            {skill}
          </span>
        ))}
      </div>
    </article>
  )
}

export default SkillGroup