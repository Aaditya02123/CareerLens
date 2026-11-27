import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import Dashboard from '../components/dashboard/Dashboard'

describe('Dashboard (Overview Page)', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  afterEach(() => {
    cleanup()
  })

  it('renders student and fresher lens by default with relevant metrics and pathways', () => {
    render(<Dashboard />)

    expect(screen.getByText('Campus to Career: Your Early Tech Pathway.')).toBeInTheDocument()
    expect(screen.getByText('Student & Fresher Pathway')).toBeInTheDocument()
    expect(screen.getByText('Campus to Industry Readiness Blueprint')).toBeInTheDocument()
    expect(screen.getByText('Resume Readiness')).toBeInTheDocument()
    expect(screen.getByText('Internship & Junior Roles')).toBeInTheDocument()
    expect(screen.getByText('Roles Aligned with Entry & Project Signals')).toBeInTheDocument()
    expect(screen.getByText('Backend Engineer Intern')).toBeInTheDocument()
  })

  it('switches to professional track when professional button is clicked', async () => {
    const user = userEvent.setup()
    render(<Dashboard />)

    const professionalBtn = screen.getByRole('button', { name: /Professionals/i })
    await user.click(professionalBtn)

    expect(screen.getByText('Seniority & Transition: Your Career Velocity.')).toBeInTheDocument()
    expect(screen.getByText('Professional & Switcher Pathway')).toBeInTheDocument()
    expect(screen.getByText('Commercial Impact')).toBeInTheDocument()
    expect(screen.getByText('Roles Aligned with Commercial Experience')).toBeInTheDocument()
    expect(screen.getByText('Senior Backend Engineer (Platform)')).toBeInTheDocument()
  })

  it('switches to dual / unified view displaying both pathways', async () => {
    const user = userEvent.setup()
    render(<Dashboard />)

    const dualViewBtn = screen.getByRole('button', { name: /Dual View/i })
    await user.click(dualViewBtn)

    expect(screen.getByText('All-in-One Career Intelligence Workspace.')).toBeInTheDocument()
    expect(screen.getByText('Student & Fresher Pathway')).toBeInTheDocument()
    expect(screen.getByText('Professional & Switcher Pathway')).toBeInTheDocument()
    expect(screen.getByText('Overall Career Signal')).toBeInTheDocument()
  })

  it('calls onNavigate callback when quick launchpad and action buttons are clicked', async () => {
    const user = userEvent.setup()
    const handleNavigate = vi.fn()
    render(<Dashboard onNavigate={handleNavigate} />)

    const resumeBtn = screen.getByRole('button', { name: /01 · Resume/i })
    await user.click(resumeBtn)
    expect(handleNavigate).toHaveBeenCalledWith('Resume')

    const jobsBtn = screen.getByRole('button', { name: /02 · Matching/i })
    await user.click(jobsBtn)
    expect(handleNavigate).toHaveBeenCalledWith('Jobs')

    const roadmapBtn = screen.getByRole('button', { name: /03 · Roadmap/i })
    await user.click(roadmapBtn)
    expect(handleNavigate).toHaveBeenCalledWith('Roadmap')

    const interviewBtn = screen.getByRole('button', { name: /04 · Practice/i })
    await user.click(interviewBtn)
    expect(handleNavigate).toHaveBeenCalledWith('Interviews')
  })
})
