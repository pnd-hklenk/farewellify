"""
Farewellify - A simple app to organize farewell cards for colleagues
"""
import os
import uuid
import smtplib
import zipfile
import io
import json
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone
from urllib.parse import quote
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory, session, send_file
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

# Google Drive for folder creation (optional)
try:
    from gmail_auth import create_farewell_folder, is_drive_connected
    DRIVE_AVAILABLE = True
except ImportError:
    DRIVE_AVAILABLE = False

load_dotenv()

# Miro API configuration (after load_dotenv to read from .env file)
MIRO_ACCESS_TOKEN = os.getenv('MIRO_ACCESS_TOKEN', '')
MIRO_TEAM_ID = os.getenv('MIRO_TEAM_ID', '')
MIRO_API_BASE = 'https://api.miro.com/v2'

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', os.urandom(24).hex())
CORS(app)

# File upload configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Error handler for file too large
@app.errorhandler(413)
@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    return jsonify({
        'success': False,
        'error': f'File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)}MB.'
    }), 413

# Generic error handler to ensure API errors return JSON, not HTML
@app.errorhandler(500)
def handle_internal_error(e):
    return jsonify({
        'success': False,
        'error': 'Internal server error. Please try again or contact support.'
    }), 500

@app.errorhandler(Exception)
def handle_exception(e):
    # Pass through HTTP errors that already have handlers
    if hasattr(e, 'code') and e.code in [413]:
        raise e
    # Return JSON for any other unhandled exceptions
    app.logger.error(f'Unhandled exception: {str(e)}')
    return jsonify({
        'success': False,
        'error': 'An unexpected error occurred. Please try again.'
    }), 500

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://datpxrveaizpigltowju.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')
SUPABASE_STORAGE_BUCKET = os.getenv('SUPABASE_STORAGE_BUCKET', 'uploads')

# Initialize Supabase client with explicit options to avoid schema cache issues
supabase: Client = None
if SUPABASE_KEY:
    from supabase.client import ClientOptions
    supabase = create_client(
        SUPABASE_URL, 
        SUPABASE_KEY,
        options=ClientOptions(schema='public')
    )


def upload_to_supabase_storage(file_data: bytes, filename: str) -> str:
    """Upload a file to Supabase Storage and return the public URL"""
    if not supabase:
        raise Exception('Supabase not configured')
    
    # Determine content type
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    content_types = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'pdf': 'application/pdf',
        'gif': 'image/gif'
    }
    content_type = content_types.get(ext, 'application/octet-stream')
    
    # Upload to Supabase Storage
    try:
        result = supabase.storage.from_(SUPABASE_STORAGE_BUCKET).upload(
            filename,
            file_data,
            file_options={"content-type": content_type}
        )
        
        # Get public URL
        public_url = supabase.storage.from_(SUPABASE_STORAGE_BUCKET).get_public_url(filename)
        return public_url
    except Exception as e:
        app.logger.error(f'Supabase storage upload error: {str(e)}')
        raise

# SMTP Email configuration
SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
EMAIL_FROM = os.getenv('EMAIL_FROM', 'no-reply@pandata.de')


