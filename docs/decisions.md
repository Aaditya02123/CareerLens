# Architectural Decision Log

Record durable decisions here as the project evolves. Each entry should include the context, decision, consequences, date, and any alternatives considered.

## D-000: First-party authentication and protected resources

- **Status:** Accepted
- **Date:** 2026-11-24
- **Context:** Career records and resumes were accessible through unprotected API identifiers.
- **Decision:** Use Argon2 password hashes and short-lived signed JWT access tokens. All application routes except health and authentication require a bearer token. User-owned resource routes must verify ownership before calling services.
- **Consequences:** Client applications must authenticate before calling protected APIs; new endpoints must use the shared current-user and ownership helpers.

## D-001: Start as a modular monolith

- **Status:** Accepted
- **Date:** 2026-09-02
- **Context:** CareerLens covers several distinct domains but is being built as a learning-oriented major project.
- **Decision:** Use one Next.js frontend and one FastAPI backend with internal module boundaries; do not begin with microservices.
- **Consequences:** Development and debugging stay simpler. Modules must still have clear responsibilities so that future extraction remains possible if justified.

## D-002: Keep existing systems external

- **Status:** Accepted
- **Date:** 2026-09-02
- **Context:** Plugs and Outreach Assistant already exist and serve specialized purposes.
- **Decision:** Preserve both systems and access them later through integration adapters.
- **Consequences:** CareerLens needs normalized contracts and error handling at integration boundaries, but avoids an unnecessary rewrite.

## D-003: Keep AI/NLP out of API routes

- **Status:** Accepted
- **Date:** 2026-09-02
- **Context:** Model-backed logic needs testing, evaluation, and iteration independent of HTTP concerns.
- **Decision:** Place AI/NLP logic behind service-facing interfaces rather than inside FastAPI route handlers.
- **Consequences:** Route handlers remain thin; model choices can evolve with less impact on the API.

## D-004: Persist interview blueprints as validated aggregates

- **Status:** Accepted
- **Date:** 2026-11-16
- **Context:** Interview practice needs a repeatable role-specific plan and
  rubric before a conversational session can begin.
- **Decision:** Store an `InterviewBlueprint` with child competency, ordered
  question, and rubric records. Generate it in a service through the existing
  provider-neutral LLM interface, validate structured output and grounding,
  then persist the aggregate atomically through a repository.
- **Consequences:** Blueprint retrieval is deterministic and auditable, and
  later sessions can reference a stable plan. Provider output that cannot be
  grounded is rejected; no candidate performance scores are generated at this
  stage. The development `init_db.py` registration remains the schema setup
  mechanism until migration tooling is introduced.
- **Alternatives considered:** Keeping blueprints only in memory would lose
  reproducibility; changing the existing `InterviewSession` question table
  would mix planning with execution and risk breaking current APIs.

## D-005: Isolate executable sessions from the legacy interview tables

- **Status:** Accepted
- **Date:** 2026-11-16
- **Context:** The repository already contains an older mock-interview
  session API with different lifecycle values and answer contracts.
- **Decision:** Implement J5.2 with `InterviewExecutionSession`, immutable
  `InterviewSessionQuestion` snapshots, and `InterviewSessionAnswer` records.
  Creation and answer/progress updates are transactional, and the next
  question is always derived from persisted question order and answers.
- **Consequences:** Existing interview APIs remain compatible while the new
  blueprint engine has explicit created/in-progress/completed lifecycle
  semantics. The source blueprint is never mutated; future evaluation can
  reference stable session snapshots.
- **Alternatives considered:** Altering the existing `interview_sessions`
  table would require a risky lifecycle migration and could break committed
  clients and tests.

## D-006: Make adaptivity an explicit idempotent operation

- **Status:** Accepted
- **Date:** 2026-11-16
- **Context:** LLM generation is slow and may fail, while answers must remain
  durable and repeatable interview decisions must not create duplicate
  follow-ups.
- **Decision:** Keep answer submission synchronous and deterministic. Expose a
  separate adaptive-decision request after a planned answer. Generate outside
  database locks, then use a short locked transaction plus a unique
  session/parent-question constraint to persist one `continue` or one
  follow-up decision. Follow-ups are session-question snapshots ordered
  immediately after their parent.
