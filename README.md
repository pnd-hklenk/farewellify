# Farewellify 🎉

A web app for organizing farewell cards at Pandata. Collect messages from the team, track submissions, send reminders, and store everything in Google Drive.

## Quick Links

| What | URL |
|------|-----|
| **Create Event** | http://localhost:5001/ |
| **Admin Dashboard** | http://localhost:5001/admin/{access_code} |
| **Submit Message** | http://localhost:5001/submit/{event_id}?email={email} |

## Features

- ✅ **Employee List** - All Pandata employees pre-loaded, auto-excludes honoree
- ✅ **Personalized Links** - Each team member gets their own link (no login required)
- ✅ **Gmail Integration** - Send invitations and reminders directly from the app
- ✅ **Google Drive** - Auto-creates folders in format `YYMM FirstName` (e.g., "2601 Julian")
- ✅ **File Uploads** - Team members can upload PDFs, images, or type messages
- ✅ **Pandata Branding** - Corporate design (colors, fonts) applied

## Getting Started

### 1. Install dependencies

```bash
pip3 install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your credentials (Supabase is pre-configured)
```

### 3. Run the app

```bash
python3 app.py
```

Open http://localhost:5001

### 4. Configure Email (recommended)

Add your SMTP credentials to `.env`:

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=no-reply@pandata.de
```

For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833) (not your regular password).

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/ARCHITECTURE.md) | System overview, components, data flow |
| [Database](docs/DATABASE.md) | Tables, schemas, Supabase setup |
| [API Reference](docs/API.md) | All REST endpoints |
| [Email Setup](docs/EMAIL_SETUP.md) | SMTP email configuration |
| [Google Drive](docs/GOOGLE_INTEGRATION.md) | Drive OAuth for auto-folders (optional) |
| [Development](docs/DEVELOPMENT.md) | Local development guide |
| [Changelog](docs/CHANGELOG.md) | Version history and changes |

## Project Structure

```
farewellify/
├── app.py                 # Flask application (main entry point)
├── gmail_auth.py          # Google OAuth (Gmail + Drive)
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (secrets)
├── .env.example           # Template for .env
├── templates/
│   ├── index.html         # Create event form
│   ├── admin.html         # Admin dashboard
│   └── submit.html        # Team member submission form
├── assets/
│   └── farewellify-logo.png  # App logo (displayed on all pages)
├── docs/
│   ├── ARCHITECTURE.md    # System architecture
│   ├── DATABASE.md        # Database schema
│   ├── API.md             # API documentation
│   ├── GOOGLE_INTEGRATION.md
│   └── DEVELOPMENT.md
├── uploads/               # Uploaded files (created automatically)
└── .cursor/rules/         # AI agent instructions
```

## Tech Stack

- **Backend**: Python Flask
- **Database**: Supabase (PostgreSQL)
- **Frontend**: HTML + Tailwind CSS
- **Email**: SMTP (Gmail or any SMTP provider)
- **Storage**: Google Drive API (optional) + local uploads

## Key Concepts

### Personalized Links
Each team member gets a unique link like:
```
http://localhost:5001/submit/{event_id}?email=adam.butz@pandata.de
```
No login required - the email parameter identifies them.

### Honoree Protection
The person leaving (honoree) is **always excluded** from:
- The employee selection list
- The team members list
- All email communications

This ensures the farewell card stays a surprise.

### Auto-Folders
When an event is created with Google Drive connected, a folder is automatically created:
- **Location**: Pandata farewell cards folder
- **Format**: `YYMM FirstName` (e.g., "2601 Julian" for January 2026)
