BEGIN;

ALTER TABLE interview_answers
    ADD COLUMN IF NOT EXISTS question_id INTEGER;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM interview_answers answer
        LEFT JOIN interview_questions question
            ON question.session_id = answer.session_id
           AND question.question = answer.question
           AND question.question_category = answer.question_category
        GROUP BY answer.id
        HAVING COUNT(question.id) <> 1
    ) THEN
        RAISE EXCEPTION
            'Cannot safely backfill interview_answers.question_id: '
            'at least one answer has zero or multiple matching questions.';
    END IF;
END
$$;

UPDATE interview_answers AS answer
SET question_id = question.id
FROM interview_questions AS question
WHERE question.session_id = answer.session_id
  AND question.question = answer.question
  AND question.question_category = answer.question_category
  AND answer.question_id IS NULL;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM interview_answers
        WHERE question_id IS NULL
    ) THEN
        RAISE EXCEPTION
            'Cannot make interview_answers.question_id NOT NULL: '
            'one or more answers remain unmapped.';
    END IF;
END
$$;

ALTER TABLE interview_answers
    ADD CONSTRAINT fk_interview_answers_question_id
    FOREIGN KEY (question_id)
    REFERENCES interview_questions(id);

ALTER TABLE interview_answers
    ALTER COLUMN question_id SET NOT NULL;

COMMIT;