- **Consequences:** Provider failures are safely retryable and cannot lose a
  submitted answer. Concurrent requests may duplicate provider work, but only
  one persisted decision wins and subsequent requests return it. Adaptivity is
  bounded to one follow-up per planned question and three per session.
- **Alternatives considered:** Calling the provider while holding the session
  row lock would simplify serialization but would hold a database lock during
  network latency and increase contention.

## D-007: Persist rubric-grounded answer evaluations and scorecards

- **Status:** Accepted
- **Date:** 2026-11-16
- **Context:** Executed interview answers need explainable feedback and a
  repeatable aggregate without blocking answer submission or making hiring
  decisions.
- **Decision:** Evaluate answers in a separate service using the persisted
  blueprint rubric and provider-neutral structured JSON. Persist one
  criterion-level evaluation per answer and one derived scorecard per
  execution session. Provider calls occur before the short persistence
  transaction; uniqueness constraints make retries idempotent.
- **Consequences:** Scores are auditable and pending answers are explicit.
  Provider failures leave session answers unchanged. The scorecard is
  advisory only and does not alter progression or rank candidates. A future
  migration must create the evaluation tables and snapshot rubric criteria on
  execution questions.
- **Alternatives considered:** Recomputing evaluations on every read would
  lose reproducibility; adding scoring to answer submission would make
  provider availability a prerequisite for completing an interview.

## D-008: Constrain structured interview generation at the provider boundary

- **Status:** Accepted
- **Date:** 2026-11-17
- **Context:** Local Ollama models sometimes returned prose instead of the
  JSON required by blueprint and answer-evaluation schemas.
- **Decision:** Keep the existing provider abstraction, add native Ollama JSON
  schema requests for providers that support them, parse one unambiguous JSON
  object centrally, and validate it with the existing Pydantic models. Allow
  at most one corrective retry for output or grounding validation failures.
  Provider connectivity and timeout errors propagate without retry, and no
  invalid output is persisted.
- **Consequences:** Compatible models receive stronger structural guidance and
  malformed responses fail predictably. Model capability still matters; a
  model that cannot satisfy the schema remains an explicit provider failure.
- **Alternatives considered:** Relying only on prompt instructions was less
  reliable. Adding a second LLM framework would increase dependencies and
  obscure the replaceable provider boundary.

## D-009: Structured LLM generation observability and safe error classification

- **Status:** Accepted
- **Date:** 2026-11-20
- **Context:** Structured LLM workflows (blueprints, adaptive follow-ups, answer scorecards) require visibility into stage latencies, retries, and failure reasons without exposing candidate resume details, prompt contents, or evaluation text in logs.
- **Decision:** Introduce a lightweight LLM observability module with structured JSON event logging, explicit failure categorization (`GenerationFailureCategory`), per-attempt stage timing metrics (provider wait, JSON parsing, Pydantic validation, grounding checks), and scoped correlation contexts. Restrict logged fields strictly to safe telemetry and non-sensitive provider metadata.
- **Consequences:** Production and test environments gain traceable generation observability and error categorization without leaking candidate PII or evaluation text. Services log timings predictably and failure categories map cleanly to retry and monitoring semantics.
- **Alternatives considered:** Logging raw prompts and responses would compromise user privacy and leak candidate data; generic Python exception logging lacked structured telemetry and granular stage timings.

## D-010: Semantic CSS theme tokens and dark/light mode toggle

- **Status:** Accepted
- **Date:** 2026-11-20
- **Context:** Hardcoded dark arbitrary Tailwind values (`bg-[#0a0a0a]`, `text-white/35`) caused severe low-contrast readability defects (failing WCAG AA) and prevented light theme support across workspaces.
- **Decision:** Establish semantic CSS variables (`--cl-bg`, `--cl-surface`, `--cl-text`, `--cl-text-soft`, `--cl-muted`, `--cl-faint`, `--cl-border`, `--cl-accent`, `--cl-input-bg`) for both dark (`[data-theme="dark"]`) and light (`[data-theme="light"]`) themes. Persist the chosen mode in `localStorage` with OS color-scheme fallback and provide an accessible toggle in `Topbar`.
- **Consequences:** All components across Dashboard, Jobs, Resumes, Roadmaps, and Interviews adapt uniformly with high-contrast text and cohesive styling in both dark and light modes.
- **Alternatives considered:** Scoped per-page dark classes resulted in duplicated, divergent color rules and visual bugs.

