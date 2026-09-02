# CareerLens Development Guide

## Project context

CareerLens is a learning-oriented B.Tech major project: an AI-powered career intelligence platform for students, freshers, professionals, and career switchers. It will support career profiles, resume intelligence, job discovery and matching, skill-gap analysis, learning roadmaps, applications, user-approved outreach, and personalized mock interviews.

The project starts as a modular monolith. The intended request path is:

`Next.js frontend -> FastAPI backend -> service layer -> repositories/database`

Keep AI/NLP work separate from API routes. PostgreSQL with pgvector is the planned initial data store for relational and vector-search needs.

## Planned stack

- Frontend: Next.js, TypeScript, React, Tailwind CSS
- Backend: Python, FastAPI
- Data: PostgreSQL and pgvector
- AI/NLP: sentence-transformers initially, LLM integrations where justified, Whisper-compatible speech-to-text

Docker is deferred until the project has a clear local development shape.

## Existing components

- **Plugs** is an existing LinkedIn job-scraping application built with FastAPI, Playwright, MongoDB, and Flutter. Do not rewrite it. Integrate it later through a dedicated adapter or integration layer.
- **Outreach Assistant** is an existing C#/.NET executable. Treat it as an external, user-approved integration; do not rewrite it without explicit instruction.

## Working rules

1. Work incrementally. Keep each implementation small, focused, and understandable.
2. Before a significant feature, explain the intended change, files affected, and why they are needed. Pause for developer direction when requirements or architecture are ambiguous.
3. Do not add dependencies unless they are needed for the current approved change.
4. Do not rewrite working components or make major architectural decisions without explicit instruction.
5. Keep API routes thin. Put business logic in services and database access in repositories.
6. Keep AI/NLP modules independent of route handlers so they can be evaluated and changed safely.
7. Treat outreach as opt-in and user-approved. Never design automated outreach that bypasses user control.
8. After each change, run proportionate checks and summarize what changed, why, and how it was verified.
9. Record durable architectural choices in `docs/decisions.md`.
10. Add learning-oriented explanations and, where useful, future notes under `docs/learning-notes/`.

## Current scope

This repository bootstrap intentionally contains no application implementation, authentication, scraping, AI pipeline, database schema, or frontend setup. Add those only through later focused tasks.
