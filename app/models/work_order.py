"""
Work order and technician data models.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum

class WorkOrderStatus(str, Enum):
    """Work order status options."""
    NEW = "New"
    SCHEDULED = "Scheduled"
    ASSIGNED = "Assigned"
    DISPATCHED = "Dispatched"
    IN_PROGRESS = "In Progress"
    ON_HOLD = "On Hold"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

class UrgencyLevel(str, Enum):
    """Urgency levels for work orders."""
    ROUTINE = "Routine"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    URGENT = "Urgent"
    EMERGENCY = "Emergency"

class TechnicianStatus(str, Enum):
    """Technician availability status."""
    AVAILABLE = "Available"
    ON_JOB = "On Job"
    OFFLINE = "Offline"
    BREAK = "Break"

class WorkOrder(BaseModel):
    """Work order data model."""
    work_order_id: str = Field(..., description="Unique work order identifier")
    customer_id: str = Field(..., description="Customer ID")
    property_id: str = Field(..., description="Property ID")
    service_id: str = Field(..., description="Service type ID")
    problem_description: str = Field(..., description="Customer reported issue")
    status: WorkOrderStatus = Field(default=WorkOrderStatus.NEW, description="Current status")
    urgency: UrgencyLevel = Field(default=UrgencyLevel.MEDIUM, description="Urgency level")
    request_date_time: datetime = Field(default_factory=datetime.now, description="Request timestamp")
    scheduled_date_time: Optional[datetime] = Field(None, description="Scheduled appointment time")
    assigned_technician_id: Optional[str] = Field(None, description="Assigned technician ID")
    completion_date_time: Optional[datetime] = Field(None, description="Completion timestamp")
    completion_notes: Optional[str] = Field(None, description="Completion notes")
    
    def is_active(self) -> bool:
        """Check if work order is still active."""
        return self.status not in [WorkOrderStatus.COMPLETED, WorkOrderStatus.CANCELLED]
    
    def is_emergency(self) -> bool:
        """Check if work order is emergency priority."""
        return self.urgency == UrgencyLevel.EMERGENCY
    
    def __str__(self) -> str:
        return f"WorkOrder({self.work_order_id}: {self.status.value})"

class Technician(BaseModel):
    """Technician data model."""
    technician_id: str = Field(..., description="Unique technician identifier")
    technician_name: str = Field(..., description="Technician name")
    contact_number: str = Field(..., description="Contact number")
    skillset: List[str] = Field(default_factory=list, description="List of skills")
    operating_zones: List[str] = Field(default_factory=list, description="Operating areas")
    current_status: TechnicianStatus = Field(default=TechnicianStatus.AVAILABLE, description="Current status")
    
    def has_skill(self, required_skill: str) -> bool:
        """Check if technician has required skill."""
        return required_skill.lower() in [skill.lower() for skill in self.skillset]
    
    def can_serve_zone(self, zone: str) -> bool:
        """Check if technician can serve the zone."""
        return zone.lower() in [z.lower() for z in self.operating_zones]
    
    def __str__(self) -> str:
        return f"Technician({self.technician_id}: {self.technician_name})"

class TechnicianAvailability(BaseModel):
    """Technician availability slot."""
    technician_id: str = Field(..., description="Technician ID")
    technician_name: str = Field(..., description="Technician name")
    skillset: List[str] = Field(default_factory=list, description="Skills (denormalized)")
    zone: str = Field(..., description="Operating zone")
    available_date: datetime = Field(..., description="Available date")
    available_start_time: datetime = Field(..., description="Start time")
    available_end_time: datetime = Field(..., description="End time")
    
    def is_available_at(self, requested_time: datetime) -> bool:
        """Check if technician is available at requested time."""
        return (
            self.available_start_time <= requested_time <= self.available_end_time
        )
    
    def __str__(self) -> str:
        return f"Availability({self.technician_name}: {self.available_date.date()})"