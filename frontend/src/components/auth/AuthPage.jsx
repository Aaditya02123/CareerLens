import { useEffect, useId, useMemo, useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import {
  AlertCircle,
  ArrowRight,
  Briefcase,
  CheckCircle2,
  Eye,
  EyeOff,
  GraduationCap,
  Lock,
  Mail,
  ShieldCheck,
  Sparkles,
  User as UserIcon,
  X,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

export default function AuthPage({ isModal = false, onClose = null, initialMode = null }) {
  const { login, register, authMode: contextAuthMode, setAuthMode: setContextAuthMode } = useAuth()
  const [mode, setMode] = useState(() => initialMode || contextAuthMode || 'login')

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState(null)
  const [successMessage, setSuccessMessage] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const nameInputId = useId()
  const emailInputId = useId()
  const passwordInputId = useId()

  useEffect(() => {
    if (contextAuthMode && !initialMode) {
      setMode(contextAuthMode)
    }
  }, [contextAuthMode, initialMode])

  const handleModeChange = (newMode) => {
    setMode(newMode)
    setContextAuthMode?.(newMode)
    setError(null)
    setSuccessMessage(null)
  }

  // Password analysis
  const passwordMetrics = useMemo(() => {
    const hasMinLength = password.length >= 12
    const hasMixedCase = /[a-z]/.test(password) && /[A-Z]/.test(password)
    const hasNumberOrSymbol = /[\d!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]/.test(password)

    let score = 0
    if (password.length > 0) score += 1
    if (hasMinLength) score += 1
    if (hasMixedCase) score += 1
    if (hasNumberOrSymbol) score += 1

    return {
      hasMinLength,
      hasMixedCase,
      hasNumberOrSymbol,
      score,
      label:
        score <= 1
          ? 'Weak'
          : score === 2
            ? 'Fair'
            : score === 3
              ? 'Good'
              : 'Strong',
      color:
        score <= 1
          ? 'bg-[var(--cl-danger)]'
          : score === 2
            ? 'bg-[var(--cl-warning)]'
            : 'bg-[var(--cl-success)]',
      textColor:
        score <= 1
          ? 'text-[var(--cl-danger)]'
          : score === 2
            ? 'text-[var(--cl-warning)]'
            : 'text-[var(--cl-success)]',
    }
  }, [password])

  const handleQuickDemo = (role) => {
    setError(null)
    setSuccessMessage(null)
    if (role === 'student') {
      setEmail('student@careerlens.dev')
      setName('Aaditya Soni')
      setPassword('CareerLens2026!Student')
    } else {
      setEmail('professional@careerlens.dev')
      setName('Alex Morgan')
      setPassword('CareerLens2026!Pro')
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setSuccessMessage(null)

    if (mode === 'register' && !name.trim()) {
      setError('Please provide your full name.')
      return
    }

    if (!email.trim() || !email.includes('@')) {
      setError('Please provide a valid email address.')
      return
    }

    if (mode === 'register' && password.length < 12) {
      setError('CareerLens requires a secure password of at least 12 characters.')
      return
    }

    if (mode === 'login' && !password) {
      setError('Please enter your password.')
      return
    }

    setIsSubmitting(true)
    try {
      if (mode === 'register') {
        await register(name.trim(), email.trim(), password)
        setSuccessMessage('Account created successfully! Welcome to CareerLens.')
      } else {
        await login(email.trim(), password)
        setSuccessMessage('Welcome back! You are now signed in.')
      }
      if (isModal && onClose) {
        setTimeout(() => onClose(), 600)
      }
    } catch (err) {
      setError(err?.message || 'Authentication failed. Please check your credentials.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div
      className={
        isModal
          ? 'relative w-full max-w-md overflow-hidden rounded-[var(--radius-lg)] border border-[var(--cl-border-strong)] bg-[var(--cl-surface)] p-6 sm:p-8 shadow-[var(--shadow-soft)]'
          : 'relative mx-auto w-full max-w-lg overflow-hidden rounded-[var(--radius-lg)] border border-[var(--cl-border)] bg-[var(--cl-surface)] p-6 sm:p-8 shadow-[var(--shadow-soft)]'
      }
    >
      {/* Background ambient lighting blur */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -top-24 -left-24 h-56 w-56 rounded-full bg-[var(--cl-accent)] opacity-10 blur-3xl"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -bottom-24 -right-24 h-56 w-56 rounded-full bg-[var(--cl-success)] opacity-10 blur-3xl"
      />

      {/* Modal Close Button */}
      {isModal && onClose && (
        <button
          type="button"
          onClick={onClose}
          aria-label="Close dialog"
          className="absolute top-4 right-4 z-10 grid h-8 w-8 place-items-center rounded-full border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] text-[var(--cl-muted)] transition hover:text-[var(--cl-text)]"
        >
          <X className="h-4 w-4" />
        </button>
      )}

      {/* Header Branding */}
      <div className="relative text-center">
        <motion.div
          initial={{ scale: 0.85, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: 'spring', stiffness: 400, damping: 25 }}
          className="mx-auto inline-flex items-center gap-2 rounded-full border border-[var(--cl-accent)]/30 bg-[var(--cl-accent-soft)] px-3.5 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--cl-accent)]"
        >
          <Sparkles className="h-3.5 w-3.5" />
          CareerLens Security
        </motion.div>

        <h2 className="mt-3 text-2xl sm:text-3xl font-semibold tracking-tight text-[var(--cl-text)]">
          {mode === 'login' ? 'Sign in to CareerLens' : 'Create your account'}
        </h2>
        <p className="mt-1 text-xs sm:text-sm text-[var(--cl-muted)]">
          {mode === 'login'
            ? 'Access your resume intelligence, learning roadmap, and mock interviews.'
            : 'Join students and professionals leveling up their career velocity.'}
        </p>
      </div>

      {/* Mode Switcher Tabs */}
      <div
        role="tablist"
        aria-label="Authentication modes"
        className="relative mt-6 grid grid-cols-2 rounded-[var(--radius-md)] border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-1"
      >
        <button
          type="button"
          role="tab"
          aria-selected={mode === 'login'}
          onClick={() => handleModeChange('login')}
          className={`relative z-10 py-2 text-xs sm:text-sm font-medium transition ${
            mode === 'login' ? 'text-[var(--cl-text)]' : 'text-[var(--cl-muted)] hover:text-[var(--cl-text-soft)]'
          }`}
        >
          {mode === 'login' && (
            <motion.div
              layoutId="auth-tab-pill"
              className="absolute inset-0 rounded-[calc(var(--radius-md)-2px)] bg-[var(--cl-surface)] shadow-xs"
              transition={{ type: 'spring', stiffness: 450, damping: 32 }}
            />
          )}
          <span className="relative z-10">Sign In</span>
        </button>

        <button
          type="button"
          role="tab"
          aria-selected={mode === 'register'}
          onClick={() => handleModeChange('register')}
          className={`relative z-10 py-2 text-xs sm:text-sm font-medium transition ${
            mode === 'register' ? 'text-[var(--cl-text)]' : 'text-[var(--cl-muted)] hover:text-[var(--cl-text-soft)]'
          }`}
        >
          {mode === 'register' && (
            <motion.div
              layoutId="auth-tab-pill"
              className="absolute inset-0 rounded-[calc(var(--radius-md)-2px)] bg-[var(--cl-surface)] shadow-xs"
              transition={{ type: 'spring', stiffness: 450, damping: 32 }}
            />
          )}
          <span className="relative z-10">Create Account</span>
        </button>
      </div>

      {/* Demo Credentials Quick Switcher */}
      <div className="mt-4 rounded-[var(--radius-md)] border border-[var(--cl-border)] bg-[var(--cl-surface-soft)] p-3">
        <div className="flex items-center justify-between text-xs text-[var(--cl-muted)]">
          <span className="font-medium">Quick Demo Accounts:</span>
          <span className="text-[10px] text-[var(--cl-faint)]">1-Click Fill</span>
        </div>
        <div className="mt-2 grid grid-cols-2 gap-2">
          <button
            type="button"
            onClick={() => handleQuickDemo('student')}
            className="flex items-center justify-center gap-1.5 rounded-[var(--radius-sm)] border border-[var(--cl-border)] bg-[var(--cl-surface)] px-2.5 py-1.5 text-xs font-medium text-[var(--cl-text-soft)] transition hover:border-[var(--cl-accent)] hover:text-[var(--cl-accent)]"
          >
            <GraduationCap className="h-3.5 w-3.5 text-[var(--cl-accent)]" />
            <span>Student Lens</span>
          </button>
          <button
            type="button"
            onClick={() => handleQuickDemo('professional')}
            className="flex items-center justify-center gap-1.5 rounded-[var(--radius-sm)] border border-[var(--cl-border)] bg-[var(--cl-surface)] px-2.5 py-1.5 text-xs font-medium text-[var(--cl-text-soft)] transition hover:border-[var(--cl-accent)] hover:text-[var(--cl-accent)]"
          >
            <Briefcase className="h-3.5 w-3.5 text-[var(--cl-accent)]" />
            <span>Professional</span>
          </button>
        </div>
      </div>

      {/* Error & Success Feedback Alerts */}
      <AnimatePresence mode="wait">
        {error && (
          <motion.div
            key="error-alert"
            initial={{ opacity: 0, y: -8, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.98 }}
            className="mt-4 flex items-start gap-2.5 rounded-[var(--radius-md)] border border-[var(--cl-danger-soft)] bg-[var(--cl-danger-soft)] p-3 text-xs text-[var(--cl-danger)]"
            role="alert"
          >
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <span className="leading-snug">{error}</span>
          </motion.div>
        )}

        {successMessage && (
          <motion.div
            key="success-alert"
            initial={{ opacity: 0, y: -8, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.98 }}
            className="mt-4 flex items-start gap-2.5 rounded-[var(--radius-md)] border border-[var(--cl-success-soft)] bg-[var(--cl-success-soft)] p-3 text-xs text-[var(--cl-success)]"
            role="status"
          >
            <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
            <span className="leading-snug">{successMessage}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Form */}
      <form onSubmit={handleSubmit} className="mt-4 space-y-4">
        {/* Name Input (Register mode only) */}
        <AnimatePresence initial={false}>
          {mode === 'register' && (
            <motion.div
              key="name-field"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.2 }}
            >
              <label
                htmlFor={nameInputId}
                className="block text-xs font-medium text-[var(--cl-text-soft)]"
              >
                Full Name
              </label>
              <div className="relative mt-1">
                <span className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-[var(--cl-faint)]">
                  <UserIcon className="h-4 w-4" />
                </span>
                <input
                  id={nameInputId}
                  type="text"
                  required={mode === 'register'}
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Aaditya Soni"
                  className="w-full rounded-[var(--radius-md)] border border-[var(--cl-border)] bg-[var(--cl-input-bg)] py-2.5 pr-3 pl-9 text-xs sm:text-sm text-[var(--cl-text)] placeholder-[var(--cl-faint)] transition focus:border-[var(--cl-accent)] focus:outline-none"
                />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Email Input */}
        <div>
          <label
            htmlFor={emailInputId}
            className="block text-xs font-medium text-[var(--cl-text-soft)]"
          >
            Email Address
          </label>
          <div className="relative mt-1">
            <span className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-[var(--cl-faint)]">
              <Mail className="h-4 w-4" />
            </span>
            <input
              id={emailInputId}
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@domain.com"
              className="w-full rounded-[var(--radius-md)] border border-[var(--cl-border)] bg-[var(--cl-input-bg)] py-2.5 pr-3 pl-9 text-xs sm:text-sm text-[var(--cl-text)] placeholder-[var(--cl-faint)] transition focus:border-[var(--cl-accent)] focus:outline-none"
            />
          </div>
        </div>

        {/* Password Input */}
        <div>
          <div className="flex items-center justify-between">
            <label
              htmlFor={passwordInputId}
              className="block text-xs font-medium text-[var(--cl-text-soft)]"
            >
              Password
            </label>
            {mode === 'register' && (
              <span className="text-[10px] text-[var(--cl-faint)]">Min 12 characters</span>
            )}
          </div>
          <div className="relative mt-1">
            <span className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-[var(--cl-faint)]">
              <Lock className="h-4 w-4" />
            </span>
            <input
              id={passwordInputId}
              type={showPassword ? 'text' : 'password'}
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={mode === 'register' ? 'At least 12 characters' : 'Enter your password'}
              className="w-full rounded-[var(--radius-md)] border border-[var(--cl-border)] bg-[var(--cl-input-bg)] py-2.5 pr-10 pl-9 text-xs sm:text-sm text-[var(--cl-text)] placeholder-[var(--cl-faint)] transition focus:border-[var(--cl-accent)] focus:outline-none"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              aria-label={showPassword ? 'Hide password' : 'Show password'}
              className="absolute inset-y-0 right-0 flex items-center pr-3 text-[var(--cl-faint)] transition hover:text-[var(--cl-text)]"
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
        </div>

        {/* Password Strength Checklist (Register Mode) */}
        {mode === 'register' && password.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="space-y-1.5 pt-1"
          >
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-[var(--cl-muted)]">Password Strength</span>
              <span className={`font-semibold ${passwordMetrics.textColor}`}>
                {passwordMetrics.label}
              </span>
            </div>
            {/* Progress bar */}
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-[var(--cl-surface-muted)]">
              <div
                className={`h-full transition-all duration-300 ${passwordMetrics.color}`}
                style={{ width: `${(passwordMetrics.score / 4) * 100}%` }}
              />
            </div>
            {/* Real-time Checklist */}
            <div className="grid grid-cols-1 gap-1 pt-1 text-[11px] text-[var(--cl-muted)] sm:grid-cols-2">
              <div className="flex items-center gap-1.5">
                <CheckCircle2
                  className={`h-3 w-3 ${
                    passwordMetrics.hasMinLength
                      ? 'text-[var(--cl-success)]'
                      : 'text-[var(--cl-faint)]'
                  }`}
                />
                <span className={passwordMetrics.hasMinLength ? 'text-[var(--cl-text)]' : ''}>
                  12+ characters
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                <CheckCircle2
                  className={`h-3 w-3 ${
                    passwordMetrics.hasMixedCase
                      ? 'text-[var(--cl-success)]'
                      : 'text-[var(--cl-faint)]'
                  }`}
                />
                <span className={passwordMetrics.hasMixedCase ? 'text-[var(--cl-text)]' : ''}>
                  Upper & lower case
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                <CheckCircle2
                  className={`h-3 w-3 ${
                    passwordMetrics.hasNumberOrSymbol
                      ? 'text-[var(--cl-success)]'
                      : 'text-[var(--cl-faint)]'
                  }`}
                />
                <span className={passwordMetrics.hasNumberOrSymbol ? 'text-[var(--cl-text)]' : ''}>
                  Number or symbol
                </span>
              </div>
            </div>
          </motion.div>
        )}

        {/* Submit Button */}
        <motion.button
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.98 }}
          type="submit"
          disabled={isSubmitting}
          data-testid="auth-submit-btn"
          aria-label={mode === 'login' ? 'Submit Sign In' : 'Submit Registration'}
          className="mt-6 flex w-full items-center justify-center gap-2 rounded-[var(--radius-md)] bg-[var(--cl-accent)] px-4 py-2.5 text-xs sm:text-sm font-semibold text-[var(--cl-accent-contrast)] shadow-xs transition hover:bg-[var(--cl-accent-hover)] disabled:opacity-50"
        >
          {isSubmitting ? (
            <span className="flex items-center gap-2">
              <svg
                className="h-4 w-4 animate-spin text-current"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8v8H4z"
                />
              </svg>
              <span>{mode === 'login' ? 'Authenticating...' : 'Creating Account...'}</span>
            </span>
          ) : (
            <>
              <span>{mode === 'login' ? 'Sign In' : 'Create CareerLens Account'}</span>
              <ArrowRight className="h-4 w-4" />
            </>
          )}
        </motion.button>
      </form>

      {/* Security Footer Notice */}
      <div className="mt-6 flex items-center justify-center gap-1.5 text-[11px] text-[var(--cl-faint)]">
        <ShieldCheck className="h-3.5 w-3.5 text-[var(--cl-success)]" />
        <span>Argon2 hashed & JWT Bearer verified</span>
      </div>
    </div>
  )
}
