# Berri MasterMind and Proctoring Architecture in CareerLens

## Overview

Modern technical and behavioral recruitment faces two distinct challenges:
1. **Recruiter Need:** Scalable, reliable L1 candidate screening with verified integrity signals that discourage cheating without requiring expensive human proctors.
2. **Candidate Need:** Hyper-actionable interview coaching that goes beyond generic scores to show *what an ideal answer looks like*, *where specific technical nuances were missed*, and *how to upskill immediately*.

CareerLens addresses both needs through an integrated, dual-mode AI interviewing system inspired by **BerriBot's MasterMind dynamic cross-examination** and **Berri Proctor verification layer**.

---

## 1. The Pre-Flight Hardware Check

Before an interview session begins, candidate anxiety is minimized and technical difficulties are prevented via `HardwareCheckScreen.jsx`:
- **Webcam Mirror:** Live stream with a face alignment oval guide.
- **Web Audio Meter:** Connects an `AudioContext` and `AnalyserNode` to sample microphone volume in real time.
- **Speaker Chime:** Synthesizes a soft three-tone harmonic chime (`C5 -> E5 -> G5`) to test candidate audio output.
- **Network Latency Check:** Pings `/health` to verify stable round-trip latency.

---

## 2. Real-Time Interaction & Voice/Speech Pipeline

```
   Candidate Speaks                 Browser STT                      FastAPI Session Engine
+--------------------+        +-----------------------+            +-------------------------+
| Live Microphone    | -----> | Web Speech API        | ---------> | POST /sessions/{id}/    |
| & Audio Meter      |        | SpeechRecognition     |            | answers                 |
+--------------------+        +-----------------------+            +------------+------------+
                                                                                |
                                                                                v
   Candidate Hears                  Browser TTS                    Model Answer & Proctoring
+--------------------+        +-----------------------+            +-------------------------+
| Native Audio       | <----- | SpeechSynthesis       | <--------- | STAR Exemplar Synthesis |
| Output             |        | (Natural Voice)       |            | & Integrity Audit Log   |
+--------------------+        +-----------------------+            +-------------------------+
```

### Zero-Cost Voice Stack
- **Speech-to-Text (STT):** Browser-native `webkitSpeechRecognition` captures live interim and final transcripts with zero server GPU cost.
- **Text-to-Speech (TTS):** Browser-native `window.speechSynthesis` speaks questions aloud with natural pacing and zero network latency.
- **Visual Waveform:** The AI Interviewer card renders an animated waveform reflecting real-time state:
  - `"AI Speaking..."`: Waveform pulses while reading question.
  - `"Listening to Candidate..."`: Dynamically expands based on microphone volume level.
  - `"Analyzing response..."`: Rotates while processing turn.

---

## 3. Berri Proctor Integrity Layer

To preserve academic and enterprise recruitment integrity, `InterviewProctoringService` logs telemetry events to the `interview_proctoring_events` table:
- **`tab_switch`** (Medium severity): Detected via `document.addEventListener('visibilitychange')`.
- **`window_blur`** (Low severity): Detected via `window.addEventListener('blur')`.
- **`paste_detected`** (High severity): Intercepts clipboard paste attempts in the workspace.
- **`no_face` / `multiple_faces`** (Medium/High severity): Flagged when face presence is broken.

### Integrity Scoring Algorithm
- Starts at 100 points.
- Low severity events: -2 points.
- Medium severity events: -8 points.
- High severity events: -15 points.
- Status threshold:
  - `clean`: Score >= 85
  - `needs_review`: Score between 65 and 84
  - `flagged`: Score < 65

---

## 4. MasterMind Exemplar Answer Coaching Engine

Rather than showing only a numerical grade, `InterviewModelAnswerService` breaks down each evaluated answer across four dimensions:
1. **Candidate Transcript:** What was actually said.
2. **Exemplar STAR Answer:** How a senior/staff engineer would structure the response using Situation, Task, Action, and Result with architectural trade-offs.
3. **Missing Critical Nuances:** Pinpoints edge cases, error-handling mechanisms, or metrics omitted.
4. **Delivery & Speech Metrics:**
   - **Words Per Minute (WPM):** Optimal delivery pace is 120–160 WPM.
   - **Filler Word Detection:** Tracks instances of *"um"*, *"like"*, *"basically"*, *"you know"*, *"actually"*.
   - **Clarity Score:** Quantitative diction and structure rating out of 10.

---

## 5. Closed-Loop CareerLens Synergy

Standalone interview apps leave candidates with unaddressed weaknesses. In CareerLens, every identified interview gap features a 1-click **"Add Weaknesses to My Roadmap"** action:
- `POST /interview-preparation/sessions/{session_id}/sync-roadmap`
- Reads low-scoring criteria and improvement areas from the interview scorecard.
- Matches or provisions new `LearningRoadmapItem` milestones in the candidate's `LearningRoadmap`.
- Directly connects interview practice to structured career upskilling!
