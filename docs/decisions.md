# Architectural Decision Log

Record durable decisions here as the project evolves. Each entry should include the context, decision, consequences, date, and any alternatives considered.

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
