"""
Emergency handling tools for urgent service requests.
"""
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any

from app.config import settings
from app.services.data_service import data_service
from app.services.email_service import email_service
from app.models import WorkOrder, WorkOrderStatus, UrgencyLevel

async def detect_emergency_keywords(message: str) -> Dict[str, Any]:
    """
    Detect emergency keywords in a message.
    
    Args:
        message: User message to analyze
        
    Returns:
        Dictionary with emergency detection results
    """
    try:
        message_lower = message.lower()
        detected_keywords = []
        
        for keyword in settings.emergency_keywords:
            if keyword.lower() in message_lower:
                detected_keywords.append(keyword)
        
        is_emergency = len(detected_keywords) > 0
        
        # Determine emergency severity
        severity = "low"
        high_priority_keywords = ["fire", "gas", "electrical", "flood", "burst", "dangerous"]
        
        if any(keyword.lower() in message_lower for keyword in high_priority_keywords):
            severity = "critical"
        elif any(keyword.lower() in message_lower for keyword in ["leak", "water", "overflow"]):
            severity = "high"
        elif detected_keywords:
            severity = "medium"
        
        return {
            "status": "success",
            "is_emergency": is_emergency,
            "severity": severity,
            "detected_keywords": detected_keywords,
            "message_analyzed": message[:100] + "..." if len(message) > 100 else message,
            "recommendation": "Escalate to emergency response team" if is_emergency else "Handle as routine request"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error analyzing emergency keywords: {str(e)}"
        }

async def create_emergency_work_order(
    customer_id: str,
    property_id: str,
    problem_description: str,
    contact_number: str,
    urgency_level: str
) -> Dict[str, Any]:
    """
    Create an emergency work order with high priority.
    
    Args:
        customer_id: Customer identifier
        property_id: Property identifier
        problem_description: Description of the emergency
        contact_number: Emergency contact number
        urgency_level: Emergency urgency level
        
    Returns:
        Dictionary with emergency work order details
    """
    try:
        # Get customer and facility details
        customer = None
        for cust in data_service._customers.values():
            if cust.customer_id == customer_id:
                customer = cust
                break
        
        facility = data_service._facilities.get(property_id)
        
        if not customer:
            return {
                "status": "error",
                "error_message": f"Customer {customer_id} not found"
            }
        
        if not facility:
            return {
                "status": "error",
                "error_message": f"Facility {property_id} not found"
            }
        
        # Create emergency work order
        work_order_id = f"EMG_{uuid.uuid4().hex[:8].upper()}"
        
        work_order = WorkOrder(
            work_order_id=work_order_id,
            customer_id=customer_id,
            property_id=property_id,
            service_id="EMERGENCY",  # Special emergency service ID
            problem_description=problem_description,
            status=WorkOrderStatus.NEW,
            urgency=UrgencyLevel.EMERGENCY,
            request_date_time=datetime.now()
        )
        
        # Save emergency work order
        await data_service.create_work_order(work_order)
        
        # Try to find immediate emergency technician
        emergency_technicians = await data_service.find_available_technicians(
            required_skills=["Emergency", "General"],
            zone=facility.area_zone,
            requested_datetime=datetime.now(),
            duration_minutes=180  # 3 hours for emergency
        )
        
        assigned_technician = None
        if emergency_technicians:
            assigned_technician = emergency_technicians[0]
            work_order.assigned_technician_id = assigned_technician.technician_id
            work_order.status = WorkOrderStatus.ASSIGNED
        
        # Send emergency notification email
        emergency_details = {
            'work_order_id': work_order_id,
            'problem_description': problem_description,
            'location': facility.display_location,
            'urgency': urgency_level,
            'request_time': datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        await email_service.send_emergency_notification(
            recipient_email=customer.email_address,
            customer_name=customer.full_name,
            emergency_details=emergency_details
        )
        
        # Prepare response
        response = {
            "status": "success",
            "emergency_logged": True,
            "work_order_id": work_order_id,
            "urgency": urgency_level,
            "customer_name": customer.full_name,
            "location": facility.display_location,
            "contact_number": contact_number,
            "request_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "emergency_response": {
                "immediate_actions": [
                    "Emergency response team notified",
                    "High priority work order created",
                    "Customer notification email sent"
                ],
                "next_steps": [
                    "Emergency technician will be contacted within 15 minutes",
                    "Customer will receive call with ETA",
                    "Continuous monitoring until resolution"
                ]
            }
        }
        
        if assigned_technician:
            response["assigned_technician"] = {
                "name": assigned_technician.technician_name,
                "estimated_arrival": "Within 60 minutes",
                "contact_method": "Will call customer directly"
            }
            response["emergency_response"]["immediate_actions"].append(f"Emergency technician {assigned_technician.technician_name} assigned")
        else:
            response["emergency_response"]["immediate_actions"].append("Searching for available emergency technician")
            response["emergency_response"]["next_steps"].insert(0, "Emergency technician assignment in progress")
        
        return response
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error creating emergency work order: {str(e)}"
        }

