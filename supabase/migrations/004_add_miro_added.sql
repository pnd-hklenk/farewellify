-- Add miro_added flag to submissions
-- Tracks whether a submission has been manually added to a Miro board,
-- allowing organizers to tick off contributions as they place them.

ALTER TABLE submissions
    ADD COLUMN IF NOT EXISTS miro_added BOOLEAN NOT NULL DEFAULT FALSE;