## D-011: Audience persona lenses and light/dark theme contrast correction

- **Status:** Accepted
- **Date:** 2026-11-24
- **Context:** The Overview Page mixed disparate career metrics without distinguishing between the needs of students/freshers (entry roles, project proof, 8-week foundation roadmaps) and working professionals (commercial impact, senior/staff roles, architecture deltas). Additionally, arbitrary dark gradients (`linear-gradient(..., #0f1722)`), unreadable pastel status text (`text-red-100`, `text-emerald-100` on light backgrounds), and poor button contrast in light mode degraded visual legibility.
- **Decision:**
  1. Introduce an interactive Audience Persona Selector on the Overview Page (`student`, `professional`, and `unified`), tailoring the hero banner, KPI metrics, career journey blueprints, recommended opportunities, and skill gap radar to the active lens.
  2. Wire up top-level workspace navigation (`onNavigate`) across the Overview Page to provide a direct launchpad into Resume, Jobs, Roadmap, and Interview workspaces.
  3. Correct light and dark mode CSS tokens: replace hardcoded dark color stops with semantic CSS variables (`var(--cl-surface-muted)`), add `--cl-accent-contrast` (`#090d14` in dark, `#ffffff` in light) for crisp button text contrast, and replace low-contrast Tailwind text utilities with semantic status tokens (`var(--cl-danger)`, `var(--cl-success)`).
- **Consequences:** The overview experience is cleanly organized and immediately relevant to both early-career students and experienced professionals. Both light and dark modes achieve full WCAG AA contrast compliance without visual clipping or inverted gradients.
- **Alternatives considered:** Creating entirely separate page routes for students and professionals would duplicate workspace navigation and fragment the application monolith.

## D-012: Frontend authentication state integration and animated credential experience

- **Status:** Accepted
- **Date:** 2026-11-24
- **Context:** Following the backend first-party authentication milestone (D-000), the frontend lacked an authentication layer, login/registration UI, and token management, leaving client requests unauthenticated. Furthermore, the backend strictly requires >= 12 character passwords (hashed with Argon2), which needed clear user guidance and visual feedback.
- **Decision:**
  1. Install `lucide-react` for security and form iconography and `motion` for physics-based spring animations.
  2. Build a comprehensive authentication UI (`AuthPage` and `AuthModal`) featuring spring-animated tab switching between Sign In and Create Account, dynamic password strength meter with live validation of the 12-character requirement, password visibility toggle, error/success banners, and 1-click demo account quick-fill.
  3. Create `AuthContext` to manage authentication state, automatic session re-verification with `/auth/me`, and persistent local storage synchronization.
  4. Integrate `getAuthHeaders()` into frontend API services and update `Topbar` and `Sidebar` with authenticated user profiles, initials avatar, and sign-out controls.
  5. Add `OPTIONS` and `DELETE` methods to backend CORSMiddleware to prevent preflight blocking of custom `Authorization` headers.
- **Consequences:** Users can register and log in with immediate animated visual feedback. All frontend requests transmit bearer tokens when authenticated. The UI adapts seamlessly to dark and light modes.
- **Alternatives considered:** Relying purely on basic un-animated forms would result in high user friction and failed registrations due to the backend's 12-character password minimum.

## D-013: Grounded deterministic fallback for match explanations during LLM provider downtime

