import { useCallback, useEffect, useRef, useState } from 'react'

export function useSpeechSynthesis() {
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [isSupported, setIsSupported] = useState(false)
  const [voices, setVoices] = useState([])
  const [selectedVoice, setSelectedVoice] = useState(null)

  const utteranceRef = useRef(null)

  useEffect(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      setIsSupported(true)

      const updateVoices = () => {
        const available = window.speechSynthesis.getVoices()
        setVoices(available)

        // Select a natural English voice if available
        const preferred =
          available.find(
            (v) =>
              v.lang.startsWith('en') &&
              (v.name.includes('Natural') ||
                v.name.includes('Google') ||
                v.name.includes('Samantha') ||
                v.name.includes('Daniel'))
          ) || available.find((v) => v.lang.startsWith('en'))

        if (preferred) {
          setSelectedVoice(preferred)
        }
      }

      updateVoices()
      window.speechSynthesis.onvoiceschanged = updateVoices
    }
  }, [])

  const speak = useCallback(
    (text, onStart = null, onEnd = null) => {
      if (!isSupported || !window.speechSynthesis) return

      try {
        window.speechSynthesis.cancel()

        const utterance = new SpeechSynthesisUtterance(text)
        if (selectedVoice) {
          utterance.voice = selectedVoice
        }
        utterance.rate = 1.0
        utterance.pitch = 1.0

        utterance.onstart = () => {
          setIsSpeaking(true)
          if (onStart) onStart()
        }

        utterance.onend = () => {
          setIsSpeaking(false)
          if (onEnd) onEnd()
        }

        utterance.onerror = () => {
          setIsSpeaking(false)
          if (onEnd) onEnd()
        }

        utteranceRef.current = utterance
        window.speechSynthesis.speak(utterance)
      } catch {
        setIsSpeaking(false)
        if (onEnd) onEnd()
      }
    },
    [isSupported, selectedVoice]
  )

  const cancel = useCallback(() => {
    if (isSupported && window.speechSynthesis) {
      window.speechSynthesis.cancel()
      setIsSpeaking(false)
    }
  }, [isSupported])

  return {
    isSpeaking,
    isSupported,
    voices,
    selectedVoice,
    setSelectedVoice,
    speak,
    cancel,
  }
}
