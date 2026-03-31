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
  "submitUrl": "/submit/{event_id}"
}
```

**Notes:**
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
    "message": "Hi Pandatas..."
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

### Download All Submissions

```http
GET /api/admin/{access_code}/download-all
```

**Response:**
- Returns a ZIP file containing all photos, handwritten notes, and a summary text file

**ZIP Contents:**
- `00_messages_summary.txt` - All text messages with names
- `01_Adam_Butz_note.jpg` - Handwritten notes
- `01_Adam_Butz_photo01.jpg` - Photos (numbered if multiple)

---

### Create Miro Collage

```http
POST /api/admin/{access_code}/create-miro-collage
```

**Response:**
```json
{
  "success": true,
  "boardUrl": "https://miro.com/app/board/uXjVGKePJ4s=",
  "boardId": "uXjVGKePJ4s=",
  "stats": {
    "submissions": 2,
    "photosAdded": 5,
    "notesAdded": 1,
    "messagesAdded": 1
  }
}
```

**Error Responses:**
```json
{ "error": "Miro API not configured. Please add MIRO_ACCESS_TOKEN and MIRO_TEAM_ID to .env" }  // 400
{ "error": "No submissions yet. Add some messages before creating a collage!" }  // 400
{ "error": "Event not found" }  // 404
```

**Notes:**
- Requires `MIRO_ACCESS_TOKEN` and `MIRO_TEAM_ID` in `.env`
- Creates a new board in the configured Miro team
- Auto-generates grid layout based on submission count
- Photos are arranged in fan/stack pattern with rotation
- Messages appear on colored sticky notes with format: `"Message..." – FirstName`

---

## Miro Status

### Check Miro Configuration

```http
GET /api/miro/status
```

**Response (configured):**
```json
{
  "configured": true,
  "teamId": "3074457357930600413"
}
```

**Response (not configured):**
```json
{
  "configured": false,
  "teamId": null
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

## Email Status

### Check Email Configuration

```http
GET /api/email/status
```

**Response (configured):**
```json
{
  "emailConfigured": true
}
```

**Response (not configured):**
```json
{
  "emailConfigured": false
}
```

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