- **Status:** Accepted
- **Date:** 2026-11-24
- **Context:** The `/matching/resumes/{resume_id}/jobs/{job_id}/ai-explanation` endpoint relies on local LLM generation (Ollama) solely to formulate the candidate-facing `why_it_fits` text sentence, while `gap`, `next_step`, and underlying matching scores are already computed deterministically from verified resume evidence. When the local Ollama instance is not running, times out, or encounters errors, the API previously threw an uncaught provider error that mapped to HTTP 503 (`Service Unavailable`), breaking job intelligence in the UI and polluting client console logs. Additionally, generic `except Exception` blocks in the endpoint handler inadvertently masked `HTTPException` (such as 401 Unauthorized or 403 Forbidden from resume ownership checks) into 503 errors.
- **Decision:**
  1. Implement `build_deterministic_why_it_fits()` in `job_explanation_service.py` to deterministically synthesize candidate-facing alignment text directly from verified matched required skills, matched preferred skills, and evidence source types (projects, experience, education).
  2. Wrap LLM generation in `generate_job_explanation()` with graceful fallback: if the LLM provider fails or is unreachable, log a warning and fall back to the grounded deterministic `why_it_fits` text rather than failing the request.
  3. Explicitly re-raise `HTTPException` before generic exception handling in `match_explaination.py` to prevent security and validation exceptions from masking as 503 errors.
  4. Update `embedding_service.py` to attempt `local_files_only=True` for SentenceTransformer loading first, eliminating HuggingFace network retry timeouts during offline operation.
- **Consequences:** The job intelligence workspace remains fully operational and highly available even when local LLM services are offline or under heavy load. The resulting explanations strictly adhere to CareerLens grounding rules (never hallucinating skills or unverified experience). Authorization errors (403) and resource errors (404) are accurately reported with their true HTTP status codes.
- **Alternatives considered:** Failing the entire match intelligence endpoint with 503 whenever Ollama is offline degraded user experience for a supplementary feature whose underlying match data was already completely calculated and available.

## D-014: Berri MasterMind interactive interview room and Berri Proctor integrity verification

- **Status:** Accepted
- **Date:** 2026-11-25
- **Context:** The interview workspace was limited to static scorecard reviews of past sessions without a live, voice/face-enabled interactive interview taker. Furthermore, modern recruitment screening demands integrity verification (proctoring telemetry for tab switches, blur, and copy/paste) alongside hyper-actionable candidate coaching (exemplar STAR model answers, speech pacing/filler word analysis, and closed-loop roadmap synchronization).
- **Decision:**
  1. **Berri Proctor Integrity Layer:** Created `ProctoringEvent` model (`interview_proctoring_events` table) and `InterviewProctoringService` to capture telemetry events (`tab_switch`, `window_blur`, `paste_detected`, `no_face`, `multiple_faces`, `audio_anomaly`), computing an integrity trust score (0-100) and chronological timeline.
  2. **Interactive Audio/Video Interview Room:** Built `HardwareCheckScreen` (camera mirror, Web Audio RMS microphone volume meter, speaker test, and network latency check) and `LiveInterviewRoom` (pulsing AI waveform with state awareness, speech synthesis question playback, live Web Speech API speech-to-text, video mirror, and candidate code/scratchpad drawer).
  3. **MasterMind Exemplar Coaching Engine:** Built `InterviewModelAnswerService` and `ModelAnswerModal` to formulate staff-level STAR model answers, pinpoint exact missing technical nuances, calculate delivery metrics (WPM, filler words count/detected, clarity score), and compare candidate transcripts with benchmarks.
  4. **Closed-Loop Ecosystem Synergy:** Implemented `InterviewRoadmapSyncService` (`POST /sync-roadmap`) enabling 1-click provisioning of identified interview weaknesses directly into the candidate's CareerLens `LearningRoadmap`.
- **Consequences:** CareerLens delivers a complete, enterprise-ready AI interview and proctoring suite with dual modes (Practice Coaching vs Proctored Screening), operating at $0 external cost via browser-native Web Audio/Speech APIs and resilient local/free-tier LLM fallbacks.
- **Alternatives considered:** Relying on third-party paid interview APIs (e.g. Agora or proprietary proctoring platforms) would incur recurring per-minute cloud costs and vendor lock-in.

## Decision template

```markdown
## D-XXX: Short title

- **Status:** Proposed | Accepted | Superseded
- **Date:** YYYY-MM-DD
- **Context:** Why is a decision needed?
- **Decision:** What was chosen?
- **Consequences:** Benefits, trade-offs, and follow-up work.
- **Alternatives considered:** Optional.
```