def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """Send an email via SMTP"""
    
    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"Email not configured. Would send to {to_email}: {subject}")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_FROM
        msg['To'] = to_email
        
        # Attach HTML content
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Send email via SMTP
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(EMAIL_FROM, to_email, msg.as_string())
        
        print(f"Email sent to {to_email}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


# Email status route
@app.route('/api/email/status')
def email_status():
    """Check email configuration status"""
    email_configured = bool(SMTP_USER and SMTP_PASSWORD)
    drive_configured = DRIVE_AVAILABLE and is_drive_connected() if DRIVE_AVAILABLE else False
    
    return jsonify({
        'emailConfigured': email_configured,
        'emailProvider': 'SMTP' if email_configured else None,
        'emailFrom': EMAIL_FROM if email_configured else None,
        'driveConfigured': drive_configured
    })


@app.route('/')
def index():
    """Home page - create a new farewell event"""
    return render_template('index.html')


@app.route('/api/events', methods=['POST'])
def create_event():
    """Create a new farewell event"""
    if not supabase:
        return jsonify({'error': 'Database not configured'}), 500
    
    data = request.json
    honoree_name = data['honoreeName']
    
    # Auto-create Google Drive folder (YYMM Vorname format)
    drive_folder_url = None
    if DRIVE_AVAILABLE and is_drive_connected():
        # Extract first name for folder naming
        first_name = honoree_name.split()[0] if ' ' in honoree_name else honoree_name
        folder_result = create_farewell_folder(first_name, data.get('deadline'))
        if folder_result:
            drive_folder_url = folder_result['folder_url']
            print(f"Created Drive folder: {drive_folder_url}")
    
    # Create the event
    event_data = {
        'honoree_name': honoree_name,
        'honoree_email': data.get('honoreeEmail'),
        'organizer_name': data['organizerName'],
        'organizer_email': data['organizerEmail'],
        'deadline': data['deadline'],
        'message': data.get('message', ''),
        'google_drive_folder_url': drive_folder_url
    }
    
    result = supabase.table('farewell_events').insert(event_data).execute()
    event = result.data[0]

    # Mark honoree as inactive — they're leaving, remove from future events & notifications
    honoree_email = data.get('honoreeEmail', '').lower()
    if honoree_email:
        supabase.table('employees').update({'is_active': False}).eq('email', honoree_email).execute()

    # Add team members (NEVER include the honoree!)
    team_members = data.get('teamMembers', [])
    
    for member in team_members:
        # Double-check: never add the honoree as a team member
        if member['email'].lower() == honoree_email:  # honoree_email defined above
            continue
            
        member_data = {
            'event_id': event['id'],
            'name': member['name'],
            'email': member['email']
        }
        supabase.table('team_members').insert(member_data).execute()
    
    return jsonify({
        'success': True,
        'event': event,
        'adminUrl': f"/admin/{event['access_code']}",
        'submitUrl': f"/submit/{event['id']}",
        'driveFolderUrl': drive_folder_url
    })


@app.route('/api/events/<event_id>/send-invitations', methods=['POST'])
def send_invitations(event_id):
    """Send invitation emails to all team members"""
    if not supabase:
        return jsonify({'error': 'Database not configured'}), 500
    
    # Get event details
    event = supabase.table('farewell_events').select('*').eq('id', event_id).limit(1).execute()
    if not event.data or len(event.data) == 0:
        return jsonify({'error': 'Event not found'}), 404
    
    event_data = event.data[0]
    
    # Get team members
    members = supabase.table('team_members').select('*').eq('event_id', event_id).execute()
    
    base_url = request.host_url.rstrip('/')
    submit_url = f"{base_url}/submit/{event_id}"

    # Skip members who are inactive (have already left the company)
    inactive = supabase.table('employees').select('email').eq('is_active', False).execute()
    inactive_emails = {e['email'].lower() for e in inactive.data}

    sent_count = 0
    honoree_first_name = event_data['honoree_name'].split()[0]

    # Format deadline as "Thursday, 29.01."
    deadline_date = datetime.fromisoformat(event_data['deadline'].replace('Z', '+00:00'))
    weekdays_en = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    formatted_deadline = f"{weekdays_en[deadline_date.weekday()]}, {deadline_date.strftime('%d.%m.')}"

    for member in members.data:
        if member['email'].lower() in inactive_emails:
            continue
        # Create personalized link for this team member
        personal_link = f"{submit_url}?email={quote(member['email'])}"
        member_first_name = member['name'].split()[0]

        subject = f"Farewell Card for {honoree_first_name} 🎉"
        html_content = f"""
        <html>
        <body style="font-family: 'Open Sans', Arial, sans-serif; margin: 0; padding: 20px; background-color: #eeeeee;">
            <table width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                    <td align="center">
                        <table width="600" cellpadding="0" cellspacing="0" border="0" style="background-color: white; border-radius: 8px; border-top: 4px solid #fa4f4f;">
                            <tr>
                                <td align="left" style="padding: 30px;">
                                    <h2 style="color: #434343; margin-top: 0; margin-bottom: 20px;">Farewell Card for {honoree_first_name}</h2>
                                    <p style="color: #434343; margin: 0 0 15px 0;">Hi {member_first_name},</p>
                                    <p style="color: #434343; margin: 0 0 15px 0;">It is <strong>{honoree_first_name}'s</strong> last day on <strong>{formatted_deadline}</strong>, and so we would like you to contribute to their farewell card.</p>
                                    <p style="color: #434343; margin: 0 0 25px 0;">Please upload or draft your message via our new farewell app:</p>
                                    <table cellpadding="0" cellspacing="0" border="0">
                                        <tr>
                                            <td align="left" style="padding: 10px 0 25px 0;">
                                                <a href="{personal_link}" style="background-color: #fa4f4f; color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">Add Your Message</a>
                                            </td>
                                        </tr>
                                    </table>
                                    <hr style="border: none; border-top: 1px solid #eeeeee; margin: 20px 0;">
                                    <p style="color: #999999; font-size: 12px; margin: 0;">
                                        This is your personalized link – no login required!<br>
                                        Organized by {event_data['organizer_name'].split()[0]}
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        if send_email(member['email'], subject, html_content):
            sent_count += 1
            # Update invited_at timestamp
            supabase.table('team_members').update({'invited_at': datetime.now(timezone.utc).isoformat()}).eq('id', member['id']).execute()
    
    skipped = sum(1 for m in members.data if m['email'].lower() in inactive_emails)
    return jsonify({
        'success': True,
        'sentCount': sent_count,
        'totalMembers': len(members.data),
        'skippedInactive': skipped,
    })


@app.route('/api/events/<event_id>/send-reminders', methods=['POST'])
def send_reminders(event_id):
    """Send reminder emails to team members who haven't submitted"""
    if not supabase:
        return jsonify({'error': 'Database not configured'}), 500
    
    # Get event details
    event = supabase.table('farewell_events').select('*').eq('id', event_id).limit(1).execute()
    if not event.data or len(event.data) == 0:
        return jsonify({'error': 'Event not found'}), 404
    
    event_data = event.data[0]
    
    # Get team members who haven't submitted
    members = supabase.table('team_members').select('*').eq('event_id', event_id).execute()
    submissions = supabase.table('submissions').select('team_member_id').eq('event_id', event_id).execute()
    
    submitted_ids = {s['team_member_id'] for s in submissions.data}
    pending_members = [m for m in members.data if m['id'] not in submitted_ids]
    
    base_url = request.host_url.rstrip('/')
    submit_url = f"{base_url}/submit/{event_id}"

    # Skip members who are inactive (have already left the company)
    inactive = supabase.table('employees').select('email').eq('is_active', False).execute()
    inactive_emails = {e['email'].lower() for e in inactive.data}
    pending_members = [m for m in pending_members if m['email'].lower() not in inactive_emails]

    sent_count = 0
    honoree_first_name = event_data['honoree_name'].split()[0]

    # Format deadline as "Thursday, 29.01."
    deadline_date = datetime.fromisoformat(event_data['deadline'].replace('Z', '+00:00'))
    weekdays_en = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    formatted_deadline = f"{weekdays_en[deadline_date.weekday()]}, {deadline_date.strftime('%d.%m.')}"

    for member in pending_members:
        personal_link = f"{submit_url}?email={quote(member['email'])}"
        member_first_name = member['name'].split()[0]
        
        subject = f"Reminder: Farewell Card for {honoree_first_name} ⏰"
        html_content = f"""
        <html>
        <body style="font-family: 'Open Sans', Arial, sans-serif; margin: 0; padding: 20px; background-color: #eeeeee;">
            <table width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                    <td align="center">
                        <table width="600" cellpadding="0" cellspacing="0" border="0" style="background-color: white; border-radius: 8px; border-top: 4px solid #434343;">
                            <tr>
                                <td align="left" style="padding: 30px;">
                                    <h2 style="color: #434343; margin-top: 0; margin-bottom: 20px;">⏰ Friendly Reminder!</h2>
                                    <p style="color: #434343; margin: 0 0 15px 0;">Hi {member_first_name},</p>
                                    <p style="color: #434343; margin: 0 0 15px 0;">Just a friendly reminder: <strong>{honoree_first_name}'s</strong> last day is on <strong>{formatted_deadline}</strong>, and we haven't received your contribution to their farewell card yet.</p>
                                    <p style="color: #434343; margin: 0 0 25px 0;">Please upload or draft your message via our farewell app:</p>
                                    <table cellpadding="0" cellspacing="0" border="0">
                                        <tr>
                                            <td align="left" style="padding: 10px 0 25px 0;">
                                                <a href="{personal_link}" style="background-color: #fa4f4f; color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">Add Your Message Now</a>
                                            </td>
                                        </tr>
                                    </table>
                                    <hr style="border: none; border-top: 1px solid #eeeeee; margin: 20px 0;">
                                    <p style="color: #999999; font-size: 12px; margin: 0;">
                                        This is your personalized link – no login required!
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        if send_email(member['email'], subject, html_content):
            sent_count += 1
            # Update reminder_sent_at timestamp
            supabase.table('team_members').update({'reminder_sent_at': datetime.now(timezone.utc).isoformat()}).eq('id', member['id']).execute()
    
    return jsonify({
        'success': True,
        'sentCount': sent_count,
        'pendingMembers': len(pending_members)
    })


@app.route('/submit/<event_id>')
def submit_page(event_id):
    """Page for team members to submit their messages"""
    return render_template('submit.html', event_id=event_id)


@app.route('/api/events/<event_id>')
def get_event(event_id):
    """Get event details (public info only) + team member info and existing submission if email provided"""
    if not supabase:
        return jsonify({'error': 'Database not configured'}), 500
    
    event = supabase.table('farewell_events').select('id, honoree_name, deadline, message, google_drive_folder_url').eq('id', event_id).limit(1).execute()
    if not event.data or len(event.data) == 0:
        return jsonify({'error': 'Event not found'}), 404
    
    result = event.data[0]
    
    # If email parameter provided, look up the team member's name and existing submission
    email = request.args.get('email')
    if email:
        member = supabase.table('team_members').select('id, name, email').eq('event_id', event_id).eq('email', email).limit(1).execute()
        if member.data and len(member.data) > 0:
            result['team_member_name'] = member.data[0]['name']
            result['team_member_email'] = member.data[0]['email']
            
            # Check for existing submission
            submission = supabase.table('submissions').select('*').eq('event_id', event_id).eq('team_member_id', member.data[0]['id']).limit(1).execute()
            if submission.data and len(submission.data) > 0:
                result['existing_submission'] = {
                    'message': submission.data[0].get('message'),
                    'file_url': submission.data[0].get('file_url'),
                    'photo_urls': submission.data[0].get('photo_urls'),  # New field for multiple photos
                    'submitted_at': submission.data[0].get('submitted_at')
                }
    
    return jsonify(result)


@app.route('/api/submissions', methods=['POST'])
def create_submission():
    """Submit a message for a farewell event"""
    if not supabase:
        return jsonify({'error': 'Database not configured'}), 500
    
    try:
        event_id = request.form.get('eventId')
        email = request.form.get('email')
        name = request.form.get('name')
        message = request.form.get('message')
        existing_photos = request.form.get('existingPhotos')  # JSON array of existing photo URLs to keep
        
        if not event_id or not email:
            return jsonify({'error': 'Missing required fields (eventId or email)'}), 400
        
        # Handle file uploads
        file_url = None
        photo_urls = []
        
        # Keep existing photos if specified
        if existing_photos:
            try:
                photo_urls = json.loads(existing_photos)
            except:
                photo_urls = []
        
        # Handle handwritten note (messageFile) - this becomes file_url
        if 'messageFile' in request.files:
            msg_file = request.files['messageFile']
            if msg_file and msg_file.filename and allowed_file(msg_file.filename):
                ext = msg_file.filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{event_id}_msg_{uuid.uuid4().hex[:8]}.{ext}"
                # Upload to Supabase Storage
                file_data = msg_file.read()
                file_url = upload_to_supabase_storage(file_data, unique_filename)
        
        # Handle multiple photo files (up to 15)
        photo_files = request.files.getlist('photos')
        for photo in photo_files[:15]:  # Limit to 15 photos
            if photo and photo.filename and allowed_file(photo.filename):
                ext = photo.filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{event_id}_photo_{uuid.uuid4().hex[:8]}.{ext}"
                # Upload to Supabase Storage
                file_data = photo.read()
                photo_url = upload_to_supabase_storage(file_data, unique_filename)
                photo_urls.append(photo_url)
        
        # Legacy: Handle single 'file' upload (for backwards compatibility)
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{event_id}_{uuid.uuid4().hex[:8]}.{ext}"
                # Upload to Supabase Storage
                file_data = file.read()
                photo_url = upload_to_supabase_storage(file_data, unique_filename)
                photo_urls.append(photo_url)
        
        # Find the team member
        member = supabase.table('team_members').select('*').eq('event_id', event_id).eq('email', email).limit(1).execute()
        
        if not member.data or len(member.data) == 0:
            # Create a new team member if they weren't pre-registered
            new_member = {
                'event_id': event_id,
                'name': name or email.split('@')[0],
                'email': email
            }
            member = supabase.table('team_members').insert(new_member).execute()
            member_id = member.data[0]['id']
        else:
            member_id = member.data[0]['id']
        
        # Check if already submitted
        existing = supabase.table('submissions').select('*').eq('event_id', event_id).eq('team_member_id', member_id).execute()
        
        # Build submission data - start without photo_urls to ensure basic submission works
        submission_data = {
            'event_id': event_id,
            'team_member_id': member_id,
            'message': message if message else None,
            'file_url': file_url
        }
        
        # Keep old file_url if no new one uploaded
        if existing.data and not file_url and existing.data[0].get('file_url'):
            submission_data['file_url'] = existing.data[0]['file_url']
        
        # Try to save with photo_urls first
        if photo_urls:
            submission_data['photo_urls'] = json.dumps(photo_urls)
        
        try:
            if existing.data:
                supabase.table('submissions').update(submission_data).eq('id', existing.data[0]['id']).execute()
            else:
                supabase.table('submissions').insert(submission_data).execute()
            
            return jsonify({'success': True})
        except Exception as db_error:
            error_msg = str(db_error)
            print(f"Database error (with photo_urls): {error_msg}")
            
            # If photo_urls column doesn't exist, try without it
            if 'photo_urls' in error_msg or 'column' in error_msg.lower():
                if 'photo_urls' in submission_data:
                    del submission_data['photo_urls']
                try:
                    if existing.data:
                        supabase.table('submissions').update(submission_data).eq('id', existing.data[0]['id']).execute()
                    else:
                        supabase.table('submissions').insert(submission_data).execute()
                    return jsonify({
                        'success': True, 
                        'warning': 'Photos not saved - photo_urls column missing in database'
                    })
                except Exception as e2:
                    print(f"Database error (without photo_urls): {str(e2)}")
                    return jsonify({'success': False, 'error': f'Database error: {str(e2)}'}), 500
            
            return jsonify({'success': False, 'error': f'Database error: {error_msg}'}), 500
            
    except Exception as e:
        print(f"Submission error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500


@app.route('/uploads/<filename>')
def serve_upload(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/assets/<filename>')
def serve_assets(filename):
    """Serve static assets (logo, icons, etc.)"""
    assets_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
    return send_from_directory(assets_folder, filename)


@app.route('/api/employees')
def get_employees():
    """Get all active employees, optionally excluding specific emails"""
    if not supabase:
        return jsonify({'error': 'Database not configured'}), 500
    
    # Get emails to exclude (honoree and organizer)
    exclude_emails = request.args.getlist('exclude')
    
    employees = supabase.table('employees').select('name, email').eq('is_active', True).order('name').execute()
    
    # Filter out excluded emails
    if exclude_emails:
        employees_data = [e for e in employees.data if e['email'] not in exclude_emails]
    else:
        employees_data = employees.data
    
    return jsonify(employees_data)


@app.route('/admin/<access_code>')
def admin_page(access_code):
    """Admin dashboard for the organizer"""
    return render_template('admin.html', access_code=access_code)


@app.route('/api/admin/<access_code>')
def get_admin_data(access_code):
    """Get admin dashboard data"""
    if not supabase:
        return jsonify({'error': 'Database not configured'}), 500
    
    # Get event by access code
    event = supabase.table('farewell_events').select('*').eq('access_code', access_code).limit(1).execute()
    if not event.data or len(event.data) == 0:
        return jsonify({'error': 'Event not found'}), 404
    
    event_data = event.data[0]
    event_id = event_data['id']
    
    # Get team members
    members = supabase.table('team_members').select('*').eq('event_id', event_id).execute()
    
    # Get submissions
    submissions = supabase.table('submissions').select('*').eq('event_id', event_id).execute()
    
    submitted_ids = {s['team_member_id']: s for s in submissions.data}
    
    # Build member list with submission status
    member_list = []
    for member in members.data:
        submission = submitted_ids.get(member['id'])
        # Parse photo_urls JSON if present
        photo_urls = []
        if submission and submission.get('photo_urls'):
            try:
                photo_urls = json.loads(submission['photo_urls'])
            except:
                pass
        
        member_list.append({
            'id': member['id'],
            'name': member['name'],
            'email': member['email'],
            'invitedAt': member['invited_at'],
            'reminderSentAt': member['reminder_sent_at'],
            'hasSubmitted': member['id'] in submitted_ids,
            'submittedAt': submission['submitted_at'] if submission else None,
            'message': submission['message'] if submission else None,
            'fileUrl': submission['file_url'] if submission else None,
            'photoUrls': photo_urls,
            'submissionId': submission['id'] if submission else None,
            'miroAdded': submission.get('miro_added', False) if submission else False,
        })
    
    # Calculate detailed stats
    submitted_count = len(submissions.data)
    invited_count = sum(1 for m in members.data if m['invited_at'] and m['id'] not in submitted_ids)
    not_invited_count = sum(1 for m in members.data if not m['invited_at'] and m['id'] not in submitted_ids)
    
    return jsonify({
        'event': {
            'id': event_data['id'],
            'honoreeName': event_data['honoree_name'],
            'honoreeEmail': event_data['honoree_email'],
            'organizerName': event_data['organizer_name'],
            'organizerEmail': event_data['organizer_email'],
            'deadline': event_data['deadline'],
            'message': event_data['message'],
            'googleDriveFolderUrl': event_data['google_drive_folder_url'],
            'createdAt': event_data['created_at']
        },
        'members': member_list,
        'stats': {
            'total': len(members.data),
            'submitted': submitted_count,
            'invited': invited_count,
            'notInvited': not_invited_count
        }
    })


@app.route('/api/admin/<access_code>/submissions/<submission_id>/miro-added', methods=['PATCH'])
def toggle_miro_added(access_code, submission_id):
    """Toggle the miro_added flag on a submission"""
    if not supabase:
        return jsonify({'error': 'Database not configured'}), 500

    event = supabase.table('farewell_events').select('id').eq('access_code', access_code).limit(1).execute()
    if not event.data:
        return jsonify({'error': 'Event not found'}), 404

    event_id = event.data[0]['id']
    data = request.get_json() or {}
    miro_added = data.get('miroAdded', False)

    # Scope the update to this event to prevent cross-event tampering
    result = supabase.table('submissions').update({'miro_added': miro_added}).eq('id', submission_id).eq('event_id', event_id).execute()
    if not result.data:
        return jsonify({'error': 'Submission not found'}), 404

    return jsonify({'success': True, 'miroAdded': miro_added})


@app.route('/api/admin/<access_code>/add-member', methods=['POST'])
def add_team_member(access_code):
    """Add a new team member to the event"""
    if not supabase:
        return jsonify({'error': 'Database not configured'}), 500
    
    # Get event by access code
    event = supabase.table('farewell_events').select('*').eq('access_code', access_code).limit(1).execute()
    if not event.data or len(event.data) == 0:
        return jsonify({'error': 'Event not found'}), 404
    
    event_data = event.data[0]
    event_id = event_data['id']
    
    data = request.json
    email = data.get('email', '').strip().lower()
    name = data.get('name', '').strip()
    send_invite = data.get('sendInvite', False)
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    # Check if this email is the honoree
    if event_data.get('honoree_email') and email == event_data['honoree_email'].lower():
        return jsonify({'error': 'Cannot add the honoree as a team member'}), 400
    
    # Check if member already exists
    existing = supabase.table('team_members').select('*').eq('event_id', event_id).eq('email', email).limit(1).execute()
    if existing.data and len(existing.data) > 0:
        return jsonify({'error': 'This email is already in the team list'}), 400
    
    # Create new team member
    member_name = name if name else email.split('@')[0].replace('.', ' ').title()
    new_member = {
        'event_id': event_id,
        'name': member_name,
        'email': email
    }
    
    result = supabase.table('team_members').insert(new_member).execute()
    member_id = result.data[0]['id']
    
    invite_sent = False
    
    # Send invitation if requested
    if send_invite:
        try:
            personal_link = f"{request.host_url.rstrip('/')}/submit/{event_id}?email={quote(email)}"
            honoree_first_name = event_data['honoree_name'].split()[0]
            deadline_date = datetime.fromisoformat(event_data['deadline'].replace('Z', '+00:00'))
            weekdays_en = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            formatted_deadline = f"{weekdays_en[deadline_date.weekday()]}, {deadline_date.strftime('%d.%m.')}"
            member_first_name = member_name.split()[0]

            subject = f"Farewell Card for {honoree_first_name} 🎉"
            html_content = f"""
        <html>
        <body style="font-family: 'Open Sans', Arial, sans-serif; margin: 0; padding: 20px; background-color: #eeeeee;">
            <table width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                    <td align="center">
                        <table width="600" cellpadding="0" cellspacing="0" border="0" style="background-color: white; border-radius: 8px; border-top: 4px solid #fa4f4f;">
                            <tr>
                                <td align="left" style="padding: 30px;">
                                    <h2 style="color: #434343; margin-top: 0; margin-bottom: 20px;">Farewell Card for {honoree_first_name}</h2>
                                    <p style="color: #434343; margin: 0 0 15px 0;">Hi {member_first_name},</p>
                                    <p style="color: #434343; margin: 0 0 15px 0;">It is <strong>{honoree_first_name}'s</strong> last day on <strong>{formatted_deadline}</strong>, and so we would like you to contribute to their farewell card.</p>
                                    <p style="color: #434343; margin: 0 0 25px 0;">Please upload or draft your message via our new farewell app:</p>
                                    <table cellpadding="0" cellspacing="0" border="0">
                                        <tr>
                                            <td align="left" style="padding: 10px 0 25px 0;">
                                                <a href="{personal_link}" style="background-color: #fa4f4f; color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">Add Your Message</a>
                                            </td>
                                        </tr>
                                    </table>
                                    <hr style="border: none; border-top: 1px solid #eeeeee; margin: 20px 0;">
                                    <p style="color: #999999; font-size: 12px; margin: 0;">
                                        This is your personalized link – no login required!<br>
                                        Organized by {event_data['organizer_name'].split()[0]}
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

            if send_email(email, subject, html_content):
                supabase.table('team_members').update({'invited_at': datetime.now(timezone.utc).isoformat()}).eq('id', member_id).execute()
                invite_sent = True
        except Exception as e:
            app.logger.error(f'Error sending invitation: {str(e)}')
    
    return jsonify({
        'success': True,
        'memberId': member_id,
        'memberName': member_name,
        'inviteSent': invite_sent
    })


@app.route('/api/admin/<access_code>/download-all')
def download_all_submissions(access_code):
    """Download all submissions as a ZIP file"""
    if not supabase:
        return jsonify({'error': 'Database not configured'}), 500
    
    # Get event by access code
    event = supabase.table('farewell_events').select('*').eq('access_code', access_code).limit(1).execute()
    if not event.data or len(event.data) == 0:
        return jsonify({'error': 'Event not found'}), 404
    
    event_data = event.data[0]
    event_id = event_data['id']
    honoree_name = event_data['honoree_name']
    
    # Get all submissions with team member info
    submissions = supabase.table('submissions').select('*, team_members(name, email)').eq('event_id', event_id).execute()
    
    if not submissions.data:
        return jsonify({'error': 'No submissions yet'}), 404
    
    # Create ZIP file in memory
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add a summary text file
        summary_lines = [f"Farewell Card for {honoree_name}", "=" * 40, ""]
        
        for idx, submission in enumerate(submissions.data, 1):
            member_name = submission['team_members']['name'] if submission.get('team_members') else 'Unknown'
            member_email = submission['team_members']['email'] if submission.get('team_members') else ''
            safe_name = member_name.replace(' ', '_').replace('/', '-')
            
            # Add message to summary
            summary_lines.append(f"From: {member_name} ({member_email})")
            if submission.get('message'):
                summary_lines.append(f'"{submission["message"]}"')
            
            # Add handwritten note file to ZIP if exists
            if submission.get('file_url'):
                file_url = submission['file_url']
                summary_lines.append(f"Handwritten note: {file_url}")
                
                # Determine file extension
                ext = os.path.splitext(file_url.split('?')[0])[1] or '.jpg'
                zip_filename = f"{idx:02d}_{safe_name}_note{ext}"
                
                # Check if it's a Supabase Storage URL or local file
                if file_url.startswith('http'):
                    # Fetch from Supabase Storage
                    try:
                        response = requests.get(file_url, timeout=30)
                        if response.status_code == 200:
                            zip_file.writestr(zip_filename, response.content)
                    except Exception as e:
                        app.logger.error(f'Error fetching file {file_url}: {str(e)}')
                else:
                    # Legacy: local file
                    file_path = file_url.lstrip('/')
                    full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_path)
                    if os.path.exists(full_path):
                        zip_file.write(full_path, zip_filename)
            
            # Add all photos to ZIP
            if submission.get('photo_urls'):
                try:
                    photo_urls = json.loads(submission['photo_urls'])
                    for photo_idx, photo_url in enumerate(photo_urls, 1):
                        # Determine file extension
                        ext = os.path.splitext(photo_url.split('?')[0])[1] or '.jpg'
                        zip_filename = f"{idx:02d}_{safe_name}_photo{photo_idx:02d}{ext}"
                        
                        # Check if it's a Supabase Storage URL or local file
                        if photo_url.startswith('http'):
                            # Fetch from Supabase Storage
                            try:
                                response = requests.get(photo_url, timeout=30)
                                if response.status_code == 200:
                                    zip_file.writestr(zip_filename, response.content)
                            except Exception as e:
                                app.logger.error(f'Error fetching photo {photo_url}: {str(e)}')
                        else:
                            # Legacy: local file
                            file_path = photo_url.lstrip('/')
                            full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_path)
                            if os.path.exists(full_path):
                                zip_file.write(full_path, zip_filename)
                    
                    summary_lines.append(f"Photos: {len(photo_urls)}")
                except:
                    pass
            
            summary_lines.append("")
        
        # Add summary file
        summary_content = "\n".join(summary_lines)
        zip_file.writestr("00_messages_summary.txt", summary_content)
    
    zip_buffer.seek(0)
    
    # Create filename
    safe_honoree = honoree_name.replace(' ', '_').replace('/', '-')
    filename = f"farewell_{safe_honoree}.zip"
    
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=filename
    )


