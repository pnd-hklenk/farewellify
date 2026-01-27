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
│  - GET  /api/gmail/status        Check Google connection             │
└────────┬────────────────────────────────────┬───────────────────────┘
         │                                    │
         ▼                                    ▼
┌─────────────────────┐          ┌────────────────────────────────────┐
│      SUPABASE       │          │    GOOGLE APIS (gmail_auth.py)     │
│    (PostgreSQL)     │          ├────────────────────────────────────┤
├─────────────────────┤          │  - Gmail API (send emails)         │
│ - farewell_events   │          │  - Drive API (create folders)      │
│ - team_members      │          │                                    │
│ - submissions       │          │  OAuth 2.0 flow:                   │
│ - employees         │          │  1. /api/gmail/connect             │
└─────────────────────┘          │  2. Google consent screen          │
                                 │  3. /api/gmail/callback            │
                                 │  4. Token stored locally           │
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
                                              ├─→ Generate personalized link
                                              ├─→ Replace [LINK] placeholder
                                              ├─→ Send email via Gmail API
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
| Gmail routes | OAuth flow for Google connection |

### gmail_auth.py (Google Integration)

Handles OAuth 2.0 for Gmail and Drive:

| Function | Purpose |
|----------|---------|
| `start_auth_flow()` | Begin OAuth, return Google consent URL |
| `complete_auth_flow()` | Handle callback, save tokens |
| `send_email_via_gmail()` | Send HTML email via Gmail API |
| `create_farewell_folder()` | Create Drive folder with `YYMM Name` format |
| `is_gmail_connected()` | Check if tokens are valid |
| `disconnect_gmail()` | Remove stored tokens |

### Templates

| File | Purpose |
|------|---------|
| `index.html` | Create event form with employee checkboxes |
| `admin.html` | Dashboard showing stats, team list, send buttons |
| `submit.html` | Message textarea + file upload for team members |

All templates use **Pandata corporate design**:
- Colors: `#fa4f4f` (red), `#434343` (charcoal), `#eeeeee` (gray)
- Font: Open Sans

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
- Files renamed to: `{uuid}_{original_name}`
- Max size: 10MB
- Allowed types: PDF, JPG, PNG

### Google Drive
- Folders created in shared parent folder
- ID: `1r0vtpUvIrJdpKiBDmA6MbH9EQ81c0HlM`
- Format: `YYMM Vorname` (e.g., "2601 Julian")
- Permissions: Anyone with link can edit
