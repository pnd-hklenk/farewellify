# Changelog

All notable changes to this project are documented in this file.

---

## [2026-06-25] - Fix invitation emails never sent + editable invite message

### Fixed

#### Invitation email bug (`team_members.invited_at` schema)
- **Root cause:** The `invited_at` column had `DEFAULT now()`, so every team member was marked as "invited" the moment they were inserted — before any email was sent.
- **Effect:** The "Send Invitations" button on the admin page was always disabled (showed 0 "not invited"). Organizers could only click "Remind All Pending", which sent reminder-style emails (different subject/body) instead of the original invitation.
- **Fix:** Migration `005_fix_invited_at_default` drops the DEFAULT. New members start with `invited_at = NULL`; it's only set when `send_email()` succeeds.

#### Admin page reloads after sending invitations
- `sendInvitations()` now calls `loadData()` on success so the stats, button states, and message field update immediately.

### Added

#### Editable invitation message (`admin.html`, `app.py`)
- New "Invitation Message" section on the admin page between stats and action buttons.
- Textarea shows the event's `message` field; editable while no invitations have been sent, then locked (disabled + hint text).
- "Save" button calls new `PATCH /api/admin/{access_code}/update-message` endpoint.
- Endpoint validates that no team member has `invited_at` set before allowing the update.

#### Custom message in invitation emails
- Both `send_invitations` and `add_team_member` (inline invite) now use the event's `message` as the email body when set, falling back to `MODE_COPY` defaults when empty.
- Custom message is HTML-escaped (`html.escape`) and newlines converted to `<br>` for safe email rendering.

### Decisions
- **Reuse `farewell_events.message` rather than a new column** — the field already exists and is filled during event creation. No schema change needed for the custom message feature.
- **Lock editing after any invitation sent** — prevents divergence between emails already sent and future ones. Server-side enforcement via `invited_at` check.
- **HTML-escape custom messages** — even though the organizer is a trusted user, escaping prevents accidental HTML breakage (e.g. `<` or `&` in the message).

### Files modified
- `app.py` — `import html`, new `update_event_message` endpoint, custom message in both invite email builders
- `templates/admin.html` — invite message UI section, `saveInviteMessage()` JS, `loadData()` call after send
- `supabase/migrations/005_fix_invited_at_default.sql` — `ALTER TABLE team_members ALTER COLUMN invited_at DROP DEFAULT`
- `docs/API.md` — new endpoint docs, updated send-invitations notes
- `docs/DATABASE.md` — updated `message` and `invited_at` descriptions, added migration docs
- `.claude/rules/knowledge-event-types.md` — updated API surface, backend copy, decisions, migration history
- `docs/CHANGELOG.md` — this entry

---

## [2026-06-08] - Expand allowed file types and improve upload error handling

### Fixed

#### File uploads (`app.py`, `submit.html`)
- **Root cause:** Only PDF, JPG, and PNG were accepted. iPhone photos (HEIC) and other common formats (GIF, WebP) were silently rejected — the backend skipped them without any error, and the frontend file picker wouldn't even show them.
- **Fix:** Added GIF, HEIC, and WebP to `ALLOWED_EXTENSIONS` (backend) and all `accept` attributes (frontend).
- **Explicit errors:** All three upload handlers (`messageFile`, `photos`, legacy `file`) now return a 400 JSON error naming the rejected file and listing allowed types, instead of silently skipping.
- **Client-side validation:** Added `validateFile()` in `submit.html` that checks both file type and size (50MB) before uploading, with clear `alert()` messages.

#### UI text (`submit.html`)
- Updated "PDF, JPG, or PNG" → "PDF, JPG, PNG, GIF, HEIC, or WebP" in the handwritten note upload area.
- Updated "Accepted formats: JPG, PNG" → "Accepted formats: JPG, PNG, GIF, HEIC, WebP" in the photo upload area.

#### Admin dashboard (`admin.html`)
- Image preview regex now matches `.heic` files (previously only matched jpg/jpeg/png/gif/webp).

### Changed

