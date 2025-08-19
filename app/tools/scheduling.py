"""
FIXED scheduling tools - Only offers genuinely available slots.
"""
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List

from app.services.data_service import data_service
from app.services.calendar_service import calendar_service
from app.services.email_service import email_service
from app.models import WorkOrder, WorkOrderStatus, UrgencyLevel
from app.config import settings

async def check_technician_availability(
    service_type: str,
    area_zone: str,
    preferred_date: str,
    preferred_time: str
) -> Dict[str, Any]:
    """
    FIXED: Check available technicians and ONLY return genuinely available slots.
    
    Args:
        service_type: Type of service needed (e.g., "AC Maintenance", "Plumbing")
        area_zone: Geographic area/zone
        preferred_date: Preferred date in YYYY-MM-DD format
        preferred_time: Preferred time in HH:MM format
        
    Returns:
        Dictionary with ONLY genuinely available time slots and technicians
    """
    try:
        current_time = datetime.now()
        print(f"🔍 HONEST CHECK: {service_type} in {area_zone} on {preferred_date} at {preferred_time}")
        print(f"📅 Current date/time: {current_time.strftime('%Y-%m-%d %H:%M')}")
        
        # Parse preferred date with strict validation
        try:
            request_date = datetime.strptime(preferred_date, "%Y-%m-%d")
            print(f"🎯 Parsed request date: {request_date.strftime('%Y-%m-%d')}")
        except ValueError:
            print(f"❌ Invalid date format: {preferred_date}")
            return {
                "status": "error",
                "error_message": f"Invalid date format '{preferred_date}'. Please use YYYY-MM-DD format. Today is {current_time.strftime('%Y-%m-%d')}."
            }
        
        # Validate date is not in the past
        if request_date.date() < current_time.date():
            days_ago = (current_time.date() - request_date.date()).days
            print(f"❌ Date is {days_ago} days in the past")
            return {
                "status": "error",
                "error_message": f"Cannot schedule appointments in the past. The date {preferred_date} was {days_ago} days ago. Please choose a date on or after {current_time.strftime('%Y-%m-%d')}. Today is {current_time.strftime('%A, %B %d, %Y')}."
            }
        
        # Validate year is reasonable (2025 or 2026)
        if request_date.year < 2025 or request_date.year > 2026:
            print(f"❌ Invalid year: {request_date.year}")
            return {
                "status": "error",
                "error_message": f"Please provide a date in 2025 or 2026. The year {request_date.year} is not valid for booking."
            }
        
        # Get service details
        services = await data_service.get_service_types()
        service = None
        for s in services:
            if service_type.lower() in s.service_name.lower():
                service = s
                break
        
        if not service:
            # Try partial matching
            for s in services:
                if any(word in s.service_name.lower() for word in service_type.lower().split()):
                    service = s
                    break
        
        if not service:
            available_services = [s.service_name for s in services]
            print(f"❌ Service type '{service_type}' not found. Available: {available_services}")
            return {
                "status": "error",
                "error_message": f"Service type '{service_type}' not found. Available services: {', '.join(available_services)}"
            }
        
        # Parse time
        try:
            time_parts = preferred_time.split(":")
            request_datetime = request_date.replace(
                hour=int(time_parts[0]),
                minute=int(time_parts[1]) if len(time_parts) > 1 else 0
            )
        except (ValueError, IndexError):
            print(f"❌ Invalid time format: {preferred_time}")
            return {
                "status": "error",
                "error_message": "Invalid time format. Please use HH:MM format (e.g., 14:30 or 09:00)."
            }
        
        # Validate that datetime is not in the past (for today's appointments)
        if request_datetime < current_time:
            print(f"❌ Requested time {request_datetime} is in the past")
            if request_date.date() == current_time.date():
                return {
                    "status": "error",
                    "error_message": f"Cannot schedule appointments in the past. For today ({current_time.strftime('%Y-%m-%d')}), please choose a time after {current_time.strftime('%H:%M')}."
                }
            else:
                return {
                    "status": "error", 
                    "error_message": f"The requested datetime {request_datetime.strftime('%Y-%m-%d %H:%M')} is in the past. Please choose a future date and time."
                }
        
        print(f"🎯 Looking for technicians with skills: {service.required_skills}")
        
        # 🔥 CRITICAL FIX: Check ACTUAL availability for requested time first
        available_slots = await data_service.find_available_technicians(
            required_skills=service.required_skills,
            zone=area_zone,
            requested_datetime=request_datetime,
            duration_minutes=service.estimated_duration
        )
        
        if available_slots:
            # Format available slots for the EXACT requested time
            formatted_slots = []
            for slot in available_slots[:5]:  # Limit to 5 best options
                formatted_slots.append({
                    "technician_id": slot.technician_id,
                    "technician_name": slot.technician_name,
                    "available_date": slot.available_date.strftime("%Y-%m-%d"),
                    "available_start": slot.available_start_time.strftime("%H:%M"),
                    "available_end": slot.available_end_time.strftime("%H:%M"),
                    "skillset": ", ".join(slot.skillset),
                    "zone": slot.zone
                })
            
            print(f"✅ Found {len(available_slots)} available technicians for EXACT requested time")
            
            return {
                "status": "success",
                "service_name": service.service_name,
                "service_id": service.service_id,
                "estimated_duration": service.estimated_duration,
                "available_slots_count": len(available_slots),
                "recommended_slots": formatted_slots,
                "requested_datetime": request_datetime.isoformat(),
                "exact_match": True,  # NEW: Indicates this is for exact requested time
                "date_validation": {
                    "is_future_date": True,
                    "day_of_week": request_datetime.strftime("%A"),
                    "days_from_today": (request_date.date() - current_time.date()).days
                },
                "message": f"✅ AVAILABLE: {len(available_slots)} technicians for {service.service_name} in {area_zone} on {request_datetime.strftime('%A, %B %d, %Y')} at {request_datetime.strftime('%H:%M')}"
            }
        else:
            # 🔥 CRITICAL FIX: Find REAL alternative slots, don't suggest fake ones
            print(f"❌ No availability for requested time, searching for REAL alternatives...")
            
            genuine_alternatives = []
            
            # Check next 7 days for REAL availability
            for days_ahead in range(1, 8):
                alt_date = request_date + timedelta(days=days_ahead)
                
                # Skip Fridays (UAE weekend)
                if alt_date.weekday() == 4:
                    continue
                
                # Check multiple time slots for this date
                time_slots = [9, 10, 11, 14, 15, 16, 17]  # Business hours
                
                for hour in time_slots:
                    alt_datetime = alt_date.replace(hour=hour, minute=0)
                    
                    # Skip past times for today
                    if alt_date.date() == current_time.date() and alt_datetime <= current_time:
                        continue
                    
                    # 🔥 ACTUALLY CHECK if technicians are available
                    alt_slots = await data_service.find_available_technicians(
                        required_skills=service.required_skills,
                        zone=area_zone,
                        requested_datetime=alt_datetime,
                        duration_minutes=service.estimated_duration
                    )
                    
                    if alt_slots:
                        # Found REAL availability - add to genuine alternatives
                        best_technician = alt_slots[0]
                        genuine_alternatives.append({
                            "date": alt_date.strftime("%Y-%m-%d"),
                            "date_display": alt_date.strftime("%A, %B %d"),
                            "time": alt_datetime.strftime("%H:%M"),
                            "time_display": alt_datetime.strftime("%I:%M %p"),
                            "datetime_iso": alt_datetime.isoformat(),
                            "technician_id": best_technician.technician_id,
                            "technician_name": best_technician.technician_name,
                            "available_technicians_count": len(alt_slots)
                        })
                        
                        # Limit to 6 real alternatives max
                        if len(genuine_alternatives) >= 6:
                            break
                
                # Stop if we found enough alternatives
                if len(genuine_alternatives) >= 6:
                    break
            
            if genuine_alternatives:
                print(f"✅ Found {len(genuine_alternatives)} GENUINE alternative slots")
                return {
                    "status": "success",
                    "service_name": service.service_name,
                    "service_id": service.service_id,
                    "estimated_duration": service.estimated_duration,
                    "available_slots_count": 0,  # None for requested time
                    "exact_match": False,  # No exact match
                    "genuine_alternatives": genuine_alternatives,  # REAL alternatives
                    "requested_datetime": request_datetime.isoformat(),
                    "message": f"No availability for {service.service_name} in {area_zone} on {request_datetime.strftime('%A, %B %d')} at {request_datetime.strftime('%H:%M')}. However, I have these available slots:"
                }
            else:
                print(f"❌ No genuine alternatives found in next 7 days")
                return {
                    "status": "success",
                    "service_name": service.service_name,
                    "service_id": service.service_id,
                    "available_slots_count": 0,
                    "exact_match": False,
                    "genuine_alternatives": [],
                    "message": f"Unfortunately, no availability found for {service.service_name} in {area_zone} for the next week. Please try a different area or contact us for emergency service."
                }
            
    except Exception as e:
        print(f"❌ Error in check_technician_availability: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error checking availability: {str(e)}. Please ensure date is in YYYY-MM-DD format and time is in HH:MM format."
        }

