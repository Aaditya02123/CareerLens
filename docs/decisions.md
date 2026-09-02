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
