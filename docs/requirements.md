# Functional Areas

This document captures the major planned capabilities. It is a scope map, not an implementation specification.

## 1. Identity and profile

- User authentication and authorization
- Career profile, preferences, experience, education, and skills

## 2. Resume intelligence

- Resume upload and safe storage
- Structured extraction and user review of inferred information
- Resume-derived skills and experience signals

## 3. Jobs and matching

- Job discovery through normalized job-data sources
- Explainable hybrid matching between profiles/resumes and jobs
- Filters, saved jobs, and transparent match explanations

## 4. Skills and learning

- Skill-gap analysis against roles or target jobs
- Personalized, editable learning roadmaps

## 5. Application workflow

- Application tracking with statuses, dates, and notes
- User-approved outreach through the existing Outreach Assistant integration

## 6. Interview practice

- Personalized interview-question generation
- Browser-based mock interviews using camera and microphone
- Whisper-compatible speech-to-text transcription
- Answer analysis and actionable feedback

## 7. Research and evaluation

- Evaluation of job matching quality and explainability
- Evaluation of interview-question and feedback usefulness
- Documented datasets, metrics, assumptions, and limitations

## Cross-cutting requirements

- Protect user data, resumes, recordings, and API credentials.
- Require explicit user approval for outreach actions.
- Make AI-generated recommendations explainable where practical.
- Keep external integrations replaceable through adapters.
- Build and evaluate features incrementally, with tests appropriate to each change.
