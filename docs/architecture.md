# Planned Architecture

## Overview

CareerLens will begin as a modular monolith: one web frontend and one FastAPI backend, with clear internal module boundaries. This keeps the project practical for learning and deployment while avoiding premature microservices.

```text
Browser (Next.js / React)
          |
          v
FastAPI API routes
          |
          v
Application services
   |          |          |
   v          v          v
Repositories  AI/NLP     Integration adapters
   |          |          |
   v          v          +--> Plugs job-scraping application
PostgreSQL    Model/LLM  +--> Outreach Assistant (.NET executable)
  + pgvector  providers
```

## Intended responsibilities

### Frontend

The Next.js application will provide the user interface, collect explicit user input and consent, and call the backend API. It should not contain business rules, scraping logic, or direct database access.

### Backend API

FastAPI route handlers will validate requests, apply authentication and authorization once introduced, and delegate work to services. Routes should remain thin and should not embed AI or persistence logic.

### Application services

Services will coordinate use cases such as resume analysis, job matching, roadmap generation, application tracking, outreach approval, and interview feedback. They own business workflows and policy checks.

### Repositories and database

Repositories will isolate persistence concerns. PostgreSQL is planned for application data; pgvector will initially support embedding storage and similarity search. The data model and migrations will be designed only when the first persistence feature is approved.

### AI/NLP modules

AI and NLP capabilities will live outside API routes. Initial candidates are sentence-transformers for embeddings, Whisper-compatible transcription, and narrowly scoped LLM integrations. Each model-dependent feature should expose a testable interface and support evaluation.

### Integration adapters

External systems are accessed through adapters rather than being absorbed into the core application:

- **Plugs:** retain its existing FastAPI, Playwright, MongoDB, and Flutter implementation. A future adapter will normalize its job output for CareerLens.
- **Outreach Assistant:** retain the existing .NET executable. A future integration will require explicit user approval before any outreach action and will record the action outcome.

## Initial module boundaries

The backend will eventually be organized by functional modules, for example profile, resume, jobs, matching, skills, roadmaps, applications, outreach, and interviews. Shared infrastructure should be kept small and introduced only when a feature requires it.

### Interview blueprint foundation

The interview preparation module now has a persisted blueprint aggregate. A
blueprint references a resume and job, and owns competency, question-plan, and
rubric child records. Generation is an application-service workflow: the
service loads persisted resume analysis and job requirements, calls the
provider-neutral `LLMGenerationProvider`, validates grounded structured JSON,
and asks a repository to persist the complete aggregate atomically. API routes
only validate HTTP input, map domain errors, and return Pydantic responses.

Blueprint generation is deliberately separate from an executed
`InterviewSession`. The existing deterministic question/session flow remains
backward compatible, while future milestones can start a session from a
validated blueprint. Blueprint records store references and the evidence
strings needed to explain why a question is relevant; raw resume contents and
candidate performance scores are not stored in the blueprint.

The J5.2 execution engine uses `InterviewExecutionSession` and immutable
`InterviewSessionQuestion` snapshots. A session is created from a persisted
blueprint in one transaction, starts explicitly, and accepts only the next
unanswered snapshot in order. Answers and progress are committed together;
the final answer transitions the session to `completed`. This separate table
family preserves the existing legacy interview-session API while making
blueprint execution resumable and auditable.

Adaptive decisions are requested explicitly after a planned answer through
`POST /interview-preparation/sessions/{session_id}/adaptive-decision`. The
answer is already committed before provider generation starts, so provider
failure leaves the answer and session progress intact. A unique
session/parent-question decision constraint makes retries idempotent; a short
row-locked transaction persists either a `continue` decision or one follow-up
snapshot. Follow-ups use fractional conversation ordering and do not open a
second answer model.

## Deferred decisions

- Authentication provider and authorization model
- Database schema, migration tooling, and local PostgreSQL workflow
- API versioning and error-response conventions
- LLM provider, data-retention policy, and evaluation datasets
- Real-time interview transport and media storage policy
- Docker and deployment topology

These must be decided deliberately as related features are introduced.
