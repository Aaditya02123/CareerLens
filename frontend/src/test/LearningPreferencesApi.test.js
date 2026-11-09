import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  fetchLearningPreferences,
  saveLearningPreferences,
} from '../services/api/learningPreferences'

afterEach(() => {
  vi.restoreAllMocks()
})

describe('learning preferences API service', () => {
  it('fetches preferences for the supplied user', async () => {
    const responseBody = {
      id: null,
      user_id: 3,
      weekly_hours: 10,
      target_completion_date: null,
      pace: 'balanced',
      preferred_resource_types: [],
      is_saved: false,
    }

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify(responseBody), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    )

    await expect(fetchLearningPreferences(3)).resolves.toEqual(
      responseBody,
    )
    expect(fetch).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/users/3/learning-preferences',
    )
  })

  it('saves preferences and surfaces API errors', async () => {
    const payload = {
      weekly_hours: 8,
      target_completion_date: null,
      pace: 'flexible',
      preferred_resource_types: ['practice'],
    }

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({ detail: 'Preferences could not be saved.' }),
          {
            status: 500,
            headers: { 'Content-Type': 'application/json' },
          },
        ),
      ),
    )

    await expect(saveLearningPreferences(3, payload)).rejects.toThrow(
      'Preferences could not be saved.',
    )
    expect(fetch).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/users/3/learning-preferences',
      expect.objectContaining({
        method: 'PUT',
        body: JSON.stringify(payload),
      }),
    )
  })
})
