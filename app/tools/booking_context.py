"""
Fixed booking context management with alternative date handling.
"""
from typing import Dict, Any, Optional
from datetime import datetime
import re

# Global booking context storage (in production, this would be in session state)
_booking_contexts = {}

async def store_booking_context(
    session_id: str,
    customer_id: str,
    property_id: str,
    service_type: str,
    service_id: str,
    problem_description: str,
    area_zone: str,
    urgency: str
) -> Dict[str, Any]:
    """
    Store booking context for later use when customer confirms appointment.
    """
    try:
        context = {
            "customer_id": customer_id,
            "property_id": property_id,
            "service_type": service_type,
            "service_id": service_id,
            "problem_description": problem_description,
            "area_zone": area_zone,
            "urgency": urgency,
            "created_at": datetime.now().isoformat(),
            "available_technicians": [],
            "last_checked_datetime": None,
            "suggested_alternatives": [],  # NEW: Store suggested dates
            "original_requested_date": None,  # NEW: Track original request
            "current_preferred_date": None   # NEW: Track what customer wants now
        }
        
        _booking_contexts[session_id] = context
        
        print(f"💾 Stored booking context for session {session_id}")
        print(f"   Customer: {customer_id}")
        print(f"   Service: {service_type}")
        print(f"   Location: {area_zone}")
        
        return {
            "status": "success",
            "context_stored": True,
            "session_id": session_id,
            "message": "Booking context saved successfully"
        }
        
    except Exception as e:
        print(f"❌ Error storing booking context: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Failed to store booking context: {str(e)}"
        }

async def update_booking_context(
    session_id: str,
    technician_id: str,
    technician_name: str,
    checked_datetime: str
) -> Dict[str, Any]:
    """
    Update booking context with availability check results.
    """
    try:
        if session_id not in _booking_contexts:
            return {
                "status": "error",
                "error_message": "No booking context found for this session"
            }
        
        context = _booking_contexts[session_id]
        context["preferred_technician_id"] = technician_id
        context["preferred_technician_name"] = technician_name
        context["last_checked_datetime"] = checked_datetime
        
        # If this is the first check, store as original request
        if context["original_requested_date"] is None:
            context["original_requested_date"] = checked_datetime
        
        # Always update current preferred date
        context["current_preferred_date"] = checked_datetime
        
        print(f"🔄 Updated booking context for session {session_id}")
        print(f"   Technician: {technician_name}")
        print(f"   DateTime: {checked_datetime}")
        
        return {
            "status": "success",
            "context_updated": True,
            "message": "Booking context updated with availability"
        }
        
    except Exception as e:
        print(f"❌ Error updating booking context: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Failed to update booking context: {str(e)}"
        }

# NEW FUNCTION: Handle alternative date acceptance
# Replace the update_preferred_date function in your booking_context.py with this:

async def update_preferred_date(
    session_id: str,
    new_preferred_date: str,
    alternative_dates: str
) -> Dict[str, Any]:
    """
    Update the preferred date when customer accepts an alternative.
    
    Args:
        session_id: Session identifier
        new_preferred_date: New preferred date in YYYY-MM-DD format
        alternative_dates: Comma-separated string of alternative dates that were suggested
        
    Returns:
        Confirmation of date update
    """
    try:
        if session_id not in _booking_contexts:
            return {
                "status": "error",
                "error_message": "No booking context found for this session"
            }
        
        context = _booking_contexts[session_id]
        
        # Convert string to list if provided
        if alternative_dates:
            alt_list = [date.strip() for date in alternative_dates.split(",")]
            context["suggested_alternatives"] = alt_list
        
        # Update current preferred date
        context["current_preferred_date"] = new_preferred_date
        
        print(f"📅 Updated preferred date for session {session_id}")
        print(f"   Original request: {context.get('original_requested_date')}")
        print(f"   New preferred: {new_preferred_date}")
        
        return {
            "status": "success",
            "date_updated": True,
            "original_date": context.get("original_requested_date"),
            "new_preferred_date": new_preferred_date,
            "message": f"Preferred date updated to {new_preferred_date}"
        }
        
    except Exception as e:
        print(f"❌ Error updating preferred date: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Failed to update preferred date: {str(e)}"
        }

async def get_booking_context(session_id: str) -> Dict[str, Any]:
    """
    Retrieve stored booking context for a session.
    """
    try:
        if session_id not in _booking_contexts:
            return {
                "status": "error",
                "error_message": "No booking context found for this session"
            }
        
        context = _booking_contexts[session_id]
        
        return {
            "status": "success",
            "context_found": True,
            "booking_context": context
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to retrieve booking context: {str(e)}"
        }

