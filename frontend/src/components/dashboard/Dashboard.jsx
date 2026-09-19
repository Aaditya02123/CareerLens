import ActivityItem from './ActivityItem'
import JobOpportunity from './JobOpportunity'
import StatItem from './StatItem'

const stats = [
  {
    label: 'Resume readiness',
    value: '82%',
    trend: 'Demo',
    detail: 'Structured resume intelligence will surface clarity, skills, and gaps.',
  },
  {
    label: 'Matching opportunities',
    value: '14',
    trend: 'Demo',
    detail: 'Role matches will combine skills, semantics, and explainable signals.',
  },
  {
    label: 'Applications',
    value: '5',
    trend: 'Demo',
    detail: 'Track saved, applied, interview, offer, and rejected stages.',
  },
  {
    label: 'Interview readiness',
    value: '68%',
    trend: 'Demo',
    detail: 'Mock interview practice will connect questions to jobs and resumes.',
  },
]

const opportunities = [
  {
    role: 'Backend Engineer Intern',
    company: 'Northstar Labs',
    location: 'Remote',
    match: 86,
    matchedSkills: ['Python', 'FastAPI', 'PostgreSQL'],
    missingSkill: 'Docker',
  },
  {
    role: 'Full Stack Developer',
    company: 'CivicTech Studio',
    location: 'Bengaluru',
    match: 79,
    matchedSkills: ['React', 'API Design', 'MongoDB'],
    missingSkill: 'System Design',
  },
  {
    role: 'AI Application Engineer',
    company: 'SignalWorks',
    location: 'Hybrid',
    match: 74,
    matchedSkills: ['Python', 'PyTorch', 'REST APIs'],
    missingSkill: 'Vector Search',
  },
]

const skillGaps = [
  { skill: 'Docker', status: 'Gap', priority: 'High' },
  { skill: 'System Design', status: 'Developing', priority: 'High' },
  { skill: 'Vector Search', status: 'Next', priority: 'Medium' },
  { skill: 'Testing Strategy', status: 'Improve', priority: 'Medium' },
]

const activities = [
  {
    title: 'Resume analyzed',
    description: 'CareerLens identified backend, AI, and project-based strengths.',
    time: 'Today',
    tone: 'success',
  },
  {
    title: 'Application saved',
    description: 'Backend Engineer Intern added to the application tracker.',
    time: 'Yesterday',
    tone: 'neutral',
  },
  {
    title: 'Interview completed',
    description: 'Mock interview feedback highlighted stronger technical structure.',
    time: 'This week',
    tone: 'warning',
  },
]

function Dashboard() {
  return (
    <div className="space-y-8">
      <section className="grid gap-6 xl:grid-cols-[1.35fr_0.65fr]">
        <div className="rounded-[var(--radius-lg)] border border-[var(--cl-border-strong)] bg-[linear-gradient(145deg,var(--cl-surface),#0f1722)] p-6 shadow-[var(--shadow-soft)] sm:p-8">
          <p className="text-sm font-medium text-[var(--cl-accent)]">
            Good afternoon
          </p>
          <div className="mt-5 max-w-3xl">
            <h2 className="text-4xl font-semibold tracking-tight text-[var(--cl-text)] sm:text-5xl">
              Your career intelligence, in one place.
            </h2>
            <p className="mt-5 max-w-2xl text-base leading-7 text-[var(--cl-muted)]">
              CareerLens brings resume intelligence, job matching, skill gaps,
              roadmaps, applications, and interview practice into one calm
              workspace.
            </p>
          </div>

          <div className="mt-8 grid gap-3 border-t border-[var(--cl-border)] pt-6 sm:grid-cols-3">
            <div>
              <p className="text-2xl font-semibold text-[var(--cl-text)]">
                4
              </p>
              <p className="mt-1 text-sm text-[var(--cl-muted)]">
                intelligence modules active
              </p>
            </div>
            <div>
              <p className="text-2xl font-semibold text-[var(--cl-text)]">
                3
              </p>
              <p className="mt-1 text-sm text-[var(--cl-muted)]">
                high-priority skills to build
              </p>
            </div>
            <div>
              <p className="text-2xl font-semibold text-[var(--cl-text)]">
                1
              </p>
              <p className="mt-1 text-sm text-[var(--cl-muted)]">
                focused interview loop
              </p>
            </div>
          </div>
        </div>

        <aside className="rounded-[var(--radius-lg)] border border-[var(--cl-border)] bg-[var(--cl-surface)] p-6">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[var(--cl-faint)]">
            CareerLens intelligence
          </p>
          <h3 className="mt-4 text-2xl font-semibold tracking-tight text-[var(--cl-text)]">
            Explainable guidance, not guesswork.
          </h3>
          <p className="mt-4 text-sm leading-6 text-[var(--cl-muted)]">
            The platform is being shaped around transparent signals: matched
            skills, missing skills, job context, interview evidence, and
            learning next steps.
          </p>

          <div className="mt-6 space-y-3">
            {['Resume signals', 'Job fit', 'Skill gaps'].map((item) => (
              <div
                key={item}
                className="flex items-center justify-between rounded-[var(--radius-md)] border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] px-4 py-3"
              >
                <span className="text-sm text-[var(--cl-text-soft)]">
                  {item}
                </span>
                <span className="text-xs font-medium text-[var(--cl-accent)]">
                  Ready
                </span>
              </div>
            ))}
          </div>
        </aside>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {stats.map((item) => (
          <StatItem key={item.label} {...item} />
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="rounded-[var(--radius-lg)] border border-[var(--cl-border)] bg-[var(--cl-surface)] p-6">
          <div className="flex flex-col gap-3 border-b border-[var(--cl-border)] pb-5 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[var(--cl-faint)]">
                Recommended opportunities
              </p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-[var(--cl-text)]">
                Roles aligned with your current signal
              </h2>
            </div>
            <span className="text-sm text-[var(--cl-muted)]">
              Demo data for UI foundation
            </span>
          </div>

          <div>
            {opportunities.map((job) => (
              <JobOpportunity key={`${job.company}-${job.role}`} {...job} />
            ))}
          </div>
        </div>

        <div className="space-y-6">
          <section className="rounded-[var(--radius-lg)] border border-[var(--cl-border)] bg-[var(--cl-surface)] p-6">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[var(--cl-faint)]">
              Career focus
            </p>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight text-[var(--cl-text)]">
              Skill gap priorities
            </h2>

            <div className="mt-5 space-y-3">
              {skillGaps.map((item) => (
                <div
                  key={item.skill}
                  className="flex items-center justify-between gap-4 rounded-[var(--radius-md)] border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] px-4 py-3"
                >
                  <div>
                    <p className="text-sm font-medium text-[var(--cl-text)]">
                      {item.skill}
                    </p>
                    <p className="mt-1 text-xs text-[var(--cl-muted)]">
                      {item.status}
                    </p>
                  </div>
                  <span className="rounded-full border border-[var(--cl-border)] px-2.5 py-1 text-xs text-[var(--cl-accent)]">
                    {item.priority}
                  </span>
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-[var(--radius-lg)] border border-[var(--cl-border)] bg-[var(--cl-surface)] p-6">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[var(--cl-faint)]">
              Recent activity
            </p>
            <ul className="mt-5 space-y-5">
              {activities.map((activity) => (
                <ActivityItem key={activity.title} {...activity} />
              ))}
            </ul>
          </section>
        </div>
      </section>
    </div>
  )
}

export default Dashboard