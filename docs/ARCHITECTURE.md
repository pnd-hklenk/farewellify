# Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACES                              │
├─────────────────┬─────────────────┬─────────────────────────────────┤
│  Create Event   │  Admin Dashboard │   Submit Form                   │
│  (index.html)   │  (admin.html)    │   (submit.html)                 │
└────────┬────────┴────────┬─────────┴─────────────┬───────────────────┘
         │                 │                       │
         ▼                 ▼                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       FLASK APPLICATION (app.py)                     │
├─────────────────────────────────────────────────────────────────────┤
│  Routes:                                                             │
│  - POST /api/events              Create farewell event               │
│  - POST /api/events/{id}/send-invitations                            │
│  - POST /api/events/{id}/send-reminders                              │
│  - POST /api/events/{id}/submissions                                 │
│  - GET  /api/admin/{code}        Get event data for admin            │
│  - GET  /api/employees           Get active employees                │
│  - GET  /api/email/status        Check email + drive status          │
└────────┬────────────────────────────────────┬───────────────────────┘
         │                                    │
         ▼                                    ▼
┌─────────────────────┐          ┌────────────────────────────────────┐
│      SUPABASE       │          │         EXTERNAL SERVICES          │
│    (PostgreSQL)     │          ├────────────────────────────────────┤
├─────────────────────┤          │  RESEND (resend.com)               │
│ - farewell_events   │          │  - Send transactional emails       │
│ - team_members      │          │  - No OAuth required (API key)     │
│ - submissions       │          │                                    │
│ - employees         │          │  GOOGLE DRIVE (optional)           │
└─────────────────────┘          │  - Create folders via OAuth        │
                                 │  - Token stored in gmail_token.json│
                                 └────────────────────────────────────┘
```

## Data Flow

### 1. Creating a Farewell Event

```
User fills form → POST /api/events
                       │
                       ├─→ Create Drive folder (if connected)
                       ├─→ Insert into farewell_events
                       ├─→ Insert team_members (excluding honoree!)
                       │
                       └─→ Return admin URL + submit URL
```

### 2. Sending Invitations

```
Admin clicks "Send Invitations" → POST /api/events/{id}/send-invitations
                                        │
                                        ├─→ Get event details
                                        ├─→ Get all team members
                                        │
                                        └─→ For each member:
                                              ├─→ Generate personalized link (?email=xxx)
                                              ├─→ Build HTML email with first name greeting
                                              ├─→ Send via Resend API
                                              └─→ Update invited_at timestamp
```

### 3. Submitting a Message

```
Team member opens link → GET /submit/{event_id}?email=xxx
                              │
                              └─→ Pre-fill email field

Team member submits → POST /api/events/{id}/submissions
                           │
                           ├─→ Find team_member by email
                           ├─→ Save uploaded file (if any)
                           ├─→ Insert into submissions
                           │
                           └─→ Return success
```

## Component Details

### app.py (Flask Application)

The main entry point. Handles:

| Function | Purpose |
|----------|---------|
| `create_event()` | Create event + auto-folder + team members |
| `send_invitations()` | Email all team members with personalized links |
| `send_reminders()` | Email only those who haven't submitted |
| `create_submission()` | Save message + optional file upload |
| `get_admin_data()` | Return all event data for admin dashboard |
| `get_employees()` | Return active employees (with exclusion filter) |
| `serve_upload()` | Serve uploaded files |
| `send_email()` | Send email via Resend API |

### gmail_auth.py (Google Drive Integration)

Handles OAuth 2.0 for Google Drive (optional, for auto-folder creation):

| Function | Purpose |
|----------|---------|
| `start_auth_flow()` | Begin OAuth, return Google consent URL |
| `complete_auth_flow()` | Handle callback, save tokens |
| `create_farewell_folder()` | Create Drive folder with `YYMM Vorname` format |
| `is_drive_connected()` | Check if Drive tokens are valid |
| `get_drive_service()` | Get authenticated Drive API client |

### Email Service (Resend)

Emails are sent via [Resend](https://resend.com) API:

| Feature | Implementation |
|---------|----------------|
| API Key | `RESEND_API_KEY` environment variable |
| From address | `EMAIL_FROM` environment variable |
| Personalization | First name greeting ("Hi Adam,") |
| No login required | Personalized links with `?email=xxx` |

### Templates

| File | Purpose |
|------|---------|
| `index.html` | Create event form with employee checkboxes |
| `admin.html` | Dashboard showing stats, team list, send buttons |
| `submit.html` | Message textarea + file upload for team members |

All templates use **Pandata corporate design**:
- Colors: `#fa4f4f` (red), `#434343` (charcoal), `#eeeeee` (gray)
- Font: Open Sans
- Logo: Farewellify logo displayed on all pages

### Static Assets

| File | Purpose |
|------|---------|
| `assets/farewellify-logo.png` | Main logo (displayed on all pages, used as favicon) |

Assets are served via the `/assets/<filename>` route.

## Security Considerations

### Honoree Protection (Critical!)

The honoree must NEVER receive any communication:

1. **Frontend**: `loadEmployees()` excludes honoree email from checkbox list
2. **Backend**: `create_event()` skips honoree when adding team members
3. **Double-check**: Even if somehow added, they'd need to know the submit URL

### Personalized Links

- Links contain email in query param: `?email=xxx`
- No authentication required (by design - for ease of use)
- Email is trusted because we control who receives the link

### OAuth Tokens

- Stored in `gmail_token.json` (gitignored)
- Refresh token enables long-term access
- Can be revoked via Google account or app's disconnect button

## File Storage

### Local Uploads
- Directory: `uploads/`
- Files renamed to: `{event_id}_{uuid}.{ext}` or `{event_id}_msg_{uuid}.{ext}` for handwritten notes
- Max size: 50MB
- Allowed types: PDF, JPG, PNG

### Google Drive
- Folders created in shared parent folder
- ID: `1r0vtpUvIrJdpKiBDmA6MbH9EQ81c0HlM`
- Format: `YYMM Vorname` (e.g., "2601 Julian")
- Permissions: Anyone with link can edit