# ============================================
# MIRO COLLAGE INTEGRATION
# ============================================

import random
import math

# Sticky note colors - rotating through these for variety (like in Josef/Lorenzo/Mascha examples)
STICKY_COLORS = [
    'yellow',         # Kräftiges Gelb
    'light_pink',     # Rosa
    'pink',           # Pink
    'violet',         # Lila
    'light_green',    # Hellgrün
    'light_blue',     # Hellblau
    'cyan',           # Türkis
    'light_yellow',   # Helles Gelb
]


def miro_api_request(method, endpoint, data=None):
    """Make a request to the Miro API"""
    if not MIRO_ACCESS_TOKEN:
        raise Exception('Miro API not configured')
    
    headers = {
        'Authorization': f'Bearer {MIRO_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    url = f'{MIRO_API_BASE}{endpoint}'
    
    if method == 'GET':
        response = requests.get(url, headers=headers)
    elif method == 'POST':
        response = requests.post(url, headers=headers, json=data)
    else:
        raise Exception(f'Unsupported method: {method}')
    
    if response.status_code >= 400:
        app.logger.error(f'Miro API error: {response.status_code} - {response.text}')
        raise Exception(f'Miro API error: {response.text}')
    
    return response.json()


def create_miro_board(name: str) -> dict:
    """Create a new Miro board"""
    data = {
        'name': name,
        'teamId': MIRO_TEAM_ID
    }
    return miro_api_request('POST', '/boards', data)


def add_miro_image(board_id: str, image_url: str, x: float, y: float, width: int = 300, rotation: float = 0) -> dict:
    """Add an image to a Miro board from URL with optional rotation"""
    data = {
        'data': {
            'url': image_url
        },
        'position': {
            'x': x,
            'y': y,
            'origin': 'center'
        },
        'geometry': {
            'width': width,
            'rotation': rotation
        }
    }
    return miro_api_request('POST', f'/boards/{board_id}/images', data)


def add_miro_sticky_note(board_id: str, content: str, x: float, y: float, color: str = 'yellow', width: int = 200) -> dict:
    """Add a sticky note to a Miro board"""
    # Miro sticky notes have a max content length
    truncated_content = content[:1000] if content else ''
    
    data = {
        'data': {
            'content': truncated_content,
            'shape': 'square'
        },
        'style': {
            'fillColor': color
        },
        'position': {
            'x': x,
            'y': y,
            'origin': 'center'
        },
        'geometry': {
            'width': width
        }
    }
    return miro_api_request('POST', f'/boards/{board_id}/sticky_notes', data)


def add_miro_text(board_id: str, content: str, x: float, y: float, font_size: int = 24, color: str = '#1a1a1a') -> dict:
    """Add a text element to a Miro board"""
    data = {
        'data': {
            'content': content
        },
        'style': {
            'fontSize': str(font_size),
            'color': color
        },
        'position': {
            'x': x,
            'y': y,
            'origin': 'center'
        }
    }
    return miro_api_request('POST', f'/boards/{board_id}/texts', data)


def add_miro_shape(board_id: str, shape: str, x: float, y: float, width: int, height: int, fill_color: str = '#fa4f4f', border_color: str = '', border_width: float = 0) -> dict:
    """Add a shape to a Miro board"""
    style = {
        'fillColor': fill_color
    }
    # Miro requires borderWidth > 1.0, so only add it if specified
    if border_width > 1.0:
        style['borderWidth'] = str(border_width)
        if border_color:
            style['borderColor'] = border_color
    
    data = {
        'data': {
            'shape': shape
        },
        'style': style,
        'position': {
            'x': x,
            'y': y,
            'origin': 'center'
        },
        'geometry': {
            'width': width,
            'height': height
        }
    }
    return miro_api_request('POST', f'/boards/{board_id}/shapes', data)


def get_sticky_color(index: int) -> str:
    """Get a sticky note color, rotating through the palette"""
    return STICKY_COLORS[index % len(STICKY_COLORS)]


def calculate_grid_positions(num_items: int, board_width: int, board_height: int, start_y: int = 350):
    """
    Calculate grid positions with good spacing for a collage.
    Each submission gets a dedicated area to avoid overlapping.
    """
    positions = []
    
    # Determine grid size based on number of items
    if num_items <= 4:
        cols = 2
    elif num_items <= 9:
        cols = 3
    elif num_items <= 16:
        cols = 4
    else:
        cols = 5
    
    rows = math.ceil(num_items / cols)
    
    # Calculate cell sizes with generous padding
    cell_width = (board_width - 400) / cols  # Leave margin on sides
    cell_height = (board_height - start_y - 200) / rows  # Leave margin at bottom
    
    # Minimum cell size
    cell_width = max(cell_width, 600)
    cell_height = max(cell_height, 500)
    
    for i in range(num_items):
        col = i % cols
        row = i // cols
        
        # Center of each cell
        base_x = 200 + (col * cell_width) + (cell_width / 2)
        base_y = start_y + (row * cell_height) + (cell_height / 2)
        
        # Add slight randomness (but not too much to avoid overlapping)
        x_jitter = random.uniform(-cell_width * 0.1, cell_width * 0.1)
        y_jitter = random.uniform(-cell_height * 0.1, cell_height * 0.1)
        
        positions.append({
            'x': base_x + x_jitter,
            'y': base_y + y_jitter,
            'cell_width': cell_width,
            'cell_height': cell_height
        })
    
    return positions, cols, rows, cell_width, cell_height


@app.route('/api/admin/<access_code>/create-miro-collage', methods=['POST'])
def create_miro_collage(access_code):
    """Create a Miro board collage with all submitted photos and messages"""
    if not MIRO_ACCESS_TOKEN or not MIRO_TEAM_ID:
        return jsonify({'error': 'Miro API not configured. Please add MIRO_ACCESS_TOKEN and MIRO_TEAM_ID to .env'}), 400
    
    if not supabase:
        return jsonify({'error': 'Database not configured'}), 500
    
    # Get event by access code
    event = supabase.table('farewell_events').select('*').eq('access_code', access_code).limit(1).execute()
    if not event.data or len(event.data) == 0:
        return jsonify({'error': 'Event not found'}), 404
    
    event_data = event.data[0]
    event_id = event_data['id']
    honoree_name = event_data['honoree_name']
    
    # Get all submissions with team member info
    submissions = supabase.table('submissions').select('*, team_members(name, email)').eq('event_id', event_id).execute()
    
    if not submissions.data:
        return jsonify({'error': 'No submissions yet. Add some messages before creating a collage!'}), 400
    
    try:
        # Create Miro board
        board = create_miro_board(f'Farewell {honoree_name}')
        board_id = board['id']
        board_url = board['viewLink']
        
        # Calculate board size based on number of submissions
        num_submissions = len(submissions.data)
        
        # Dynamic board sizing
        if num_submissions <= 4:
            BOARD_WIDTH = 2500
            BOARD_HEIGHT = 2000
        elif num_submissions <= 9:
            BOARD_WIDTH = 3500
            BOARD_HEIGHT = 2800
        elif num_submissions <= 16:
            BOARD_WIDTH = 4500
            BOARD_HEIGHT = 3500
        else:
            BOARD_WIDTH = 5500
            BOARD_HEIGHT = 4500
        
        TITLE_Y = 120
        CONTENT_START_Y = 350
        
        # =====================
        # 1. ADD DECORATIVE FRAME/BACKGROUND
        # =====================
        # Outer frame (red border) - borderWidth must be > 1.0
        add_miro_shape(board_id, 'rectangle', BOARD_WIDTH / 2, BOARD_HEIGHT / 2, 
                      BOARD_WIDTH - 40, BOARD_HEIGHT - 40, '#ffffff', '#fa4f4f', 12.0)
        
        # Inner decorative line
        add_miro_shape(board_id, 'rectangle', BOARD_WIDTH / 2, BOARD_HEIGHT / 2,
                      BOARD_WIDTH - 100, BOARD_HEIGHT - 100, '#fefefe', '#dddddd', 4.0)
        
        # =====================
        # 2. ADD TITLE (large, centered, styled like Josef/Lorenzo)
        # =====================
        # Title background bar
        add_miro_shape(board_id, 'rectangle', BOARD_WIDTH / 2, TITLE_Y, 
                      BOARD_WIDTH - 200, 140, '#fa4f4f')
        
        # Title text (white on red background)
        title_text = f'<strong>FAREWELL {honoree_name.upper()}!</strong>'
        add_miro_text(board_id, title_text, BOARD_WIDTH / 2, TITLE_Y, font_size=64, color='#ffffff')
        
        # =====================
        # 3. CALCULATE LAYOUT - Grid with good spacing
        # =====================
        positions, cols, rows, cell_w, cell_h = calculate_grid_positions(
            num_submissions, BOARD_WIDTH, BOARD_HEIGHT, CONTENT_START_Y
        )
        
        # Track stats
        photos_added = 0
        notes_added = 0
        messages_added = 0
        
        # =====================
        # 4. ADD CONTENT FOR EACH SUBMISSION
        # =====================
        for idx, submission in enumerate(submissions.data):
            member_name = submission['team_members']['name'] if submission.get('team_members') else 'Anonymous'
            message = submission.get('message', '')
            file_url = submission.get('file_url')  # Handwritten note
            photo_urls_json = submission.get('photo_urls')
            
            # Get position for this submission
            pos = positions[idx]
            center_x = pos['x']
            center_y = pos['y']
            
            # Get color for this submission's sticky note
            sticky_color = get_sticky_color(idx)
            
            # Parse photo URLs
            photo_urls = []
            if photo_urls_json:
                try:
                    photo_urls = json.loads(photo_urls_json)
                except:
                    pass
            
            # Collect all images
            all_images = []
            
            # Add handwritten note as image if it's an image file
            if file_url and file_url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                all_images.append({'url': file_url, 'type': 'handwritten'})
                notes_added += 1
            
            # Add photos
            for photo_url in photo_urls:
                all_images.append({'url': photo_url, 'type': 'photo'})
            
            # =====================
            # 4a. ADD PHOTOS - spread within the cell
            # =====================
            photo_size = min(280, cell_w * 0.4)  # Scale photo size based on cell
            
            if len(all_images) == 1:
                # Single image - center it
                img = all_images[0]
                rotation = random.uniform(-5, 5)
                try:
                    add_miro_image(board_id, img['url'], center_x, center_y - 50, int(photo_size), rotation)
                    photos_added += 1
                except Exception as e:
                    app.logger.warning(f'Could not add image: {str(e)}')
                    
            elif len(all_images) >= 2:
                # Multiple images - arrange in a fan/stack pattern (no limit)
                num_photos = len(all_images)
                
                # Adjust photo size based on count
                if num_photos > 8:
                    photo_size = min(200, cell_w * 0.3)
                elif num_photos > 5:
                    photo_size = min(240, cell_w * 0.35)
                
                for img_idx, img in enumerate(all_images):
                    # Spread photos in a fan pattern
                    angle_offset = (img_idx - num_photos / 2) * 12  # Degrees between photos
                    
                    # Position with offset - spread more when there are many photos
                    spread_x = min(50, 300 / num_photos)
                    offset_x = (img_idx - num_photos / 2) * spread_x
                    offset_y = abs(img_idx - num_photos / 2) * 15 - 50
                    
                    img_x = center_x + offset_x
                    img_y = center_y + offset_y
                    
                    # Slight rotation for fan effect (reduced)
                    rotation = angle_offset * 0.3 + random.uniform(-2, 2)
                    
                    # Slightly vary size
                    size = int(photo_size * (0.95 + random.uniform(0, 0.1)))
                    
                    try:
                        add_miro_image(board_id, img['url'], img_x, img_y, size, rotation)
                        photos_added += 1
                    except Exception as e:
                        app.logger.warning(f'Could not add image: {str(e)}')
            
            # =====================
            # 4b. ADD STICKY NOTE WITH MESSAGE
            # =====================
            # Get first name only for signature
            first_name = member_name.split()[0] if member_name else ''
            
            if message:
                # Position sticky note below photos
                sticky_y = center_y + (cell_h * 0.35)
                sticky_x = center_x + random.uniform(-50, 50)
                
                # Format: Message first, then first name at the bottom
                sticky_content = f'"{message}"<br><br>– {first_name}'
                
                # Sticky note size based on message length
                sticky_width = min(280, max(180, len(message) * 1.5))
                
                try:
                    add_miro_sticky_note(board_id, sticky_content, sticky_x, sticky_y, sticky_color, int(sticky_width))
                    messages_added += 1
                except Exception as e:
                    app.logger.warning(f'Could not add sticky note: {str(e)}')
            
            # If no photos and no message, just add first name label
            elif not all_images:
                try:
                    add_miro_sticky_note(board_id, first_name, center_x, center_y, sticky_color, 150)
                except Exception as e:
                    app.logger.warning(f'Could not add label: {str(e)}')
        
        # =====================
        # 5. UPDATE DATABASE
        # =====================
        try:
            supabase.table('farewell_events').update({
                'miro_board_url': board_url
            }).eq('id', event_id).execute()
        except Exception as db_e:
            app.logger.warning(f'Could not save miro_board_url: {str(db_e)}')
        
        return jsonify({
            'success': True,
            'boardUrl': board_url,
            'boardId': board_id,
            'stats': {
                'submissions': num_submissions,
                'photosAdded': photos_added,
                'notesAdded': notes_added,
                'messagesAdded': messages_added
            }
        })
        
    except Exception as e:
        app.logger.error(f'Error creating Miro collage: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to create Miro board: {str(e)}'}), 500


@app.route('/api/miro/status')
def miro_status():
    """Check if Miro API is configured"""
    return jsonify({
        'configured': bool(MIRO_ACCESS_TOKEN and MIRO_TEAM_ID),
        'teamId': MIRO_TEAM_ID if MIRO_TEAM_ID else None
    })


if __name__ == '__main__':
    app.run(debug=True, port=5001)
