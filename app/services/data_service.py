"""
Corrected data service that works with your existing CSV files.
"""
import csv
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path

from app.config import settings
from app.models import (
    Customer, Contract, Facility, ServiceType, WorkOrder, 
    Technician, TechnicianAvailability, WorkOrderStatus, UrgencyLevel,
    ServiceCategory, AccountStatus, PropertyType, TechnicianStatus
)

class DataService:
    """
    Enhanced data service that works with your existing CSV files.
    """
    
    def __init__(self):
        self._customers: Dict[str, Customer] = {}
        self._contracts: Dict[str, Contract] = {}
        self._facilities: Dict[str, Facility] = {}
        self._service_types: Dict[str, ServiceType] = {}
        self._work_orders: Dict[str, WorkOrder] = {}
        self._technicians: Dict[str, Technician] = {}
        self._availability_slots: List[TechnicianAvailability] = []
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the service by loading data from your CSV files."""
        if self._initialized:
            return
            
        await self._load_csv_data()
        self._initialized = True
        print(f"✅ Data service initialized with {len(self._customers)} customers, {len(self._facilities)} facilities, {len(self._technicians)} technicians")
    
    async def _load_csv_data(self) -> None:
        """Load data from your existing CSV files."""
        try:
            # Load customers from your CSV
            customers_file = settings.data_dir / "customers.csv"
            if customers_file.exists():
                await self._load_customers_csv(customers_file)
                print(f"📊 Loaded {len(self._customers)} customers from CSV")
            
            # Load facilities from your CSV
            facilities_file = settings.data_dir / "facilities.csv"
            if facilities_file.exists():
                await self._load_facilities_csv(facilities_file)
                print(f"🏢 Loaded {len(self._facilities)} facilities from CSV")
            
            # Load technicians from your CSV
            technicians_file = settings.data_dir / "technicians.csv"
            if technicians_file.exists():
                await self._load_technicians_csv(technicians_file)
                print(f"👷 Loaded {len(self._technicians)} technicians from CSV")
            
            # Load availability from your CSV
            availability_file = settings.data_dir / "availability.csv"
            if availability_file.exists():
                await self._load_availability_csv(availability_file)
                print(f"📅 Loaded {len(self._availability_slots)} availability slots from CSV")
            
            # Load work orders from your CSV
            work_orders_file = settings.data_dir / "work_orders.csv"
            if work_orders_file.exists():
                await self._load_work_orders_csv(work_orders_file)
                print(f"📋 Loaded {len(self._work_orders)} work orders from CSV")
                
        except Exception as e:
            print(f"❌ Error loading CSV files: {e}")
            print("📝 Make sure CSV files are in the data/ directory")
    
    async def _load_customers_csv(self, file_path: Path) -> None:
        """Load customers from your CSV file."""
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    # Handle phone number as float/int in CSV
                    phone_str = str(int(float(row['phone_number']))) if row['phone_number'] else ""
                    if not phone_str.startswith('+'):
                        phone_str = '+971' + phone_str  # Add UAE country code if missing
                    
                    customer = Customer(
                        customer_id=row['customer_id'],
                        full_name=row['full_name'],
                        phone_number=phone_str,
                        email_address=row['email_address'],
                        preferred_language=row.get('preferred_language', 'English'),
                        account_status=AccountStatus(row.get('account_status', 'Active'))
                    )
                    self._customers[customer.customer_id] = customer
                except Exception as e:
                    print(f"⚠️ Error loading customer row: {e}")
                    continue
    
    async def _load_facilities_csv(self, file_path: Path) -> None:
        """Load facilities from your CSV file."""
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    # Handle unit_number and floor as float/int in CSV
                    unit_number = str(int(float(row['unit_number']))) if row['unit_number'] and str(row['unit_number']).lower() != 'nan' else None
                    floor = str(int(float(row['floor']))) if row['floor'] and str(row['floor']).lower() != 'nan' else None
                    
                    facility = Facility(
                        property_id=row['property_id'],
                        customer_id=row['customer_id'],
                        building_name=row['building_name'],
                        unit_number=unit_number,
                        floor=floor,
                        full_address=row['full_address'],
                        city=row['city'],
                        emirate=row['emirate'],
                        area_zone=row['area_zone'],
                        property_type=PropertyType(row['property_type'])
                    )
                    self._facilities[facility.property_id] = facility
                except Exception as e:
                    print(f"⚠️ Error loading facility row: {e}")
                    continue
    
    async def _load_technicians_csv(self, file_path: Path) -> None:
        """Load technicians from your CSV file."""
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    # Handle contact number as float/int in CSV
                    contact_str = str(int(float(row['contact_number']))) if row['contact_number'] else ""
                    if not contact_str.startswith('+'):
                        contact_str = '+971' + contact_str  # Add UAE country code if missing
                    
                    technician = Technician(
                        technician_id=row['technician_id'],
                        technician_name=row['technician_name'],
                        contact_number=contact_str,
                        skillset=row['skillset'].split(',') if row['skillset'] else [],
                        operating_zones=row['operating_zones'].split(',') if row['operating_zones'] else [],
                        current_status=TechnicianStatus(row.get('current_status', 'Available'))
                    )
                    self._technicians[technician.technician_id] = technician
                except Exception as e:
                    print(f"⚠️ Error loading technician row: {e}")
                    continue
    
    async def _load_availability_csv(self, file_path: Path) -> None:
        """Load technician availability from your CSV file."""
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    availability = TechnicianAvailability(
                        technician_id=row['technician_id'],
                        technician_name=row['technician_name'],
                        skillset=row['skillset'].split(',') if row['skillset'] else [],
                        zone=row['zone'],
                        available_date=datetime.fromisoformat(row['available_date']),
                        available_start_time=datetime.fromisoformat(row['available_start_time']),
                        available_end_time=datetime.fromisoformat(row['available_end_time'])
                    )
                    self._availability_slots.append(availability)
                except Exception as e:
                    print(f"⚠️ Error loading availability row: {e}")
                    continue
    
    async def _load_work_orders_csv(self, file_path: Path) -> None:
        """Load work orders from your CSV file."""
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    work_order = WorkOrder(
                        work_order_id=row['work_order_id'],
                        customer_id=row['customer_id'],
                        property_id=row['property_id'],
                        service_id=row['service_id'],
                        problem_description=row['problem_description'],
                        status=WorkOrderStatus(row.get('status', 'New')),
                        urgency=UrgencyLevel(row.get('urgency', 'Medium')),
                        request_date_time=datetime.fromisoformat(row['request_date_time'])
                    )
                    self._work_orders[work_order.work_order_id] = work_order
                except Exception as e:
                    print(f"⚠️ Error loading work order row: {e}")
                    continue
    
    # Customer Data Platform (CDP) methods
    async def find_customer_by_phone(self, phone_number: str) -> Optional[Customer]:
        """Find customer by phone number with robust voice-friendly matching."""
        await self.initialize()
        
        # Clean input phone number
        clean_phone = phone_number.replace(" ", "").replace("-", "").replace("+", "").replace("(", "").replace(")", "")
        
        # Remove common speech recognition artifacts
        clean_phone = clean_phone.replace("o", "0").replace("O", "0")  # Handle O/0 confusion
        
        print(f"🔍 Searching for phone: '{phone_number}' → cleaned: '{clean_phone}'")
        
        for customer in self._customers.values():
            stored_phone = customer.phone_number.replace(" ", "").replace("-", "").replace("+", "").replace("(", "").replace(")", "")
            
            print(f"   Comparing with: {customer.full_name} - stored: '{customer.phone_number}' → cleaned: '{stored_phone}'")
            
            # Try multiple matching strategies
            matches = [
                # Exact match
                clean_phone == stored_phone,
                
                # Input matches end of stored (for partial inputs)
                stored_phone.endswith(clean_phone) and len(clean_phone) >= 7,
                
                # Stored matches end of input (for inputs with extra digits)
                clean_phone.endswith(stored_phone) and len(stored_phone) >= 7,
                
                # UAE specific: input without country code matches stored
                stored_phone.endswith(clean_phone) and stored_phone.startswith("971"),
                
                # UAE specific: add 971 to input and check
                ("971" + clean_phone) == stored_phone,
                
                # UAE specific: input starts with 0, remove it and check
                clean_phone.startswith("0") and stored_phone.endswith(clean_phone[1:]) and len(clean_phone[1:]) >= 7,
                
                # Last 8 digits match (for local numbers)
                len(clean_phone) >= 8 and len(stored_phone) >= 8 and stored_phone[-8:] == clean_phone[-8:],
            ]
            
            if any(matches):
                print(f"   ✅ MATCH FOUND: {customer.full_name}")
                return customer
            else:
                print(f"   ❌ No match")
        
        print(f"❌ No customer found for phone: {phone_number}")
        return None
    
    async def find_customer_by_email(self, email: str) -> Optional[Customer]:
        """Find customer by email address."""
        await self.initialize()
        for customer in self._customers.values():
            if customer.email_address.lower() == email.lower():
                return customer
        return None
    
    async def get_customer_facilities(self, customer_id: str) -> List[Facility]:
        """Get all facilities for a customer."""
        await self.initialize()
        return [f for f in self._facilities.values() if f.customer_id == customer_id]
    
    # Computer Aided Facilities Management (CAFM) methods
    async def find_facility_by_details(self, building_name: str, unit_number: Optional[str]) -> Optional[Facility]:
        """Find facility by building name and unit number."""
        await self.initialize()
        
        for facility in self._facilities.values():
            # Check building name match (partial match allowed)
            building_match = building_name.lower() in facility.building_name.lower() or \
                           facility.building_name.lower() in building_name.lower()
            
            # Check unit number match
            if unit_number and unit_number.lower() != 'none':
                unit_match = facility.unit_number and str(facility.unit_number) == str(unit_number)
            else:
                unit_match = facility.unit_number is None
            
            if building_match and (unit_number is None or unit_match):
                return facility
        
        # If no exact match, try just building name
        for facility in self._facilities.values():
            if building_name.lower() in facility.building_name.lower():
                return facility
                
        return None
    
    async def get_work_order_by_id(self, work_order_id: str) -> Optional[WorkOrder]:
        """Get work order by ID."""
        await self.initialize()
        return self._work_orders.get(work_order_id)
    
    async def get_customer_work_orders(self, customer_id: str, active_only: bool) -> List[WorkOrder]:
        """Get work orders for a customer."""
        await self.initialize()
        work_orders = [wo for wo in self._work_orders.values() if wo.customer_id == customer_id]
        
        if active_only:
            work_orders = [wo for wo in work_orders if wo.is_active()]
        
        return sorted(work_orders, key=lambda x: x.request_date_time, reverse=True)
    
    async def create_work_order(self, work_order: WorkOrder) -> str:
        """Create a new work order."""
        await self.initialize()
        self._work_orders[work_order.work_order_id] = work_order
        print(f"💾 Work order created: {work_order.work_order_id}")
        return work_order.work_order_id
    
    # Workforce Management (WFM) methods
    async def find_available_technicians(
        self, 
        required_skills: List[str],
        zone: str,
        requested_datetime: datetime,
        duration_minutes: int
    ) -> List[TechnicianAvailability]:
        """Find available technicians matching criteria."""
        await self.initialize()
        
        print(f"🔍 Searching for technicians:")
        print(f"   Skills: {required_skills}")
        print(f"   Zone: {zone}")
        print(f"   DateTime: {requested_datetime}")
        print(f"   Duration: {duration_minutes} minutes")
        
        available_slots = []
        end_time = requested_datetime + timedelta(minutes=duration_minutes)
        
        for slot in self._availability_slots:
            # Check if technician has required skills (flexible matching)
            has_skills = True
            for skill in required_skills:
                skill_found = any(
                    skill.lower() in slot_skill.lower() or slot_skill.lower() in skill.lower()
                    for slot_skill in slot.skillset
                )
                if not skill_found:
                    has_skills = False
                    break
            
            if not has_skills:
                continue
            
            # Check zone match (flexible matching)
            zone_match = any(
                zone.lower() in slot_zone.lower() or slot_zone.lower() in zone.lower()
                for slot_zone in [slot.zone]
            ) or slot.zone.lower() == zone.lower()
            
            if not zone_match:
                continue
            
            # Check time availability
            time_available = (
                slot.available_start_time <= requested_datetime and
                slot.available_end_time >= end_time
            )
            
            if time_available:
                available_slots.append(slot)
                print(f"   ✅ Found: {slot.technician_name} ({slot.technician_id}) - {slot.skillset}")
        
        print(f"🎯 Total available technicians: {len(available_slots)}")
        return available_slots
    
    async def get_technician_by_id(self, technician_id: str) -> Optional[Technician]:
        """Get technician by ID."""
        await self.initialize()
        return self._technicians.get(technician_id)
    
    async def get_service_types(self) -> List[ServiceType]:
        """Get all available service types."""
        await self.initialize()
        # Return comprehensive service types for PoC
        return [
            ServiceType(
                service_id="SVC001",
                service_name="AC Routine Maintenance",
                service_description="Regular AC system maintenance and inspection",
                category=ServiceCategory.HVAC,
                required_skills=["HVAC"],
                default_urgency=UrgencyLevel.ROUTINE,
                estimated_duration=120
            ),
            ServiceType(
                service_id="SVC002",
                service_name="Emergency Plumbing Repair",
                service_description="Urgent plumbing repairs including leaks",
                category=ServiceCategory.PLUMBING,
                required_skills=["Plumbing"],
                default_urgency=UrgencyLevel.EMERGENCY,
                estimated_duration=90
            ),
            ServiceType(
                service_id="SVC003",
                service_name="Electrical Repair",
                service_description="Electrical system repairs and installations",
                category=ServiceCategory.ELECTRICAL,
                required_skills=["Electrical"],
                default_urgency=UrgencyLevel.ROUTINE,
                estimated_duration=150
            ),
            ServiceType(
                service_id="SVC004",
                service_name="General Maintenance",
                service_description="General facility maintenance tasks",
                category=ServiceCategory.GENERAL_MAINTENANCE,
                required_skills=["General"],
                default_urgency=UrgencyLevel.ROUTINE,
                estimated_duration=100
            ),
            ServiceType(
                service_id="SVC005",
                service_name="AC Repair",
                service_description="Air conditioning system repairs and troubleshooting",
                category=ServiceCategory.HVAC,
                required_skills=["HVAC"],
                default_urgency=UrgencyLevel.URGENT,
                estimated_duration=150
            ),
            ServiceType(
                service_id="SVC006",
                service_name="Plumbing Repair",
                service_description="General plumbing repairs and maintenance",
                category=ServiceCategory.PLUMBING,
                required_skills=["Plumbing"],
                default_urgency=UrgencyLevel.MEDIUM,
                estimated_duration=120
            ),
            ServiceType(
                service_id="SVC007",
                service_name="AC Maintenance",
                service_description="Air conditioning maintenance and cleaning",
                category=ServiceCategory.HVAC,
                required_skills=["HVAC"],
                default_urgency=UrgencyLevel.ROUTINE,
                estimated_duration=120
            )
        ]
    
    async def get_service_by_name(self, service_name: str) -> Optional[ServiceType]:
        """Get service type by name with flexible matching."""
        services = await self.get_service_types()
        service_name_lower = service_name.lower()
        
        # First try exact match
        for service in services:
            if service.service_name.lower() == service_name_lower:
                return service
        
        # Then try partial match
        for service in services:
            if service_name_lower in service.service_name.lower():
                return service
        
        # Try keyword matching
        for service in services:
            if any(word in service.service_name.lower() for word in service_name_lower.split()):
                return service
        
        # Finally try reverse matching (service name contains user input)
        for service in services:
            if any(word in service_name_lower for word in service.service_name.lower().split()):
                return service
                
        return None

# Global data service instance
data_service = DataService()