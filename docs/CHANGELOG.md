# Changelog

All notable changes to this project are documented in this file.

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
