import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider } from '../context/AuthContext'
import AuthPage from '../components/auth/AuthPage'

describe('Authentication UI & Workflows', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.restoreAllMocks()
  })

  afterEach(() => {
    cleanup()
  })

  it('renders sign-in mode by default with email and password inputs', () => {
    render(
      <AuthProvider>
        <AuthPage initialMode="login" />
      </AuthProvider>,
    )

    expect(screen.getByText('Sign in to CareerLens')).toBeInTheDocument()
    expect(screen.getByLabelText(/Email Address/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^Password$/i)).toBeInTheDocument()
    expect(screen.queryByLabelText(/Full Name/i)).not.toBeInTheDocument()
    expect(screen.getByTestId('auth-submit-btn')).toBeInTheDocument()
  })

  it('switches to create account mode and reveals the full name input and password guidelines', async () => {
    const user = userEvent.setup()
    render(
      <AuthProvider>
        <AuthPage initialMode="login" />
      </AuthProvider>,
    )

    const createAccountTab = screen.getByRole('tab', { name: /Create Account/i })
    await user.click(createAccountTab)

    expect(screen.getByText('Create your account')).toBeInTheDocument()
    expect(screen.getByLabelText(/Full Name/i)).toBeInTheDocument()
    expect(screen.getByText(/Min 12 characters/i)).toBeInTheDocument()
  })

  it('validates password minimum length of 12 characters on registration', async () => {
    const user = userEvent.setup()
    render(
      <AuthProvider>
        <AuthPage initialMode="register" />
      </AuthProvider>,
    )

    const nameInput = screen.getByLabelText(/Full Name/i)
    const emailInput = screen.getByLabelText(/Email Address/i)
    const passwordInput = screen.getByLabelText(/^Password$/i)
    const submitBtn = screen.getByTestId('auth-submit-btn')

    await user.type(nameInput, 'John Doe')
    await user.type(emailInput, 'john@example.com')
    await user.type(passwordInput, 'short')
    await user.click(submitBtn)

    expect(
      screen.getByText(/CareerLens requires a secure password of at least 12 characters/i),
    ).toBeInTheDocument()
  })

  it('autofills credentials when clicking quick demo account buttons', async () => {
    const user = userEvent.setup()
    render(
      <AuthProvider>
        <AuthPage initialMode="login" />
      </AuthProvider>,
    )

    const studentBtn = screen.getByRole('button', { name: /Student Lens/i })
    await user.click(studentBtn)

    const emailInput = screen.getByLabelText(/Email Address/i)
    const passwordInput = screen.getByLabelText(/^Password$/i)

    expect(emailInput.value).toBe('student@careerlens.dev')
    expect(passwordInput.value).toBe('CareerLens2026!Student')
  })

  it('toggles password visibility when clicking eye button', async () => {
    const user = userEvent.setup()
    render(
      <AuthProvider>
        <AuthPage initialMode="login" />
      </AuthProvider>,
    )

    const passwordInput = screen.getByLabelText(/^Password$/i)
    expect(passwordInput.type).toBe('password')

    const toggleBtn = screen.getByRole('button', { name: /Show password/i })
    await user.click(toggleBtn)
    expect(passwordInput.type).toBe('text')

    const hideBtn = screen.getByRole('button', { name: /Hide password/i })
    await user.click(hideBtn)
    expect(passwordInput.type).toBe('password')
  })

  it('handles successful sign in and stores credentials in localStorage', async () => {
    const user = userEvent.setup()
    const mockUserResponse = {
      access_token: 'fake.jwt.token',
      token_type: 'bearer',
      user: {
        id: 1,
        email: 'student@careerlens.dev',
        name: 'Aaditya Soni',
      },
    }

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify(mockUserResponse), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    )

    render(
      <AuthProvider>
        <AuthPage initialMode="login" />
      </AuthProvider>,
    )

    await user.click(screen.getByRole('button', { name: /Student Lens/i }))
    await user.click(screen.getByTestId('auth-submit-btn'))

    await waitFor(() => {
      expect(screen.getByText(/Welcome back! You are now signed in/i)).toBeInTheDocument()
    })

    expect(localStorage.getItem('careerlens_auth_token')).toBe('fake.jwt.token')
    expect(JSON.parse(localStorage.getItem('careerlens_auth_user'))).toEqual(
      mockUserResponse.user,
    )
  })
})
