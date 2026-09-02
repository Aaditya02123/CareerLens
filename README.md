# CareerLens

CareerLens is a B.Tech major project for career intelligence. It is planned as an AI-assisted platform that helps people find relevant jobs, understand skill gaps, plan learning, manage applications, use approved outreach tools, and practise personalized mock interviews.

## Status

The repository is in its documentation-first bootstrap stage. No application features, dependencies, database schema, or deployment setup have been implemented yet.

## Planned technology

- Next.js, TypeScript, React, and Tailwind CSS for the web interface
- Python and FastAPI for the backend
- PostgreSQL with pgvector for data and vector search
- sentence-transformers, LLM integrations where appropriate, and Whisper-compatible speech-to-text for AI/NLP capabilities

## Repository layout

- `frontend/` — future Next.js application
- `backend/` — future FastAPI modular monolith
- `integrations/` — boundaries for existing external systems
- `docs/` — architecture, requirements, decisions, and learning notes

Read [the architecture overview](docs/architecture.md), [functional requirements](docs/requirements.md), and [decision log](docs/decisions.md) before starting a feature.
