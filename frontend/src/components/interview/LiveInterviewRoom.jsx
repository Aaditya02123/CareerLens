import { useCallback, useEffect, useRef, useState } from 'react'
import {
  Mic,
  MicOff,
  Volume2,
  Video,
  VideoOff,
  Send,
  Code2,
  Sparkles,
  ShieldAlert,
  ShieldCheck,
  RotateCcw,
  Clock,
} from 'lucide-react'
import { useSpeechRecognition } from '../../hooks/useSpeechRecognition'
import { useSpeechSynthesis } from '../../hooks/useSpeechSynthesis'
import { useAudioMeter } from '../../hooks/useAudioMeter'
import {
  fetchModelAnswerComparison,
  recordProctoringEvent,
  submitInterviewAnswer,
} from '../../services/api/interviewProctoring'
import ModelAnswerModal from './ModelAnswerModal'

export default function LiveInterviewRoom({
  session,
  mode = 'practice', // 'practice' | 'proctored'
  stream = null,
  onFinish,
  onExit,
}) {
  const videoRef = useRef(null)
  const answerStartTimeRef = useRef(0)
  const hasSpokenQuestionRef = useRef({})

  const [activeQuestionIndex, setActiveQuestionIndex] = useState(0)
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')
  const [scratchpadOpen, setScratchpadOpen] = useState(false)
  const [scratchpadText, setScratchpadText] = useState('')
  const [proctorFlagsCount, setProctorFlagsCount] = useState(0)
  const [showModelModal, setShowModelModal] = useState(false)
  const [lastModelData, setLastModelData] = useState(null)
  const [isCameraOn, setIsCameraOn] = useState(true)
  const [isMicOn, setIsMicOn] = useState(true)
  const [interviewComplete, setInterviewComplete] = useState(false)
  const [elapsedSeconds, setElapsedSeconds] = useState(0)

  const questions = session?.questions || []
  const currentQuestion = questions[activeQuestionIndex] || null

  const {
    isListening,
    transcript,
    interimTranscript,
    startListening,
    stopListening,
    resetTranscript,
  } = useSpeechRecognition()

  const { isSpeaking: isAiSpeaking, speak, cancel: cancelAiSpeech } =
    useSpeechSynthesis()

  const { audioLevel, isSpeaking: isCandidateSpeaking } = useAudioMeter(stream)

  // Attach media stream to video element
  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream
    }
  }, [stream])

  // Interview timer
  useEffect(() => {
    if (interviewComplete) return
    const timer = setInterval(() => {
      setElapsedSeconds((prev) => prev + 1)
    }, 1000)
    return () => clearInterval(timer)
  }, [interviewComplete])

  // Proctoring telemetry listeners (tab switch, window blur, paste)
  useEffect(() => {
    if (!session?.id) return

    const handleVisibilityChange = () => {
      if (document.hidden) {
        setProctorFlagsCount((c) => c + 1)
        void recordProctoringEvent(session.id, 'tab_switch', 'medium', {
          timestamp: new Date().toISOString(),
          question_order: currentQuestion?.question_order,
        })
      }
    }

    const handleWindowBlur = () => {
      setProctorFlagsCount((c) => c + 1)
      void recordProctoringEvent(session.id, 'window_blur', 'low', {
        timestamp: new Date().toISOString(),
      })
    }

    const handlePaste = (event) => {
      setProctorFlagsCount((c) => c + 1)
      void recordProctoringEvent(session.id, 'paste_detected', 'high', {
        pasted_length: event.clipboardData?.getData('text')?.length || 0,
      })
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    window.addEventListener('blur', handleWindowBlur)
    window.addEventListener('paste', handlePaste)

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
      window.removeEventListener('blur', handleWindowBlur)
      window.removeEventListener('paste', handlePaste)
    }
  }, [session?.id, currentQuestion?.question_order])

  // Automatically speak new questions once
  useEffect(() => {
    if (!currentQuestion || hasSpokenQuestionRef.current[currentQuestion.id]) return

    hasSpokenQuestionRef.current[currentQuestion.id] = true
    answerStartTimeRef.current = Date.now()
    resetTranscript()

    speak(
      currentQuestion.question,
      () => {},
      () => {
        // Automatically start speech recognition when AI finishes speaking
        if (isMicOn) {
          startListening()
        }
      }
    )
  }, [currentQuestion, speak, isMicOn, startListening, resetTranscript])

  const handleReplayQuestion = useCallback(() => {
    if (!currentQuestion) return
    speak(currentQuestion.question)
  }, [currentQuestion, speak])

  const toggleMic = () => {
    if (stream) {
      stream.getAudioTracks().forEach((track) => {
        track.enabled = !track.enabled
      })
    }
    if (isMicOn) {
      stopListening()
      setIsMicOn(false)
    } else {
      startListening()
      setIsMicOn(true)
    }
  }

  const toggleCamera = () => {
    if (stream) {
      stream.getVideoTracks().forEach((track) => {
        track.enabled = !track.enabled
      })
      setIsCameraOn((prev) => !prev)
    }
  }

  // Answer Submission Flow
  const handleSubmitAnswer = async () => {
    if (!currentQuestion || submitting) return
    const candidateResponse = (
      transcript + (scratchpadText ? `\n\n[Candidate Scratchpad Notes]:\n${scratchpadText}` : '')
    ).trim()

    if (!candidateResponse) {
      setSubmitError('Please provide an answer before submitting.')
      return
    }

    setSubmitting(true)
    setSubmitError('')
    stopListening()
    cancelAiSpeech()

    const durationSeconds = Math.max(
      5,
      Math.round((Date.now() - answerStartTimeRef.current) / 1000)
    )

    try {
      const answerRecord = await submitInterviewAnswer(
        session.id,
        currentQuestion.id,
        currentQuestion.question_order,
        candidateResponse
      )

      // Fetch Model STAR Answer for coaching
      try {
        const modelData = await fetchModelAnswerComparison(
          session.id,
          answerRecord.id || 1,
          durationSeconds
        )
        setLastModelData(modelData)
        if (mode === 'practice') {
          setShowModelModal(true)
        }
      } catch {
        // Fallback model answer continues seamlessly
      }

      // Advance to next question or complete
      if (activeQuestionIndex < questions.length - 1) {
        setActiveQuestionIndex((prev) => prev + 1)
        resetTranscript()
        setScratchpadText('')
      } else {
        setInterviewComplete(true)
      }
    } catch (err) {
      setSubmitError(err?.message || 'Failed to submit answer. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  const formatTimer = (totalSec) => {
    const mins = Math.floor(totalSec / 60)
    const secs = totalSec % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  if (interviewComplete) {
    return (
      <div className="mx-auto max-w-2xl rounded-2xl border border-[var(--cl-border)] bg-[var(--cl-surface)] p-8 text-center shadow-[var(--shadow-soft)] space-y-6">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-500/15 text-emerald-400">
          <Sparkles className="h-7 w-7" />
        </div>

        <div>
          <h2 className="text-2xl font-medium tracking-tight text-[var(--cl-text)]">
            Interview Session Completed!
          </h2>
          <p className="mt-2 text-sm text-[var(--cl-muted)]">
            All questions have been recorded and evaluated against role rubrics.
          </p>
        </div>

        <div className="rounded-xl border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-4 text-xs text-[var(--cl-muted)] flex justify-around">
          <div>
            <span className="block font-medium text-[var(--cl-text)] text-sm">
              {questions.length} Questions
            </span>
            <span>Completed</span>
          </div>
          <div>
            <span className="block font-medium text-[var(--cl-text)] text-sm">
              {formatTimer(elapsedSeconds)}
            </span>
            <span>Duration</span>
          </div>
          <div>
            <span className="block font-medium text-[var(--cl-text)] text-sm">
              {proctorFlagsCount === 0 ? 'Clean (100%)' : `${proctorFlagsCount} Flag(s)`}
            </span>
            <span>Integrity Check</span>
          </div>
        </div>

        <button
          type="button"
          onClick={() => onFinish(session.id)}
          className="w-full rounded-xl bg-[var(--cl-accent)] py-3 text-xs font-semibold text-[var(--cl-accent-contrast)] shadow-md hover:opacity-95 transition"
        >
          View Full Scorecard & Integrity Audit
        </button>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-6xl space-y-4">
      {/* Top Session Status Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-[var(--cl-border)] bg-[var(--cl-surface)] px-5 py-3 shadow-[var(--shadow-soft)]">
        <div className="flex items-center gap-3">
          <span className="flex h-2.5 w-2.5 rounded-full bg-emerald-400 animate-pulse" />
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wider text-[var(--cl-accent)]">
              AI Interview Room • {mode === 'proctored' ? 'Proctored Screening' : 'Practice & Coaching'}
            </p>
            <h2 className="text-sm font-medium text-[var(--cl-text)]">
              Question {activeQuestionIndex + 1} of {questions.length}
            </h2>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Timer */}
          <div className="flex items-center gap-1.5 rounded-lg border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] px-3 py-1.5 text-xs font-mono text-[var(--cl-text-soft)]">
            <Clock className="h-3.5 w-3.5 text-[var(--cl-muted)]" />
            <span>{formatTimer(elapsedSeconds)}</span>
          </div>

          {/* Proctoring Status Badge */}
          {mode === 'proctored' ? (
            <div
              className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-medium border ${
                proctorFlagsCount > 0
                  ? 'border-amber-500/20 bg-amber-500/10 text-amber-400'
                  : 'border-emerald-500/20 bg-emerald-500/10 text-emerald-400'
              }`}
            >
              {proctorFlagsCount > 0 ? (
                <>
                  <ShieldAlert className="h-3.5 w-3.5" />
                  <span>{proctorFlagsCount} Flag(s)</span>
                </>
              ) : (
                <>
                  <ShieldCheck className="h-3.5 w-3.5" />
                  <span>Verified Clean</span>
                </>
              )}
            </div>
          ) : (
            <span className="rounded-full bg-[var(--cl-accent)]/15 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider text-[var(--cl-accent)]">
              Coaching Active
            </span>
          )}

          {onExit && (
            <button
              type="button"
              onClick={onExit}
              className="rounded-lg border border-[var(--cl-border)] px-3 py-1.5 text-xs font-medium text-[var(--cl-muted)] hover:bg-[var(--cl-surface-muted)] transition"
            >
              Exit Room
            </button>
          )}
        </div>
      </div>

      {/* Main Split Grid */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
        {/* Left Column: AI Interviewer & Question Card (5 cols) */}
        <div className="flex flex-col gap-4 lg:col-span-5">
          {/* AI Persona Waveform Orb */}
          <div className="flex flex-col items-center justify-center rounded-2xl border border-[var(--cl-border)] bg-[var(--cl-surface)] p-6 shadow-[var(--shadow-soft)] min-h-[220px]">
            <div className="relative flex items-center justify-center">
              {/* Pulsing visual circles */}
              <div
                className={`absolute h-24 w-24 rounded-full transition-all duration-300 ${
                  isAiSpeaking
                    ? 'scale-125 bg-[var(--cl-accent)]/20 animate-ping'
                    : isCandidateSpeaking
                    ? 'scale-110 bg-emerald-500/15'
                    : 'bg-zinc-800/40'
                }`}
              />
              <div
                className={`relative flex h-20 w-20 items-center justify-center rounded-full border shadow-xl transition-all ${
                  isAiSpeaking
                    ? 'border-[var(--cl-accent)] bg-[var(--cl-accent)]/20 text-[var(--cl-accent)]'
                    : isCandidateSpeaking
                    ? 'border-emerald-500 bg-emerald-500/10 text-emerald-400'
                    : 'border-[var(--cl-border)] bg-[var(--cl-surface-muted)] text-[var(--cl-muted)]'
                }`}
              >
                <Sparkles className="h-8 w-8" />
              </div>
            </div>

            {/* AI State Label */}
            <div className="mt-4 text-center">
              <span className="rounded-full px-3 py-1 text-xs font-medium bg-[var(--cl-surface-muted)] border border-[var(--cl-border)] text-[var(--cl-text-soft)]">
                {isAiSpeaking
                  ? 'AI Speaking...'
                  : isListening
                  ? 'Listening to Candidate...'
                  : submitting
                  ? 'Analyzing response...'
                  : 'Ready for answer'}
              </span>
            </div>
          </div>

          {/* Current Question Card */}
          <div className="flex-1 rounded-2xl border border-[var(--cl-border)] bg-[var(--cl-surface)] p-6 shadow-[var(--shadow-soft)] space-y-3">
            <div className="flex items-center justify-between">
              <span className="rounded-full bg-[var(--cl-surface-muted)] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider text-[var(--cl-accent)]">
                {currentQuestion?.target_competency || 'General Assessment'}
              </span>

              <button
                type="button"
                onClick={handleReplayQuestion}
                className="flex items-center gap-1 rounded-lg px-2 py-1 text-[11px] font-medium text-[var(--cl-muted)] hover:text-[var(--cl-text)] transition"
              >
                <Volume2 className="h-3.5 w-3.5" />
                Listen Again
              </button>
            </div>

            <h3 className="text-base font-medium leading-relaxed text-[var(--cl-text)]">
              "{currentQuestion?.question}"
            </h3>

            {currentQuestion?.assessment_objective && (
              <div className="rounded-xl border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-3 text-xs text-[var(--cl-muted)] leading-5">
                <span className="font-medium text-[var(--cl-text-soft)] block mb-0.5">
                  Assessment Focus:
                </span>
                {currentQuestion.assessment_objective}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Candidate Webcam & Response Workspace (7 cols) */}
        <div className="flex flex-col gap-4 lg:col-span-7">
          {/* Webcam Mirror Banner with Controls */}
          <div className="relative aspect-video w-full overflow-hidden rounded-2xl border border-[var(--cl-border)] bg-black/80 shadow-inner">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className={`h-full w-full object-cover scale-x-[-1] transition-opacity ${
                isCameraOn ? 'opacity-100' : 'opacity-0'
              }`}
            />

            {!isCameraOn && (
              <div className="absolute inset-0 flex flex-col items-center justify-center text-zinc-500">
                <VideoOff className="h-10 w-10 mb-2" />
                <span className="text-xs">Camera Feed Paused</span>
              </div>
            )}

            {/* Live Audio Level Meter */}
            <div className="absolute bottom-3 left-3 flex items-center gap-2 rounded-full bg-black/75 px-3 py-1.5 text-xs backdrop-blur-md">
              <Mic className={`h-3.5 w-3.5 ${isCandidateSpeaking ? 'text-emerald-400' : 'text-zinc-400'}`} />
              <div className="h-1.5 w-20 overflow-hidden rounded-full bg-zinc-700">
                <div
                  className="h-full bg-emerald-400 transition-all duration-75"
                  style={{ width: `${Math.min(100, audioLevel * 1.5)}%` }}
                />
              </div>
            </div>

            {/* Top Device Toggles */}
            <div className="absolute top-3 right-3 flex items-center gap-2">
              <button
                type="button"
                onClick={toggleMic}
                className={`rounded-full p-2 backdrop-blur-md transition ${
                  isMicOn ? 'bg-black/60 text-white hover:bg-black/80' : 'bg-red-500 text-white'
                }`}
                title={isMicOn ? 'Mute Microphone' : 'Unmute Microphone'}
              >
                {isMicOn ? <Mic className="h-3.5 w-3.5" /> : <MicOff className="h-3.5 w-3.5" />}
              </button>

              <button
                type="button"
                onClick={toggleCamera}
                className={`rounded-full p-2 backdrop-blur-md transition ${
                  isCameraOn ? 'bg-black/60 text-white hover:bg-black/80' : 'bg-red-500 text-white'
                }`}
                title={isCameraOn ? 'Turn Off Camera' : 'Turn On Camera'}
              >
                {isCameraOn ? <Video className="h-3.5 w-3.5" /> : <VideoOff className="h-3.5 w-3.5" />}
              </button>

              <button
                type="button"
                onClick={() => setScratchpadOpen((o) => !o)}
                className={`flex items-center gap-1 rounded-full px-3 py-1 text-xs backdrop-blur-md transition ${
                  scratchpadOpen
                    ? 'bg-[var(--cl-accent)] text-[var(--cl-accent-contrast)]'
                    : 'bg-black/60 text-zinc-300 hover:bg-black/80'
                }`}
              >
                <Code2 className="h-3.5 w-3.5" />
                <span>{scratchpadOpen ? 'Hide Scratchpad' : 'Scratchpad'}</span>
              </button>
            </div>
          </div>

          {/* Slide-out Scratchpad / Code Editor */}
          {scratchpadOpen && (
            <div className="rounded-2xl border border-[var(--cl-border)] bg-[var(--cl-surface)] p-4 shadow-[var(--shadow-soft)] space-y-2 animate-fade-in">
              <div className="flex items-center justify-between text-xs text-[var(--cl-muted)]">
                <span className="font-semibold uppercase tracking-wider text-[var(--cl-faint)]">
                  Candidate Scratchpad / Code Workspace
                </span>
                <span className="text-[10px]">Notes are submitted with your answer</span>
              </div>
              <textarea
                value={scratchpadText}
                onChange={(e) => setScratchpadText(e.target.value)}
                placeholder="Write code snippets, architectural trade-offs, or algorithm outlines here..."
                rows={5}
                className="w-full font-mono text-xs rounded-xl border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-3 text-[var(--cl-text)] focus:border-[var(--cl-accent)] focus:outline-none"
              />
            </div>
          )}

          {/* Live Speech-to-Text Transcription Box */}
          <div className="rounded-2xl border border-[var(--cl-border)] bg-[var(--cl-surface)] p-5 shadow-[var(--shadow-soft)] space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-[var(--cl-text-soft)]">
                Live Speech Transcription
              </span>
              <button
                type="button"
                onClick={resetTranscript}
                className="flex items-center gap-1 text-[11px] text-[var(--cl-muted)] hover:text-[var(--cl-text)] transition"
              >
                <RotateCcw className="h-3 w-3" />
                Clear
              </button>
            </div>

            <div className="min-h-[110px] rounded-xl border border-[var(--cl-border)] bg-[var(--cl-surface-muted)] p-4 text-xs leading-6 text-[var(--cl-text)]">
              {transcript ? (
                <>
                  <span>{transcript}</span>
                  {interimTranscript && (
                    <span className="text-[var(--cl-muted)] italic"> {interimTranscript}</span>
                  )}
                </>
              ) : interimTranscript ? (
                <span className="text-[var(--cl-muted)] italic">{interimTranscript}</span>
              ) : (
                <span className="text-[var(--cl-faint)] italic">
                  Speak clearly into your microphone. Your answer will appear here in real time...
                </span>
              )}
            </div>

            {submitError && (
              <p className="text-xs text-red-400 font-medium">{submitError}</p>
            )}

            {/* Answer Action Bar */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
              <div className="text-[10px] text-[var(--cl-muted)]">
                {isListening ? (
                  <span className="flex items-center gap-1.5 text-emerald-400 font-medium">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    Microphone listening...
                  </span>
                ) : (
                  <span>Microphone paused</span>
                )}
              </div>

              <div className="flex items-center gap-2">
                {lastModelData && mode === 'practice' && (
                  <button
                    type="button"
                    onClick={() => setShowModelModal(true)}
                    className="flex items-center gap-1.5 rounded-xl border border-[var(--cl-border)] px-3 py-2 text-xs font-medium text-[var(--cl-accent)] hover:bg-[var(--cl-surface-muted)] transition"
                  >
                    <Sparkles className="h-3.5 w-3.5" />
                    Review Exemplar Answer
                  </button>
                )}

                <button
                  type="button"
                  disabled={submitting}
                  onClick={handleSubmitAnswer}
                  className="flex items-center gap-2 rounded-xl bg-[var(--cl-accent)] px-5 py-2.5 text-xs font-semibold text-[var(--cl-accent-contrast)] shadow-md hover:opacity-95 disabled:opacity-50 transition"
                >
                  <Send className="h-3.5 w-3.5" />
                  {submitting ? 'Submitting & Evaluating...' : 'Submit Answer'}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Model Answer Coaching Modal */}
      {showModelModal && lastModelData && (
        <ModelAnswerModal
          sessionId={session?.id}
          modelData={lastModelData}
          onClose={() => setShowModelModal(false)}
        />
      )}
    </div>
  )
}
