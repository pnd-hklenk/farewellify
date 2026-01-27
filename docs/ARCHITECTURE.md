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
│  - POST /api/admin/{code}/create-miro-collage  Create Miro board     │
│  - GET  /api/employees           Get active employees                │
│  - GET  /api/email/status        Check email + drive status          │
│  - GET  /api/miro/status         Check Miro API configuration        │
└────────┬────────────────────────────────────┬───────────────────────┘
         │                                    │
         ▼                                    ▼
┌─────────────────────┐          ┌────────────────────────────────────┐
│      SUPABASE       │          │         EXTERNAL SERVICES          │
├─────────────────────┤          ├────────────────────────────────────┤
│  PostgreSQL:        │          │  SMTP EMAIL                        │
│  - farewell_events  │          │  - Send invitations & reminders    │
│  - team_members     │          │  - Gmail or any SMTP provider      │
│  - submissions      │          │  - Configured via .env             │
│  - employees        │          │                                    │
├─────────────────────┤          │  MIRO API (optional)               │
│  Storage:           │          │  - Create farewell collage boards  │
│  - uploads bucket   │          │  - Auto-place photos + messages    │
│    (photos, notes)  │          │                                    │
└─────────────────────┘          └────────────────────────────────────┘
```

## Data Flow

### 1. Creating a Farewell Event

```
User fills form → POST /api/events
                       │
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
                                              ├─→ Send via SMTP
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
| `send_email()` | Send email via SMTP |
| `create_miro_collage()` | Create Miro board with photos + messages |

### Email Service (SMTP)

Emails are sent via SMTP:

| Feature | Implementation |
|---------|----------------|
| SMTP Host | `SMTP_HOST` environment variable (default: smtp.gmail.com) |
| SMTP Port | `SMTP_PORT` environment variable (default: 587) |
| Credentials | `SMTP_USER` and `SMTP_PASSWORD` environment variables |
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

### Organizer Participation

The organizer CAN participate in the farewell card:
- Organizer appears in the team members list and can select themselves
- They receive a personalized link like everyone else
- This allows the organizer to also upload photos and messages

### Personalized Links

- Links contain email in query param: `?email=xxx`
- No authentication required (by design - for ease of use)
- Email is trusted because we control who receives the link

## File Storage

### Supabase Storage
Files are stored in Supabase Storage for persistence across deployments.

| Setting | Value |
|---------|-------|
| Bucket | `uploads` |
| Public | Yes |
| Max size | 50MB |
| Allowed types | JPEG, PNG, GIF, PDF |

File naming convention:
- Photos: `{event_id}_photo_{uuid}.{ext}`
- Handwritten notes: `{event_id}_msg_{uuid}.{ext}`

Storage policies allow public read/write access to the `uploads` bucket.

### Download ZIP
The admin dashboard provides a "Download ZIP" button that:
1. Fetches all files from Supabase Storage
2. Creates a ZIP with all photos and notes
3. Includes `00_messages_summary.txt` with all text messages
