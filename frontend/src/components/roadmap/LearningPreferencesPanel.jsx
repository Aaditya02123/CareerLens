import { useCallback, useEffect, useRef, useState } from 'react'
import { useAuth } from '../../context/AuthContext'

import {
  fetchLearningPreferences,
  saveLearningPreferences,
} from '../../services/api/learningPreferences'

const DEFAULT_WEEKLY_HOURS = 10
const DEFAULT_PACE = 'balanced'
const RESOURCE_TYPES = [
  {
    value: 'official_docs',
    label: 'Official documentation',
  },
  { value: 'tutorial', label: 'Tutorials' },
  { value: 'practice', label: 'Practice' },
  { value: 'course', label: 'Courses' },
]

const PACE_OPTIONS = [
  { value: 'flexible', label: 'Flexible' },
  { value: 'balanced', label: 'Balanced' },
  { value: 'intensive', label: 'Intensive' },
]

function getTodayIsoDate() {
  const today = new Date()
  const month = String(today.getMonth() + 1).padStart(2, '0')
  const day = String(today.getDate()).padStart(2, '0')

  return `${today.getFullYear()}-${month}-${day}`
}

function getDefaultForm() {
  return {
    weeklyHours: String(DEFAULT_WEEKLY_HOURS),
    targetCompletionDate: '',
    pace: DEFAULT_PACE,
    preferredResourceTypes: [],
  }
}

function formFromResponse(response) {
  return {
    weeklyHours: String(
      response?.weekly_hours ?? DEFAULT_WEEKLY_HOURS,
    ),
    targetCompletionDate: response?.target_completion_date || '',
    pace: response?.pace || DEFAULT_PACE,
    preferredResourceTypes: Array.isArray(
      response?.preferred_resource_types,
    )
      ? response.preferred_resource_types
      : [],
  }
}

function validateForm(form) {
  const errors = {}
  const weeklyHours = Number(form.weeklyHours)
  const today = getTodayIsoDate()

  if (!Number.isInteger(weeklyHours) || weeklyHours < 1 || weeklyHours > 168) {
    errors.weeklyHours = 'Enter a whole number from 1 to 168 hours.'
  }

  if (form.targetCompletionDate && form.targetCompletionDate < today) {
    errors.targetCompletionDate = 'Choose today or a future date.'
  }

  return {
    errors,
    payload: {
      weekly_hours: weeklyHours,
      target_completion_date: form.targetCompletionDate || null,
      pace: form.pace,
      preferred_resource_types: form.preferredResourceTypes,
    },
  }
}

