import { useState, useMemo, useEffect } from 'react'
import ActivityItem from './ActivityItem'
import JobOpportunity from './JobOpportunity'
import StatItem from './StatItem'

const STUDENT_METRICS = [
  {
    label: 'Resume Readiness',
    value: '84%',
    trend: 'High Project Signal',
    detail: 'Extracted full-stack project evidence, Python, React, and database fundamentals.',
  },
  {
    label: 'Internship & Junior Roles',
    value: '16',
    trend: 'Entry Matches',
    detail: 'Matched opportunities curated for campus placements, interns, and early career.',
  },
  {
    label: 'Core Skill Gaps',
    value: '3',
    trend: 'Actionable',
    detail: 'High-leverage gaps to bridge: Docker, System Design Basics, and Unit Testing.',
  },
  {
    label: 'Interview Readiness',
    value: '74%',
    trend: 'Starter Loop',
    detail: 'Foundational CS concepts and STAR behavioral frameworks evaluated.',
  },
]

const PROFESSIONAL_METRICS = [
  {
    label: 'Commercial Impact',
    value: '91%',
    trend: 'Senior Signal',
    detail: 'Strong density of quantified business metrics, scalability, and code ownership.',
  },
  {
    label: 'Mid / Senior Matches',
    value: '12',
    trend: 'Senior & Lead',
    detail: 'Roles aligned with Senior Backend, Full Stack Lead, and AI Systems Architect.',
  },
  {
    label: 'Architecture Gaps',
    value: '2',
    trend: 'Targeted',
    detail: 'Strategic delta: Distributed Caching (Kafka) and Vector Databases at Scale.',
  },
  {
    label: 'System Design Readiness',
    value: '82%',
    trend: 'Staff Loop',
    detail: 'High rubric scores on architectural trade-offs, latency, and reliability.',
  },
]

const UNIFIED_METRICS = [
  {
    label: 'Overall Career Signal',
    value: '87%',
    trend: 'Dual Match',
    detail: 'Unified intelligence combining foundational skills and senior industry readiness.',
  },
  {
    label: 'Matching Opportunities',
    value: '28',
    trend: 'All Tiers',
    detail: 'Diverse roles spanning internships, associate positions, and senior roles.',
  },
  {
    label: 'Prioritized Gaps',
    value: '5',
    trend: 'Curated',
    detail: 'Sequenced roadmap from practical containerization to distributed systems.',
  },
  {
    label: 'Interview Blueprints',
    value: '4',
    trend: 'Active',
    detail: 'Tailored rubrics available for junior coding and senior architecture rounds.',
  },
]

const STUDENT_OPPORTUNITIES = [
  {
    role: 'Backend Engineer Intern',
    company: 'Northstar Labs',
    location: 'Remote',
    match: 86,
    matchedSkills: ['Python', 'FastAPI', 'PostgreSQL', 'REST APIs'],
    missingSkill: 'Docker',
    tier: 'Internship',
  },
  {
    role: 'Junior Frontend Developer',
    company: 'CivicTech Studio',
    location: 'Bengaluru',
    match: 82,
    matchedSkills: ['React', 'JavaScript', 'Tailwind CSS', 'Git'],
    missingSkill: 'TypeScript',
    tier: 'Entry Level',
  },
  {
    role: 'Associate AI Engineer',
    company: 'SignalWorks',
    location: 'Hybrid',
    match: 78,
    matchedSkills: ['Python', 'Pandas', 'REST APIs', 'SQL'],
    missingSkill: 'Vector Search',
    tier: 'Graduate',
  },
]

const PROFESSIONAL_OPPORTUNITIES = [
  {
    role: 'Senior Backend Engineer (Platform)',
    company: 'Northstar Enterprise',
    location: 'Remote',
    match: 89,
    matchedSkills: ['Python', 'FastAPI', 'PostgreSQL', 'Microservices', 'Distributed Systems'],
    missingSkill: 'Kafka',
    tier: 'Mid-Senior',
  },
  {
    role: 'Full Stack Engineering Lead',
    company: 'CivicTech Global',
    location: 'Bengaluru',
    match: 85,
    matchedSkills: ['React 19', 'FastAPI', 'Architecture', 'Team Mentorship'],
    missingSkill: 'Kubernetes',
    tier: 'Lead / Staff',
  },
  {
    role: 'Staff AI Systems Architect',
    company: 'SignalWorks Core',
    location: 'Hybrid',
    match: 82,
    matchedSkills: ['Python', 'LLM Orchestration', 'RAG Systems', 'System Design'],
    missingSkill: 'Distributed Vector Indexing',
    tier: 'Staff',
  },
]

