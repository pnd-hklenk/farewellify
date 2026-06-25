# Database Schema

The app uses **Supabase** (PostgreSQL) for data storage.

## Connection

```
URL: https://wjmslehtpfwpyjykfshu.supabase.co
```

Credentials are in `.env` - see `.env.example` for the template.

## Tables

### farewell_events

Main table storing each event (farewell card or 5-year anniversary book).

| Column | Type | Description |
|--------|------|-------------|
| `id` | uuid (PK) | Auto-generated unique ID |
| `honoree_name` | text | Name of the person being honoured |
| `honoree_email` | text | Email (used for exclusion from invites) |
| `organizer_name` | text | Who's organizing |
| `organizer_email` | text | Organizer's email |
| `deadline` | timestamp | Last day (farewell) or anniversary date |
| `message` | text | Invitation message — included in the invitation email body. Editable on the admin page before invitations are sent. |
| `access_code` | text | Unique code for admin URL |
| `google_drive_folder_url` | text | Link to Google Drive folder (optional) |
| `miro_board_url` | text | Link to Miro collage board (optional) |
| `event_type` | text NOT NULL DEFAULT `'farewell'` | One of `'farewell'` or `'anniversary'`. `CHECK` constraint enforces values. Drives all user-facing copy + the honoree-deactivation rule. |
| `created_at` | timestamp | Auto-set on creation |

**Access Code**: Generated automatically by Supabase trigger. Used in admin URL:
```
/admin/{access_code}
```

### team_members

People invited to submit messages.

| Column | Type | Description |
|--------|------|-------------|
| `id` | uuid (PK) | Auto-generated unique ID |
| `event_id` | uuid (FK) | References farewell_events.id |
| `name` | text | Team member's name |
| `email` | text | Team member's email |
| `invited_at` | timestamp | When invitation email was sent (NULL until sent — no DEFAULT) |
| `reminder_sent_at` | timestamp | When last reminder was sent |
| `created_at` | timestamp | Auto-set on creation |

### submissions

Messages submitted by team members.

| Column | Type | Description |
|--------|------|-------------|
| `id` | uuid (PK) | Auto-generated unique ID |
| `event_id` | uuid (FK) | References farewell_events.id |
| `team_member_id` | uuid (FK) | References team_members.id |
| `message` | text | The farewell message |
| `file_url` | text | URL to uploaded file (if any) |
| `photo_urls` | text | JSON array of photo URLs (up to 15) |
| `miro_added` | boolean DEFAULT false | Whether this submission has been added to Miro |
| `submitted_at` | timestamp | When submitted |

### employees

Master list of all Pandata employees.

| Column | Type | Description |
|--------|------|-------------|
| `id` | uuid (PK) | Auto-generated unique ID |
| `name` | text | Full name |
| `email` | text | Email address |
| `is_active` | boolean | Whether to show in selection |
| `created_at` | timestamp | Auto-set on creation |

**Note**: `is_active = false` for employees on leave (e.g., maternity), and is auto-set to `false` when a **farewell** event is created for that employee. Anniversary events do **not** deactivate the honoree.

## Entity Relationship Diagram

```
┌─────────────────────┐
│    employees        │
├─────────────────────┤
│ id (PK)             │
│ name                │
│ email               │
│ is_active           │
└─────────────────────┘
         │
         │ (used to populate team selection)
         ▼
┌─────────────────────┐       ┌─────────────────────┐
│  farewell_events    │       │    team_members     │
├─────────────────────┤       ├─────────────────────┤
│ id (PK)             │◄──────│ event_id (FK)       │
│ honoree_name        │       │ id (PK)             │
│ honoree_email       │       │ name                │
│ organizer_name      │       │ email               │
│ organizer_email     │       │ invited_at          │
│ deadline            │       │ reminder_sent_at    │
│ message             │       └──────────┬──────────┘
│ access_code         │                  │
└─────────────────────┘                  │
                                         │
                              ┌──────────▼──────────┐
                              │    submissions      │
                              ├─────────────────────┤
                              │ id (PK)             │
                              │ event_id (FK)       │
                              │ team_member_id (FK) │
                              │ message             │
                              │ file_url            │
                              └─────────────────────┘
```

## SQL to Create Tables

If you need to recreate the tables:

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Farewell events
CREATE TABLE farewell_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    honoree_name TEXT NOT NULL,
    honoree_email TEXT,
    organizer_name TEXT NOT NULL,
    organizer_email TEXT NOT NULL,
    deadline TIMESTAMP WITH TIME ZONE NOT NULL,
    message TEXT,
    access_code TEXT UNIQUE DEFAULT substr(md5(random()::text), 1, 8),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Team members
