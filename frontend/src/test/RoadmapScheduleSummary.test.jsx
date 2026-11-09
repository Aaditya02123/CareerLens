import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'

import RoadmapScheduleSummary from '../components/roadmap/RoadmapScheduleSummary'

afterEach(() => {
  cleanup()
})
function schedule(overrides = {}) {
  return {
    resume_id: 1,
    job_id: 10,
    configured: true,
    weekly_hours: 10,
    target_completion_date: '2099-12-31',
    pace: 'balanced',
    remaining_minimum_hours: 12,
    remaining_maximum_hours: 20,
    estimated_minimum_weeks: 2,
    estimated_maximum_weeks: 2,
    schedule_status: 'on_track',
    items: [],
    ...overrides,
  }
}

describe('RoadmapScheduleSummary', () => {
  it('displays configured schedule values and on-track status', () => {
    render(<RoadmapScheduleSummary schedule={schedule()} />)

    expect(screen.getByText('On track')).toBeInTheDocument()
    expect(screen.getByText('12–20 hrs')).toBeInTheDocument()
    expect(screen.getByText('2–2 wks')).toBeInTheDocument()
    expect(screen.getByText(/Preferences: saved/)).toBeInTheDocument()
    expect(screen.getByText(/2099/)).toBeInTheDocument()
  })

  it.each([
    ['not_configured', 'Using defaults'],
    ['no_estimate', 'Estimate unavailable'],
    ['completed', 'Roadmap complete'],
    ['no_target_date', 'No target date'],
    ['at_risk', 'At risk'],
  ])('renders the %s status', (status, label) => {
    render(
      <RoadmapScheduleSummary
        schedule={schedule({ schedule_status: status })}
      />,
    )

    expect(screen.getByText(label)).toBeInTheDocument()
  })

  it('handles zero remaining effort and unknown statuses safely', () => {
    render(
      <RoadmapScheduleSummary
        schedule={schedule({
          schedule_status: 'future_status',
          remaining_minimum_hours: 0,
          remaining_maximum_hours: 0,
        })}
      />,
    )

    expect(screen.getByText('Status unavailable')).toBeInTheDocument()
    expect(screen.getByText('0 hrs')).toBeInTheDocument()
    expect(screen.getByText('Complete')).toBeInTheDocument()
  })

  it('shows loading, error, and retry states', async () => {
    const user = userEvent.setup()
    const onRetry = vi.fn()
    const { rerender } = render(
      <RoadmapScheduleSummary loading onRetry={onRetry} />,
    )

    expect(screen.getByLabelText('Loading roadmap schedule')).toBeInTheDocument()

    rerender(
      <RoadmapScheduleSummary
        error="Schedule unavailable"
        onRetry={onRetry}
      />,
    )
    expect(screen.getByText('Schedule unavailable')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Retry schedule' }))
    expect(onRetry).toHaveBeenCalledTimes(1)
  })
})
