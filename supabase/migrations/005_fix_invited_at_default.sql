-- Fix: invited_at should NOT default to now().
-- New team members must start with invited_at = NULL so the admin page
-- correctly shows them as "not invited" until an email is actually sent.
ALTER TABLE team_members ALTER COLUMN invited_at DROP DEFAULT;
