"""
ADK tools for the facilities management AI agent.
"""
from .customer_lookup import (
    find_customer_by_phone,
    find_customer_by_email,
    find_facility_by_location,
    get_customer_service_history
)
from .scheduling import (
    check_technician_availability,
    book_appointment,
    get_available_time_slots,
    reschedule_appointment
)
from .work_order import (
    get_work_order_status,
    search_work_orders_by_customer,
    update_work_order_status
)
from .emergency import (
    detect_emergency_keywords,
    create_emergency_work_order,
    provide_emergency_safety_advice,
    escalate_emergency
)

__all__ = [
    # Customer lookup tools
    "find_customer_by_phone",
    "find_customer_by_email", 
    "find_facility_by_location",
    "get_customer_service_history",
    
    # Scheduling tools
    "check_technician_availability",
    "book_appointment",
    "get_available_time_slots",
    "reschedule_appointment",
    
    # Work order tools
    "get_work_order_status",
    "search_work_orders_by_customer", 
    "update_work_order_status",
    
    # Emergency tools
    "detect_emergency_keywords",
    "create_emergency_work_order",
    "provide_emergency_safety_advice",
    "escalate_emergency"
]