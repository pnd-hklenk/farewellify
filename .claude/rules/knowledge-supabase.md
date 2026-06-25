# Knowledge: supabase.md

> Persistent project knowledge. Loaded automatically by PandaOS via `.claude/rules/`.

## Project

| Setting | Value |
|---------|-------|
| Project ref | `wjmslehtpfwpyjykfshu` |
| URL | `https://wjmslehtpfwpyjykfshu.supabase.co` |
| Old/stale ref (do NOT use) | `datpxrveaizpigltowju` (still in seed migration URLs) |

## Authentication key

The Flask backend uses `SUPABASE_KEY` from the environment. This should be the **service role key**, not the anon key:

- The app is server-side only (key never exposed to browsers).
- The service role key bypasses RLS, avoiding policy gaps.
- If the anon key is used instead, all table + storage RLS policies must be in place (see below).

## Storage

| Setting | Value |
|---------|-------|
| Bucket | `uploads` |
| Public | Yes |
| Max file size | 50 MB |
| Allowed types | JPEG, PNG, GIF, PDF, HEIC, WebP |

### RLS policies on `storage.objects`

These were added via migration `allow_public_storage_uploads` (2026-06-04) after a production 403 error blocked photo uploads:

| Policy | Command | Expression |
|--------|---------|------------|
| Allow public uploads to uploads bucket | INSERT | `WITH CHECK (bucket_id = 'uploads')` |
| Allow public read from uploads bucket | SELECT | `USING (bucket_id = 'uploads')` |
| Allow public update in uploads bucket | UPDATE | `USING (bucket_id = 'uploads')` |

No DELETE policy exists because the app never deletes storage objects.

### Table RLS policies

All four public tables (`farewell_events`, `team_members`, `submissions`, `employees`) have permissive `USING (true)` / `WITH CHECK (true)` policies. These are wide open by design — access control is at the application layer (personalized links, access codes).

## Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | Service role key over anon key | Server-side only; avoids RLS friction. Storage policies remain as defence-in-depth. |
| 2 | Storage RLS policies scoped to `bucket_id = 'uploads'` | Targeted — only the uploads bucket is exposed, not all of storage. |
| 3 | No DELETE policy on storage | The app never deletes uploaded files. Add one if that changes. |
| 4 | Wide-open table RLS | Acceptable because there is no direct client-side Supabase access. All queries go through Flask. |

## Logging

Storage uploads log both success and failure via `app.logger` (in `app.py`) so errors appear in GCP Cloud Run logs. If a storage upload fails, the log includes the filename, file size, content type, and the exception. Submission errors also log `event_id` and `email` for correlation. `gmail_auth.py` uses `logging.getLogger(__name__)`.

Do not reintroduce `print()` for error output — use `app.logger` (in Flask context) or `logging.getLogger(__name__)` (in standalone modules).

## Things NOT to do

- Do not revert to the anon key without verifying all storage + table policies are in place.
- Do not add a new storage bucket without adding corresponding RLS policies.
- Do not reference the old project ref `datpxrveaizpigltowju` in code or docs (it is a different, stale project).
