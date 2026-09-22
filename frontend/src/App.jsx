import { useEffect, useMemo, useState } from 'react'
import AppShell from './components/layout/AppShell'
import Dashboard from './components/dashboard/Dashboard'
import ResumeWorkspace from './components/resume/ResumeWorkspace'
import JobsWorkspace from './components/jobs/JobsWorkspace'

function App() {
  const [backendStatus, setBackendStatus] = useState('loading')
  const [activeSection, setActiveSection] = useState('Overview')

  useEffect(() => {
    fetch('http://127.0.0.1:8000/health')
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Request failed with status ${response.status}`)
        }

        return response.json()
      })
      .then((data) => setBackendStatus(data.status))
      .catch(() => setBackendStatus('unavailable'))
  }, [])

  const pageContext = useMemo(() => {
    if (activeSection === 'Overview') {
      return {
        title: 'Overview',
        description: 'Your career intelligence workspace is ready.',
      }
    }

    if (activeSection === 'Resume') {
      return {
        title: 'Resume',
        description:
          'Upload once. Turn your resume into structured career intelligence.',
      }
    }

    if (activeSection === 'Jobs') {
      return {
        title: 'Jobs',
        description:
          'Discover opportunities, understand your match, and identify the skills that can move you closer to the role.',
      }
    }

    return {
      title: activeSection,
      description: 'This section will be connected in a later slice.',
    }
  }, [activeSection])

  return (
    <AppShell
      activeSection={activeSection}
      backendStatus={backendStatus}
      pageTitle={pageContext.title}
      pageDescription={pageContext.description}
      onNavigate={setActiveSection}
    >
      {activeSection === 'Overview' ? (
        <Dashboard />
      ) : activeSection === 'Resume' ? (
        <ResumeWorkspace />
      ) : activeSection === 'Jobs' ? (
        <JobsWorkspace />
      ) : (
        <section className="rounded-[var(--radius-lg)] border border-[var(--cl-border)] bg-[var(--cl-surface)] p-8 shadow-[var(--shadow-soft)]">
          <p className="text-sm font-medium uppercase tracking-[0.22em] text-[var(--cl-accent)]">
            {activeSection}
          </p>

          <h1 className="mt-4 text-3xl font-semibold tracking-tight text-[var(--cl-text)]">
            {activeSection} workspace is coming next.
          </h1>

          <p className="mt-3 max-w-2xl text-sm leading-6 text-[var(--cl-muted)]">
            The navigation shell is in place so future CareerLens modules can
            be added incrementally without changing the overall product frame.
          </p>
        </section>
      )}
    </AppShell>
  )
}

export default App