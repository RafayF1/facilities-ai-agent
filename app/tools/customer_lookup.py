"""
Customer lookup tools for the facilities management AI agent.
"""
from typing import Dict, Any, Optional
import re

from app.services.data_service import data_service
from app.models import Customer, Facility

async def find_customer_by_phone(phone_number: str) -> Dict[str, Any]:
    """
    Find customer information by phone number.
    
    Args:
        phone_number: Customer's phone number
        
    Returns:
        Dictionary with customer information or error message
    """
    try:
        # Clean and normalize phone number
        clean_phone = re.sub(r'[^\d+]', '', phone_number)
        
        customer = await data_service.find_customer_by_phone(clean_phone)
        
        if customer:
            # Get customer facilities
            facilities = await data_service.get_customer_facilities(customer.customer_id)
            
            return {
                "status": "success",
                "customer_found": True,
                "customer_id": customer.customer_id,
                "full_name": customer.full_name,
                "phone_number": customer.phone_number,
                "email_address": customer.email_address,
                "account_status": customer.account_status.value,
                "facilities_count": len(facilities),
                "facilities": [
                    {
                        "property_id": f.property_id,
                        "building_name": f.building_name,
                        "unit_number": f.unit_number or "N/A",
                        "display_location": f.display_location,
                        "property_type": f.property_type.value,
                        "area_zone": f.area_zone
                    }
                    for f in facilities
                ]
            }
        else:
            return {
                "status": "success",
                "customer_found": False,
                "message": f"No customer found with phone number {phone_number}. Please verify the number or provide additional details."
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error looking up customer: {str(e)}"
        }

async def find_customer_by_email(email_address: str) -> Dict[str, Any]:
    """
    Find customer information by email address.
    
    Args:
        email_address: Customer's email address
        
    Returns:
        Dictionary with customer information or error message
    """
    try:
        customer = await data_service.find_customer_by_email(email_address)
        
        if customer:
            facilities = await data_service.get_customer_facilities(customer.customer_id)
            
            return {
                "status": "success",
                "customer_found": True,
                "customer_id": customer.customer_id,
                "full_name": customer.full_name,
                "phone_number": customer.phone_number,
                "email_address": customer.email_address,
                "account_status": customer.account_status.value,
                "facilities_count": len(facilities),
                "facilities": [
                    {
                        "property_id": f.property_id,
                        "building_name": f.building_name,
                        "unit_number": f.unit_number or "N/A",
                        "display_location": f.display_location,
                        "property_type": f.property_type.value,
                        "area_zone": f.area_zone
                    }
                    for f in facilities
                ]
            }
        else:
            return {
                "status": "success",
                "customer_found": False,
                "message": f"No customer found with email {email_address}. Please verify the email or provide additional details."
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error looking up customer: {str(e)}"
        }

async def find_facility_by_location(building_name: str, unit_number: str) -> Dict[str, Any]:
    """
    Find facility information by building name and unit number.
    
    Args:
        building_name: Name of the building
        unit_number: Unit/apartment number (use "none" if no unit number)
        
    Returns:
        Dictionary with facility information or error message
    """
    try:
        # Handle "none" case for unit_number
        unit_num = None if unit_number.lower() == "none" else unit_number
        
        facility = await data_service.find_facility_by_details(building_name, unit_num)
        
        if facility:
            # Get customer information for this facility
            customer = await data_service.find_customer_by_phone(facility.customer_id)
            if not customer:
                # Try to find customer by ID if phone lookup fails
                for cust in data_service._customers.values():
                    if cust.customer_id == facility.customer_id:
                        customer = cust
                        break
            
            return {
                "status": "success",
                "facility_found": True,
                "property_id": facility.property_id,
                "building_name": facility.building_name,
                "unit_number": facility.unit_number or "N/A",
                "floor": facility.floor or "N/A",
                "display_location": facility.display_location,
                "full_address": facility.full_address,
                "city": facility.city,
                "emirate": facility.emirate,
                "area_zone": facility.area_zone,
                "property_type": facility.property_type.value,
                "customer_name": customer.full_name if customer else "Unknown",
                "customer_id": facility.customer_id
            }
        else:
            return {
                "status": "success",
                "facility_found": False,
                "message": f"No facility found for building '{building_name}'" + 
                          (f" unit '{unit_number}'" if unit_number.lower() != "none" else "") + 
                          ". Please verify the location details."
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error looking up facility: {str(e)}"
        }

async def get_customer_service_history(customer_id: str) -> Dict[str, Any]:
    """
    Get service history for a customer.
    
    Args:
        customer_id: Customer identifier
        
    Returns:
        Dictionary with service history information
    """
    try:
        work_orders = await data_service.get_customer_work_orders(customer_id)
        
        if work_orders:
            history = []
            for wo in work_orders[:10]:  # Limit to last 10 orders
                history.append({
                    "work_order_id": wo.work_order_id,
                    "service_type": wo.service_id,
                    "problem_description": wo.problem_description,
                    "status": wo.status.value,
                    "urgency": wo.urgency.value,
                    "request_date": wo.request_date_time.strftime("%Y-%m-%d %H:%M"),
                    "scheduled_date": wo.scheduled_date_time.strftime("%Y-%m-%d %H:%M") if wo.scheduled_date_time else None,
                    "completion_date": wo.completion_date_time.strftime("%Y-%m-%d %H:%M") if wo.completion_date_time else None,
                    "is_active": wo.is_active()
                })
            
            return {
                "status": "success",
                "total_orders": len(work_orders),
                "recent_orders": len(history),
                "service_history": history
            }
        else:
            return {
                "status": "success",
                "total_orders": 0,
                "message": "No service history found for this customer."
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error retrieving service history: {str(e)}"
        }