const STUDENT_SKILL_GAPS = [
  { skill: 'Docker', domain: 'Tooling', status: 'Gap', priority: 'High', effort: '6 hrs' },
  { skill: 'System Design Basics', domain: 'Foundations', status: 'Developing', priority: 'High', effort: '12 hrs' },
  { skill: 'Unit & Integration Testing', domain: 'Quality', status: 'Next', priority: 'Medium', effort: '8 hrs' },
  { skill: 'Git Collaboration Workflows', domain: 'Tooling', status: 'In Progress', priority: 'Low', effort: '4 hrs' },
]

const PROFESSIONAL_SKILL_GAPS = [
  { skill: 'Distributed Caching & Kafka', domain: 'Architecture', status: 'Gap', priority: 'High', effort: '14 hrs' },
  { skill: 'Vector Databases at Scale', domain: 'AI Platform', status: 'Developing', priority: 'High', effort: '10 hrs' },
  { skill: 'High-Throughput System Design', domain: 'Systems', status: 'In Progress', priority: 'Medium', effort: '16 hrs' },
  { skill: 'Distributed Observability & Tracing', domain: 'Reliability', status: 'Next', priority: 'Low', effort: '6 hrs' },
]

const ACTIVITIES = [
  {
    title: 'Resume intelligence parsed',
    description: 'Extracted verified technical skills, project links, and experience signals.',
    time: '2 hours ago',
    tone: 'success',
    category: 'Resume',
  },
  {
    title: 'Role match score generated',
    description: 'Backend Engineer Intern matched with 86% explainable signal.',
    time: 'Yesterday',
    tone: 'neutral',
    category: 'Jobs',
  },
  {
    title: 'Adaptive roadmap milestone updated',
    description: 'Docker fundamentals prioritized with a 6-hour targeted study plan.',
    time: '2 days ago',
    tone: 'neutral',
    category: 'Roadmap',
  },
  {
    title: 'Mock interview evaluation recorded',
    description: 'Answer scorecard generated with rubric evidence and feedback.',
    time: '3 days ago',
    tone: 'warning',
    category: 'Interview',
  },
]