#### Documentation
- `docs/API.md` — Fixed wrong endpoint path (`/api/events/{id}/submissions` → `/api/submissions`), added missing `photos` and `existingPhotos` fields, updated allowed file types.
- `docs/DEVELOPMENT.md` — Updated troubleshooting file type list.
- `docs/ARCHITECTURE.md` — Allowed types already included HEIC/WebP (no change needed).
- `.claude/rules/knowledge-supabase.md` — Allowed types already included HEIC/WebP (no change needed).

### Decisions
- **HEIC excluded from Miro image check** (intentional): `app.py:1363` checks for image extensions to place on Miro boards but omits `.heic` because Miro's API only supports JPEG, PNG, GIF, and WebP. HEIC handwritten notes will still be stored and downloadable — they just won't appear on the Miro collage.
- **Backend returns 400 with filename**: The error message includes the uploaded filename for clarity. This is safe because the response is JSON consumed by `alert()`, not rendered as HTML.

### Files modified
- `app.py` — `ALLOWED_EXTENSIONS`, content type map, explicit error returns for all 3 upload handlers
- `templates/submit.html` — `accept` attributes, UI text, `validateFile()` + `MAX_FILE_SIZE` + `ALLOWED_EXTENSIONS` in JS
- `templates/admin.html` — image preview regex
- `docs/API.md` — endpoint path, form fields, allowed types
- `docs/DEVELOPMENT.md` — troubleshooting file types
- `docs/CHANGELOG.md` — this entry

---

## [2026-06-08] - Add proper logging for storage uploads and submissions

### Changed

#### Logging (`app.py`, `gmail_auth.py`)
- Replaced all `print()` calls with proper `logging` / `app.logger` calls across both files.
- Configured gunicorn logger integration for production (GCP Cloud Run) with a safe fallback for local dev and `flask run`.
- Storage uploads now log on success (filename, size, content type) and on failure — so 403-type errors will appear in GCP Cloud Run logs instead of being silently swallowed.
- Submission errors now include `event_id` and `email` in the log message for easier correlation.
- `gmail_auth.py` uses a module-level `logging.getLogger(__name__)` logger.

### Fixed
- **Logging setup guard**: The original gunicorn logger integration would wipe Flask's default handler if gunicorn wasn't present (e.g. running `flask run` without `--debug`). Now only overrides handlers when gunicorn is actually running.

### Files modified
- `app.py` — Logging setup, all `print()` → `app.logger`, upload success/failure logging with context
- `gmail_auth.py` — `import logging`, all `print()` → `logger`

---

## [2026-06-04] - Fix storage upload RLS error (403)

### Fixed

#### Storage RLS policies (Supabase)
- **Root cause:** The `storage.objects` table had RLS enabled but **no policies** for the `uploads` bucket. Photo uploads via the Supabase anon key failed with `403 — new row violates row-level security policy`.
- **Fix:** Added INSERT, SELECT, and UPDATE policies on `storage.objects` scoped to `bucket_id = 'uploads'`. Applied as a Supabase migration (`allow_public_storage_uploads`).

#### Stale Supabase project URL
- The hardcoded default `SUPABASE_URL` in `app.py` and several docs still referenced the old project (`datpxrveaizpigltowju`). Updated to the current project (`wjmslehtpfwpyjykfshu`).

### Changed
- **`.env.example`**: Updated `SUPABASE_KEY` placeholder from `your_anon_public_key_here` to `your_service_role_key_here`. The service role key is appropriate for server-side apps (the key is never exposed to browsers) and bypasses RLS entirely, avoiding future policy gaps.
- **`docs/DATABASE.md`**: Documented storage RLS policies in the SQL setup section and migrations section. Added missing `photo_urls`, `miro_added`, and `submitted_at` columns to the submissions table docs.

### Decisions
- **Storage RLS policies over disabling RLS**: We added targeted policies rather than disabling RLS on `storage.objects`, preserving defense-in-depth.
- **Service role key recommended for production**: Since the Flask backend is the only Supabase client and runs server-side, the service role key is safe and avoids RLS friction. The storage policies remain as a fallback if the anon key is ever used.

