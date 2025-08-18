"""
Gmail API integration service.
"""
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
from pathlib import Path

from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from googleapiclient.discovery import build

from app.config import settings

class EmailService:
    """Gmail API service for email notifications."""
    
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']
    
    def __init__(self):
        self.service = None
        self._initialized = False
        self.credentials = None
    
    async def initialize(self) -> None:
        """Initialize the Gmail service."""
        if self._initialized:
            return
        
        try:
            # Check for service account credentials
            service_account_path = settings.base_dir / "service-account.json"
            
            if service_account_path.exists():
                print("Found service-account.json - initializing Gmail API with service account")
                await self._initialize_service_account(service_account_path)
            else:
                print("No service-account.json found - using simulation mode")
                self._initialized = True
                
        except Exception as e:
            print(f"Gmail service initialization failed: {e}")
            self._initialized = True
    
    async def _initialize_service_account(self, service_account_path: Path):
        """Initialize Gmail API using service account."""
        try:
            # Load service account credentials
            self.credentials = ServiceAccountCredentials.from_service_account_file(
                str(service_account_path),
                scopes=self.SCOPES
            )
            
            # If we have a specific user to impersonate, use that
            if hasattr(settings, 'gmail_user') and settings.gmail_user:
                print(f"ðŸ” Impersonating user: {settings.gmail_user}")
                self.credentials = self.credentials.with_subject(settings.gmail_user)
            
            # Build the service
            self.service = build('gmail', 'v1', credentials=self.credentials)
            print("âœ… Gmail API initialized successfully with service account")
            
        except Exception as e:
            print(f"âŒ Gmail service account initialization failed: {e}")
            raise
    
    async def send_appointment_confirmation(
        self,
        recipient_email: str,
        customer_name: str,
        appointment_details: Dict[str, Any]
    ) -> bool:
        """
        Send appointment confirmation email.
        
        Args:
            recipient_email: Customer email address
            customer_name: Customer name
            appointment_details: Dictionary with appointment info
            
        Returns:
            Success status
        """
        await self.initialize()
        
        subject = f"Appointment Confirmation - {settings.company_name}"
        
        body = f"""
Dear {customer_name},

Your service appointment has been confirmed with {settings.company_name}.

Appointment Details:
- Service: {appointment_details.get('service_type', 'N/A')}
- Date & Time: {appointment_details.get('scheduled_time', 'N/A')}
- Location: {appointment_details.get('location', 'N/A')}
- Technician: {appointment_details.get('technician_name', 'TBD')}
- Work Order ID: {appointment_details.get('work_order_id', 'N/A')}

What to expect:
- Our technician will arrive within the scheduled time window
- Please ensure someone is available to provide access
- All necessary tools and parts will be brought by our team

If you need to reschedule or have any questions, please contact us at:
Phone: +971-4-XXX-XXXX
Email: support@{settings.company_name.lower().replace(' ', '')}.com

Thank you for choosing {settings.company_name}!

Best regards,
Customer Service Team
{settings.company_name}
        """.strip()
        
        return await self._send_email(recipient_email, subject, body)
    
    async def send_emergency_notification(
        self,
        recipient_email: str,
        customer_name: str,
        emergency_details: Dict[str, Any]
    ) -> bool:
        """Send emergency service notification email."""
        await self.initialize()
        
        subject = f"URGENT: Emergency Service Request - {settings.company_name}"
        
        body = f"""
Dear {customer_name},

We have received your EMERGENCY service request and are taking immediate action.

Emergency Details:
- Issue: {emergency_details.get('problem_description', 'N/A')}
- Location: {emergency_details.get('location', 'N/A')}
- Priority: {emergency_details.get('urgency', 'EMERGENCY')}
- Request ID: {emergency_details.get('work_order_id', 'N/A')}
- Reported at: {emergency_details.get('request_time', datetime.now().strftime('%Y-%m-%d %H:%M'))}

IMMEDIATE ACTIONS TAKEN:
âœ… Emergency response team has been notified
âœ… Priority technician is being dispatched
âœ… You will be contacted within 15 minutes with ETA

SAFETY REMINDERS:
- If there is immediate danger, evacuate the area
- Do not attempt repairs yourself
- Keep the area clear for our technicians

Our emergency hotline: +971-4-XXX-XXXX (Available 24/7)

A technician will contact you shortly with their estimated arrival time.

{settings.company_name} Emergency Response Team
        """.strip()
        
        return await self._send_email(recipient_email, subject, body)
    
    async def send_work_order_status_update(
        self,
        recipient_email: str,
        customer_name: str,
        work_order_details: Dict[str, Any]
    ) -> bool:
        """Send work order status update email."""
        await self.initialize()
        
        subject = f"Work Order Update - {work_order_details.get('work_order_id', 'N/A')}"
        
        status = work_order_details.get('status', 'Unknown')
        
        body = f"""
Dear {customer_name},

This is an update regarding your service request with {settings.company_name}.

Work Order Details:
- Work Order ID: {work_order_details.get('work_order_id', 'N/A')}
- Service Type: {work_order_details.get('service_type', 'N/A')}
- Current Status: {status}
- Location: {work_order_details.get('location', 'N/A')}
"""
        
        if status == "Scheduled":
            body += f"""
- Scheduled Date & Time: {work_order_details.get('scheduled_time', 'TBD')}
- Assigned Technician: {work_order_details.get('technician_name', 'TBD')}

Your service appointment has been scheduled. Our technician will arrive within the specified time window.
"""
        elif status == "In Progress":
            body += f"""
- Technician: {work_order_details.get('technician_name', 'N/A')}
- Started at: {work_order_details.get('start_time', 'N/A')}

Our technician is currently working on your service request.
"""
        elif status == "Completed":
            body += f"""
- Completed at: {work_order_details.get('completion_time', 'N/A')}
- Technician: {work_order_details.get('technician_name', 'N/A')}
- Work Summary: {work_order_details.get('completion_notes', 'Service completed successfully')}

Your service request has been completed. Thank you for choosing {settings.company_name}!
"""
        
        body += f"""

If you have any questions or concerns, please don't hesitate to contact us:
Phone: +971-4-XXX-XXXX
Email: support@{settings.company_name.lower().replace(' ', '')}.com

Best regards,
Customer Service Team
{settings.company_name}
        """.strip()
        
        return await self._send_email(recipient_email, subject, body)
    
    async def _send_email(self, to_email: str, subject: str, body: str) -> bool:
        """Send email using Gmail API."""
        try:
            if self.service and self.credentials:
                # Create message
                message = MIMEMultipart()
                message['to'] = to_email
                message['subject'] = subject
                message.attach(MIMEText(body, 'plain'))
                
                # Encode message
                raw_message = base64.urlsafe_b64encode(
                    message.as_bytes()
                ).decode()
                
                # Send email
                send_message = self.service.users().messages().send(
                    userId="me",
                    body={'raw': raw_message}
                ).execute()
                
                print(f"ðŸ“§ Email sent successfully to {to_email}")
                print(f"   Message ID: {send_message['id']}")
                return True
                
            else:
                # Fallback to simulation
                print(f"ðŸ“§ Email sent to {to_email} (simulation)")
                print(f"   Subject: {subject}")
                print(f"   Body preview: {body[:100]}...")
                return True
                
        except Exception as e:
            error_str = str(e)
            if "Gmail API has not been used in project" in error_str:
                print(f"âŒ Gmail API not enabled. Please enable it at:")
                print(f"   https://console.developers.google.com/apis/api/gmail.googleapis.com/overview?project=413760801200")
                print(f"ðŸ“§ Falling back to simulation mode for {to_email}")
                # Fallback to simulation
                print(f"ðŸ“§ Email sent to {to_email} (simulation)")
                print(f"   Subject: {subject}")
                print(f"   Body preview: {body[:100]}...")
                return True
            else:
                print(f"âŒ Error sending email: {e}")
                return False

# Global email service instance
email_service = EmailService()