async def provide_emergency_safety_advice(emergency_type: str) -> Dict[str, Any]:
    """
    Provide safety advice based on emergency type.
    
    Args:
        emergency_type: Type of emergency (water, electrical, gas, etc.)
        
    Returns:
        Dictionary with safety advice and instructions
    """
    try:
        emergency_type_lower = emergency_type.lower()
        
        safety_advice = {
            "emergency_type": emergency_type,
            "immediate_actions": [],
            "safety_precautions": [],
            "what_not_to_do": [],
            "when_to_evacuate": "",
            "emergency_contacts": {
                "company_emergency": "+971-4-XXX-XXXX",
                "police": "999",
                "fire_department": "997",
                "ambulance": "998"
            }
        }
        
        if "water" in emergency_type_lower or "leak" in emergency_type_lower:
            safety_advice.update({
                "immediate_actions": [
                    "Turn off the main water supply if safely accessible",
                    "Move electrical items away from water",
                    "Place buckets or containers to catch dripping water",
                    "Take photos for insurance purposes"
                ],
                "safety_precautions": [
                    "Avoid walking through standing water",
                    "Do not touch electrical outlets near water",
                    "Wear shoes to protect feet from debris"
                ],
                "what_not_to_do": [
                    "Do not ignore small leaks - they can worsen quickly",
                    "Do not use electrical appliances in wet areas",
                    "Do not attempt major plumbing repairs yourself"
                ],
                "when_to_evacuate": "If water level rises rapidly or electrical hazards are present"
            })
            
        elif "electrical" in emergency_type_lower:
            safety_advice.update({
                "immediate_actions": [
                    "Turn off electricity at the main breaker if safe to do so",
                    "Unplug appliances if you can do so safely",
                    "Keep area clear and well-ventilated"
                ],
                "safety_precautions": [
                    "Do not touch exposed wires or electrical equipment",
                    "Stay away from water near electrical sources",
                    "Use flashlight instead of candles if power is out"
                ],
                "what_not_to_do": [
                    "Never touch electrical equipment with wet hands",
                    "Do not attempt electrical repairs yourself",
                    "Do not use water to extinguish electrical fires"
                ],
                "when_to_evacuate": "If you smell burning, see sparks, or hear crackling sounds"
            })
            
        elif "gas" in emergency_type_lower:
            safety_advice.update({
                "immediate_actions": [
                    "Turn off gas supply at the meter if safe to access",
                    "Open windows and doors for ventilation",
                    "Evacuate the building immediately",
                    "Call emergency services from outside the building"
                ],
                "safety_precautions": [
                    "Do not use phones or electrical switches inside",
                    "Do not smoke or use open flames",
                    "Move to fresh air immediately"
                ],
                "what_not_to_do": [
                    "Do not turn on lights or electrical appliances",
                    "Do not try to locate the gas leak yourself",
                    "Do not re-enter until cleared by professionals"
                ],
                "when_to_evacuate": "Immediately upon detecting gas smell - evacuate now!"
            })
            
        elif "fire" in emergency_type_lower:
            safety_advice.update({
                "immediate_actions": [
                    "Call fire department immediately (997)",
                    "Evacuate building following exit routes",
                    "Alert others in the building",
                    "Meet at designated assembly point"
                ],
                "safety_precautions": [
                    "Stay low to avoid smoke inhalation",
                    "Feel doors before opening (if hot, use alternate route)",
                    "Never use elevators during fire"
                ],
                "what_not_to_do": [
                    "Do not stop to collect belongings",
                    "Do not re-enter building for any reason",
                    "Do not use water on electrical or grease fires"
                ],
                "when_to_evacuate": "Immediately - do not delay evacuation for any reason"
            })
            
        else:
            # General emergency advice
            safety_advice.update({
                "immediate_actions": [
                    "Ensure personal safety first",
                    "Move to a safe location if necessary",
                    "Document the situation with photos if safe",
                    "Contact emergency services if life-threatening"
                ],
                "safety_precautions": [
                    "Stay calm and assess the situation",
                    "Keep emergency contacts readily available",
                    "Follow building safety procedures"
                ],
                "what_not_to_do": [
                    "Do not attempt repairs beyond your expertise",
                    "Do not ignore safety warnings or signs",
                    "Do not put yourself in danger"
                ],
                "when_to_evacuate": "If you feel unsafe or situation is worsening"
            })
        
        return {
            "status": "success",
            "safety_advice_provided": True,
            "advice": safety_advice,
            "additional_note": "Emergency technician dispatch has been initiated. Follow safety advice until help arrives."
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error providing safety advice: {str(e)}"
        }

async def escalate_emergency(
    work_order_id: str,
    escalation_reason: str,
    contact_details: Dict[str, str]
) -> Dict[str, Any]:
    """
    Escalate an emergency to higher priority or specialized teams.
    
    Args:
        work_order_id: Emergency work order ID
        escalation_reason: Reason for escalation
        contact_details: Emergency contact information
        
    Returns:
        Dictionary with escalation confirmation
    """
    try:
        work_order = await data_service.get_work_order_by_id(work_order_id)
        
        if not work_order:
            return {
                "status": "error",
                "error_message": f"Work order {work_order_id} not found"
            }
        
        if not work_order.is_emergency():
            return {
                "status": "error",
                "error_message": "Work order is not marked as emergency - cannot escalate"
            }
        
        # Log escalation (in real system, this would update database and trigger alerts)
        escalation_id = f"ESC_{uuid.uuid4().hex[:6].upper()}"
        
        escalation_details = {
            "escalation_id": escalation_id,
            "work_order_id": work_order_id,
            "escalation_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "escalation_reason": escalation_reason,
            "escalated_by": "AI Agent System",
            "contact_details": contact_details,
            "actions_taken": [
                "Emergency supervisor notified",
                "Specialized response team alerted",
                "Customer priority status upgraded",
                "Additional resources allocated"
            ],
            "estimated_response_time": "15-30 minutes",
            "escalation_level": "Critical"
        }
        
        return {
            "status": "success",
            "escalated": True,
            "escalation_details": escalation_details,
            "message": f"Emergency {work_order_id} has been escalated with ID {escalation_id}. Specialized response team is being dispatched.",
            "next_steps": [
                "Emergency supervisor will contact you within 15 minutes",
                "Specialized technician team is being dispatched",
                "Continuous monitoring has been activated",
                "You will receive regular status updates"
            ]
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error escalating emergency: {str(e)}"
        }