"""
Facility and service type data models.
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum
from .work_order import UrgencyLevel

class PropertyType(str, Enum):
    """Types of properties."""
    RESIDENTIAL = "Residential"
    COMMERCIAL = "Commercial"
    HOSPITAL = "Hospital"
    MALL = "Mall"
    OFFICE = "Office"

class ServiceCategory(str, Enum):
    """Service categories."""
    HVAC = "HVAC"
    PLUMBING = "Plumbing"
    ELECTRICAL = "Electrical"
    CLEANING = "Cleaning"
    GENERAL_MAINTENANCE = "General Maintenance"
    SECURITY = "Security"
    LANDSCAPING = "Landscaping"

class Facility(BaseModel):
    """Facility/Property data model."""
    property_id: str = Field(..., description="Unique property identifier")
    customer_id: str = Field(..., description="Customer ID (foreign key)")
    building_name: str = Field(..., description="Building name")
    unit_number: Optional[str] = Field(None, description="Unit/apartment/office number")
    floor: Optional[str] = Field(None, description="Floor number")
    full_address: str = Field(..., description="Complete address")
    city: str = Field(..., description="City")
    emirate: str = Field(..., description="Emirate/State")
    area_zone: str = Field(..., description="Area or zone for routing")
    property_type: PropertyType = Field(..., description="Type of property")
    
    @property
    def display_location(self) -> str:
        """Get formatted location display."""
        parts = [self.building_name]
        if self.unit_number:
            parts.append(f"Unit {self.unit_number}")
        if self.floor:
            parts.append(f"Floor {self.floor}")
        return ", ".join(parts)
    
    def __str__(self) -> str:
        return f"Facility({self.property_id}: {self.display_location})"

class ServiceType(BaseModel):
    """Service type data model."""
    service_id: str = Field(..., description="Unique service identifier")
    service_name: str = Field(..., description="Service name")
    service_description: str = Field(..., description="Service description")
    category: ServiceCategory = Field(..., description="Service category")
    required_skills: List[str] = Field(default_factory=list, description="Required technician skills")
    default_urgency: UrgencyLevel = Field(default=UrgencyLevel.ROUTINE, description="Default urgency level")
    estimated_duration: int = Field(default=120, description="Estimated duration in minutes")
    
    def __str__(self) -> str:
        return f"ServiceType({self.service_id}: {self.service_name})"