"""
Customer data models.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum

class AccountStatus(str, Enum):
    """Customer account status."""
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    SUSPENDED = "Suspended"

class ContractType(str, Enum):
    """Contract types."""
    RESIDENTIAL_BASIC = "Residential Basic"
    RESIDENTIAL_GOLD = "Residential Gold"
    COMMERCIAL_BASIC = "Commercial Basic"
    COMMERCIAL_PREMIUM = "Commercial Premium"
    HOSPITAL_SPECIALIZED = "Hospital Specialized"

class ContractStatus(str, Enum):
    """Contract status."""
    ACTIVE = "Active"
    EXPIRED = "Expired"
    PENDING = "Pending"
    CANCELLED = "Cancelled"

class Customer(BaseModel):
    """Customer data model."""
    customer_id: str = Field(..., description="Unique customer identifier")
    full_name: str = Field(..., description="Customer's full name")
    phone_number: str = Field(..., description="Primary contact number")
    email_address: str = Field(..., description="Email address")
    preferred_language: str = Field(default="English", description="Preferred language")
    account_status: AccountStatus = Field(default=AccountStatus.ACTIVE, description="Account status")
    created_at: datetime = Field(default_factory=datetime.now, description="Account creation date")
    
    def __str__(self) -> str:
        return f"Customer({self.customer_id}: {self.full_name})"

class Contract(BaseModel):
    """Contract data model."""
    contract_id: str = Field(..., description="Unique contract identifier")
    customer_id: str = Field(..., description="Customer ID (foreign key)")
    contract_type: ContractType = Field(..., description="Type of contract")
    start_date: datetime = Field(..., description="Contract start date")
    end_date: Optional[datetime] = Field(None, description="Contract end date")
    status: ContractStatus = Field(default=ContractStatus.ACTIVE, description="Contract status")
    
    def is_active(self) -> bool:
        """Check if contract is currently active."""
        now = datetime.now()
        return (
            self.status == ContractStatus.ACTIVE and
            self.start_date <= now and
            (self.end_date is None or self.end_date >= now)
        )
    
    def __str__(self) -> str:
        return f"Contract({self.contract_id}: {self.contract_type.value})"