"""
Farewellify - A simple app to organize farewell cards for colleagues
"""
import os
import uuid
import smtplib
import zipfile
import io
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
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

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://datpxrveaizpigltowju.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_KEY else None

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
    
    # Add team members (NEVER include the honoree!)
    team_members = data.get('teamMembers', [])
    honoree_email = data.get('honoreeEmail', '').lower()
    
    for member in team_members:
        # Double-check: never add the honoree as a team member
        if member['email'].lower() == honoree_email:
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
    
    sent_count = 0
    honoree_first_name = event_data['honoree_name'].split()[0]
    
    # Format deadline as "Thursday, 29.01."
    deadline_date = datetime.fromisoformat(event_data['deadline'].replace('Z', '+00:00'))
    weekdays_en = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    formatted_deadline = f"{weekdays_en[deadline_date.weekday()]}, {deadline_date.strftime('%d.%m.')}"
    
    for member in members.data:
        # Create personalized link for this team member
        personal_link = f"{submit_url}?email={member['email']}"
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
            supabase.table('team_members').update({'invited_at': datetime.utcnow().isoformat()}).eq('id', member['id']).execute()
    
    return jsonify({
        'success': True,
        'sentCount': sent_count,
        'totalMembers': len(members.data)
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
    
    sent_count = 0
    honoree_first_name = event_data['honoree_name'].split()[0]
    
    # Format deadline as "Thursday, 29.01."
    deadline_date = datetime.fromisoformat(event_data['deadline'].replace('Z', '+00:00'))
    weekdays_en = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    formatted_deadline = f"{weekdays_en[deadline_date.weekday()]}, {deadline_date.strftime('%d.%m.')}"
    
    for member in pending_members:
        personal_link = f"{submit_url}?email={member['email']}"
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
            supabase.table('team_members').update({'reminder_sent_at': datetime.utcnow().isoformat()}).eq('id', member['id']).execute()
    
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
    
    event_id = request.form.get('eventId')
    email = request.form.get('email')
    name = request.form.get('name')
    message = request.form.get('message')
    existing_photos = request.form.get('existingPhotos')  # JSON array of existing photo URLs to keep
    
    if not event_id or not email:
        return jsonify({'error': 'Missing required fields'}), 400
    
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
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            msg_file.save(filepath)
            file_url = f"/uploads/{unique_filename}"
    
    # Handle multiple photo files (up to 15)
    photo_files = request.files.getlist('photos')
    for photo in photo_files[:15]:  # Limit to 15 photos
        if photo and photo.filename and allowed_file(photo.filename):
            ext = photo.filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{event_id}_photo_{uuid.uuid4().hex[:8]}.{ext}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            photo.save(filepath)
            photo_urls.append(f"/uploads/{unique_filename}")
    
    # Legacy: Handle single 'file' upload (for backwards compatibility)
    if 'file' in request.files:
        file = request.files['file']
        if file and file.filename and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{event_id}_{uuid.uuid4().hex[:8]}.{ext}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)
            photo_urls.append(f"/uploads/{unique_filename}")
    
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
    
    # Build submission data
    submission_data = {
        'event_id': event_id,
        'team_member_id': member_id,
        'message': message if message else None,
        'file_url': file_url
    }
    
    # Add photo_urls if there are any photos
    if photo_urls:
        submission_data['photo_urls'] = json.dumps(photo_urls)
    
    try:
        if existing.data:
            # Update existing submission
            # Keep old file_url if no new one uploaded
            if not file_url and existing.data[0].get('file_url'):
                submission_data['file_url'] = existing.data[0]['file_url']
            supabase.table('submissions').update(submission_data).eq('id', existing.data[0]['id']).execute()
        else:
            # Create new submission
            supabase.table('submissions').insert(submission_data).execute()
        
        return jsonify({'success': True})
    except Exception as e:
        error_msg = str(e)
        # Check if error is about missing photo_urls column
        if 'photo_urls' in error_msg:
            # Try again without photo_urls
            del submission_data['photo_urls']
            try:
                if existing.data:
                    supabase.table('submissions').update(submission_data).eq('id', existing.data[0]['id']).execute()
                else:
                    supabase.table('submissions').insert(submission_data).execute()
                return jsonify({
                    'success': True, 
                    'warning': 'Photos not saved - please add photo_urls column to submissions table in Supabase'
                })
            except Exception as e2:
                return jsonify({'success': False, 'error': str(e2)}), 500
        return jsonify({'success': False, 'error': error_msg}), 500


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
            'photoUrls': photo_urls
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
                file_path = submission['file_url'].lstrip('/')
                full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_path)
                summary_lines.append(f"Handwritten note: {submission['file_url']}")
                
                if os.path.exists(full_path):
                    ext = os.path.splitext(full_path)[1]
                    zip_filename = f"{idx:02d}_{safe_name}_note{ext}"
                    zip_file.write(full_path, zip_filename)
            
            # Add all photos to ZIP
            if submission.get('photo_urls'):
                try:
                    photo_urls = json.loads(submission['photo_urls'])
                    for photo_idx, photo_url in enumerate(photo_urls, 1):
                        file_path = photo_url.lstrip('/')
                        full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_path)
                        
                        if os.path.exists(full_path):
                            ext = os.path.splitext(full_path)[1]
                            zip_filename = f"{idx:02d}_{safe_name}_photo{photo_idx:02d}{ext}"
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


if __name__ == '__main__':
    app.run(debug=True, port=5001)
