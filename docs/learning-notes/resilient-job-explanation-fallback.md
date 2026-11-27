# Resilient Job Explanation and Deterministic Fallback Architecture

## Overview

In CareerLens, candidate-to-job matching combines deterministic skill and vector semantic analysis into an explainable hybrid score. While hybrid matching and deterministic evidence extraction are authoritative and fast, generating human-readable narrative summaries can leverage local Large Language Models (LLMs) such as Ollama.

However, relying entirely on an external or local daemon for a supplementary explanation introduces a single point of failure: if the local LLM is offline, restarting, or under heavy inference load, a raw dependency failure can bring down the entire endpoint with `503 Service Unavailable`.

This document explains how CareerLens achieves high availability, strict grounding, and robust error propagation for match intelligence.

---

## The Dual-Layer Architecture

### 1. Authoritative Deterministic Core
Before any LLM interaction occurs, the system evaluates the candidate's verified resume analysis against the target job requirements:
- **`required_skill_score` & `preferred_skill_score`**: Exact set operations on verified skills.
- **`semantic_score`**: Cosine similarity between resume and job embeddings.
- **`evidence`**: Direct and supporting excerpts extracted from projects, experience, education, and certifications.
- **`gap`**: Deterministic enumeration of missing required skills (`build_deterministic_gap`).
- **`next_step`**: Deterministic recommended action prioritized by missing skills or project proof (`build_deterministic_next_step`).

### 2. Candidate-Facing Phrasing Layer
The only component delegated to the LLM is `why_it_fits`: a 1-to-2 sentence candidate-facing natural language summary explaining how the matched skills align with the role.

```
                              +----------------------------+
                              |   explain_match()          |
                              |   (Authoritative Core)     |
                              +--------------+-------------+
                                             |
                               +-------------v-------------+
                               |    JobExplanationResult    |
                               +-------------+-------------+
                                             |
                 +---------------------------+---------------------------+
                 |                                                       |
        [Ollama Running]                                        [Ollama Offline / Error]
                 |                                                       |
                 v                                                       v
   JobExplanationGenerator                                build_deterministic_why_it_fits
   (qwen3.5 LLM generation)                              (Grounded deterministic synthesis)
                 |                                                       |
                 +---------------------------+---------------------------+
                                             |
                                             v
                              Return HTTP 200 OK
```

---

## Deterministic Fallback: `build_deterministic_why_it_fits`

When the LLM provider fails, times out, or is offline, the service falls back to `build_deterministic_why_it_fits()`:

```python
def build_deterministic_why_it_fits(
    explanation: MatchExplanationResponse,
    job_title: str,
    company: str | None = None,
) -> str:
    # 1. Synthesize verified matched required skills
    # 2. If none, synthesize matched preferred skills
    # 3. Incorporate verified evidence types (projects, experience, education)
```

### Grounding Principles
- **Zero Hallucination:** The fallback strictly uses `explanation.matched_required_skills` and `explanation.matched_preferred_skills`.
- **Target Role Grounding:** Incorporates `job_title` and `company` cleanly into the sentence.
- **Evidence Reinforcement:** If projects or experience support the match, acknowledges hands-on project proof without guessing specifics.
- **Formatting Constraint:** Plain text only, exactly 1-2 concise sentences.

---

## FastAPI Exception Propagation Best Practice

In FastAPI endpoints, care must be taken with generic `try...except Exception` blocks:

```python
# ANTI-PATTERN: Masks 401/403/404 exceptions as 503
try:
    require_owned_resume(resume_id, current_user, db)  # Raises HTTPException(403)
    result = generate_job_explanation(...)
except Exception as error:
    raise HTTPException(status_code=503, detail="...") from error
```

Because `HTTPException` inherits from Python's standard `Exception`, the handler catches FastAPI's own security exceptions and converts them into misleading 503 errors.

### Correct Pattern:
```python
try:
    require_owned_resume(resume_id, current_user, db)
    result = generate_job_explanation(...)
    return AIJobExplanationResponse(**result.model_dump())
except HTTPException:
    raise
except ResumeAnalysisNotFoundError as error:
    raise HTTPException(status_code=404, detail=str(error)) from error
except Exception as error:
    raise HTTPException(status_code=503, detail="The AI explanation service is currently unavailable.") from error
```

By explicitly re-raising `HTTPException`, authentication (401) and authorization (403) checks immediately bubble up to the client with their accurate status codes and messages.
