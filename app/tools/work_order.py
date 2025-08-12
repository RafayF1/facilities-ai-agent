"""
Work order management tools for checking status and history.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.services.data_service import data_service
from app.services.email_service import email_service

async def get_work_order_status(work_order_id: str) -> Dict[str, Any]:
    """
    Get the current status of a work order.
    
    Args:
        work_order_id: Work order identifier
        
    Returns:
        Dictionary with work order status information
    """
    try:
        work_order = await data_service.get_work_order_by_id(work_order_id)
        
        if not work_order:
            return {
                "status": "error",
                "error_message": f"Work order {work_order_id} not found. Please verify the work order number."
            }
        
        # Get related information
        technician = None
        if work_order.assigned_technician_id:
            technician = await data_service.get_technician_by_id(work_order.assigned_technician_id)
        
        facility = data_service._facilities.get(work_order.property_id)
        customer = None
        for cust in data_service._customers.values():
            if cust.customer_id == work_order.customer_id:
                customer = cust
                break
        
        # Calculate status details
        status_details = {
            "work_order_id": work_order.work_order_id,
            "current_status": work_order.status.value,
            "urgency": work_order.urgency.value,
            "problem_description": work_order.problem_description,
            "request_date": work_order.request_date_time.strftime("%Y-%m-%d %H:%M"),
            "customer_name": customer.full_name if customer else "Unknown",
            "location": facility.display_location if facility else "Unknown location",
            "is_active": work_order.is_active(),
            "is_emergency": work_order.is_emergency()
        }
        
        # Add scheduling information
        if work_order.scheduled_date_time:
            status_details["scheduled_date"] = work_order.scheduled_date_time.strftime("%Y-%m-%d %H:%M")
            
            # Calculate time until appointment
            now = datetime.now()
            if work_order.scheduled_date_time > now:
                time_diff = work_order.scheduled_date_time - now
                if time_diff.days > 0:
                    status_details["time_until_appointment"] = f"{time_diff.days} days"
                elif time_diff.seconds > 3600:
                    hours = time_diff.seconds // 3600
                    status_details["time_until_appointment"] = f"{hours} hours"
                else:
                    minutes = time_diff.seconds // 60
                    status_details["time_until_appointment"] = f"{minutes} minutes"
            else:
                status_details["appointment_status"] = "Overdue"
        
        # Add technician information
        if technician:
            status_details["assigned_technician"] = {
                "name": technician.technician_name,
                "contact": technician.contact_number,
                "skillset": technician.skillset
            }
        
        # Add completion information
        if work_order.completion_date_time:
            status_details["completion_date"] = work_order.completion_date_time.strftime("%Y-%m-%d %H:%M")
            status_details["completion_notes"] = work_order.completion_notes
        
        # Status-specific messages
        status_messages = {
            "New": "Your request has been received and is being processed.",
            "Scheduled": f"Your service appointment is scheduled for {status_details.get('scheduled_date', 'TBD')}.",
            "Assigned": f"A technician ({technician.technician_name if technician else 'TBD'}) has been assigned to your request.",
            "Dispatched": "The technician is on their way to your location.",
            "In Progress": "The technician is currently working on your service request.",
            "On Hold": "Your service request is temporarily on hold. We will contact you with updates.",
            "Completed": "Your service request has been completed successfully.",
            "Cancelled": "Your service request has been cancelled."
        }
        
        status_details["status_message"] = status_messages.get(work_order.status.value, "Status unknown")
        
        return {
            "status": "success",
            "work_order_found": True,
            "work_order_details": status_details
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error retrieving work order status: {str(e)}"
        }

async def search_work_orders_by_customer(
    customer_id: Optional[str],
    phone_number: Optional[str],
    building_name: Optional[str],
    active_only: bool
) -> Dict[str, Any]:
    """
    Search work orders by customer information.
    
    Args:
        customer_id: Customer identifier
        phone_number: Customer phone number
        building_name: Building name for location-based search
        active_only: Whether to return only active work orders
        
    Returns:
        Dictionary with matching work orders
    """
    try:
        work_orders = []
        
        if customer_id:
            work_orders = await data_service.get_customer_work_orders(customer_id, active_only)
        elif phone_number:
            # Find customer by phone first
            customer = await data_service.find_customer_by_phone(phone_number)
            if customer:
                work_orders = await data_service.get_customer_work_orders(customer.customer_id, active_only)
            else:
                return {
                    "status": "success",
                    "work_orders_found": 0,
                    "message": f"No customer found with phone number {phone_number}"
                }
        elif building_name:
            # Find facilities by building name and get work orders for those properties
            matching_facilities = []
            for facility in data_service._facilities.values():
                if building_name.lower() in facility.building_name.lower():
                    matching_facilities.append(facility)
            
            if matching_facilities:
                all_work_orders = []
                for facility in matching_facilities:
                    customer_orders = await data_service.get_customer_work_orders(facility.customer_id, active_only)
                    # Filter by property
                    property_orders = [wo for wo in customer_orders if wo.property_id == facility.property_id]
                    all_work_orders.extend(property_orders)
                work_orders = all_work_orders
            else:
                return {
                    "status": "success",
                    "work_orders_found": 0,
                    "message": f"No facilities found matching building name '{building_name}'"
                }
        else:
            return {
                "status": "error",
                "error_message": "At least one search parameter (customer_id, phone_number, or building_name) is required"
            }
        
        if work_orders:
            # Format work orders for response
            formatted_orders = []
            for wo in work_orders[:10]:  # Limit to 10 most recent
                # Get facility details
                facility = data_service._facilities.get(wo.property_id)
                
                order_info = {
                    "work_order_id": wo.work_order_id,
                    "status": wo.status.value,
                    "urgency": wo.urgency.value,
                    "problem_description": wo.problem_description[:100] + "..." if len(wo.problem_description) > 100 else wo.problem_description,
                    "request_date": wo.request_date_time.strftime("%Y-%m-%d %H:%M"),
                    "location": facility.display_location if facility else "Unknown",
                    "is_active": wo.is_active(),
                    "is_emergency": wo.is_emergency()
                }
                
                if wo.scheduled_date_time:
                    order_info["scheduled_date"] = wo.scheduled_date_time.strftime("%Y-%m-%d %H:%M")
                
                if wo.completion_date_time:
                    order_info["completion_date"] = wo.completion_date_time.strftime("%Y-%m-%d %H:%M")
                
                formatted_orders.append(order_info)
            
            return {
                "status": "success",
                "work_orders_found": len(work_orders),
                "showing_orders": len(formatted_orders),
                "active_only": active_only,
                "work_orders": formatted_orders
            }
        else:
            return {
                "status": "success",
                "work_orders_found": 0,
                "message": "No work orders found matching the search criteria"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error searching work orders: {str(e)}"
        }

async def update_work_order_status(
    work_order_id: str,
    new_status: str,
    notes: Optional[str],
    notify_customer: bool
) -> Dict[str, Any]:
    """
    Update the status of a work order.
    
    Args:
        work_order_id: Work order identifier
        new_status: New status value
        notes: Optional notes about the status change
        notify_customer: Whether to send email notification
        
    Returns:
        Dictionary with update confirmation
    """
    try:
        work_order = await data_service.get_work_order_by_id(work_order_id)
        
        if not work_order:
            return {
                "status": "error",
                "error_message": f"Work order {work_order_id} not found"
            }
        
        old_status = work_order.status.value
        
        # Update status (this would typically update the database)
        # For PoC, we'll simulate the update
        if new_status.lower() == "completed":
            work_order.completion_date_time = datetime.now()
            if notes:
                work_order.completion_notes = notes
        
        # Send customer notification if requested
        if notify_customer:
            # Get customer details
            customer = None
            for cust in data_service._customers.values():
                if cust.customer_id == work_order.customer_id:
                    customer = cust
                    break
            
            if customer:
                # Get facility details
                facility = data_service._facilities.get(work_order.property_id)
                
                work_order_details = {
                    'work_order_id': work_order_id,
                    'service_type': work_order.service_id,
                    'status': new_status,
                    'location': facility.display_location if facility else "Unknown",
                    'completion_notes': notes
                }
                
                if new_status.lower() == "completed":
                    work_order_details['completion_time'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                await email_service.send_work_order_status_update(
                    recipient_email=customer.email_address,
                    customer_name=customer.full_name,
                    work_order_details=work_order_details
                )
        
        return {
            "status": "success",
            "work_order_id": work_order_id,
            "status_updated": True,
            "old_status": old_status,
            "new_status": new_status,
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "notes": notes,
            "customer_notified": notify_customer,
            "message": f"Work order status updated from '{old_status}' to '{new_status}'"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error updating work order status: {str(e)}"
        }