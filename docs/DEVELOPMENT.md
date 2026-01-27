# Development Guide

## Prerequisites

- Python 3.8+
- pip3
- A Supabase account (already configured)
- Google account (for email/Drive features)

## Local Setup

### 1. Clone and Install

```bash
cd /Users/hannahkl/Documents/GitHub/farewellify
pip3 install -r requirements.txt
```

### 2. Environment Variables

The `.env` file should contain:

```bash
# Supabase (already configured)
SUPABASE_URL=https://datpxrveaizpigltowju.supabase.co
SUPABASE_KEY=your-key-here

# Flask secret (for OAuth sessions)
FLASK_SECRET_KEY=any-random-string-here

# SMTP fallback (optional, Gmail OAuth preferred)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
```

### 3. Run the App

```bash
python3 app.py
```

App runs at http://localhost:5001

## Project Structure

```
farewellify/
├── app.py                 # Main Flask app - all routes here
├── gmail_auth.py          # Google OAuth logic
├── requirements.txt       # Dependencies
├── .env                   # Secrets (gitignored)
├── .env.example           # Template
├── gmail_credentials.json # Google OAuth client (gitignored)
├── gmail_token.json       # OAuth tokens (gitignored, auto-created)
├── uploads/               # Uploaded files (auto-created)
├── templates/
│   ├── index.html         # Create event form
│   ├── admin.html         # Admin dashboard
│   └── submit.html        # Team submission form
├── docs/                  # Documentation
└── .cursor/rules/         # AI agent instructions
```

## Making Changes

### Backend (app.py)

The Flask app is a single file. Key sections:

1. **Configuration** (lines 1-50) - Imports, env vars, constants
2. **Email functions** (lines 50-90) - SMTP and Gmail sending
3. **Gmail OAuth routes** (lines 90-170) - Connect/disconnect/callback
4. **Page routes** (lines 170-210) - HTML page serving
5. **API routes** (lines 210-500) - REST endpoints

### Frontend (templates/)

Templates use:
- **Tailwind CSS** via CDN
- **Font Awesome** for icons
- Vanilla JavaScript (no framework)

Pandata colors are defined in Tailwind config in each template:

```javascript
tailwind.config = {
    theme: {
        extend: {
            colors: {
                'pandata-red': '#fa4f4f',
                'pandata-charcoal': '#434343',
                'pandata-gray': '#595959',
                'pandata-gray-light': '#eeeeee'
            }
        }
    }
}
```

### Adding a New API Endpoint

```python
@app.route('/api/new-endpoint', methods=['POST'])
def new_endpoint():
    if not supabase:
        return jsonify({'error': 'Database not configured'}), 500
    
    data = request.json
    # Do something...
    
    return jsonify({'success': True})
```

### Adding a New Page

1. Create `templates/newpage.html`
2. Add route in `app.py`:
   ```python
   @app.route('/newpage')
   def newpage():
       return render_template('newpage.html')
   ```

## Database Operations

### Using Supabase in Python

```python
# Query
result = supabase.table('employees').select('*').eq('is_active', True).execute()
employees = result.data

# Insert
supabase.table('submissions').insert({
    'event_id': event_id,
    'message': 'Hello!'
}).execute()

# Update
supabase.table('team_members').update({
    'invited_at': datetime.utcnow().isoformat()
}).eq('id', member_id).execute()

# Delete
supabase.table('employees').delete().eq('email', 'test@test.com').execute()
```

### Common Patterns

**Get single record** (use `.limit(1)` not `.single()`):
```python
result = supabase.table('farewell_events').select('*').eq('id', event_id).limit(1).execute()
if not result.data:
    return jsonify({'error': 'Not found'}), 404
event = result.data[0]
```

**Filter by exclusion**:
```python
# In Python (not SQL)
excluded = ['julian@pandata.de', 'hannah@pandata.de']
employees = [e for e in result.data if e['email'] not in excluded]
```

## Testing

### Manual Testing Checklist

1. **Create Event**
   - [ ] Fill all fields
   - [ ] Enter honoree email → check they're excluded from list
   - [ ] Submit → get admin URL and submit URL

2. **Admin Dashboard**
   - [ ] Open admin URL
   - [ ] Check stats show correct numbers
   - [ ] Click "Send Invitations" (if Gmail connected)
   - [ ] Click "Send Reminders"

3. **Submit Message**
   - [ ] Open submit URL with `?email=xxx`
   - [ ] Check email is pre-filled
   - [ ] Submit text message
   - [ ] Submit with file upload
   - [ ] Check admin dashboard shows submission

4. **Google Integration**
   - [ ] Connect Gmail
   - [ ] Create event → check Drive folder created
   - [ ] Send invitation → check email received
   - [ ] Disconnect → check status updates

### API Testing with curl

```bash
# Create event
curl -X POST http://localhost:5001/api/events \
  -H "Content-Type: application/json" \
  -d '{
    "honoreeName": "Test Person",
    "organizerName": "Tester",
    "organizerEmail": "test@test.com",
    "deadline": "2026-02-01",
    "teamMembers": []
  }'

# Get employees
curl "http://localhost:5001/api/employees?exclude=julian@pandata.de"

# Check Gmail status
curl http://localhost:5001/api/gmail/status
```

## Common Issues

### "Database not configured"

Check `.env` has correct `SUPABASE_URL` and `SUPABASE_KEY`.

### ".single() errors"

Don't use `.single()` - it causes Pydantic errors when no results. Use:
```python
.limit(1).execute()
# Then check: if not result.data: ...
```

### CORS errors

The app doesn't set CORS headers. If calling from a different domain, add:
```python
from flask_cors import CORS
CORS(app)
```

### File upload fails

Check:
- File is under 50MB
- File type is PDF, JPG, or PNG
- `uploads/` directory exists (auto-created)

## Deployment

The app is designed for local use. For production:

1. Use a proper WSGI server (gunicorn, uwsgi)
2. Set `debug=False` in `app.run()`
3. Use environment variables for all secrets
4. Add proper HTTPS
5. Consider cloud file storage instead of local `uploads/`
6. Add authentication for admin routes

## Useful Commands

```bash
# Run app
python3 app.py

# Install new dependency
pip3 install package-name
pip3 freeze > requirements.txt

# Check running processes on port 5001
lsof -i :5001

# Kill process on port 5001
kill $(lsof -t -i:5001)
```