function Dashboard({ onNavigate }) {
  const [selectedTrack, setSelectedTrack] = useState(() => {
    try {
      const saved = localStorage.getItem('careerlens-track')
      if (saved === 'student' || saved === 'professional' || saved === 'unified') {
        return saved
      }
    } catch {
      // Fallback
    }
    return 'student'
  })

  useEffect(() => {
    try {
      localStorage.setItem('careerlens-track', selectedTrack)
    } catch {
      // Ignore storage errors
    }
  }, [selectedTrack])

  const greeting = useMemo(() => {
    const hour = new Date().getHours()
    if (hour < 12) return 'Good morning'
    if (hour < 18) return 'Good afternoon'
    return 'Good evening'
  }, [])

  const currentMetrics = useMemo(() => {
    if (selectedTrack === 'student') return STUDENT_METRICS
    if (selectedTrack === 'professional') return PROFESSIONAL_METRICS
    return UNIFIED_METRICS
  }, [selectedTrack])

  const currentOpportunities = useMemo(() => {
    if (selectedTrack === 'student') return STUDENT_OPPORTUNITIES
    if (selectedTrack === 'professional') return PROFESSIONAL_OPPORTUNITIES
    return [...STUDENT_OPPORTUNITIES.slice(0, 2), ...PROFESSIONAL_OPPORTUNITIES.slice(0, 2)]
  }, [selectedTrack])

  const currentSkillGaps = useMemo(() => {
    if (selectedTrack === 'student') return STUDENT_SKILL_GAPS
    if (selectedTrack === 'professional') return PROFESSIONAL_SKILL_GAPS
    return [...STUDENT_SKILL_GAPS.slice(0, 2), ...PROFESSIONAL_SKILL_GAPS.slice(0, 2)]
  }, [selectedTrack])

  const handleNavigate = (section) => {
    if (typeof onNavigate === 'function') {
      onNavigate(section)
    }
  }

  return (
    <div className="space-y-8">
      {/* Hero Zone with Track Switcher */}
      <section className="relative overflow-hidden rounded-[var(--radius-lg)] border border-[var(--cl-border-strong)] bg-[linear-gradient(145deg,var(--cl-surface),var(--cl-surface-muted))] p-6 shadow-[var(--shadow-soft)] sm:p-8">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="max-w-2xl">
            <div className="flex flex-wrap items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-[var(--cl-accent)]" />
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--cl-accent)]">
                {greeting} · CareerLens Intelligence
              </p>
            </div>

            <h1 className="mt-3 text-3xl font-bold tracking-tight text-[var(--cl-text)] sm:text-4xl">
              {selectedTrack === 'student'
                ? 'Campus to Career: Your Early Tech Pathway.'
                : selectedTrack === 'professional'
                ? 'Seniority & Transition: Your Career Velocity.'
                : 'All-in-One Career Intelligence Workspace.'}
            </h1>

            <p className="mt-3 text-sm leading-6 text-[var(--cl-muted)] sm:text-base">
              {selectedTrack === 'student'
                ? 'Translate academic coursework, GitHub repos, and college projects into verified market skills, internship matches, and structured interview practice.'
                : selectedTrack === 'professional'
                ? 'Benchmark commercial experience, close high-scale architectural skill gaps, target mid-to-senior roles, and practice advanced system design loops.'
                : 'Complete career intelligence supporting both early-stage student skill acquisition and experienced engineering seniority leveling.'}
            </p>
          </div>

          {/* Persona Track Selector */}
          <div className="flex flex-col gap-2 rounded-2xl border border-[var(--cl-border)] bg-[var(--cl-surface)] p-2 shadow-xs sm:w-auto">
            <span className="px-3 pt-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--cl-faint)]">
              Active Audience Lens
            </span>
            <div className="flex flex-wrap gap-1.5 sm:flex-nowrap">
              <button
                type="button"
                onClick={() => setSelectedTrack('student')}
                className={[
                  'flex items-center gap-2 rounded-xl px-3.5 py-2 text-xs font-semibold transition',
                  selectedTrack === 'student'
                    ? 'bg-[var(--cl-accent)] text-[var(--cl-accent-contrast)] shadow-xs'
                    : 'text-[var(--cl-muted)] hover:bg-[var(--cl-surface-muted)] hover:text-[var(--cl-text)]',
                ].join(' ')}
              >
                <span>🎓</span>
                <span>Students & Freshers</span>
              </button>

              <button
                type="button"
                onClick={() => setSelectedTrack('professional')}
                className={[
                  'flex items-center gap-2 rounded-xl px-3.5 py-2 text-xs font-semibold transition',
                  selectedTrack === 'professional'
                    ? 'bg-[var(--cl-accent)] text-[var(--cl-accent-contrast)] shadow-xs'
                    : 'text-[var(--cl-muted)] hover:bg-[var(--cl-surface-muted)] hover:text-[var(--cl-text)]',
                ].join(' ')}
              >
                <span>💼</span>
                <span>Professionals</span>
              </button>

              <button
                type="button"
                onClick={() => setSelectedTrack('unified')}
                className={[
                  'flex items-center gap-2 rounded-xl px-3.5 py-2 text-xs font-semibold transition',
                  selectedTrack === 'unified'
                    ? 'bg-[var(--cl-accent)] text-[var(--cl-accent-contrast)] shadow-xs'
                    : 'text-[var(--cl-muted)] hover:bg-[var(--cl-surface-muted)] hover:text-[var(--cl-text)]',
                ].join(' ')}
              >
                <span>⚡</span>
                <span>Dual View</span>
              </button>
            </div>
          </div>
        </div>

        {/* Quick Launchpad Buttons */}
        <div className="mt-8 grid grid-cols-2 gap-3 border-t border-[var(--cl-border)] pt-6 sm:grid-cols-4">
          <button
            type="button"
            onClick={() => handleNavigate('Resume')}
            className="group flex flex-col items-start rounded-xl border border-[var(--cl-border)] bg-[var(--cl-surface)] p-3 text-left transition hover:border-[var(--cl-accent)]/50 hover:bg-[var(--cl-surface-soft)]"
          >
            <span className="text-[10px] font-semibold uppercase tracking-wider text-[var(--cl-faint)] group-hover:text-[var(--cl-accent)]">
              01 · Resume
            </span>
            <span className="mt-1 text-sm font-semibold text-[var(--cl-text)]">
              Structured Evidence
            </span>
            <span className="mt-0.5 text-xs text-[var(--cl-muted)]">
              Upload & parse signals →
            </span>
          </button>

          <button
            type="button"
            onClick={() => handleNavigate('Jobs')}
            className="group flex flex-col items-start rounded-xl border border-[var(--cl-border)] bg-[var(--cl-surface)] p-3 text-left transition hover:border-[var(--cl-accent)]/50 hover:bg-[var(--cl-surface-soft)]"
          >
            <span className="text-[10px] font-semibold uppercase tracking-wider text-[var(--cl-faint)] group-hover:text-[var(--cl-accent)]">
              02 · Matching
            </span>
            <span className="mt-1 text-sm font-semibold text-[var(--cl-text)]">
              Role Intelligence
            </span>
            <span className="mt-0.5 text-xs text-[var(--cl-muted)]">
              Explore matches & gaps →
            </span>
          </button>

          <button
            type="button"
            onClick={() => handleNavigate('Roadmap')}
            className="group flex flex-col items-start rounded-xl border border-[var(--cl-border)] bg-[var(--cl-surface)] p-3 text-left transition hover:border-[var(--cl-accent)]/50 hover:bg-[var(--cl-surface-soft)]"
          >
            <span className="text-[10px] font-semibold uppercase tracking-wider text-[var(--cl-faint)] group-hover:text-[var(--cl-accent)]">
              03 · Roadmap
            </span>
            <span className="mt-1 text-sm font-semibold text-[var(--cl-text)]">
              Skill Bridging
            </span>
            <span className="mt-0.5 text-xs text-[var(--cl-muted)]">
              Curated learning plans →
            </span>
          </button>

          <button
            type="button"
            onClick={() => handleNavigate('Interviews')}
            className="group flex flex-col items-start rounded-xl border border-[var(--cl-border)] bg-[var(--cl-surface)] p-3 text-left transition hover:border-[var(--cl-accent)]/50 hover:bg-[var(--cl-surface-soft)]"
          >
            <span className="text-[10px] font-semibold uppercase tracking-wider text-[var(--cl-faint)] group-hover:text-[var(--cl-accent)]">
              04 · Practice
            </span>
            <span className="mt-1 text-sm font-semibold text-[var(--cl-text)]">
              Mock Interviews
            </span>
            <span className="mt-0.5 text-xs text-[var(--cl-muted)]">
              Grounded scorecards →
            </span>
          </button>
        </div>
      </section>

      {/* KPI Stats Grid */}
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {currentMetrics.map((item) => (
          <StatItem key={item.label} {...item} />
        ))}
      </section>

      {/* Dual Journey Cards (Showcasing Structured Pathways) */}
      {(selectedTrack === 'unified' || selectedTrack === 'student') && (
        <section
          className={[
            'rounded-[var(--radius-lg)] border border-[var(--cl-border)] bg-[var(--cl-surface)] p-6 shadow-xs',
            selectedTrack === 'unified' ? 'border-l-4 border-l-blue-500' : '',
          ].join(' ')}
        >
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-base">🎓</span>
                <span className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--cl-accent)]">
                  Student & Fresher Pathway
                </span>
              </div>
              <h2 className="mt-1 text-xl font-bold tracking-tight text-[var(--cl-text)]">
                Campus to Industry Readiness Blueprint
              </h2>
            </div>
            <span className="rounded-full border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] px-3 py-1 text-xs text-[var(--cl-muted)]">
              Early Career Lens
            </span>
          </div>

          <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-xl border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-4">
              <span className="text-xs font-bold text-[var(--cl-accent)]">Step 1</span>
              <p className="mt-1 text-sm font-semibold text-[var(--cl-text)]">Project Proof</p>
              <p className="mt-1 text-xs text-[var(--cl-muted)]">
                Translate coursework and GitHub repos into verified production tech signals.
              </p>
            </div>
            <div className="rounded-xl border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-4">
              <span className="text-xs font-bold text-[var(--cl-accent)]">Step 2</span>
              <p className="mt-1 text-sm font-semibold text-[var(--cl-text)]">Tooling Bridging</p>
              <p className="mt-1 text-xs text-[var(--cl-muted)]">
                Acquire industry essentials often omitted in college: Docker, Git, CI/CD, and REST design.
              </p>
            </div>
            <div className="rounded-xl border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-4">
              <span className="text-xs font-bold text-[var(--cl-accent)]">Step 3</span>
              <p className="mt-1 text-sm font-semibold text-[var(--cl-text)]">Targeted Roadmap</p>
              <p className="mt-1 text-xs text-[var(--cl-muted)]">
                Follow an 8-week structured progression tailored to entry and junior role benchmarks.
              </p>
            </div>
            <div className="rounded-xl border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-4">
              <span className="text-xs font-bold text-[var(--cl-accent)]">Step 4</span>
              <p className="mt-1 text-sm font-semibold text-[var(--cl-text)]">Starter Interviews</p>
              <p className="mt-1 text-xs text-[var(--cl-muted)]">
                Drill CS fundamentals, data structures, and STAR behavioral questions with AI rubrics.
              </p>
            </div>
          </div>
        </section>
      )}

      {(selectedTrack === 'unified' || selectedTrack === 'professional') && (
        <section
          className={[
            'rounded-[var(--radius-lg)] border border-[var(--cl-border)] bg-[var(--cl-surface)] p-6 shadow-xs',
            selectedTrack === 'unified' ? 'border-l-4 border-l-amber-500' : '',
          ].join(' ')}
        >
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-base">💼</span>
                <span className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--cl-accent)]">
                  Professional & Switcher Pathway
                </span>
              </div>
              <h2 className="mt-1 text-xl font-bold tracking-tight text-[var(--cl-text)]">
                Seniority Leveling & Lateral Transition Blueprint
              </h2>
            </div>
            <span className="rounded-full border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] px-3 py-1 text-xs text-[var(--cl-muted)]">
              Senior & Switcher Lens
            </span>
          </div>

          <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-xl border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-4">
              <span className="text-xs font-bold text-[var(--cl-accent)]">Stage 1</span>
              <p className="mt-1 text-sm font-semibold text-[var(--cl-text)]">Impact Quantification</p>
              <p className="mt-1 text-xs text-[var(--cl-muted)]">
                Surface measurable business scale, revenue outcomes, latency reductions, and leadership.
              </p>
            </div>
            <div className="rounded-xl border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-4">
              <span className="text-xs font-bold text-[var(--cl-accent)]">Stage 2</span>
              <p className="mt-1 text-sm font-semibold text-[var(--cl-text)]">Architecture Delta</p>
              <p className="mt-1 text-xs text-[var(--cl-muted)]">
                Bridge modern tech gaps: distributed caching, vector search, Kafka, and cloud scale.
              </p>
            </div>
            <div className="rounded-xl border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-4">
              <span className="text-xs font-bold text-[var(--cl-accent)]">Stage 3</span>
              <p className="mt-1 text-sm font-semibold text-[var(--cl-text)]">Strategic Matching</p>
              <p className="mt-1 text-xs text-[var(--cl-muted)]">
                Discover mid-to-senior opportunities matching your commercial seniority and compensation band.
              </p>
            </div>
            <div className="rounded-xl border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-4">
              <span className="text-xs font-bold text-[var(--cl-accent)]">Stage 4</span>
              <p className="mt-1 text-sm font-semibold text-[var(--cl-text)]">System Design Loops</p>
              <p className="mt-1 text-xs text-[var(--cl-muted)]">
                Practice high-scale architectural trade-offs, concurrency, and team leadership scenarios.
              </p>
            </div>
          </div>
        </section>
      )}

      {/* Main Content Grid: Opportunities (Left) & Skill Gaps + Activity (Right) */}
      <section className="grid gap-6 xl:grid-cols-[1.25fr_0.75fr]">
        {/* Left Column: Targeted Opportunities */}
        <div className="rounded-[var(--radius-lg)] border border-[var(--cl-border)] bg-[var(--cl-surface)] p-6 shadow-xs">
          <div className="flex flex-col gap-3 border-b border-[var(--cl-border)] pb-5 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--cl-faint)]">
                Targeted Opportunities
              </p>
              <h2 className="mt-1 text-2xl font-bold tracking-tight text-[var(--cl-text)]">
                {selectedTrack === 'student'
                  ? 'Roles Aligned with Entry & Project Signals'
                  : selectedTrack === 'professional'
                  ? 'Roles Aligned with Commercial Experience'
                  : 'Curated Opportunities Across Tiers'}
              </h2>
            </div>
            <button
              type="button"
              onClick={() => handleNavigate('Jobs')}
              className="text-xs font-semibold text-[var(--cl-accent)] hover:underline"
            >
              View all in Jobs →
            </button>
          </div>

          <div className="divide-y divide-[var(--cl-border)]">
            {currentOpportunities.map((job) => (
              <JobOpportunity
                key={`${job.company}-${job.role}`}
                {...job}
                onSelect={() => handleNavigate('Jobs')}
              />
            ))}
          </div>

          <div className="mt-5 border-t border-[var(--cl-border)] pt-4 text-center">
            <button
              type="button"
              onClick={() => handleNavigate('Jobs')}
              className="inline-flex items-center gap-2 rounded-xl border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] px-4 py-2.5 text-xs font-semibold text-[var(--cl-text)] transition hover:border-[var(--cl-accent)]/50 hover:bg-[var(--cl-surface-soft)]"
            >
              <span>Explore All Matching Jobs with Explainable Signals</span>
              <span>→</span>
            </button>
          </div>
        </div>

        {/* Right Column: Skill Gaps, Activity, and Mentorship Tip */}
        <div className="space-y-6">
          {/* Skill Gap Radar */}
          <section className="rounded-[var(--radius-lg)] border border-[var(--cl-border)] bg-[var(--cl-surface)] p-6 shadow-xs">
            <div className="flex items-center justify-between border-b border-[var(--cl-border)] pb-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--cl-faint)]">
                  Skill Gap Radar
                </p>
                <h3 className="mt-1 text-lg font-bold text-[var(--cl-text)]">
                  Prioritized Learning Delta
                </h3>
              </div>
              <button
                type="button"
                onClick={() => handleNavigate('Roadmap')}
                className="text-xs font-semibold text-[var(--cl-accent)] hover:underline"
              >
                Roadmap →
              </button>
            </div>

            <div className="mt-4 space-y-3">
              {currentSkillGaps.map((item) => (
                <div
                  key={item.skill}
                  className="flex items-center justify-between gap-3 rounded-xl border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] px-4 py-3 transition hover:border-[var(--cl-border-strong)]"
                >
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-[var(--cl-text)]">
                      {item.skill}
                    </p>
                    <div className="mt-1 flex items-center gap-2">
                      <span className="text-[11px] text-[var(--cl-muted)]">{item.domain}</span>
                      <span className="text-[10px] text-[var(--cl-faint)]">·</span>
                      <span className="text-[11px] text-[var(--cl-muted)]">Est: {item.effort}</span>
                    </div>
                  </div>
                  <span
                    className={[
                      'shrink-0 rounded-full border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider',
                      item.priority === 'High'
                        ? 'border-[var(--cl-warning)]/40 bg-[var(--cl-warning-soft)] text-[var(--cl-warning)]'
                        : 'border-[var(--cl-accent)]/30 bg-[var(--cl-accent-soft)] text-[var(--cl-accent)]',
                    ].join(' ')}
                  >
                    {item.priority} Priority
                  </span>
                </div>
              ))}
            </div>

            <button
              type="button"
              onClick={() => handleNavigate('Roadmap')}
              className="mt-4 w-full rounded-xl border border-[var(--cl-border)] bg-[var(--cl-surface-soft)] py-2.5 text-center text-xs font-semibold text-[var(--cl-text-soft)] transition hover:border-[var(--cl-accent)]/50 hover:text-[var(--cl-accent)]"
            >
              Open Adaptive Roadmap Workspace →
            </button>
          </section>

          {/* Mentorship / Actionable Advice Tip */}
          <section className="rounded-[var(--radius-lg)] border border-[var(--cl-accent)]/30 bg-[var(--cl-accent-soft)] p-5">
            <div className="flex items-start gap-3">
              <span className="text-lg">💡</span>
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-[var(--cl-accent)]">
                  {selectedTrack === 'student' ? 'Student Career Tip' : 'Professional Strategy Tip'}
                </p>
                <p className="mt-1.5 text-xs leading-5 text-[var(--cl-text-soft)]">
                  {selectedTrack === 'student'
                    ? 'Recruiters review GitHub repositories and live demos before resume text. Ensure your project README explains architectural decisions, setup instructions, and key technical trade-offs.'
                    : 'For mid and senior engineering roles, ground your interview answers in measurable metrics (e.g. latency, error rates, scaling limits) and articulate trade-offs between architectural choices.'}
                </p>
              </div>
            </div>
          </section>

          {/* Recent Activity Timeline */}
          <section className="rounded-[var(--radius-lg)] border border-[var(--cl-border)] bg-[var(--cl-surface)] p-6 shadow-xs">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--cl-faint)]">
              Intelligence Audit
            </p>
            <h3 className="mt-1 text-lg font-bold text-[var(--cl-text)]">
              Recent Activity & Milestones
            </h3>

            <ul className="mt-5 space-y-4">
              {ACTIVITIES.map((activity) => (
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
