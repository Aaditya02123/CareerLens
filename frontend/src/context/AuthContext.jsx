import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import {
  clearStoredAuth,
  fetchCurrentUser,
  getStoredToken,
  getStoredUser,
  loginUser,
  registerUser,
  setStoredToken,
  setStoredUser,
} from '../services/api/auth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => getStoredToken())
  const [user, setUser] = useState(() => getStoredUser())
  const [isLoading, setIsLoading] = useState(false)
  const [authModalOpen, setAuthModalOpen] = useState(false)
  const [authMode, setAuthMode] = useState('login')

  // Re-verify session on mount if token is present
  useEffect(() => {
    const existingToken = getStoredToken()
    if (!existingToken) return

    let isMounted = true
    setIsLoading(true)

    fetchCurrentUser(existingToken)
      .then((verifiedUser) => {
        if (isMounted) {
          setUser(verifiedUser)
          setStoredUser(verifiedUser)
        }
      })
      .catch(() => {
        // Token was invalid or expired
        if (isMounted) {
          clearStoredAuth()
          setToken(null)
          setUser(null)
        }
      })
      .finally(() => {
        if (isMounted) {
          setIsLoading(false)
        }
      })

    return () => {
      isMounted = false
    }
  }, [])

  const login = useCallback(async (email, password) => {
    setIsLoading(true)
    try {
      const data = await loginUser({ email, password })
      setStoredToken(data.access_token)
      setStoredUser(data.user)
      setToken(data.access_token)
      setUser(data.user)
      setAuthModalOpen(false)
      return data.user
    } finally {
      setIsLoading(false)
    }
  }, [])

  const register = useCallback(async (name, email, password) => {
    setIsLoading(true)
    try {
      const data = await registerUser({ name, email, password })
      setStoredToken(data.access_token)
      setStoredUser(data.user)
      setToken(data.access_token)
      setUser(data.user)
      setAuthModalOpen(false)
      return data.user
    } finally {
      setIsLoading(false)
    }
  }, [])

  const logout = useCallback(() => {
    clearStoredAuth()
    setToken(null)
    setUser(null)
  }, [])

  const openAuthModal = useCallback((mode = 'login') => {
    setAuthMode(mode)
    setAuthModalOpen(true)
  }, [])

  const closeAuthModal = useCallback(() => {
    setAuthModalOpen(false)
  }, [])

  const value = useMemo(
    () => ({
      user,
      token,
      isAuthenticated: Boolean(user && token),
      isLoading,
      login,
      register,
      logout,
      authModalOpen,
      authMode,
      setAuthMode,
      openAuthModal,
      closeAuthModal,
    }),
    [
      user,
      token,
      isLoading,
      login,
      register,
      logout,
      authModalOpen,
      authMode,
      openAuthModal,
      closeAuthModal,
    ],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    return {
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      login: async () => {},
      register: async () => {},
      logout: () => {},
      authModalOpen: false,
      authMode: 'login',
      setAuthMode: () => {},
      openAuthModal: () => {},
      closeAuthModal: () => {},
    }
  }
  return context
}