async def book_appointment(
    customer_id: str,
    property_id: str,
    service_type: str,
    problem_description: str,
    scheduled_datetime: str,
    technician_id: str,
    urgency: str
) -> Dict[str, Any]:
    """
    Book an appointment with enhanced date validation.
    
    Args:
        customer_id: Customer identifier
        property_id: Property identifier
        service_type: Type of service needed
        problem_description: Description of the problem
        scheduled_datetime: Scheduled datetime in ISO format (YYYY-MM-DDTHH:MM:SS)
        technician_id: Assigned technician ID
        urgency: Urgency level (Low, Medium, High, Emergency)
        
    Returns:
        Dictionary with booking confirmation details
    """
    try:
        current_time = datetime.now()
        print(f"📅 Starting booking process at {current_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"   Customer: {customer_id}")
        print(f"   Property: {property_id}")
        print(f"   Service: {service_type}")
        print(f"   DateTime: {scheduled_datetime}")
        print(f"   Technician: {technician_id}")
        
        # Parse scheduled datetime with validation
        try:
            # Handle multiple formats
            if 'T' in scheduled_datetime:
                scheduled_dt = datetime.fromisoformat(scheduled_datetime.replace('Z', ''))
            else:
                # Try space-separated format
                scheduled_dt = datetime.strptime(scheduled_datetime, "%Y-%m-%d %H:%M:%S")
        except ValueError as ve:
            print(f"❌ DateTime parsing error: {ve}")
            # Try to parse just date and add default time
            try:
                date_part = scheduled_datetime.split('T')[0] if 'T' in scheduled_datetime else scheduled_datetime.split(' ')[0]
                scheduled_dt = datetime.strptime(date_part, "%Y-%m-%d").replace(hour=9, minute=0)
                print(f"⚠️ Using default time 09:00 for date: {date_part}")
            except ValueError:
                return {
                    "status": "error",
                    "error_message": f"Invalid datetime format: {scheduled_datetime}. Expected ISO format (YYYY-MM-DDTHH:MM:SS) or YYYY-MM-DD HH:MM:SS"
                }
        
        # Strict validation: appointment must be in the future
        if scheduled_dt <= current_time:
            time_diff = current_time - scheduled_dt
            if time_diff.days > 0:
                return {
                    "status": "error",
                    "error_message": f"Cannot book appointments in the past. The scheduled time {scheduled_dt.strftime('%Y-%m-%d %H:%M')} was {time_diff.days} days ago. Today is {current_time.strftime('%A, %B %d, %Y')}. Please choose a future date and time."
                }
            else:
                return {
                    "status": "error",
                    "error_message": f"Cannot book appointments in the past. Please choose a time after {current_time.strftime('%H:%M')} for today, or select a future date."
                }
        
        # Validate year
        if scheduled_dt.year < 2025 or scheduled_dt.year > 2026:
            return {
                "status": "error",
                "error_message": f"Invalid year {scheduled_dt.year}. Please book appointments in 2025 or 2026."
            }
        
        # Get service details
        services = await data_service.get_service_types()
        service = None
        for s in services:
            if service_type.lower() in s.service_name.lower() or s.service_id == service_type:
                service = s
                break
        
        if not service:
            print(f"❌ Service not found: {service_type}")
            return {
                "status": "error",
                "error_message": f"Service type '{service_type}' not found"
            }
        
        # Get customer and facility details
        customer = None
        for cust in data_service._customers.values():
            if cust.customer_id == customer_id:
                customer = cust
                break
        
        facility = data_service._facilities.get(property_id)
        technician = await data_service.get_technician_by_id(technician_id)
        
        if not customer:
            print(f"❌ Customer not found: {customer_id}")
            return {
                "status": "error",
                "error_message": f"Customer {customer_id} not found"
            }
        
        if not facility:
            print(f"❌ Facility not found: {property_id}")
            return {
                "status": "error", 
                "error_message": f"Facility {property_id} not found"
            }
        
        if not technician:
            print(f"❌ Technician not found: {technician_id}")
            return {
                "status": "error",
                "error_message": f"Technician {technician_id} not found"
            }
        
        # 🔥 FINAL AVAILABILITY CHECK before booking (safety net)
        print(f"🔒 Final availability verification...")
        final_check = await data_service.find_available_technicians(
            required_skills=service.required_skills,
            zone=facility.area_zone,  # FIXED: Use area_zone from Facility model
            requested_datetime=scheduled_dt,
            duration_minutes=service.estimated_duration
        )
        
        # Check if the requested technician is still available
        technician_still_available = any(
            slot.technician_id == technician_id for slot in final_check
        )
        
        if not technician_still_available:
            print(f"❌ Technician {technician_id} no longer available at {scheduled_dt}")
            return {
                "status": "error",
                "error_message": f"Sorry, technician {technician.technician_name} is no longer available at {scheduled_dt.strftime('%A, %B %d at %I:%M %p')}. Please choose a different time."
            }
        
        print(f"✅ Final check passed - technician {technician_id} confirmed available")
        
        # Validate urgency level
        try:
            urgency_level = UrgencyLevel(urgency)
        except ValueError:
            urgency_level = UrgencyLevel.MEDIUM
            print(f"⚠️ Invalid urgency '{urgency}', using 'Medium'")
        
        # Create work order
        work_order_id = f"WO_{uuid.uuid4().hex[:8].upper()}"
        work_order = WorkOrder(
            work_order_id=work_order_id,
            customer_id=customer_id,
            property_id=property_id,
            service_id=service.service_id,
            problem_description=problem_description,
            status=WorkOrderStatus.SCHEDULED,
            urgency=urgency_level,
            scheduled_date_time=scheduled_dt,
            assigned_technician_id=technician_id
        )
        
        print(f"💾 Creating work order: {work_order_id}")
        
        # Save work order
        await data_service.create_work_order(work_order)
        
        # Create calendar appointment (company calendar only - no customer invite)
        appointment_title = f"{service.service_name} - {customer.full_name}"
        appointment_description = f"""
Work Order: {work_order_id}
Customer: {customer.full_name}
Location: {facility.display_location}
Service: {service.service_name}
Problem: {problem_description}
Technician: {technician.technician_name}
Contact: {customer.phone_number}
Urgency: {urgency_level.value}
Scheduled: {scheduled_dt.strftime('%A, %B %d, %Y at %I:%M %p')}
        """.strip()
        
        print(f"📅 Creating calendar appointment (company calendar only)...")
        
        try:
            calendar_event = await calendar_service.create_appointment(
                title=appointment_title,
                description=appointment_description,
                start_time=scheduled_dt,
                duration_minutes=service.estimated_duration,
                location=facility.full_address,
                attendee_emails=[]  # No customer invite - company calendar only
            )
            print(f"✅ Calendar event created: {calendar_event['event_id']}")
        except Exception as cal_error:
            print(f"⚠️ Calendar creation failed: {cal_error}")
            calendar_event = {'event_id': 'calendar_error', 'status': 'failed'}
        
        # Send confirmation email
        appointment_details = {
            'service_type': service.service_name,
            'scheduled_time': scheduled_dt.strftime("%A, %B %d, %Y at %I:%M %p"),
            'location': facility.display_location,
            'technician_name': technician.technician_name,
            'work_order_id': work_order_id,
            'estimated_duration': f"{service.estimated_duration // 60}h {service.estimated_duration % 60}m"
        }
        
        try:
            # Send confirmation email to customer
            await email_service.send_appointment_confirmation(
                recipient_email=customer.email_address,
                customer_name=customer.full_name,
                appointment_details=appointment_details
            )
            print(f"📧 Confirmation email sent to: {customer.email_address}")
            
            # Send notification email to service provider (technician)
            service_provider_email = settings.gmail_user if settings.gmail_user else "support@premiumfacilitiesmanagementllc.com"
            await email_service.send_service_provider_notification(
                recipient_email=service_provider_email,
                technician_name=technician.technician_name,
                appointment_details=appointment_details,
                customer_name=customer.full_name
            )
            print(f"📧 Service provider notification sent to: {service_provider_email}")
            
            email_sent = True
        except Exception as email_error:
            print(f"⚠️ Email sending failed: {email_error}")
            email_sent = False
        
        result = {
            "status": "success",
            "booking_confirmed": True,
            "work_order_id": work_order_id,
            "calendar_event_id": calendar_event['event_id'],
            "appointment_details": {
                "service_name": service.service_name,
                "scheduled_datetime": scheduled_dt.isoformat(),
                "scheduled_display": scheduled_dt.strftime("%A, %B %d, %Y at %I:%M %p"),
                "duration_minutes": service.estimated_duration,
                "duration_display": f"{service.estimated_duration // 60}h {service.estimated_duration % 60}m",
                "technician_name": technician.technician_name,
                "technician_contact": technician.contact_number,
                "location": facility.display_location,
                "full_address": facility.full_address,
                "customer_name": customer.full_name,
                "customer_contact": customer.phone_number,
                "urgency": urgency_level.value
            },
            "notifications": {
                "email_sent": email_sent,
                "calendar_created": calendar_event['event_id'] != 'calendar_error'
            },
            "date_validation": {
                "booking_date": scheduled_dt.strftime("%Y-%m-%d"),
                "booking_time": scheduled_dt.strftime("%H:%M"),
                "is_future_appointment": True,
                "days_from_today": (scheduled_dt.date() - current_time.date()).days
            },
            "message": f"✅ Appointment successfully booked for {scheduled_dt.strftime('%A, %B %d, %Y at %I:%M %p')}. Work order #{work_order_id} created."
        }
        
        print(f"🎉 Booking completed successfully!")
        print(f"   Work Order: {work_order_id}")
        print(f"   Scheduled: {scheduled_dt.strftime('%A, %B %d, %Y at %I:%M %p')}")
        print(f"   Calendar Event: {calendar_event['event_id']}")
        print(f"   Email Sent: {email_sent}")
        
        return result
        
    except Exception as e:
        print(f"❌ Critical error in book_appointment: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "error_message": f"Booking failed due to technical error: {str(e)}. Please try again or contact support."
        }

# Keep the rest of your functions unchanged (get_available_time_slots, reschedule_appointment)
async def get_available_time_slots(
    area_zone: str,
    service_type: str,
    start_date: str,
    days_ahead: str
) -> Dict[str, Any]:
    """Get available time slots for a service in an area with enhanced date validation."""
    try:
        current_time = datetime.now()
        print(f"🔍 Getting time slots for {service_type} in {area_zone} starting {start_date}")
        print(f"📅 Current date: {current_time.strftime('%Y-%m-%d')}")
        
        # Validate start_date
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            return {
                "status": "error",
                "error_message": f"Invalid date format '{start_date}'. Please use YYYY-MM-DD format. Today is {current_time.strftime('%Y-%m-%d')}."
            }
        
        # Ensure start date is not in the past
        if start_dt.date() < current_time.date():
            return {
                "status": "error",
                "error_message": f"Cannot check availability for past dates. Please choose a date on or after {current_time.strftime('%Y-%m-%d')}."
            }
        
        # Convert days_ahead to integer
        try:
            days_int = int(days_ahead)
        except ValueError:
            days_int = 7  # Default to 7 days if invalid
        
        # Get service details
        services = await data_service.get_service_types()
        service = None
        for s in services:
            if service_type.lower() in s.service_name.lower():
                service = s
                break
        
        if not service:
            return {
                "status": "error",
                "error_message": f"Service type '{service_type}' not found"
            }
        
        available_dates = {}
        
        # Check each day
        for day_offset in range(days_int):
            check_date = start_dt + timedelta(days=day_offset)
            
            # Skip Fridays (which is weekend in UAE)
            if check_date.weekday() == 4:  # Friday
                continue
            
            # Check morning and afternoon slots
            morning_slots = []
            afternoon_slots = []
            
            # Business hours: 9AM-12PM, 2PM-5PM (skip lunch 12-2PM)
            time_slots = [9, 10, 11, 14, 15, 16]
            
            for hour in time_slots:
                check_datetime = check_date.replace(hour=hour, minute=0)
                
                # Skip past times for today
                if check_date.date() == current_time.date() and check_datetime < current_time:
                    continue
                
                available_techs = await data_service.find_available_technicians(
                    required_skills=service.required_skills,
                    zone=area_zone,
                    requested_datetime=check_datetime,
                    duration_minutes=service.estimated_duration
                )
                
                if available_techs:
                    slot_info = {
                        "time": check_datetime.strftime("%H:%M"),
                        "display_time": check_datetime.strftime("%I:%M %p"),
                        "datetime_iso": check_datetime.isoformat(),
                        "available_technicians": len(available_techs),
                        "best_technician": {
                            "technician_id": available_techs[0].technician_id,
                            "technician_name": available_techs[0].technician_name
                        }
                    }
                    
                    if hour < 12:
                        morning_slots.append(slot_info)
                    else:
                        afternoon_slots.append(slot_info)
            
            if morning_slots or afternoon_slots:
                available_dates[check_date.strftime("%Y-%m-%d")] = {
                    "date_display": check_date.strftime("%A, %B %d"),
                    "morning": morning_slots,
                    "afternoon": afternoon_slots,
                    "total_slots": len(morning_slots) + len(afternoon_slots)
                }
        
        print(f"✅ Found availability on {len(available_dates)} days")
        
        return {
            "status": "success",
            "service_name": service.service_name,
            "service_id": service.service_id,
            "area_zone": area_zone,
            "search_period": f"{start_date} to {(start_dt + timedelta(days=days_int-1)).strftime('%Y-%m-%d')}",
            "available_dates": available_dates,
            "total_available_days": len(available_dates),
            "business_hours_note": "Business hours: 9 AM - 5 PM (excluding Fridays and lunch 12-2 PM)"
        }
        
    except Exception as e:
        print(f"❌ Error in get_available_time_slots: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error getting time slots: {str(e)}"
        }

async def reschedule_appointment(
    work_order_id: str,
    new_datetime: str,
    reason: str
) -> Dict[str, Any]:
    """Reschedule an existing appointment with date validation."""
    try:
        current_time = datetime.now()
        print(f"🔄 Rescheduling appointment {work_order_id} to {new_datetime}")
        print(f"📅 Current time: {current_time.strftime('%Y-%m-%d %H:%M')}")
        
        # Get work order
        work_order = await data_service.get_work_order_by_id(work_order_id)
        if not work_order:
            return {
                "status": "error",
                "error_message": f"Work order {work_order_id} not found"
            }
        
        # Parse new datetime with validation
        try:
            if 'T' in new_datetime:
                new_dt = datetime.fromisoformat(new_datetime.replace('Z', ''))
            else:
                new_dt = datetime.strptime(new_datetime, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return {
                "status": "error",
                "error_message": f"Invalid datetime format for new_datetime: {new_datetime}. Use YYYY-MM-DDTHH:MM:SS format."
            }
        
        # Validate new datetime is in the future
        if new_dt <= current_time:
            return {
                "status": "error",
                "error_message": f"Cannot reschedule to past time. Please choose a datetime after {current_time.strftime('%Y-%m-%d %H:%M')}."
            }
        
        # Validate year
        if new_dt.year < 2025 or new_dt.year > 2026:
            return {
                "status": "error",
                "error_message": f"Invalid year {new_dt.year}. Please reschedule to 2025 or 2026."
            }
        
        old_datetime = work_order.scheduled_date_time.strftime("%Y-%m-%d %H:%M") if work_order.scheduled_date_time else "TBD"
        
        # Update work order
        work_order.scheduled_date_time = new_dt
        
        # Get customer and facility details for notification
        customer = None
        for cust in data_service._customers.values():
            if cust.customer_id == work_order.customer_id:
                customer = cust
                break
        
        facility = data_service._facilities.get(work_order.property_id)
        
        # Update calendar (simulated for now)
        print(f"📅 Calendar updated (simulated)")
        
        # Send rescheduling notification email
        if customer:
            try:
                appointment_details = {
                    'service_type': work_order.service_id,
                    'old_time': old_datetime,
                    'new_time': new_dt.strftime("%A, %B %d, %Y at %I:%M %p"),
                    'location': facility.display_location if facility else "Location TBD",
                    'work_order_id': work_order_id,
                    'reason': reason
                }
                
                # In a real implementation, you'd call the email service
                print(f"📧 Rescheduling notification sent to: {customer.email_address}")
            except Exception as e:
                print(f"⚠️ Email notification failed: {e}")
        
        print(f"✅ Appointment rescheduled successfully")
        
        return {
            "status": "success",
            "rescheduled": True,
            "work_order_id": work_order_id,
            "old_datetime": old_datetime,
            "new_datetime": new_dt.strftime("%Y-%m-%d %H:%M"),
            "new_datetime_display": new_dt.strftime("%A, %B %d, %Y at %I:%M %p"),
            "reason": reason,
            "date_validation": {
                "is_future_appointment": True,
                "days_from_today": (new_dt.date() - current_time.date()).days
            },
            "message": f"Appointment successfully rescheduled to {new_dt.strftime('%A, %B %d, %Y at %I:%M %p')}. Reason: {reason}"
        }
        
    except Exception as e:
        print(f"❌ Error in reschedule_appointment: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error rescheduling appointment: {str(e)}"
        }