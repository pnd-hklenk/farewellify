# API Reference

Base URL: `http://localhost:5001`

## Events

### Create Event

```http
POST /api/events
Content-Type: application/json
```

**Request Body:**
```json
{
  "honoreeName": "Julian Arnold",
  "honoreeEmail": "julian.arnold@pandata.de",
  "organizerName": "Hannah Klenk",
  "organizerEmail": "hannah.klenk@pandata.de",
  "deadline": "2026-01-30T11:00:00",
  "message": "Hi Pandatas, we're celebrating Julian's farewell...",
  "teamMembers": [
    { "name": "Adam Butz", "email": "adam.butz@pandata.de" },
    { "name": "Aly Nagy", "email": "aly.nagy@pandata.de" }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "event": {
    "id": "uuid",
    "access_code": "abc12345",
    "honoree_name": "Julian Arnold",
    ...
  },
  "adminUrl": "/admin/abc12345",
  "submitUrl": "/submit/{event_id}",
  "driveFolderUrl": "https://drive.google.com/drive/folders/..."
}
```

**Notes:**
- If Google Drive is connected, a folder is auto-created
- The honoree is automatically excluded from team members

---

### Send Invitations

```http
POST /api/events/{event_id}/send-invitations
```

**Response:**
```json
{
  "success": true,
  "sentCount": 20,
  "totalMembers": 22
}
```

**Notes:**
- Sends personalized emails to all team members
- Each email contains a unique link: `?email={member_email}`
- Updates `invited_at` timestamp for each member

---

### Send Reminders

```http
POST /api/events/{event_id}/send-reminders
```

**Response:**
```json
{
  "success": true,
  "sentCount": 5,
  "pendingMembers": 5
}
```

**Notes:**
- Only sends to members who haven't submitted
- Updates `reminder_sent_at` timestamp

---

### Create Submission

```http
POST /api/events/{event_id}/submissions
Content-Type: multipart/form-data
```

**Form Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `eventId` | string | Yes | Event UUID |
| `email` | string | Yes | Team member's email |
| `name` | string | No | Team member's name |
| `message` | string | No | Farewell message (typed) |
| `messageFile` | file | No | Handwritten note - PDF, JPG, or PNG (max 50MB) |
| `file` | file | No | Photo - PDF, JPG, or PNG (max 50MB) |

**Response:**
```json
{
  "success": true,
  "submission": {
    "id": "uuid",
    "message": "Good luck Julian!",
    "file_url": "/uploads/abc123_photo.jpg"
  }
}
```

**Error Responses:**
```json
{ "error": "No matching team member found" }  // 400
{ "error": "File type not allowed" }          // 400
{ "error": "File too large" }                 // 400
```

---

## Admin

### Get Admin Data

```http
GET /api/admin/{access_code}
```

**Response:**
```json
{
  "event": {
    "id": "uuid",
    "honoreeName": "Julian Arnold",
    "honoreeEmail": "julian.arnold@pandata.de",
    "organizerName": "Hannah Klenk",
    "organizerEmail": "hannah.klenk@pandata.de",
    "deadline": "2026-01-30T11:00:00",
    "message": "Hi Pandatas...",
    "googleDriveFolderUrl": "https://..."
  },
  "teamMembers": [
    {
      "id": "uuid",
      "name": "Adam Butz",
      "email": "adam.butz@pandata.de",
      "invitedAt": "2026-01-27T10:00:00",
      "reminderSentAt": null,
      "hasSubmitted": true
    }
  ],
  "submissions": [
    {
      "id": "uuid",
      "memberName": "Adam Butz",
      "memberEmail": "adam.butz@pandata.de",
      "message": "Good luck Julian!",
      "fileUrl": "/uploads/abc_photo.jpg",
      "submittedAt": "2026-01-27T14:30:00"
    }
  ],
  "stats": {
    "totalMembers": 22,
    "submitted": 15,
    "pending": 7
  }
}
```

---

## Employees

### Get Employees

```http
GET /api/employees?exclude=julian.arnold@pandata.de&exclude=hannah.klenk@pandata.de
```

**Query Parameters:**
| Param | Description |
|-------|-------------|
| `exclude` | Email(s) to exclude (can repeat) |

**Response:**
```json
[
  { "name": "Adam Butz", "email": "adam.butz@pandata.de" },
  { "name": "Alexandra Cornea", "email": "alexandra.cornea@pandata.de" }
]
```

**Notes:**
- Only returns `is_active = true` employees
- Used by frontend to populate team member checkboxes
- Excludes honoree and organizer automatically

---

## Gmail/Google Integration

### Check Status

```http
GET /api/gmail/status
```

**Response (connected):**
```json
{
  "connected": true,
  "driveConnected": true,
  "available": true,
  "email": "hannah.klenk@pandata.de",
  "credentialsConfigured": true
}
```

**Response (not configured):**
```json
{
  "connected": false,
  "available": true,
  "credentialsConfigured": false
}
```

---

### Start OAuth Flow

```http
GET /api/gmail/connect
```

**Response:**
```json
{
  "authUrl": "https://accounts.google.com/o/oauth2/..."
}
```

**Notes:**
- Redirect user to `authUrl` for Google consent
- After consent, Google redirects to `/api/gmail/callback`

---

### OAuth Callback

```http
GET /api/gmail/callback?code={auth_code}&state={state}
```

**Response:**
Redirects to `/` with tokens stored in `gmail_token.json`

---

### Disconnect

```http
POST /api/gmail/disconnect
```

**Response:**
```json
{
  "success": true
}
```

**Notes:**
- Deletes `gmail_token.json`
- Google connection must be re-established

---

## Pages (HTML)

### Create Event Page
```http
GET /
```
Returns `index.html` - the form to create a new farewell event.

### Submit Page
```http
GET /submit/{event_id}?email={optional_email}
```
Returns `submit.html` - form for team members to submit messages.

If `email` is provided, it's pre-filled in the form.

### Admin Dashboard
```http
GET /admin/{access_code}
```
Returns `admin.html` - dashboard to manage the event.

---

## File Serving

### Get Uploaded File
```http
GET /uploads/{filename}
```

Serves files from the `uploads/` directory.

### Get Static Asset
```http
GET /assets/{filename}
```

Serves static assets (logo, icons) from the `assets/` directory.

**Example:**
```
GET /assets/farewellify-logo.png
```

---

## Error Responses

All endpoints may return:

```json
{
  "error": "Error message here"
}
```

Common status codes:
- `400` - Bad request (missing fields, invalid data)
- `404` - Resource not found
- `500` - Server error (usually database issues)
