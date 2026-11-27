import { useCallback, useEffect, useRef, useState } from 'react'

export function useAudioMeter(mediaStream = null) {
  const [audioLevel, setAudioLevel] = useState(0) // 0 to 100
  const [isSpeaking, setIsSpeaking] = useState(false) // VAD boolean
  const animationFrameRef = useRef(null)
  const audioContextRef = useRef(null)
  const analyserRef = useRef(null)

  const stopMeter = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current)
      animationFrameRef.current = null
    }
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close().catch(() => {})
      audioContextRef.current = null
    }
    setAudioLevel(0)
    setIsSpeaking(false)
  }, [])

  useEffect(() => {
    if (!mediaStream || mediaStream.getAudioTracks().length === 0) {
      stopMeter()
      return
    }

    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext
      if (!AudioCtx) return

      const ctx = new AudioCtx()
      audioContextRef.current = ctx

      const analyser = ctx.createAnalyser()
      analyser.fftSize = 256
      analyser.smoothingTimeConstant = 0.5
      analyserRef.current = analyser

      const source = ctx.createMediaStreamSource(mediaStream)
      source.connect(analyser)

      const dataArray = new Uint8Array(analyser.frequencyBinCount)

      const sample = () => {
        if (!analyserRef.current) return

        analyserRef.current.getByteFrequencyData(dataArray)
        let sum = 0
        for (let i = 0; i < dataArray.length; i++) {
          sum += dataArray[i]
        }
        const average = sum / dataArray.length
        const normalized = Math.min(100, Math.round((average / 128) * 100))

        setAudioLevel(normalized)
        setIsSpeaking(normalized > 14)

        animationFrameRef.current = requestAnimationFrame(sample)
      }

      animationFrameRef.current = requestAnimationFrame(sample)
    } catch {
      // Audio meter fallback if Web Audio API fails
    }

    return () => {
      stopMeter()
    }
  }, [mediaStream, stopMeter])

  return { audioLevel, isSpeaking, stopMeter }
}