### Files modified
- `app.py` — Updated default `SUPABASE_URL`
- `.env.example` — Updated key placeholder
- `docs/DATABASE.md` — Storage policies, missing columns
- `docs/DEVELOPMENT.md` — Updated Supabase URL
- `docs/CHANGELOG.md` — This entry

---

## [2026-05-11] - Event Types: Farewell vs. 5-Year Anniversary

### Added

#### Schema
- **`farewell_events.event_type`** — new `text NOT NULL DEFAULT 'farewell'` column with `CHECK (event_type IN ('farewell','anniversary'))`. Existing rows default to `'farewell'`. Migration: `add_event_type_to_farewell_events`.

#### Backend (`app.py`)
- **`MODE_COPY` dict** — single source of truth for all per-mode user-facing strings (email subjects, email bodies, Miro title / board name, ZIP filename prefix, ZIP summary heading).
- **Helpers** `get_event_mode(event_data)` and `get_copy(mode)` — defensive lookup with `'farewell'` fallback.
- `POST /api/events` accepts an `eventType` field (`farewell` | `anniversary`) and persists it.
- **Honoree auto-deactivation is now mode-gated** — only farewell honorees are flipped to `is_active=false` (anniversary honorees stay at the company, so we must NOT deactivate them).
- `GET /api/events/<event_id>` returns `event_type` (snake_case, raw column).
- `GET /api/admin/<code>` returns `eventType` (camelCase, normalised via `get_event_mode`).
- All email senders (`send_invitations`, `send_reminders`, `add_team_member` invite) and the Miro board + ZIP download now read copy from `MODE_COPY`.

#### Google Drive (`gmail_auth.py`)
- `create_farewell_folder` gained an optional `event_type='farewell'` parameter. Anniversary folders are named `YYMM 5Y FirstName` (e.g. `2605 5Y Julian`); farewells keep the existing `YYMM FirstName` format. Both share the same parent folder (`FAREWELL_CARDS_FOLDER_ID`) — there is no separate anniversary parent yet.

#### Templates
- **`index.html`** — new radio toggle (Farewell card vs. 5-year anniversary book) at the top of the create form. Tagline, "Who is leaving?/Who is celebrating 5 years?" question, submit-button label, success-modal copy, and the auto-generated team message all swap based on the selected mode (`MODE_UI` dict, `applyModeUI()`).
- **`submit.html`** — page heading, greeting subline, step-1 label, message textarea placeholder, and document title swap based on the event's `event_type` returned from the API (`LABELS` dict).
- **`admin.html`** — dashboard header label ("Farewell Card for" vs. "5-Year Anniversary Book for") and document title swap based on `event.eventType`.