export default function LearningPreferencesPanel({
  userId,
  onSaved,
}) {
  const { user } = useAuth()
  const activeUserId = user?.id || userId

  const [form, setForm] = useState(getDefaultForm)
  const [isSaved, setIsSaved] = useState(false)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [loadError, setLoadError] = useState('')
  const [saveError, setSaveError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const [validationErrors, setValidationErrors] = useState({})
  const requestIdRef = useRef(0)

  const loadPreferences = useCallback(async () => {
    if (!activeUserId) {
      setLoading(false)
      setForm(getDefaultForm())
      return
    }

    const requestId = ++requestIdRef.current
    setLoading(true)
    setLoadError('')
    setSuccessMessage('')

    try {
      const response = await fetchLearningPreferences(activeUserId)

      if (requestId !== requestIdRef.current) return

      setForm(formFromResponse(response))
      setIsSaved(response?.is_saved === true)
    } catch (error) {
      if (requestId !== requestIdRef.current) return

      setLoadError(
        error?.message ||
          'CareerLens could not load learning preferences.',
      )
    } finally {
      if (requestId === requestIdRef.current) {
        setLoading(false)
      }
    }
  }, [activeUserId])

  useEffect(() => {
    setForm(getDefaultForm())
    setIsSaved(false)
    setValidationErrors({})
    setSaveError('')
    void loadPreferences()
  }, [loadPreferences])

  function updateField(field, value) {
    setForm((current) => ({ ...current, [field]: value }))
    setValidationErrors((current) => ({ ...current, [field]: '' }))
    setSaveError('')
    setSuccessMessage('')
  }

  function toggleResourceType(resourceType) {
    setForm((current) => {
      const selected = current.preferredResourceTypes.includes(
        resourceType,
      )

      return {
        ...current,
        preferredResourceTypes: selected
          ? current.preferredResourceTypes.filter(
              (value) => value !== resourceType,
            )
          : [...current.preferredResourceTypes, resourceType],
      }
    })
    setSaveError('')
    setSuccessMessage('')
  }

  async function handleSubmit(event) {
    event.preventDefault()

    if (saving) return

    const { errors, payload } = validateForm(form)
    setValidationErrors(errors)
    setSaveError('')
    setSuccessMessage('')

    if (Object.keys(errors).length > 0) return

    setSaving(true)

    try {
      const response = await saveLearningPreferences(activeUserId, payload)

      setForm(formFromResponse(response))
      setIsSaved(response?.is_saved === true)
      setSuccessMessage('Learning preferences saved.')

      if (onSaved) {
        await onSaved(response)
      }
    } catch (error) {
      setSaveError(
        error?.message ||
          'CareerLens could not save learning preferences.',
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <section
      className="mt-6 rounded-2xl border border-[var(--cl-border)] bg-[var(--cl-surface)] p-5"
      aria-labelledby="learning-preferences-heading"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--cl-accent)]">
            Personalize your pace
          </p>
          <h2
            id="learning-preferences-heading"
            className="mt-2 text-lg font-medium text-[var(--cl-text)]"
          >
            Learning preferences
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-[var(--cl-muted)]">
            Set your availability so CareerLens can project a realistic
            learning schedule. These preferences do not change roadmap
            priorities or estimates.
          </p>
        </div>

        {!loading && !loadError && (
          <span className="rounded-full border border-[var(--cl-border)] px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.13em] text-[var(--cl-muted)]">
            {isSaved ? 'Saved preferences' : 'Using defaults'}
          </span>
        )}
      </div>

      {loading ? (
        <div
          className="mt-5 h-28 animate-pulse rounded-xl bg-[var(--cl-surface-soft)]"
          aria-label="Loading learning preferences"
        />
      ) : loadError ? (
        <div className="mt-5" role="alert">
          <p className="text-sm text-red-200/75">{loadError}</p>
          <button
            type="button"
            onClick={loadPreferences}
            className="mt-3 rounded-lg border border-[var(--cl-border)] px-3 py-2 text-xs text-[var(--cl-text-soft)] transition hover:border-[var(--cl-accent)] hover:text-[var(--cl-text)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--cl-accent)]"
          >
            Try again
          </button>
        </div>
      ) : (
        <form className="mt-5" onSubmit={handleSubmit} noValidate>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label
                htmlFor="learning-weekly-hours"
                className="block text-[10px] font-semibold uppercase tracking-[0.16em] text-[var(--cl-faint)]"
              >
                Weekly study hours
              </label>
              <input
                id="learning-weekly-hours"
                type="number"
                min="1"
                max="168"
                step="1"
                inputMode="numeric"
                value={form.weeklyHours}
                onChange={(event) =>
                  updateField('weeklyHours', event.target.value)
                }
                aria-invalid={Boolean(validationErrors.weeklyHours)}
                aria-describedby="learning-weekly-hours-help learning-weekly-hours-error"
                className="mt-2 w-full rounded-lg border border-[var(--cl-border)] bg-[var(--cl-input-bg)] px-3 py-2.5 text-sm text-[var(--cl-text-soft)] outline-none transition focus:border-[var(--cl-accent)]"
              />
              <p
                id="learning-weekly-hours-help"
                className="mt-2 text-xs text-[var(--cl-faint)]"
              >
                Choose between 1 and 168 hours per week.
              </p>
              {validationErrors.weeklyHours && (
                <p
                  id="learning-weekly-hours-error"
                  className="mt-1 text-xs text-red-200/75"
                  role="alert"
                >
                  {validationErrors.weeklyHours}
                </p>
              )}
            </div>

            <div>
              <label
                htmlFor="learning-target-date"
                className="block text-[10px] font-semibold uppercase tracking-[0.16em] text-[var(--cl-faint)]"
              >
                Target completion date
              </label>
              <input
                id="learning-target-date"
                type="date"
                min={getTodayIsoDate()}
                value={form.targetCompletionDate}
                onChange={(event) =>
                  updateField(
                    'targetCompletionDate',
                    event.target.value,
                  )
                }
                aria-invalid={Boolean(
                  validationErrors.targetCompletionDate,
                )}
                aria-describedby="learning-target-date-help learning-target-date-error"
                className="mt-2 w-full rounded-lg border border-[var(--cl-border)] bg-[var(--cl-input-bg)] px-3 py-2.5 text-sm text-[var(--cl-text-soft)] outline-none transition focus:border-[var(--cl-accent)]"
              />
              <p
                id="learning-target-date-help"
                className="mt-2 text-xs text-[var(--cl-faint)]"
              >
                Optional. Leave blank when you do not have a target date.
              </p>
              {validationErrors.targetCompletionDate && (
                <p
                  id="learning-target-date-error"
                  className="mt-1 text-xs text-red-200/75"
                  role="alert"
                >
                  {validationErrors.targetCompletionDate}
                </p>
              )}
            </div>
          </div>

          <fieldset className="mt-5">
            <legend className="block text-[10px] font-semibold uppercase tracking-[0.16em] text-[var(--cl-faint)]">
              Learning pace
            </legend>
            <div className="mt-3 grid gap-2 sm:grid-cols-3">
              {PACE_OPTIONS.map((option) => (
                <label
                  key={option.value}
                  className="flex cursor-pointer items-center gap-2 rounded-lg border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] px-3 py-2.5 text-sm text-[var(--cl-text-soft)] transition has-[:checked]:border-[var(--cl-accent)]/50 has-[:checked]:text-[var(--cl-accent)]"
                >
                  <input
                    type="radio"
                    name="learning-pace"
                    value={option.value}
                    checked={form.pace === option.value}
                    onChange={(event) =>
                      updateField('pace', event.target.value)
                    }
                    className="accent-[var(--cl-accent)]"
                  />
                  {option.label}
                </label>
              ))}
            </div>
          </fieldset>

          <fieldset className="mt-5">
            <legend className="block text-[10px] font-semibold uppercase tracking-[0.16em] text-[var(--cl-faint)]">
              Preferred resource formats
            </legend>
            <p className="mt-2 text-xs text-[var(--cl-faint)]">
              Leave all unchecked to accept every curated format.
            </p>
            <div className="mt-3 grid gap-2 sm:grid-cols-2">
              {RESOURCE_TYPES.map((resourceType) => (
                <label
                  key={resourceType.value}
                  className="flex cursor-pointer items-center gap-2 rounded-lg border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] px-3 py-2.5 text-sm text-[var(--cl-text-soft)] transition has-[:checked]:border-[var(--cl-accent)]/50 has-[:checked]:text-[var(--cl-accent)]"
                >
                  <input
                    type="checkbox"
                    checked={form.preferredResourceTypes.includes(
                      resourceType.value,
                    )}
                    onChange={() =>
                      toggleResourceType(resourceType.value)
                    }
                    className="accent-[var(--cl-accent)]"
                  />
                  {resourceType.label}
                </label>
              ))}
            </div>
          </fieldset>

          {saveError && (
            <p className="mt-4 text-sm leading-5 text-[var(--cl-danger)]" role="alert">
              {saveError}
            </p>
          )}

          {successMessage && (
            <p className="mt-4 text-sm leading-5 text-[var(--cl-success)]" role="status">
              {successMessage}
            </p>
          )}

          <button
            type="submit"
            disabled={saving}
            className="mt-5 rounded-lg bg-[var(--cl-accent)] px-4 py-2.5 text-xs font-semibold text-[var(--cl-accent-contrast)] transition hover:bg-[var(--cl-accent-hover)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--cl-accent)]/80 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {saving ? 'Saving preferences...' : 'Save preferences'}
          </button>
        </form>
      )}
    </section>
  )
}
