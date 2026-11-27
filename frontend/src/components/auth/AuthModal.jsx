import { useEffect } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { useAuth } from '../../context/AuthContext'
import AuthPage from './AuthPage'

export default function AuthModal() {
  const { authModalOpen, closeAuthModal, authMode } = useAuth()

  // Handle ESC key to close modal
  useEffect(() => {
    if (!authModalOpen) return

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        closeAuthModal()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [authModalOpen, closeAuthModal])

  return (
    <AnimatePresence>
      {authModalOpen && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6"
        >
          {/* Backdrop Blur */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={closeAuthModal}
            className="fixed inset-0 bg-[var(--cl-bg)]/80 backdrop-blur-md"
            aria-hidden="true"
          />

          {/* Modal Container */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 15 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 15 }}
            transition={{ type: 'spring', stiffness: 400, damping: 30 }}
            className="relative z-10 w-full max-w-lg"
          >
            <AuthPage isModal={true} onClose={closeAuthModal} initialMode={authMode} />
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  )
}
