BEGIN;

ALTER TABLE interview_session_questions
    ADD COLUMN IF NOT EXISTS is_follow_up BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE interview_session_questions
    ADD COLUMN IF NOT EXISTS parent_question_id INTEGER;

ALTER TABLE interview_session_questions
    ADD COLUMN IF NOT EXISTS conversation_order NUMERIC(10, 3);

UPDATE interview_session_questions
SET conversation_order = question_order
WHERE conversation_order IS NULL;

ALTER TABLE interview_session_questions
    ALTER COLUMN conversation_order SET NOT NULL;

ALTER TABLE interview_session_questions
    ALTER COLUMN blueprint_question_id DROP NOT NULL;

ALTER TABLE interview_execution_answers
    ADD COLUMN IF NOT EXISTS conversation_order NUMERIC(10, 3);

UPDATE interview_execution_answers AS answers
SET conversation_order = questions.conversation_order
FROM interview_session_questions AS questions
WHERE answers.session_question_id = questions.id
  AND answers.conversation_order IS NULL;

ALTER TABLE interview_execution_answers
    ALTER COLUMN conversation_order SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_interview_session_questions_parent'
          AND conrelid = 'interview_session_questions'::regclass
    ) THEN
        ALTER TABLE interview_session_questions
            ADD CONSTRAINT fk_interview_session_questions_parent
            FOREIGN KEY (parent_question_id)
            REFERENCES interview_session_questions(id);
    END IF;
END
$$;

CREATE UNIQUE INDEX IF NOT EXISTS
    uq_adaptive_session_conversation_order
    ON interview_session_questions(session_id, conversation_order);

CREATE TABLE IF NOT EXISTS interview_adaptive_decisions (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL
        REFERENCES interview_execution_sessions(id),
    parent_question_id INTEGER NOT NULL
        REFERENCES interview_session_questions(id),
    outcome VARCHAR(30) NOT NULL,
    rationale TEXT NOT NULL,
    follow_up_type VARCHAR(40),
    competency_reference VARCHAR(255),
    follow_up_question_id INTEGER
        REFERENCES interview_session_questions(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_adaptive_decision_session_parent
        UNIQUE (session_id, parent_question_id)
);

COMMIT;