### Decisions / Caveats
- **Single Drive parent folder.** Both modes still write into `FAREWELL_CARDS_FOLDER_ID`; only the folder name differs. If we later want a dedicated anniversary parent, add an env var (e.g. `ANNIVERSARY_BOOKS_FOLDER_ID`) and branch in `create_farewell_folder`.
- **Deadline field is reused.** For farewells it's the last day; for anniversaries it's the anniversary date. The DB column stays `deadline` to avoid a breaking rename.
- **Honoree exclusion behaviour is unchanged** — the honoree is always excluded from the invite list in both modes, keeping it a surprise.
- **Inactive employees** are skipped from invites in both modes (correct: ex-employees shouldn't be pinged for anniversaries either).
- **DB table name `farewell_events`** kept for backwards compatibility — renaming would require touching every query, RLS policy, and migration.

### Full reference
See `.claude/rules/knowledge-event-types.md` for the implementation map and a "where do I touch X?" index.

---

## [2026-01-27] - Miro Collage Integration

### Added

#### Miro Integration (`app.py`)
- **New feature: Create Miro Collage** - Automatically generate a farewell collage board in Miro from all submissions
- **Grid layout algorithm** - Photos are distributed in a non-overlapping grid based on submission count
- **Decorative frame** - White background with red border (Pandata branding)
- **Title banner** - Red banner with white "FAREWELL [NAME]!" text
- **Photo arrangement** - Multiple photos per person arranged in a fan/stack pattern with rotation
- **Sticky notes** - Messages displayed on colored sticky notes (rotating through 8 colors)
- **Message format** - `"Message text..."` followed by `– FirstName` at the bottom

#### New API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/admin/{code}/create-miro-collage` | POST | Create Miro board from submissions |
| `/api/miro/status` | GET | Check if Miro is configured |

#### New Functions
| Function | Purpose |
|----------|---------|
| `create_miro_board()` | Create a new board in Miro team |
| `add_miro_image()` | Add photo with position, size, rotation |
| `add_miro_sticky_note()` | Add colored sticky note |
| `add_miro_text()` | Add text element |
| `add_miro_shape()` | Add rectangle/frame |
| `calculate_grid_positions()` | Calculate non-overlapping positions |
| `get_sticky_color()` | Get rotating sticky note color |

#### Admin Dashboard (`templates/admin.html`)
- **New button**: "Create Miro Collage" (yellow, Miro branding)
- **Auto-detection**: Button only shows if Miro is configured
- **Direct link**: After creation, "Open in Miro" link appears

### Configuration

Add to `.env`:
```
MIRO_ACCESS_TOKEN=your-access-token
MIRO_TEAM_ID=your-team-id
```

### Database Migration

Run in Supabase SQL Editor:
```sql
ALTER TABLE farewell_events ADD COLUMN IF NOT EXISTS miro_board_url TEXT;
```

### Files Modified
- `app.py` - Miro API integration, collage generation
- `templates/admin.html` - Miro button and JavaScript
- `docs/ARCHITECTURE.md` - Miro integration documentation
- `docs/DATABASE.md` - miro_board_url column
- `docs/CHANGELOG.md` - This entry
- `README.md` - Miro feature and setup instructions
- `.env.example` - Miro configuration variables

---

## [2026-01-27] - Production Ready Release

### Changed

#### Organizer Participation
- **Organizer can now participate**: The organizer is no longer excluded from the team members list
- Organizer can select themselves to receive a personalized link and upload their own photos/messages
- Only the **honoree** is excluded from all communications (as before)

#### Documentation Cleanup
- Removed Google Drive references (feature deprecated)
- Updated email configuration to use SMTP instead of Resend
- Translated remaining German text to English ("Ein Ordner wird automatisch erstellt" → "A folder will be automatically created")
- Updated all documentation to reflect current feature set

---

## [2026-01-27] - File Upload Fixes & Email Improvements

### Fixed

#### File Upload Error Handling (`app.py`)
- **Added JSON error response for 413 errors**: Previously returned HTML error page which caused "Unexpected token '<'" JavaScript errors
- **Added `RequestEntityTooLarge` import** from werkzeug.exceptions
- **New error handler** returns proper JSON: `{"success": false, "error": "File too large. Maximum size is 50MB."}`

#### Form Submission (`templates/submit.html`)
- **Fixed duplicate file sending**: Form was sending files twice (via FormData from form + manual append), causing uploads to fail even for small files
- **Cleaned up form data construction**: Now explicitly builds FormData with only necessary fields

### Changed

#### File Size Limit
- **Increased MAX_FILE_SIZE** from 10MB to **50MB** in `app.py`
- Updated UI text in `submit.html` to show "max 50MB"
- Updated documentation in `DEVELOPMENT.md`, `API.md`, `ARCHITECTURE.md`

#### Email Templates (`app.py`)
- **Table-based HTML layout**: Changed from div-based to table-based layout for better email client compatibility (Gmail, Outlook)
- **Left-aligned content**: Using `align="left"` on `<td>` elements instead of CSS `text-align`
- **Formatted date**: Changed from "2026-01-28" to "Wednesday, 28.01." format
- **Updated wording**: "You can upload or draft" → "Please upload or draft"

#### File Upload Handling (`app.py`)
- **Separate handling for two file types**:
  - `messageFile` - handwritten notes (saved as `{event_id}_msg_{uuid}.{ext}`)
  - `file` - photos (saved as `{event_id}_{uuid}.{ext}`)
- **Smart fallback**: If only messageFile is uploaded, it becomes the primary file_url

#### Submit Form (`templates/submit.html`)
- **Added favicon**: `<link rel="icon" type="image/png" href="/assets/farewellify-logo.png">`
- **Changed header logo**: From Font Awesome icon to actual logo image

### API Changes

**POST /api/submissions** now accepts:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `eventId` | string | Yes | Event UUID |
| `email` | string | Yes | Team member's email |
| `name` | string | No | Team member's name |
| `message` | string | No | Typed farewell message |
| `messageFile` | file | No | Handwritten note (PDF, JPG, PNG, max 50MB) |
| `file` | file | No | Photo (PDF, JPG, PNG, max 50MB) |

### Documentation Cleanup
- Removed Google Drive references (feature deprecated)
- Deleted `docs/GOOGLE_INTEGRATION.md` (no longer needed)
- Updated all docs to reflect SMTP-only email setup

### Files Modified
- `app.py` - Error handler, file size, email templates, file handling
- `templates/submit.html` - Form submission logic, favicon, logo
- `docs/DEVELOPMENT.md` - Updated max file size, removed Drive references
- `docs/API.md` - New form fields, removed Gmail/Drive endpoints
- `docs/ARCHITECTURE.md` - Updated file naming format, removed Drive sections
- `docs/DATABASE.md` - Removed google_drive_folder_url column
- `README.md` - Removed Drive feature, updated project structure

---

## [2026-01-27] - Email Template & UI Refinements

### Changed

#### Email Templates (`app.py`)

**Invitation Email - NEW TEXT:**
```
Subject: Farewell Card for {name} 🎉

Hi {recipient},

It is {name}'s last day on {date}, and so we would like you 
to contribute to their farewell card.

You can upload or draft your message via our new farewell app:

[Add Your Message] (button)

---
This is your personalized link – no login required!
Organized by {organizer}
```

**Reminder Email - Updated to match:**
```
Subject: Reminder: Farewell Card for {name} ⏰

Hi {recipient},

Just a friendly reminder: {name}'s last day is on {date}, and we 
haven't received your contribution to their farewell card yet.

You can upload or draft your message via our farewell app:

[Add Your Message Now] (button)

---
This is your personalized link – no login required!
```

**Removed from both emails:**
- Google Drive folder link (no longer needed)
- Redundant deadline line (now in main text)
- Verbose "please share a few words" text

#### Submit Form (`templates/submit.html`)
- **Removed duplicate deadline**: Deadline now only shows once at the bottom of the form (removed from greeting area)

### Previous Changes (earlier today)

#### Admin Dashboard (`templates/admin.html`)
- **Smaller file previews**: Reduced image thumbnails from full-width (`max-w-xs`) to compact 64x64px thumbnails
- **Compact submission cards**: Redesigned layout with horizontal arrangement (thumbnail | name + message | download)
- **Truncated messages**: Long messages now show max 2 lines with ellipsis (`line-clamp-2`)
- **Click-to-view**: Thumbnails link to full-size image in new tab

#### Submit Form (`templates/submit.html`)
- **Removed event message display**: No longer shows the full email message with link placeholder
- **Enhanced personal greeting**: Now includes:
  - First name greeting ("Hi Adam! 👋")
  - Context line ("Please submit your message for Julian's farewell card")
- **First name only**: Honoree name now shows first name only (e.g., "Julian" not "Julian Arnold")

#### Event Creation (`templates/index.html`)
- **Simplified default message**: Internal-only message, no longer includes link placeholder

### Technical Details

**Files modified:**
- `app.py` - Email templates (invitation + reminder)
- `templates/submit.html` - Removed duplicate deadline display
- `docs/EMAIL_SETUP.md` - Updated email template documentation
- `docs/CHANGELOG.md` - This file

---

## [2026-01-26] - Initial Implementation

### Added
- Flask application with Supabase backend
- Employee management from database
- Farewell event creation
- Personalized submission links
- File upload support (photos + handwritten notes)
- Photo nudge UI with confirmation checkbox
- Resend email integration
- Google Drive folder auto-creation (optional)
- Admin dashboard with stats
- Pandata corporate design (colors, fonts)

### Security
- Honoree protection (never receives emails)
- Personalized links (no login required)
- Row Level Security in Supabase
