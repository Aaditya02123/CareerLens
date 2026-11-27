import { useCallback, useEffect, useRef, useState } from 'react'
import {
  Camera,
  CheckCircle2,
  Mic,
  Volume2,
  Wifi,
  Shield,
  Sparkles,
  AlertCircle,
  Play,
} from 'lucide-react'
import { useAudioMeter } from '../../hooks/useAudioMeter'
import { checkNetworkLatency } from '../../services/api/interviewProctoring'

export default function HardwareCheckScreen({
  session,
  onProceed,
  onCancel,
}) {
  const videoRef = useRef(null)
  const [stream, setStream] = useState(null)
  const [hasCamera, setHasCamera] = useState(false)
  const [hasMic, setHasMic] = useState(false)
  const [mediaError, setMediaError] = useState('')
  const [audioPlayed, setAudioPlayed] = useState(false)
  const [networkLatency, setNetworkLatency] = useState(null)
  const [networkLoading, setNetworkLoading] = useState(true)
  const [interviewMode, setInterviewMode] = useState('practice') // 'practice' | 'proctored'

  const { audioLevel, isSpeaking } = useAudioMeter(stream)

  // Start media devices on mount
  useEffect(() => {
    let activeStream = null

    async function initMedia() {
      try {
        setMediaError('')
        const userMedia = await navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 640 }, height: { ideal: 480 } },
          audio: true,
        })
        activeStream = userMedia
        setStream(userMedia)
        setHasCamera(userMedia.getVideoTracks().length > 0)
        setHasMic(userMedia.getAudioTracks().length > 0)

        if (videoRef.current) {
          videoRef.current.srcObject = userMedia
        }
      } catch (err) {
        setMediaError(
          err.name === 'NotAllowedError'
            ? 'Camera and microphone access was denied. Please allow permissions in your browser to proceed.'
            : `Hardware access error: ${err.message}`
        )
      }
    }

    void initMedia()

    // Test network latency
    void checkNetworkLatency().then((res) => {
      setNetworkLatency(res.latencyMs)
      setNetworkLoading(false)
    })

    return () => {
      if (activeStream) {
        activeStream.getTracks().forEach((track) => track.stop())
      }
    }
  }, [])

  // Speaker audio test chime
  const handlePlaySpeakerTest = useCallback(() => {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext
      if (!AudioCtx) {
        setAudioPlayed(true)
        return
      }
      const ctx = new AudioCtx()
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()

      osc.type = 'sine'
      osc.frequency.setValueAtTime(523.25, ctx.currentTime) // C5
      osc.frequency.exponentialRampToValueAtTime(659.25, ctx.currentTime + 0.15) // E5
      osc.frequency.exponentialRampToValueAtTime(783.99, ctx.currentTime + 0.3) // G5

      gain.gain.setValueAtTime(0.15, ctx.currentTime)
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.45)

      osc.connect(gain)
      gain.connect(ctx.destination)

      osc.start()
      osc.stop(ctx.currentTime + 0.45)
      setAudioPlayed(true)
    } catch {
      setAudioPlayed(true)
    }
  }, [])

  const canProceed = hasCamera && hasMic

  const handleStartInterview = () => {
    if (!canProceed) return
    onProceed({
      mode: interviewMode,
      stream,
    })
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      {/* Header */}
      <div className="rounded-2xl border border-[var(--cl-border)] bg-[var(--cl-surface)] p-6 shadow-[var(--shadow-soft)]">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-[var(--cl-accent)]/15 text-[var(--cl-accent)]">
                <Sparkles className="h-3.5 w-3.5" />
              </span>
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--cl-accent)]">
                Pre-Flight Hardware & Verification Check
              </p>
            </div>
            <h1 className="mt-2 text-2xl font-medium tracking-[-0.03em] text-[var(--cl-text)]">
              System & Environment Setup
            </h1>
            <p className="mt-1 text-sm text-[var(--cl-muted)]">
              Verify your camera, microphone, and speaker before entering the AI Interview Room.
            </p>
          </div>

          {session?.id && (
            <span className="rounded-full border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] px-3 py-1 text-xs font-medium text-[var(--cl-muted)]">
              Session #{session.id}
            </span>
          )}
        </div>
      </div>

      {mediaError && (
        <div className="flex items-start gap-3 rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-400">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          <p>{mediaError}</p>
        </div>
      )}

      {/* Main Grid: Video Mirror & Hardware Checklists */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-12">
        {/* Left: Video Preview */}
        <div className="space-y-4 md:col-span-7">
          <div className="relative aspect-video w-full overflow-hidden rounded-2xl border border-[var(--cl-border)] bg-black/60 shadow-inner">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="h-full w-full object-cover scale-x-[-1]"
            />

            {/* Face guide overlay */}
            <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
              <div className="h-44 w-36 rounded-[50%] border-2 border-dashed border-white/25 transition-all" />
            </div>

            {/* Live Audio Indicator Badge */}
            <div className="absolute bottom-3 left-3 flex items-center gap-2 rounded-full bg-black/70 px-3 py-1 text-xs backdrop-blur-md">
              <Mic className={`h-3.5 w-3.5 ${isSpeaking ? 'text-emerald-400' : 'text-zinc-400'}`} />
              <div className="h-1.5 w-16 overflow-hidden rounded-full bg-zinc-700">
                <div
                  className="h-full bg-emerald-400 transition-all duration-75"
                  style={{ width: `${Math.min(100, audioLevel * 1.5)}%` }}
                />
              </div>
              <span className="text-[10px] text-zinc-300 font-mono">
                {audioLevel}%
              </span>
            </div>

            {/* Camera Status */}
            <div className="absolute top-3 right-3 rounded-full bg-black/60 px-2.5 py-1 text-[10px] uppercase tracking-wider text-zinc-300 backdrop-blur-md">
              {hasCamera ? (
                <span className="flex items-center gap-1.5 text-emerald-400">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  Camera Active
                </span>
              ) : (
                'Camera Inactive'
              )}
            </div>
          </div>

          <p className="text-center text-xs text-[var(--cl-faint)]">
            Position your face inside the framing guide. Ensure good lighting without back-glare.
          </p>
        </div>

        {/* Right: Verification Cards & Mode Selector */}
        <div className="space-y-4 md:col-span-5">
          {/* Checks List */}
          <div className="rounded-2xl border border-[var(--cl-border)] bg-[var(--cl-surface)] p-5 shadow-[var(--shadow-soft)] space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--cl-text-soft)]">
              Hardware Status
            </h3>

            {/* Camera Check */}
            <div className="flex items-center justify-between rounded-xl border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-3">
              <div className="flex items-center gap-2.5">
                <Camera className="h-4 w-4 text-[var(--cl-muted)]" />
                <span className="text-xs font-medium text-[var(--cl-text)]">Camera</span>
              </div>
              {hasCamera ? (
                <CheckCircle2 className="h-4 w-4 text-emerald-500" />
              ) : (
                <span className="text-[10px] font-medium text-amber-500">Checking...</span>
              )}
            </div>

            {/* Mic Check */}
            <div className="flex items-center justify-between rounded-xl border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-3">
              <div className="flex items-center gap-2.5">
                <Mic className="h-4 w-4 text-[var(--cl-muted)]" />
                <span className="text-xs font-medium text-[var(--cl-text)]">Microphone</span>
              </div>
              {hasMic ? (
                <CheckCircle2 className="h-4 w-4 text-emerald-500" />
              ) : (
                <span className="text-[10px] font-medium text-amber-500">Checking...</span>
              )}
            </div>

            {/* Speaker Check */}
            <div className="flex items-center justify-between rounded-xl border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-3">
              <div className="flex items-center gap-2.5">
                <Volume2 className="h-4 w-4 text-[var(--cl-muted)]" />
                <span className="text-xs font-medium text-[var(--cl-text)]">Speaker Output</span>
              </div>
              <button
                type="button"
                onClick={handlePlaySpeakerTest}
                className="rounded-lg border border-[var(--cl-border)] px-2.5 py-1 text-[11px] font-medium text-[var(--cl-text-soft)] hover:bg-[var(--cl-surface)] transition"
              >
                {audioPlayed ? 'Test Again' : 'Play Chime'}
              </button>
            </div>

            {/* Network Latency */}
            <div className="flex items-center justify-between rounded-xl border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-3">
              <div className="flex items-center gap-2.5">
                <Wifi className="h-4 w-4 text-[var(--cl-muted)]" />
                <span className="text-xs font-medium text-[var(--cl-text)]">Network Ping</span>
              </div>
              <span className="text-xs font-mono text-[var(--cl-muted)]">
                {networkLoading ? 'Pinging...' : `${networkLatency} ms`}
              </span>
            </div>
          </div>

          {/* Mode Selector */}
          <div className="rounded-2xl border border-[var(--cl-border)] bg-[var(--cl-surface)] p-5 shadow-[var(--shadow-soft)] space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--cl-text-soft)]">
              Select Experience Mode
            </h3>

            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setInterviewMode('practice')}
                className={`flex flex-col items-start rounded-xl border p-3 text-left transition ${
                  interviewMode === 'practice'
                    ? 'border-[var(--cl-accent)] bg-[var(--cl-accent)]/10 text-[var(--cl-text)]'
                    : 'border-[var(--cl-border)] bg-[var(--cl-surface-muted)] text-[var(--cl-muted)] hover:border-[var(--cl-text-soft)]'
                }`}
              >
                <div className="flex items-center gap-1.5 font-medium text-xs">
                  <Sparkles className="h-3.5 w-3.5 text-[var(--cl-accent)]" />
                  Practice Mode
                </div>
                <p className="mt-1 text-[10px] leading-4 text-[var(--cl-muted)]">
                  Coaching, instant exemplar answers, and 1-click roadmap sync.
                </p>
              </button>

              <button
                type="button"
                onClick={() => setInterviewMode('proctored')}
                className={`flex flex-col items-start rounded-xl border p-3 text-left transition ${
                  interviewMode === 'proctored'
                    ? 'border-indigo-500 bg-indigo-500/10 text-[var(--cl-text)]'
                    : 'border-[var(--cl-border)] bg-[var(--cl-surface-muted)] text-[var(--cl-muted)] hover:border-[var(--cl-text-soft)]'
                }`}
              >
                <div className="flex items-center gap-1.5 font-medium text-xs">
                  <Shield className="h-3.5 w-3.5 text-indigo-400" />
                  Proctored Mode
                </div>
                <p className="mt-1 text-[10px] leading-4 text-[var(--cl-muted)]">
                  Full integrity telemetry (tab switches, paste, audit log).
                </p>
              </button>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-3 pt-2">
            {onCancel && (
              <button
                type="button"
                onClick={onCancel}
                className="flex-1 rounded-xl border border-[var(--cl-border)] py-3 text-xs font-medium text-[var(--cl-muted)] hover:bg-[var(--cl-surface-muted)] transition"
              >
                Cancel
              </button>
            )}
            <button
              type="button"
              disabled={!canProceed}
              onClick={handleStartInterview}
              className={`flex items-center justify-center gap-2 rounded-xl py-3 text-xs font-semibold shadow-md transition ${
                canProceed
                  ? 'flex-1 bg-[var(--cl-accent)] text-[var(--cl-accent-contrast)] hover:opacity-95'
                  : 'flex-1 bg-zinc-700/50 text-zinc-500 cursor-not-allowed'
              }`}
            >
              <Play className="h-3.5 w-3.5 fill-current" />
              Enter AI Interview Room
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
