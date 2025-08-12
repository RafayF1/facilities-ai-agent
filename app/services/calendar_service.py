"""
Google Calendar API integration service.
"""
import asyncio
import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path
import pickle

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.config import settings

class CalendarService:
    """Google Calendar API service for appointment management."""
    
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self):
        self.service = None
        self._initialized = False
        self.credentials = None
        self.use_real_api = False
    
    async def initialize(self) -> None:
        """Initialize the Calendar service."""
        if self._initialized:
            return
        
        try:
            # Check if we have credentials for real Google Calendar API
            creds_path = settings.base_dir / "credentials.json"
            token_path = settings.base_dir / "token.pickle"
            
            if creds_path.exists():
                print("Found credentials.json - attempting real Google Calendar API integration")
                await self._initialize_real_api(creds_path, token_path)
            else:
                print("No credentials.json found - using simulation mode")
                print("To enable real Google Calendar integration:")
                print("1. Go to Google Cloud Console")
                print("2. Enable Calendar API")
                print("3. Create credentials (Desktop application)")
                print("4. Download credentials.json to app/ folder")
                self.use_real_api = False
            
            self._initialized = True
            
        except Exception as e:
            print(f"Calendar service initialization failed: {e}")
            print("Falling back to simulation mode")
            self.use_real_api = False
            self._initialized = True
    
    async def _initialize_real_api(self, creds_path: Path, token_path: Path):
        """Initialize real Google Calendar API."""
        creds = None
        
        # Load existing token
        if token_path.exists():
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(creds_path), self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        self.credentials = creds
        self.service = build('calendar', 'v3', credentials=creds)
        self.use_real_api = True
        print("✅ Google Calendar API initialized successfully")
    
    async def create_appointment(
        self,
        title: str,
        description: str,
        start_time: datetime,
        duration_minutes: int = 120,
        attendee_emails: Optional[list] = None,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a calendar appointment.
        
        Args:
            title: Event title
            description: Event description
            start_time: Start datetime
            duration_minutes: Duration in minutes
            attendee_emails: List of attendee emails
            location: Event location
            
        Returns:
            Dict with event details including event_id
        """
        await self.initialize()
        
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        if self.use_real_api and self.service:
            try:
                # Create real Google Calendar event
                event = {
                    'summary': title,
                    'description': description,
                    'location': location,
                    'start': {
                        'dateTime': start_time.isoformat(),
                        'timeZone': 'Asia/Dubai',
                    },
                    'end': {
                        'dateTime': end_time.isoformat(),
                        'timeZone': 'Asia/Dubai',
                    },
                    'attendees': [{'email': email} for email in (attendee_emails or [])],
                    'reminders': {
                        'useDefault': False,
                        'overrides': [
                            {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                            {'method': 'popup', 'minutes': 30},       # 30 minutes before
                        ],
                    },
                    'conferenceData': {
                        'createRequest': {
                            'requestId': f"facilities-{int(start_time.timestamp())}",
                            'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                        }
                    }
                }
                
                created_event = self.service.events().insert(
                    calendarId=settings.calendar_id,
                    body=event,
                    conferenceDataVersion=1,
                    sendNotifications=True
                ).execute()
                
                event_data = {
                    'event_id': created_event['id'],
                    'title': title,
                    'description': description,
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'location': location,
                    'attendees': attendee_emails or [],
                    'status': 'confirmed',
                    'created_at': datetime.now().isoformat(),
                    'calendar_link': created_event.get('htmlLink', ''),
                    'meet_link': created_event.get('conferenceData', {}).get('entryPoints', [{}])[0].get('uri', ''),
                    'real_api': True
                }
                
                print(f"✅ Real Google Calendar appointment created: {title} at {start_time}")
                print(f"📅 Calendar link: {event_data.get('calendar_link', '')}")
                if event_data.get('meet_link'):
                    print(f"🎥 Meet link: {event_data['meet_link']}")
                
                return event_data
                
            except HttpError as error:
                print(f"❌ Google Calendar API error: {error}")
                # Fall back to simulation
                return await self._create_simulated_appointment(title, description, start_time, duration_minutes, attendee_emails, location)
                
        else:
            # Simulation mode
            return await self._create_simulated_appointment(title, description, start_time, duration_minutes, attendee_emails, location)
    
    async def _create_simulated_appointment(self, title, description, start_time, duration_minutes, attendee_emails, location):
        """Create simulated appointment for demo purposes."""
        end_time = start_time + timedelta(minutes=duration_minutes)
        event_id = f"sim_evt_{int(start_time.timestamp())}"
        
        event_data = {
            'event_id': event_id,
            'title': title,
            'description': description,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'location': location,
            'attendees': attendee_emails or [],
            'status': 'confirmed',
            'created_at': datetime.now().isoformat(),
            'calendar_link': f'https://calendar.google.com/calendar/event?eid={event_id}',
            'real_api': False
        }
        
        print(f"✅ Simulated calendar appointment created: {title} at {start_time}")
        print(f"📝 Note: To enable real Google Calendar integration, add credentials.json")
        return event_data
    
    async def update_appointment(
        self,
        event_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        start_time: Optional[datetime] = None,
        duration_minutes: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update an existing calendar appointment."""
        await self.initialize()
        
        if self.use_real_api and self.service and not event_id.startswith('sim_'):
            try:
                # Get existing event
                event = self.service.events().get(
                    calendarId=settings.calendar_id,
                    eventId=event_id
                ).execute()
                
                # Update fields if provided
                if title:
                    event['summary'] = title
                if description:
                    event['description'] = description
                if start_time:
                    end_time = start_time + timedelta(minutes=duration_minutes or 120)
                    event['start']['dateTime'] = start_time.isoformat()
                    event['end']['dateTime'] = end_time.isoformat()
                
                # Update the event
                updated_event = self.service.events().update(
                    calendarId=settings.calendar_id,
                    eventId=event_id,
                    body=event
                ).execute()
                
                print(f"✅ Real Google Calendar appointment updated: {event_id}")
                return {
                    'event_id': event_id,
                    'status': 'updated',
                    'updated_at': datetime.now().isoformat(),
                    'real_api': True
                }
                
            except HttpError as error:
                print(f"❌ Error updating Google Calendar event: {error}")
        
        # Simulate update
        print(f"✅ Simulated calendar appointment updated: {event_id}")
        return {
            'event_id': event_id,
            'status': 'updated',
            'updated_at': datetime.now().isoformat(),
            'real_api': False
        }
    
    async def cancel_appointment(self, event_id: str) -> bool:
        """Cancel a calendar appointment."""
        await self.initialize()
        
        if self.use_real_api and self.service and not event_id.startswith('sim_'):
            try:
                self.service.events().delete(
                    calendarId=settings.calendar_id,
                    eventId=event_id
                ).execute()
                
                print(f"✅ Real Google Calendar appointment cancelled: {event_id}")
                return True
                
            except HttpError as error:
                print(f"❌ Error cancelling Google Calendar event: {error}")
                return False
        
        # Simulate cancellation
        print(f"✅ Simulated calendar appointment cancelled: {event_id}")
        return True
    
    async def get_appointment(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get appointment details by event ID."""
        await self.initialize()
        
        if self.use_real_api and self.service and not event_id.startswith('sim_'):
            try:
                event = self.service.events().get(
                    calendarId=settings.calendar_id,
                    eventId=event_id
                ).execute()
                
                return {
                    'event_id': event['id'],
                    'title': event.get('summary', ''),
                    'description': event.get('description', ''),
                    'start_time': event['start'].get('dateTime', ''),
                    'end_time': event['end'].get('dateTime', ''),
                    'location': event.get('location', ''),
                    'status': event.get('status', ''),
                    'real_api': True
                }
                
            except HttpError as error:
                print(f"❌ Error getting Google Calendar event: {error}")
        
        # Simulate retrieval
        return {
            'event_id': event_id,
            'status': 'confirmed',
            'title': 'Simulated Appointment',
            'real_api': False
        }
    
    async def check_availability(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> bool:
        """Check if time slot is available in calendar."""
        await self.initialize()
        
        if self.use_real_api and self.service:
            try:
                events_result = self.service.events().list(
                    calendarId=settings.calendar_id,
                    timeMin=start_time.isoformat(),
                    timeMax=end_time.isoformat(),
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                
                events = events_result.get('items', [])
                is_available = len(events) == 0
                
                print(f"📅 Calendar availability check: {'Available' if is_available else 'Busy'} ({len(events)} conflicts)")
                return is_available
                
            except HttpError as error:
                print(f"❌ Error checking calendar availability: {error}")
        
        # For simulation, assume slots are generally available
        return True

# Global calendar service instance
calendar_service = CalendarService()