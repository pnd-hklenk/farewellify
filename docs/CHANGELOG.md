# Changelog

All notable changes to this project are documented in this file.

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

### Files Modified
- `app.py` - Error handler, file size, email templates, file handling
- `templates/submit.html` - Form submission logic, favicon, logo
- `docs/DEVELOPMENT.md` - Updated max file size
- `docs/API.md` - New form fields documented
- `docs/ARCHITECTURE.md` - Updated file naming format

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