CREATE TABLE team_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID REFERENCES farewell_events(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    invited_at TIMESTAMP WITH TIME ZONE,  -- no DEFAULT; set only when invite email is sent
    reminder_sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Submissions
CREATE TABLE submissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID REFERENCES farewell_events(id) ON DELETE CASCADE,
    team_member_id UUID REFERENCES team_members(id) ON DELETE CASCADE,
    message TEXT,
    file_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Employees (master list)
CREATE TABLE employees (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Row Level Security (optional but recommended)
ALTER TABLE farewell_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE team_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE submissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE employees ENABLE ROW LEVEL SECURITY;

-- Allow all operations (adjust for production)
CREATE POLICY "Allow all" ON farewell_events FOR ALL USING (true);
CREATE POLICY "Allow all" ON team_members FOR ALL USING (true);
CREATE POLICY "Allow all" ON submissions FOR ALL USING (true);
CREATE POLICY "Allow all" ON employees FOR ALL USING (true);

-- Storage: allow public access to the uploads bucket
CREATE POLICY "Allow public uploads to uploads bucket"
  ON storage.objects FOR INSERT TO public
  WITH CHECK (bucket_id = 'uploads');
CREATE POLICY "Allow public read from uploads bucket"
  ON storage.objects FOR SELECT TO public
  USING (bucket_id = 'uploads');
CREATE POLICY "Allow public update in uploads bucket"
  ON storage.objects FOR UPDATE TO public
  USING (bucket_id = 'uploads');
```

## Current Employee Data

The `employees` table contains all Pandata team members:

| Name | Email | Active |
|------|-------|--------|
| Adam Butz | adam.butz@pandata.de | ✅ |
| Alexandra Cornea | alexandra.cornea@pandata.de | ✅ |
| Aly Nagy | aly.nagy@pandata.de | ✅ |
| ... | ... | ... |
| Krisztina Papp | krisztina.papp@pandata.de | ❌ (maternity) |

To deactivate an employee:
```sql
UPDATE employees SET is_active = false WHERE email = 'email@pandata.de';
```

## Migrations

### Add Miro Board URL (if upgrading from older version)
```sql
ALTER TABLE farewell_events ADD COLUMN IF NOT EXISTS miro_board_url TEXT;
```

### Add Google Drive Folder URL (if upgrading from older version)
```sql
ALTER TABLE farewell_events ADD COLUMN IF NOT EXISTS google_drive_folder_url TEXT;
```

### Add photo_urls to submissions (for multiple photos)
```sql
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS photo_urls TEXT;
```

### Add storage RLS policies for the uploads bucket
Without these policies, file uploads via the anon key fail with a 403
"new row violates row-level security policy" error.
```sql
CREATE POLICY "Allow public uploads to uploads bucket"
  ON storage.objects FOR INSERT TO public
  WITH CHECK (bucket_id = 'uploads');
CREATE POLICY "Allow public read from uploads bucket"
  ON storage.objects FOR SELECT TO public
  USING (bucket_id = 'uploads');
CREATE POLICY "Allow public update in uploads bucket"
  ON storage.objects FOR UPDATE TO public
  USING (bucket_id = 'uploads');
```

### Fix invited_at default (migration 005)
The original schema had `invited_at TIMESTAMP WITH TIME ZONE DEFAULT now()` on `team_members`,
which meant every newly added member appeared as "already invited" before any email was sent.
This broke the "Send Invitations" button (always disabled) and caused reminder emails
to go out instead of invitations.
```sql
ALTER TABLE team_members ALTER COLUMN invited_at DROP DEFAULT;
```

## Queries

### Get all submissions for an event
```sql
SELECT 
    s.message,
    s.file_url,
    s.created_at,
    tm.name AS submitter_name,
    tm.email AS submitter_email
FROM submissions s
JOIN team_members tm ON s.team_member_id = tm.id
WHERE s.event_id = '{event_id}'
ORDER BY s.created_at;
```

### Get team members who haven't submitted
```sql
SELECT tm.* 
FROM team_members tm
LEFT JOIN submissions s ON tm.id = s.team_member_id
WHERE tm.event_id = '{event_id}'
AND s.id IS NULL;
```

### Get event by access code
```sql
SELECT * FROM farewell_events 
WHERE access_code = '{code}';
```
