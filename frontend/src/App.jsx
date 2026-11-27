import { useEffect, useMemo, useState } from 'react'
import { AuthProvider } from './context/AuthContext'
import AppShell from './components/layout/AppShell'
import AuthPage from './components/auth/AuthPage'
import Dashboard from './components/dashboard/Dashboard'
import JobsWorkspace from './components/jobs/JobsWorkspace'
import InterviewWorkspace from './components/interview/InterviewWorkspace'
import ResumeWorkspace from './components/resume/ResumeWorkspace'
import RoadmapWorkspace from './components/roadmap/RoadmapWorkspace'

function AppContent() {
  const [backendStatus, setBackendStatus] = useState('loading')
  const [activeSection, setActiveSection] = useState('Overview')
  const [theme, setTheme] = useState(() => {
    try {
      const saved = localStorage.getItem('careerlens-theme')
      if (saved === 'light' || saved === 'dark') {
        return saved
      }
      return window.matchMedia?.('(prefers-color-scheme: light)').matches
        ? 'light'
        : 'dark'
    } catch {
      return 'dark'
    }
  })

  useEffect(() => {
    try {
      document.documentElement.setAttribute('data-theme', theme)
      localStorage.setItem('careerlens-theme', theme)
    } catch {
      // Ignore storage errors in restricted contexts
    }
  }, [theme])

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'))
  }

  useEffect(() => {
    fetch('http://127.0.0.1:8000/health')
      .then((response) => {
        if (!response.ok) {
          throw new Error(
            `Request failed with status ${response.status}`,
          )
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
        description:
          'Your career intelligence workspace is ready.',
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

    if (activeSection === 'Roadmap') {
      return {
        title: 'Roadmap',
        description:
          'Turn your skill gaps into a focused, trackable learning plan.',
      }
    }

    if (activeSection === 'Interviews') {
      return {
        title: 'Interviews',
        description:
          'Practice deliberately, review grounded feedback, and build stronger answers over time.',
      }
    }

    if (activeSection === 'Account' || activeSection === 'Sign In') {
      return {
        title: 'Account & Security',
        description:
          'Sign in or register to securely persist your career intelligence profile.',
      }
    }

    return {
      title: activeSection,
      description:
        'This section will be connected in a later slice.',
    }
  }, [activeSection])

  return (
    <AppShell
      activeSection={activeSection}
      backendStatus={backendStatus}
      pageTitle={pageContext.title}
      pageDescription={pageContext.description}
      theme={theme}
      onToggleTheme={toggleTheme}
      onNavigate={setActiveSection}
    >
      {activeSection === 'Overview' ? (
        <Dashboard onNavigate={setActiveSection} />
      ) : activeSection === 'Resume' ? (
        <ResumeWorkspace />
      ) : activeSection === 'Jobs' ? (
        <JobsWorkspace />
      ) : activeSection === 'Roadmap' ? (
        <RoadmapWorkspace />
      ) : activeSection === 'Interviews' ? (
        <InterviewWorkspace />
      ) : activeSection === 'Account' || activeSection === 'Sign In' ? (
        <div className="py-6">
          <AuthPage initialMode="login" />
        </div>
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

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}

export default App
