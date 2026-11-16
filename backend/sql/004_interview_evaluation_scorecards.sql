BEGIN;

ALTER TABLE interview_session_questions
    ADD COLUMN IF NOT EXISTS rubric_criteria JSONB NOT NULL DEFAULT '[]'::jsonb;

CREATE TABLE IF NOT EXISTS interview_answer_evaluations (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL
        REFERENCES interview_execution_sessions(id),
    answer_id INTEGER NOT NULL
        REFERENCES interview_execution_answers(id),
    question_id INTEGER NOT NULL
        REFERENCES interview_session_questions(id),
    competency_reference VARCHAR(255) NOT NULL,
    weighted_score NUMERIC(4, 2) NOT NULL,
    strengths JSONB NOT NULL DEFAULT '[]'::jsonb,
    improvement_areas JSONB NOT NULL DEFAULT '[]'::jsonb,
    actionable_feedback JSONB NOT NULL DEFAULT '[]'::jsonb,
    evaluation_status VARCHAR(20) NOT NULL,
    provider_name VARCHAR(120) NOT NULL DEFAULT 'unknown',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_interview_answer_evaluation_answer
        UNIQUE (answer_id)
);

ALTER TABLE interview_answer_evaluations
    ADD COLUMN IF NOT EXISTS provider_name VARCHAR(120) NOT NULL DEFAULT 'unknown';

CREATE INDEX IF NOT EXISTS ix_interview_answer_evaluations_session_id
    ON interview_answer_evaluations(session_id);

CREATE INDEX IF NOT EXISTS ix_interview_answer_evaluations_answer_id
    ON interview_answer_evaluations(answer_id);

CREATE TABLE IF NOT EXISTS interview_criterion_evaluations (
    id SERIAL PRIMARY KEY,
    evaluation_id INTEGER NOT NULL
        REFERENCES interview_answer_evaluations(id),
    criterion_id VARCHAR(80) NOT NULL,
    criterion_name VARCHAR(255) NOT NULL,
    score INTEGER NOT NULL,
    explanation TEXT NOT NULL,
    evidence_excerpts JSONB NOT NULL DEFAULT '[]'::jsonb,
    improvement_suggestion TEXT NOT NULL,
    CONSTRAINT uq_interview_criterion_evaluation
        UNIQUE (evaluation_id, criterion_id)
);

CREATE TABLE IF NOT EXISTS interview_scorecards (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL
        REFERENCES interview_execution_sessions(id),
    status VARCHAR(20) NOT NULL,
    overall_score NUMERIC(4, 2),
    evaluated_answer_count INTEGER NOT NULL DEFAULT 0,
    pending_answer_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    competency_scores JSONB NOT NULL DEFAULT '[]'::jsonb,
    strengths JSONB NOT NULL DEFAULT '[]'::jsonb,
    improvement_areas JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_interview_scorecard_session
        UNIQUE (session_id)
);

COMMIT;
