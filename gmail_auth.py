"""
Google OAuth 2.0 Authentication for Gmail and Drive
No password needed - just authorize with Google!
"""
import os
import json
import base64
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# API scopes - Gmail for sending, Drive for creating folders
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/drive.file'  # Create/access files in Drive
]

# Parent folder ID for farewell cards (from user's shared folder)
FAREWELL_CARDS_FOLDER_ID = '1r0vtpUvIrJdpKiBDmA6MbH9EQ81c0HlM'

# File paths for credentials
CREDENTIALS_FILE = Path(__file__).parent / 'gmail_credentials.json'
TOKEN_FILE = Path(__file__).parent / 'gmail_token.json'


def get_gmail_service():
    """Get authenticated Gmail service or None if not authorized"""
    creds = None
    
    # Load existing token if available
    if TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        except Exception:
            pass
    
    # Check if credentials are valid
    if creds and creds.valid:
        return build('gmail', 'v1', credentials=creds)
    
    # Try to refresh expired credentials
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            save_credentials(creds)
            return build('gmail', 'v1', credentials=creds)
        except Exception:
            pass
    
    return None


def is_gmail_connected():
    """Check if Gmail is connected and working"""
    service = get_gmail_service()
    if service:
        try:
            # Quick test to see if connection works
            service.users().getProfile(userId='me').execute()
            return True
        except Exception:
            pass
    return False


def get_gmail_email():
    """Get the email address of the connected Gmail account"""
    service = get_gmail_service()
    if service:
        try:
            profile = service.users().getProfile(userId='me').execute()
            return profile.get('emailAddress')
        except Exception:
            pass
    return None


def save_credentials(creds):
    """Save credentials to token file"""
    with open(TOKEN_FILE, 'w') as f:
        f.write(creds.to_json())


def start_auth_flow(redirect_uri: str):
    """Start the OAuth flow and return the authorization URL"""
    if not CREDENTIALS_FILE.exists():
        raise FileNotFoundError(
            "Gmail credentials file not found. Please download it from Google Cloud Console."
        )
    
    flow = InstalledAppFlow.from_client_secrets_file(
        str(CREDENTIALS_FILE), 
        SCOPES,
        redirect_uri=redirect_uri
    )
    
    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    return auth_url, state, flow


def complete_auth_flow(authorization_response: str, flow):
    """Complete the OAuth flow with the authorization response"""
    flow.fetch_token(authorization_response=authorization_response)
    creds = flow.credentials
    save_credentials(creds)
    return creds


def send_email_via_gmail(to_email: str, subject: str, html_content: str) -> bool:
    """Send an email using Gmail API"""
    service = get_gmail_service()
    if not service:
        print("Gmail not connected")
        return False
    
    try:
        message = MIMEMultipart('alternative')
        message['to'] = to_email
        message['subject'] = subject
        
        html_part = MIMEText(html_content, 'html')
        message.attach(html_part)
        
        # Encode the message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        # Send the message
        service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        return True
    except Exception as e:
        print(f"Error sending email via Gmail: {e}")
        return False


def disconnect_gmail():
    """Remove Gmail authorization"""
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()
    return True


# Google Drive functions
def get_drive_service():
    """Get authenticated Google Drive service or None if not authorized"""
    creds = None
    
    if TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        except Exception:
            pass
    
    if creds and creds.valid:
        return build('drive', 'v3', credentials=creds)
    
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            save_credentials(creds)
            return build('drive', 'v3', credentials=creds)
        except Exception:
            pass
    
    return None


def create_farewell_folder(honoree_first_name: str, event_date=None) -> dict:
    """
    Create a folder for the farewell card in Google Drive.
    Format: YYMM FirstName (e.g., "2601 Julian" for January 2026, Julian)
    
    Returns dict with folder_id and folder_url, or None if failed.
    """
    from datetime import datetime
    
    service = get_drive_service()
    if not service:
        print("Google Drive not connected")
        return None
    
    try:
        # Generate folder name: YYMM FirstName
        if event_date:
            date = datetime.fromisoformat(event_date.replace('Z', '+00:00'))
        else:
            date = datetime.now()
        
        folder_name = f"{date.strftime('%y%m')} {honoree_first_name}"
        
        # Check if folder already exists
        query = f"name='{folder_name}' and '{FAREWELL_CARDS_FOLDER_ID}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(q=query, fields="files(id, name, webViewLink)").execute()
        existing = results.get('files', [])
        
        if existing:
            # Folder already exists, return it
            folder = existing[0]
            return {
                'folder_id': folder['id'],
                'folder_url': folder.get('webViewLink', f"https://drive.google.com/drive/folders/{folder['id']}")
            }
        
        # Create new folder
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [FAREWELL_CARDS_FOLDER_ID]
        }
        
        folder = service.files().create(
            body=file_metadata,
            fields='id, webViewLink'
        ).execute()
        
        # Make folder accessible to anyone with the link
        permission = {
            'type': 'anyone',
            'role': 'writer'  # Anyone can add files
        }
        service.permissions().create(
            fileId=folder['id'],
            body=permission
        ).execute()
        
        return {
            'folder_id': folder['id'],
            'folder_url': folder.get('webViewLink', f"https://drive.google.com/drive/folders/{folder['id']}")
        }
        
    except Exception as e:
        print(f"Error creating Drive folder: {e}")
        return None


def is_drive_connected():
    """Check if Google Drive is connected"""
    service = get_drive_service()
    if service:
        try:
            # Quick test
            service.files().list(pageSize=1).execute()
            return True
        except Exception:
            pass
    return False
