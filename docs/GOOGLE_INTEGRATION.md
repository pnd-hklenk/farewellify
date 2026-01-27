# Google Integration

Farewellify uses Google OAuth 2.0 for:
1. **Gmail API** - Sending invitation and reminder emails
2. **Drive API** - Auto-creating folders for each event

## Setup Steps

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Name it (e.g., "Farewellify")
4. Click "Create"

### 2. Enable APIs

1. Go to **APIs & Services** → **Library**
2. Search and enable:
   - **Gmail API**
   - **Google Drive API**

### 3. Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Select **External** (unless you have Google Workspace)
3. Fill in:
   - App name: `Farewellify`
   - User support email: your email
   - Developer contact: your email
4. Click **Save and Continue**
5. On Scopes page, click **Add or Remove Scopes**
6. Add these scopes:
   - `https://www.googleapis.com/auth/gmail.send`
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/drive.file`
7. Click **Save and Continue**
8. Add test users (your email) if in testing mode
9. Click **Save and Continue**

### 4. Create OAuth Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Select **Web application**
4. Name: `Farewellify Web Client`
5. **Authorized redirect URIs**: Add
   ```
   http://localhost:5001/api/gmail/callback
   ```
6. Click **Create**
7. Click **Download JSON**
8. Save as `gmail_credentials.json` in the project root

### 5. Connect in App

1. Start the app: `python3 app.py`
2. Go to any admin dashboard or create an event
3. Click **Connect Gmail**
4. Authorize with your Google account
5. Done! The app can now send emails and create Drive folders.

## File Structure

```
farewellify/
├── gmail_credentials.json    # OAuth client config (download from Google)
├── gmail_token.json          # Access/refresh tokens (auto-created)
└── gmail_auth.py             # OAuth logic
```

**Important**: Both `.json` files should be in `.gitignore` (they contain secrets).

## How It Works

### OAuth Flow

```
1. User clicks "Connect Gmail"
         │
         ▼
2. GET /api/gmail/connect
   → Returns Google auth URL
         │
         ▼
3. User is redirected to Google
   → Sees consent screen
   → Clicks "Allow"
         │
         ▼
4. Google redirects to /api/gmail/callback?code=xxx
         │
         ▼
5. App exchanges code for tokens
   → Saves to gmail_token.json
         │
         ▼
6. Done! App can now use Gmail & Drive APIs
```

### Token Refresh

- Access tokens expire after ~1 hour
- Refresh tokens are long-lived
- `gmail_auth.py` automatically refreshes expired tokens
- If refresh fails, user must re-authorize

## API Usage

### Sending Emails

```python
from gmail_auth import send_email_via_gmail, is_gmail_connected

if is_gmail_connected():
    send_email_via_gmail(
        to_email="team@pandata.de",
        subject="Farewell Card for Julian",
        html_content="<h1>Hello!</h1><p>Please submit your message...</p>"
    )
```

### Creating Drive Folders

```python
from gmail_auth import create_farewell_folder, is_drive_connected

if is_drive_connected():
    result = create_farewell_folder(
        honoree_first_name="Julian",
        event_date="2026-01-30"
    )
    # Returns: { 'folder_id': '...', 'folder_url': 'https://...' }
```

### Folder Naming

Format: `YYMM Vorname`

Examples:
- January 2026, Julian → `2601 Julian`
- March 2026, Sarah → `2603 Sarah`

### Parent Folder

All folders are created inside:
```
https://drive.google.com/drive/folders/1r0vtpUvIrJdpKiBDmA6MbH9EQ81c0HlM
```

This is configured in `gmail_auth.py`:
```python
FAREWELL_CARDS_FOLDER_ID = '1r0vtpUvIrJdpKiBDmA6MbH9EQ81c0HlM'
```

## Scopes

The app requests these OAuth scopes:

| Scope | Purpose |
|-------|---------|
| `gmail.send` | Send emails |
| `gmail.readonly` | Get user's email address |
| `drive.file` | Create/access files in Drive |

## Troubleshooting

### "Gmail not configured"

Missing `gmail_credentials.json`. Download from Google Cloud Console.

### "Access token expired"

Usually auto-refreshes. If not:
1. Delete `gmail_token.json`
2. Re-connect via the app

### "Insufficient permissions"

The OAuth consent might not have the right scopes:
1. Delete `gmail_token.json`
2. In Google Cloud Console, add missing scopes
3. Re-connect

### "Error 403: access_denied"

If using External user type:
1. Add your email to test users in OAuth consent screen
2. Or publish the app (requires verification for sensitive scopes)

### Folder not created

1. Check if Drive API is enabled
2. Check if `drive.file` scope was granted
3. Check if parent folder ID is correct
4. Check console for error messages

## Security Notes

### Credentials File

`gmail_credentials.json` contains:
- Client ID
- Client secret
- Redirect URIs

This file identifies your app to Google. Keep it private but it's not as sensitive as the token file.

### Token File

`gmail_token.json` contains:
- Access token (expires in ~1 hour)
- Refresh token (long-lived)

**This is the sensitive file!** With this, anyone can:
- Send emails as your account
- Access your Drive files (within scope)

### Revoking Access

To completely revoke Farewellify's access:

1. Go to https://myaccount.google.com/permissions
2. Find "Farewellify"
3. Click "Remove Access"
4. Delete local `gmail_token.json`

## Production Considerations

For deployment beyond localhost:

1. Add production redirect URI:
   ```
   https://your-domain.com/api/gmail/callback
   ```

2. Consider publishing OAuth consent screen (required for >100 users)

3. Store tokens securely (not in plaintext file)

4. Set proper CORS and security headers