async def execute_booking_from_context(
    session_id: str,
    confirmed_datetime: str,
    user_confirmation: str
) -> Dict[str, Any]:
    """
    Execute booking using stored context when user confirms appointment.
    
    FIXED: Now uses the current preferred date, not the original request.
    """
    try:
        # Check if this looks like a booking confirmation
        confirmation_patterns = [
            r'\b(yes|yeah|yep|sure|ok|okay|confirm|book|schedule)\b',
            r'\b(\d{1,2}):?(\d{2})?\s*(am|pm|p\.?m\.?|a\.?m\.?)\b',
            r'\b(afternoon|morning|evening)\b',
            r'\b(that works|sounds good|perfect|great|done)\b',
            r'\b(that\'?s fine|that\'?s good|fine)\b'  # NEW: Handle alternative acceptance
        ]
        
        is_confirmation = any(re.search(pattern, user_confirmation.lower()) for pattern in confirmation_patterns)
        
        if not is_confirmation:
            return {
                "status": "info",
                "not_confirmation": True,
                "message": "This doesn't appear to be a booking confirmation"
            }
        
        # Get booking context
        if session_id not in _booking_contexts:
            return {
                "status": "error",
                "error_message": "No booking context found. Please start the booking process again."
            }
        
        context = _booking_contexts[session_id]
        
        # CRITICAL FIX: Use current preferred date, not last checked
        final_datetime = confirmed_datetime
        
        # If user is accepting an alternative date, use the current preferred date
        if context.get("current_preferred_date") and context.get("current_preferred_date") != context.get("original_requested_date"):
            print(f"🔄 Using alternative date: {context['current_preferred_date']} instead of original: {context.get('original_requested_date')}")
            # Parse the preferred date and combine with time from confirmed_datetime
            try:
                preferred_date = datetime.fromisoformat(context["current_preferred_date"]).date()
                if 'T' in confirmed_datetime:
                    confirmed_time = datetime.fromisoformat(confirmed_datetime).time()
                else:
                    confirmed_time = datetime.strptime(confirmed_datetime, "%Y-%m-%d %H:%M:%S").time()
                
                final_datetime = datetime.combine(preferred_date, confirmed_time).isoformat()
                print(f"📅 Final booking datetime: {final_datetime}")
            except Exception as dt_error:
                print(f"⚠️ Date combination error: {dt_error}, using original: {confirmed_datetime}")
        
        # Import the book_appointment function
        from app.tools.scheduling import book_appointment
        
        # Execute the booking with the correct datetime
        booking_result = await book_appointment(
            customer_id=context["customer_id"],
            property_id=context["property_id"],
            service_type=context["service_type"],
            problem_description=context["problem_description"],
            scheduled_datetime=final_datetime,  # FIXED: Use final_datetime
            technician_id=context.get("preferred_technician_id", "TECH001"),
            urgency=context["urgency"]
        )
        
        # Clear the context after successful booking
        if booking_result.get("status") == "success":
            del _booking_contexts[session_id]
            print(f"🧹 Cleared booking context for session {session_id}")
        
        return booking_result
        
    except Exception as e:
        print(f"❌ Error executing booking from context: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Failed to execute booking: {str(e)}"
        }

async def clear_booking_context(session_id: str) -> Dict[str, Any]:
    """Clear booking context for a session."""
    try:
        if session_id in _booking_contexts:
            del _booking_contexts[session_id]
            print(f"🧹 Cleared booking context for session {session_id}")
        
        return {
            "status": "success",
            "context_cleared": True,
            "message": "Booking context cleared"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to clear booking context: {str(e)}"
        }

async def detect_booking_confirmation(user_message: str) -> Dict[str, Any]:
    """
    Detect if user message is a booking confirmation and extract time if present.
    
    ENHANCED: Better detection for alternative date acceptance.
    """
    try:
        message_lower = user_message.lower().strip()
        
        # Enhanced confirmation patterns
        confirmation_keywords = [
            "yes", "yeah", "yep", "sure", "ok", "okay", "confirm", "book", 
            "schedule", "that works", "sounds good", "perfect", "great", 
            "done", "let's do it", "go ahead", "that's fine", "that's good",
            "fine", "alright", "works for me"  # NEW: Better alternative acceptance
        ]
        
        # Time patterns
        time_patterns = [
            r'\b(\d{1,2}):?(\d{2})?\s*(am|pm|p\.?m\.?|a\.?m\.?)\b',  # 2 PM, 14:30
            r'\b(\d{1,2})\s*(am|pm|p\.?m\.?|a\.?m\.?)\b',  # 2 PM
            r'\b(morning|afternoon|evening)\b',  # time of day
            r'\b(\d{1,2}):\d{2}\b'  # 24-hour format
        ]
        
        # Check for confirmation keywords
        has_confirmation = any(keyword in message_lower for keyword in confirmation_keywords)
        
        # Extract time if present
        extracted_time = None
        for pattern in time_patterns:
            match = re.search(pattern, message_lower)
            if match:
                extracted_time = match.group(0)
                break
        
        # Check for specific time mentions
        if re.search(r'\b(\d{1,2})\s*(pm|p\.?m\.?)\b', message_lower):
            time_match = re.search(r'\b(\d{1,2})\s*(pm|p\.?m\.?)\b', message_lower)
            if time_match:
                hour = int(time_match.group(1))
                if hour != 12:
                    hour += 12
                extracted_time = f"{hour:02d}:00"
        
        return {
            "status": "success",
            "is_confirmation": has_confirmation,
            "extracted_time": extracted_time,
            "original_message": user_message,
            "confidence": "high" if has_confirmation and extracted_time else "medium" if has_confirmation else "low"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error detecting confirmation: {str(e)}"
        }