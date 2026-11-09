import { cleanup, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import RoadmapWorkspace from '../components/roadmap/RoadmapWorkspace'
import {
  fetchJobs,
} from '../services/api/jobs'
import {
  fetchLearningResources,
  fetchLearningRoadmap,
  fetchRoadmapSchedule,
  updateLearningRoadmapProgress,
} from '../services/api/learningRoadmap'
import {
  fetchLearningPreferences,
  saveLearningPreferences,
} from '../services/api/learningPreferences'
import { fetchUserResumes } from '../services/api/resumes'

vi.mock('../services/api/jobs', () => ({
  fetchJobs: vi.fn(),
}))

vi.mock('../services/api/learningRoadmap', () => ({
  fetchLearningResources: vi.fn(),
  fetchLearningRoadmap: vi.fn(),
  fetchRoadmapSchedule: vi.fn(),
  updateLearningRoadmapProgress: vi.fn(),
}))

vi.mock('../services/api/learningPreferences', () => ({
  fetchLearningPreferences: vi.fn(),
  saveLearningPreferences: vi.fn(),
}))

vi.mock('../services/api/resumes', () => ({
  CAREERLENS_DEV_USER_ID: 3,
  fetchUserResumes: vi.fn(),
}))

const jobs = [
  { id: 10, title: 'Backend Engineer', company: 'CareerLens' },
  { id: 20, title: 'Frontend Engineer', company: 'CareerLens' },
]

const resources = {
  skill: 'python',
  total_resources: 1,
  resources: [
    {
      id: 'python-docs',
      title: 'Python documentation',
      provider: 'Python',
      resource_type: 'official_docs',
      level: 'beginner',
      url: 'https://docs.python.org/3/',
    },
  ],
}

function createRoadmap(items = [
  {
    id: 1,
    skill: 'Python',
    status: 'missing',
    priority: 'high',
    reason: 'Required for the target role.',
    progress_status: 'not_started',
    minimum_hours: 4,
    maximum_hours: 8,
    effort_available: true,
  },
  {
    id: 2,
    skill: 'SQL',
    status: 'partial',
    priority: 'high',
    reason: 'A deeper SQL foundation is useful for this role.',
    progress_status: 'in_progress',
    minimum_hours: 3,
    maximum_hours: 6,
    effort_available: true,
  },
  {
    id: 3,
    skill: 'React',
    status: 'missing',
    priority: 'medium',
    reason: 'Useful for the product surface.',
    progress_status: 'completed',
    minimum_hours: 12,
    maximum_hours: 20,
    effort_available: true,
  },
]) {
  return {
    resume_id: 1,
    job_id: 10,
    total_items: items.length,
    total_minimum_hours: items.reduce(
      (total, item) => total + (item.minimum_hours || 0),
      0,
    ),
    total_maximum_hours: items.reduce(
      (total, item) => total + (item.maximum_hours || 0),
      0,
    ),
    effort_available_items: items.filter(
      (item) => item.effort_available,
    ).length,
    effort_unavailable_items: items.filter(
      (item) => !item.effort_available,
    ).length,
    roadmap: items,
  }
}

function createRoadmapSchedule(overrides = {}) {
  return {
    resume_id: 1,
    job_id: 10,
    configured: false,
    weekly_hours: 10,
    target_completion_date: null,
    pace: 'balanced',
    remaining_minimum_hours: 7,
    remaining_maximum_hours: 14,
    estimated_minimum_weeks: 1,
    estimated_maximum_weeks: 2,
    schedule_status: 'not_configured',
    items: [],
    ...overrides,
  }
}

async function renderRoadmap(roadmap = createRoadmap()) {
  fetchUserResumes.mockResolvedValue([
    {
      id: 1,
      original_filename: 'resume.pdf',
      created_at: '2026-01-01T00:00:00Z',
    },
  ])
  fetchJobs.mockResolvedValue(jobs)
  fetchLearningRoadmap.mockResolvedValue(roadmap)
  fetchLearningPreferences.mockResolvedValue({
    user_id: 3,
    weekly_hours: 10,
    target_completion_date: null,
    pace: 'balanced',
    preferred_resource_types: [],
    is_saved: false,
  })
  fetchRoadmapSchedule.mockResolvedValue(createRoadmapSchedule())
  saveLearningPreferences.mockResolvedValue({
    user_id: 3,
    weekly_hours: 10,
    target_completion_date: null,
    pace: 'balanced',
    preferred_resource_types: [],
    is_saved: true,
  })
  fetchLearningResources.mockResolvedValue(resources)
  updateLearningRoadmapProgress.mockResolvedValue({
    id: 1,
    progress_status: 'in_progress',
  })

  const user = userEvent.setup()
  render(<RoadmapWorkspace />)

  const jobSelect = await screen.findByLabelText('Target job')
  await user.selectOptions(jobSelect, '10')
  await screen.findByTestId('learning-journey-timeline')

  return user
}

beforeEach(() => {
  vi.clearAllMocks()
})

afterEach(() => {
  cleanup()
})

describe('recommended roadmap skill', () => {
  it('uses priority, gap status, and original order without mutating the roadmap', async () => {
    const items = [
      {
        id: 1,
        skill: 'Partial high',
        priority: 'high',
        status: 'partial',
        progress_status: 'not_started',
      },
      {
        id: 2,
        skill: 'Missing high',
        priority: 'high',
        status: 'missing',
        progress_status: 'not_started',
      },
      {
        id: 3,
        skill: 'Completed high',
        priority: 'high',
        status: 'missing',
        progress_status: 'completed',
      },
    ]

    await renderRoadmap(createRoadmap(items))

    expect(
      screen.getByRole('region', { name: 'Missing high' }),
    ).toBeInTheDocument()
    expect(items.map((item) => item.id)).toEqual([1, 2, 3])
  })

  it('returns no recommendation when every item is completed', async () => {
    await renderRoadmap(
      createRoadmap([
        { id: 1, progress_status: 'completed' },
        { id: 2, progress_status: 'completed' },
      ]),
    )
    expect(screen.getByText('All roadmap skills are completed.')).toBeInTheDocument()
  })
})

describe('roadmap workflow', () => {
  it('renders the journey in roadmap order and handles unknown statuses neutrally', async () => {
    await renderRoadmap(
      createRoadmap([
        {
          ...createRoadmap().roadmap[0],
          progress_status: 'unknown_status',
        },
        createRoadmap().roadmap[1],
      ]),
    )
    const timeline = screen.getByTestId('learning-journey-timeline')
    const items = within(timeline).getAllByRole('listitem')

    expect(items[0]).toHaveTextContent('Python')
    expect(items[1]).toHaveTextContent('SQL')
    expect(timeline).toHaveTextContent('Status unavailable')
    expect(screen.getByTestId('roadmap-item-1')).toBeInTheDocument()
  })

  it('combines search, filters, and sorting while keeping the roadmap summary complete', async () => {
    const user = await renderRoadmap()
    const roadmapItems = screen.getByTestId('roadmap-items')

    expect(roadmapItems.querySelectorAll('[data-testid^="roadmap-item-"]').length).toBe(3)
    expect(screen.getByText('Total skills')).toBeInTheDocument()

    const search = screen.getByLabelText('Search skills')
    await user.type(search, 'react')
    expect(roadmapItems.querySelectorAll('[data-testid^="roadmap-item-"]').length).toBe(1)
    expect(screen.getByTestId('roadmap-item-3')).toBeInTheDocument()

    await user.clear(search)
    await user.click(screen.getByRole('button', { name: /In progress/ }))
    expect(roadmapItems.querySelectorAll('[data-testid^="roadmap-item-"]').length).toBe(1)
    expect(screen.getByTestId('roadmap-item-2')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /^All/ }))
    await user.selectOptions(screen.getByLabelText('Sort roadmap'), 'skill_asc')
    const sortedIds = [...roadmapItems.querySelectorAll('[data-testid^="roadmap-item-"]')]
      .map((item) => item.dataset.testid)
    expect(sortedIds).toEqual([
      'roadmap-item-1',
      'roadmap-item-3',
      'roadmap-item-2',
    ])
  })

  it('updates progress, shows completion feedback once, and opens the next skill on request', async () => {
    const user = await renderRoadmap()
    updateLearningRoadmapProgress.mockResolvedValueOnce({
      id: 1,
      progress_status: 'completed',
    })

    await user.selectOptions(screen.getAllByLabelText('Progress')[0], 'completed')
    expect(await screen.findByText('Python is now complete.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Continue to next skill' })).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Continue to next skill' }))
    expect(screen.getByRole('heading', { level: 2, name: 'SQL' })).toBeInTheDocument()
  })

  it('does not show completion feedback when a progress update fails', async () => {
    const user = await renderRoadmap()
    updateLearningRoadmapProgress.mockRejectedValueOnce(
      new Error('Progress service unavailable'),
    )

    await user.selectOptions(screen.getAllByLabelText('Progress')[0], 'completed')
    expect(await screen.findByText('Progress service unavailable')).toBeInTheDocument()
    expect(screen.queryByText('Python is now complete.')).not.toBeInTheDocument()
  })

  it('opens focused learning without losing search state and reuses cached resources', async () => {
    const user = await renderRoadmap()
    const search = screen.getByLabelText('Search skills')
    await user.type(search, 'sql')

    await user.click(screen.getByRole('button', { name: 'Start learning' }))
    expect(screen.getByRole('heading', { level: 2, name: 'Python' })).toBeInTheDocument()

    const focusedResourceButton = screen.getByRole('button', {
      name: 'Explore learning resources',
    })
    await user.click(focusedResourceButton)
    expect(
      (await screen.findAllByText('Python documentation')).length,
    ).toBeGreaterThan(0)
    expect(fetchLearningResources).toHaveBeenCalledTimes(1)
    expect(fetchLearningResources).toHaveBeenCalledWith('Python', 3)

    await user.click(screen.getByRole('button', { name: 'Back to roadmap' }))
    expect(screen.getByLabelText('Search skills')).toHaveValue('sql')

    await user.click(screen.getByRole('button', { name: 'Start learning' }))
    expect(fetchLearningResources).toHaveBeenCalledTimes(1)
  })

  it('refreshes expanded resources after preferences are saved', async () => {
    const user = await renderRoadmap()
    await user.click(
      screen.getAllByRole('button', {
        name: 'Explore learning resources',
      })[0],
    )
    expect(
      (await screen.findAllByText('Python documentation')).length,
    ).toBeGreaterThan(0)

    await user.click(
      screen.getByRole('button', { name: 'Save preferences' }),
    )

    await waitFor(() => {
      expect(fetchLearningResources).toHaveBeenCalledTimes(2)
    })
    expect(fetchLearningResources).toHaveBeenLastCalledWith('Python', 3)
  })

  it('retries failed resources without replacing the roadmap state', async () => {
    const user = await renderRoadmap()
    fetchLearningResources
      .mockRejectedValueOnce(new Error('Resource request failed'))
      .mockResolvedValueOnce(resources)

    await user.click(
      screen.getAllByRole('button', {
        name: 'Explore learning resources',
      })[0],
    )
    expect(
      (await screen.findAllByText('Resource request failed')).length,
    ).toBeGreaterThan(0)

    await user.click(screen.getAllByRole('button', { name: 'Retry' })[0])
    expect(
      (await screen.findAllByText('Python documentation')).length,
    ).toBeGreaterThan(0)
    expect(screen.getByTestId('learning-journey-timeline')).toBeInTheDocument()
    expect(fetchLearningResources).toHaveBeenCalledTimes(2)
  })

  it('shows the all-completed state instead of a next-skill recommendation', async () => {
    await renderRoadmap(
      createRoadmap(
        createRoadmap().roadmap.map((item) => ({
          ...item,
          progress_status: 'completed',
        })),
      ),
    )

    expect(screen.getByText('All roadmap skills are completed.')).toBeInTheDocument()
    expect(
      screen.getByText(/skills completed · 100%/),
    ).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Start learning' })).not.toBeInTheDocument()
  })

  it('ignores an older roadmap response after switching jobs', async () => {
    const requests = new Map()
    fetchJobs.mockResolvedValue(jobs)
    fetchLearningRoadmap.mockImplementation((_resumeId, jobId) =>
      new Promise((resolve) => {
        requests.set(jobId, resolve)
      }),
    )

    const user = userEvent.setup()
    render(<RoadmapWorkspace />)
    const jobSelect = await screen.findByLabelText('Target job')

    await user.selectOptions(jobSelect, '10')
    await waitFor(() => expect(requests.has(10)).toBe(true))
    await user.selectOptions(jobSelect, '20')
    await waitFor(() => expect(requests.has(20)).toBe(true))

    requests.get(10)(createRoadmap())
    await Promise.resolve()
    expect(screen.queryByTestId('learning-journey-timeline')).not.toBeInTheDocument()

    requests.get(20)(
      createRoadmap([
        {
          ...createRoadmap().roadmap[0],
          skill: 'React',
        },
      ]),
    )
    expect(
      await screen.findByRole('heading', {
        level: 2,
        name: 'Frontend Engineer',
      }),
    ).toBeInTheDocument()
  })

  it('loads the schedule for the selected resume and job', async () => {
    await renderRoadmap()

    expect(fetchRoadmapSchedule).toHaveBeenCalledWith(1, 10)
    expect(
      await screen.findByRole('heading', {
        level: 3,
        name: 'Your learning projection',
      }),
    ).toBeInTheDocument()
  })

  it('refreshes the schedule after preferences are saved', async () => {
    const user = await renderRoadmap()
    const initialCallCount = fetchRoadmapSchedule.mock.calls.length

    await user.click(
      screen.getByRole('button', { name: 'Save preferences' }),
    )

    await waitFor(() => {
      expect(fetchRoadmapSchedule.mock.calls.length).toBe(
        initialCallCount + 1,
      )
    })
  })

  it('refreshes the schedule after a successful progress update', async () => {
    const user = await renderRoadmap()
    const initialCallCount = fetchRoadmapSchedule.mock.calls.length
    updateLearningRoadmapProgress.mockResolvedValueOnce({
      id: 1,
      progress_status: 'in_progress',
    })

    await user.selectOptions(
      screen.getAllByLabelText('Progress')[0],
      'in_progress',
    )

    await waitFor(() => {
      expect(fetchRoadmapSchedule.mock.calls.length).toBe(
        initialCallCount + 1,
      )
    })
  })

  it('does not refresh the schedule after a failed progress update', async () => {
    const user = await renderRoadmap()
    const initialCallCount = fetchRoadmapSchedule.mock.calls.length
    updateLearningRoadmapProgress.mockRejectedValueOnce(
      new Error('Progress service unavailable'),
    )

    await user.selectOptions(
      screen.getAllByLabelText('Progress')[0],
      'in_progress',
    )
    await screen.findByText('Progress service unavailable')

    expect(fetchRoadmapSchedule.mock.calls.length).toBe(initialCallCount)
  })

  it('ignores an older schedule response after switching jobs', async () => {
    const requests = new Map()
    fetchLearningRoadmap.mockResolvedValue(createRoadmap())
    fetchRoadmapSchedule.mockImplementation((_resumeId, jobId) =>
      new Promise((resolve) => {
        requests.set(jobId, resolve)
      }),
    )

    const user = userEvent.setup()
    render(<RoadmapWorkspace />)
    const jobSelect = await screen.findByLabelText('Target job')

    await user.selectOptions(jobSelect, '10')
    await waitFor(() => expect(requests.has(10)).toBe(true))
    await user.selectOptions(jobSelect, '20')
    await waitFor(() => expect(requests.has(20)).toBe(true))

    requests.get(10)({
      ...createRoadmapSchedule(),
      job_id: 10,
      schedule_status: 'at_risk',
    })
    await Promise.resolve()
    expect(screen.queryByText('At risk')).not.toBeInTheDocument()

    requests.get(20)({
      ...createRoadmapSchedule(),
      job_id: 20,
      schedule_status: 'on_track',
    })
    expect(await screen.findByText('On track')).toBeInTheDocument()
  })
})
