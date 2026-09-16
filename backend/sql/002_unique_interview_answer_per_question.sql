BEGIN;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM interview_answers
        GROUP BY session_id, question_id
        HAVING COUNT(*) > 1
    ) THEN
        RAISE EXCEPTION
            'Cannot add unique constraint: duplicate answers exist '
            'for at least one session_id/question_id pair.';
    END IF;
END
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname =
            'uq_interview_answers_session_question'
          AND conrelid = 'interview_answers'::regclass
    ) THEN
        ALTER TABLE interview_answers
            ADD CONSTRAINT
                uq_interview_answers_session_question
            UNIQUE (session_id, question_id);
    END IF;
END
$$;

COMMIT;