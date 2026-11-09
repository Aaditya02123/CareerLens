import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import LearningPreferencesPanel from '../components/roadmap/LearningPreferencesPanel'
import {
  fetchLearningPreferences,
  saveLearningPreferences,
} from '../services/api/learningPreferences'

vi.mock('../services/api/learningPreferences', () => ({
  fetchLearningPreferences: vi.fn(),
  saveLearningPreferences: vi.fn(),
}))

function savedPreferences(overrides = {}) {
  return {
    user_id: 3,
    weekly_hours: 12,
    target_completion_date: '2099-12-31',
    pace: 'intensive',
    preferred_resource_types: ['tutorial'],
    is_saved: true,
    ...overrides,
  }
}

beforeEach(() => {
  vi.clearAllMocks()
  fetchLearningPreferences.mockResolvedValue(savedPreferences())
  saveLearningPreferences.mockResolvedValue(savedPreferences())
})
afterEach(() => {
  cleanup()
})

describe('LearningPreferencesPanel', () => {
  it('loads and displays saved preferences', async () => {
    render(<LearningPreferencesPanel userId={3} />)

    expect(
      await screen.findByDisplayValue('12'),
    ).toBeInTheDocument()
    expect(screen.getByDisplayValue('2099-12-31')).toBeInTheDocument()
    expect(screen.getByLabelText('Intensive')).toBeChecked()
    expect(screen.getByLabelText('Tutorials')).toBeChecked()
    expect(screen.getByText('Saved preferences')).toBeInTheDocument()
  })

  it('shows defaults when preferences are not saved', async () => {
    fetchLearningPreferences.mockResolvedValueOnce({
      user_id: 3,
      weekly_hours: 10,
      target_completion_date: null,
      pace: 'balanced',
      preferred_resource_types: [],
      is_saved: false,
    })

    render(<LearningPreferencesPanel userId={3} />)

    expect(await screen.findByDisplayValue('10')).toBeInTheDocument()
    expect(screen.getByLabelText('Balanced')).toBeChecked()
    expect(screen.getByText('Using defaults')).toBeInTheDocument()
  })

  it('validates weekly hours and past target dates before saving', async () => {
    const user = userEvent.setup()
    render(<LearningPreferencesPanel userId={3} />)
    await screen.findByDisplayValue('12')

    const weeklyHours = screen.getByLabelText('Weekly study hours')
    await user.clear(weeklyHours)
    await user.type(weeklyHours, '0')

    fireEvent.change(screen.getByLabelText('Target completion date'), {
      target: { value: '2020-01-01' },
    })
    await user.click(screen.getByRole('button', { name: 'Save preferences' }))

    expect(
      screen.getByText('Enter a whole number from 1 to 168 hours.'),
    ).toBeInTheDocument()
    expect(
      screen.getByText('Choose today or a future date.'),
    ).toBeInTheDocument()
    expect(saveLearningPreferences).not.toHaveBeenCalled()
  })

  it('saves resource format selections and notifies the workspace', async () => {
    const user = userEvent.setup()
    const onSaved = vi.fn()
    render(<LearningPreferencesPanel userId={3} onSaved={onSaved} />)
    await screen.findByDisplayValue('12')

    await user.click(screen.getByLabelText('Official documentation'))
    await user.click(screen.getByRole('button', { name: 'Save preferences' }))

    await waitFor(() => {
      expect(saveLearningPreferences).toHaveBeenCalledWith(
        3,
        expect.objectContaining({
          weekly_hours: 12,
          target_completion_date: '2099-12-31',
          pace: 'intensive',
          preferred_resource_types: ['tutorial', 'official_docs'],
        }),
      )
    })
    expect(onSaved).toHaveBeenCalled()
    expect(
      await screen.findByText('Learning preferences saved.'),
    ).toBeInTheDocument()
  })

  it('preserves input and shows an error when saving fails', async () => {
    const user = userEvent.setup()
    saveLearningPreferences.mockRejectedValueOnce(
      new Error('Preferences unavailable'),
    )
    render(<LearningPreferencesPanel userId={3} />)
    await screen.findByDisplayValue('12')

    const weeklyHours = screen.getByLabelText('Weekly study hours')
    await user.clear(weeklyHours)
    await user.type(weeklyHours, '24')
    await user.click(screen.getByRole('button', { name: 'Save preferences' }))

    expect(await screen.findByText('Preferences unavailable')).toBeInTheDocument()
    expect(weeklyHours).toHaveValue(24)
  })

  it('prevents duplicate submissions while a save is pending', async () => {
    const user = userEvent.setup()
    let resolveSave
    saveLearningPreferences.mockImplementationOnce(
      () => new Promise((resolve) => {
        resolveSave = resolve
      }),
    )
    render(<LearningPreferencesPanel userId={3} />)
    await screen.findByDisplayValue('12')

    const saveButton = screen.getByRole('button', {
      name: 'Save preferences',
    })
    await user.click(saveButton)
    await user.click(saveButton)

    expect(saveLearningPreferences).toHaveBeenCalledTimes(1)

    resolveSave(savedPreferences())
    await waitFor(() => {
      expect(screen.getByText('Learning preferences saved.')).toBeInTheDocument()
    })
  })
})
