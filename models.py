from sqlalchemy import create_engine, Column, BigInteger, String, Float, DateTime, ForeignKey, Table, Integer, func, Boolean, Text, Enum, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import enum

Base = declarative_base()

# Enums for structured data
class UserRole(enum.Enum):
    USER = "user"           # Kiosk operator
    ADMIN = "admin"         # Admin (everything except webhook)
    SUPERADMIN = "superadmin"  # Can do everything
    BATTERY = "battery"     # Can only write to webhook
    DATA_ADMIN = "data_admin"  # Can only view data analytics, no user info

class PUEUsageLocation(enum.Enum):
    HUB_ONLY = "HUB_ONLY"
    BATTERY_ONLY = "BATTERY_ONLY"
    BOTH = "BOTH"

# Junction tables for many-to-many relationships
user_hub_access = Table('user_hub_access', Base.metadata,
    Column('user_id', BigInteger, ForeignKey('user.user_id'), primary_key=True),
    Column('hub_id', BigInteger, ForeignKey('solarhub.hub_id'), primary_key=True),
    Column('granted_at', DateTime, default=datetime.utcnow),
    Column('granted_by', BigInteger, ForeignKey('user.user_id'), nullable=True)
)

battery_notes = Table('bepppbattery_notes', Base.metadata,
    Column('battery_id', BigInteger, ForeignKey('bepppbattery.battery_id'), primary_key=True),
    Column('note_id', BigInteger, ForeignKey('note.id'), primary_key=True)
)

rental_notes = Table('rental_notes', Base.metadata,
    Column('rental_id', BigInteger, ForeignKey('rental.rentral_id'), primary_key=True),
    Column('note_id', BigInteger, ForeignKey('note.id'), primary_key=True)
)

pue_notes = Table('pue_notes', Base.metadata,
    Column('pue_id', BigInteger, ForeignKey('productiveuseequipment.pue_id'), primary_key=True),
    Column('note_id', BigInteger, ForeignKey('note.id'), primary_key=True)
)

pue_rental_notes = Table('puerental_notes', Base.metadata,
    Column('pue_rental_id', BigInteger, ForeignKey('puerental.pue_rental_id'), primary_key=True),
    Column('note_id', BigInteger, ForeignKey('note.id'), primary_key=True)
)

battery_rental_notes = Table('battery_rental_notes', Base.metadata,
    Column('rental_id', BigInteger, ForeignKey('battery_rentals.rental_id'), primary_key=True),
    Column('note_id', BigInteger, ForeignKey('note.id'), primary_key=True)
)

class SolarHub(Base):
    __tablename__ = 'solarhub'
    
    hub_id = Column(BigInteger, primary_key=True)
    what_three_word_location = Column(String(255))
    solar_capacity_kw = Column(BigInteger)
    country = Column(String(255))
    latitude = Column(Float)
    longitude = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    users = relationship("User", back_populates="hub", foreign_keys="User.hub_id")
    batteries = relationship("BEPPPBattery", back_populates="hub")
    pue_items = relationship("ProductiveUseEquipment", back_populates="hub")
    data_admin_users = relationship("User", 
                                  secondary=user_hub_access, 
                                  back_populates="accessible_hubs",
                                  primaryjoin="SolarHub.hub_id == user_hub_access.c.hub_id",
                                  secondaryjoin="User.user_id == user_hub_access.c.user_id")

class User(Base):
    __tablename__ = 'user'

    user_id = Column(BigInteger, primary_key=True, autoincrement=True)
    Name = Column(String(255))
    users_identification_document_number = Column(String)
    mobile_number = Column(String(255))
    address = Column(String)
    hub_id = Column(BigInteger, ForeignKey('solarhub.hub_id'))
    user_access_level = Column(String(255))  # Will store UserRole enum values
    username = Column(String(255), unique=True)
    password_hash = Column(String(255))
    short_id = Column(String(20), unique=True, index=True, nullable=True)  # QR code ID (e.g., BH-0001)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relations
    hub = relationship("SolarHub", back_populates="users", foreign_keys=[hub_id])
    battery_rentals = relationship("Rental", back_populates="user")
    pue_rentals = relationship("PUERental", back_populates="user")
    accessible_hubs = relationship("SolarHub", 
                                 secondary=user_hub_access, 
                                 back_populates="data_admin_users",
                                 primaryjoin="User.user_id == user_hub_access.c.user_id",
                                 secondaryjoin="SolarHub.hub_id == user_hub_access.c.hub_id")

class Note(Base):
    __tablename__ = 'note'
    
    id = Column(BigInteger, primary_key=True)
    content = Column(Text)  # Use Text for longer content
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(BigInteger, ForeignKey('user.user_id'), nullable=True)  # Who created the note
    
    # Relations
    creator = relationship("User")
    batteries = relationship("BEPPPBattery", secondary=battery_notes, back_populates="notes")
    rentals = relationship("Rental", secondary=rental_notes, back_populates="notes")
    pue_items = relationship("ProductiveUseEquipment", secondary=pue_notes, back_populates="notes")
    pue_rentals = relationship("PUERental", secondary=pue_rental_notes, back_populates="notes")
    battery_rentals = relationship("BatteryRental", secondary=battery_rental_notes, back_populates="notes")

class BEPPPBattery(Base):
    __tablename__ = 'bepppbattery'

    battery_id = Column(BigInteger, primary_key=True)
    hub_id = Column(BigInteger, ForeignKey('solarhub.hub_id'))
    battery_capacity_wh = Column(BigInteger)
    status = Column(String, default="available")
    battery_secret = Column(String(255), nullable=True)  # Secret for battery self-authentication
    short_id = Column(String(20), unique=True, index=True, nullable=True)  # QR code ID (e.g., BAT-0001)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_data_received = Column(DateTime, nullable=True)  # Last time we got data from this battery
    
    # Relations
    hub = relationship("SolarHub", back_populates="batteries")
    live_data = relationship("LiveData", back_populates="battery")
    rentals = relationship("Rental", back_populates="battery")
    notes = relationship("Note", secondary=battery_notes, back_populates="batteries")

class ProductiveUseEquipment(Base):
    __tablename__ = 'productiveuseequipment'

    pue_id = Column(BigInteger, primary_key=True)
    hub_id = Column(BigInteger, ForeignKey('solarhub.hub_id'))
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # *** ENHANCED PUE FIELDS ***
    power_rating_watts = Column(Float, nullable=True)  # Power consumption in watts
    usage_location = Column(Enum(PUEUsageLocation), default=PUEUsageLocation.BOTH)  # Where it can be used: hub_only, battery_only, both
    storage_location = Column(String(255), nullable=True)  # Physical storage location
    suggested_cost_per_day = Column(Float, nullable=True)  # Suggested daily rental cost
    pue_type_id = Column(Integer, ForeignKey('pue_types.type_id', ondelete='SET NULL'), nullable=True)  # Optional type classification
    short_id = Column(String(20), unique=True, index=True, nullable=True)  # QR code ID (e.g., PUE-0001)

    # Existing fields
    rental_cost = Column(Float)  # Actual rental cost (can differ from suggested)
    status = Column(String, default="available")
    rental_count = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)  # Soft delete capability
    
    # Relations
    hub = relationship("SolarHub", back_populates="pue_items")
    pue_type = relationship("PUEType", back_populates="pue_items", foreign_keys=[pue_type_id])
    notes = relationship("Note", secondary=pue_notes, back_populates="pue_items")
    pue_rentals = relationship("PUERental", back_populates="pue")
    rental_items = relationship("RentalPUEItem", back_populates="pue")
    inspections = relationship("PUEInspection", back_populates="pue", cascade="all, delete-orphan")

class LiveData(Base):
    __tablename__ = 'livedata'
    
    id = Column(BigInteger, primary_key=True)
    battery_id = Column(BigInteger, ForeignKey('bepppbattery.battery_id'))
    state_of_charge = Column(BigInteger)
    voltage = Column(Float)
    current_amps = Column(Float)
    power_watts = Column(Float)
    time_remaining = Column(BigInteger)
    temp_battery = Column(Float)
    amp_hours_consumed = Column(Float)
    charging_current = Column(Float)
    timestamp = Column(DateTime)
    usb_voltage = Column(Float)
    usb_power = Column(Float)
    usb_current = Column(Float)
    latitude = Column(Float)
    longitude = Column(Float)
    altitude = Column(Float)
    SD_card_storage_remaining = Column(Float)
    battery_orientation = Column(String(255))
    number_GPS_satellites_for_fix = Column(Integer)
    mobile_signal_strength = Column(Integer)
    event_type = Column(String(255))
    new_battery_cycle = Column(Integer)
    
    # Additional fields from webhook mapping
    charger_power = Column(Float, nullable=True)
    charger_voltage = Column(Float, nullable=True)
    gps_fix_quality = Column(Integer, nullable=True)
    charging_enabled = Column(Integer, nullable=True)
    fan_enabled = Column(Integer, nullable=True)
    inverter_enabled = Column(Integer, nullable=True)
    usb_enabled = Column(Integer, nullable=True)
    stay_awake_state = Column(Integer, nullable=True)
    tilt_sensor_state = Column(Integer, nullable=True)
    total_charge_consumed = Column(Float, nullable=True)
    err = Column(String(255), nullable=True)  # Error messages if any
    
    # Record metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    battery = relationship("BEPPPBattery", back_populates="live_data")

class Rental(Base):
    __tablename__ = 'rental'
    
    rentral_id = Column(BigInteger, primary_key=True)  # Note: keeping the typo to match existing schema
    battery_id = Column(BigInteger, ForeignKey('bepppbattery.battery_id'))
    user_id = Column(BigInteger, ForeignKey('user.user_id'))
    timestamp_taken = Column(DateTime)
    due_back = Column(DateTime)
    battery_returned_date = Column(DateTime, nullable=True)  # When battery was returned
    battery_return_condition = Column(String(50))
    battery_return_notes = Column(Text)
    status = Column(String(20), default='active')
    
    # *** ENHANCED RENTAL FIELDS ***
    total_cost = Column(Float, nullable=True)  # Total cost including PUE items
    deposit_amount = Column(Float, nullable=True)  # Security deposit
    deposit_returned = Column(Boolean, default=False)  # Whether deposit has been returned
    deposit_returned_date = Column(DateTime, nullable=True)  # When deposit was returned
    is_active = Column(Boolean, default=True)  # Whether rental is currently active
    created_at = Column(DateTime, default=datetime.utcnow)

    # *** PAYMENT & BILLING FIELDS ***
    payment_method = Column(String(50), nullable=True)  # 'upfront', 'on_return', 'deposit_only', 'partial'
    payment_type = Column(String(50), nullable=True)  # 'cash', 'mobile_money', etc. - from PaymentType settings
    payment_status = Column(String(50), nullable=True)  # 'paid', 'partial', 'deposit_only', 'unpaid', 'pending_kwh'
    amount_paid = Column(Float, nullable=True, default=0)  # Amount already paid
    amount_owed = Column(Float, nullable=True, default=0)  # Amount still owed
    kwh_usage_start = Column(Float, nullable=True)  # kWh at rental start
    kwh_usage_end = Column(Float, nullable=True)  # kWh at rental end
    kwh_usage_total = Column(Float, nullable=True)  # Total kWh consumed during rental
    standing_charge = Column(Float, nullable=True)  # Fixed fee per rental
    kwh_rate = Column(Float, nullable=True)  # Rate per kWh if using kWh-based billing

    # *** COST STRUCTURE TRACKING ***
    cost_structure_id = Column(Integer, nullable=True)  # Which cost structure was used
    cost_structure_snapshot = Column(Text, nullable=True)  # JSON snapshot of cost structure at time of rental
    estimated_cost_before_vat = Column(Float, nullable=True)  # Estimated cost before VAT
    estimated_vat = Column(Float, nullable=True)  # Estimated VAT amount
    estimated_cost_total = Column(Float, nullable=True)  # Estimated total including VAT
    final_cost_before_vat = Column(Float, nullable=True)  # Actual final cost before VAT (on return)
    final_vat = Column(Float, nullable=True)  # Actual VAT amount (on return)
    final_cost_total = Column(Float, nullable=True)  # Actual total including VAT (on return)

    # *** SUBSCRIPTION TRACKING ***
    subscription_id = Column(Integer, ForeignKey('user_subscriptions.subscription_id', ondelete='SET NULL'), nullable=True)

    # Backward compatibility - maps to battery_returned_date
    @property
    def date_returned(self):
        return self.battery_returned_date
    
    @date_returned.setter
    def date_returned(self, value):
        self.battery_returned_date = value
    
    # Relations
    battery = relationship("BEPPPBattery", back_populates="rentals")
    user = relationship("User", back_populates="battery_rentals")
    notes = relationship("Note", secondary=rental_notes, back_populates="rentals")
    pue_items = relationship("RentalPUEItem", back_populates="rental")
    subscription = relationship("UserSubscription", back_populates="rentals", foreign_keys="[Rental.subscription_id]")

class RentalPUEItem(Base):
    """
    Enhanced junction table to track individual PUE items in rentals
    with their own return dates and costs
    """
    __tablename__ = 'rental_pue_item'
    
    id = Column(BigInteger, primary_key=True)
    rental_id = Column(BigInteger, ForeignKey('rental.rentral_id'))
    pue_id = Column(BigInteger, ForeignKey('productiveuseequipment.pue_id'))
    
    # Timing
    added_at = Column(DateTime, default=datetime.utcnow)  # When PUE was added to rental
    due_back = Column(DateTime, nullable=True)  # When this PUE item is due back
    returned_date = Column(DateTime, nullable=True)  # When this specific PUE item was returned
    
    # Costs
    rental_cost = Column(Float, nullable=True)  # Cost for this specific PUE item
    deposit_amount = Column(Float, nullable=True)  # Deposit for this specific PUE item
    
    # Status
    is_returned = Column(Boolean, default=False)  # Whether this specific item has been returned
    
    # Relations
    rental = relationship("Rental", back_populates="pue_items")
    pue = relationship("ProductiveUseEquipment", back_populates="rental_items")

class PUERental(Base):
    __tablename__ = 'puerental'

    pue_rental_id = Column(BigInteger, primary_key=True)
    pue_id = Column(BigInteger, ForeignKey('productiveuseequipment.pue_id'))
    user_id = Column(BigInteger, ForeignKey('user.user_id'))
    timestamp_taken = Column(DateTime)
    due_back = Column(DateTime)
    date_returned = Column(DateTime, nullable=True)

    # Enhanced fields
    rental_cost = Column(Float, nullable=True)  # Actual cost paid
    deposit_amount = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    cost_structure_id = Column(Integer, ForeignKey('cost_structures.structure_id', ondelete='SET NULL'), nullable=True)

    # Pay-to-own tracking fields (new design)
    is_pay_to_own = Column(Boolean, server_default='false', nullable=False)
    total_item_cost = Column(Numeric(10, 2), nullable=True)  # Total cost to own the item
    total_paid_towards_ownership = Column(Numeric(10, 2), server_default='0.00', nullable=False)  # Equity payments
    total_rental_fees_paid = Column(Numeric(10, 2), server_default='0.00', nullable=False)  # Non-equity fees
    ownership_percentage = Column(Numeric(5, 2), server_default='0.00', nullable=False)  # % of ownership achieved
    pay_to_own_status = Column(String(20), nullable=True)  # 'active', 'completed', 'returned'
    ownership_completion_date = Column(DateTime, nullable=True)  # When 100% ownership achieved

    # Recurring payment tracking
    has_recurring_payment = Column(Boolean, server_default='false', nullable=False)  # Is this a recurring payment rental
    recurring_payment_frequency = Column(String(50), nullable=True)  # 'monthly', 'weekly', 'daily'
    next_payment_due_date = Column(DateTime(timezone=True), nullable=True)  # When next payment is due
    last_payment_date = Column(DateTime(timezone=True), nullable=True)  # When last payment was made

    # Relations
    pue = relationship("ProductiveUseEquipment", back_populates="pue_rentals")
    user = relationship("User", back_populates="pue_rentals")
    notes = relationship("Note", secondary=pue_rental_notes, back_populates="pue_rentals")
    pay_to_own_ledger = relationship("PUEPayToOwnLedger", back_populates="pue_rental", uselist=False, cascade="all, delete-orphan")

# Analytics helper models for aggregation results
class BatteryUsageStats:
    """Helper class for battery usage statistics"""
    def __init__(self, battery_id, hub_id, total_power_wh, avg_power_w, median_power_w, 
                 data_points, time_period_start, time_period_end):
        self.battery_id = battery_id
        self.hub_id = hub_id
        self.total_power_wh = total_power_wh
        self.avg_power_w = avg_power_w
        self.median_power_w = median_power_w
        self.data_points = data_points
        self.time_period_start = time_period_start
        self.time_period_end = time_period_end

class RentalAnalytics:
    """Helper class for rental analytics"""
    def __init__(self, pue_id, pue_name, total_rentals, avg_rental_duration_hours, 
                 most_frequent_user_id, total_revenue):
        self.pue_id = pue_id
        self.pue_name = pue_name
        self.total_rentals = total_rentals
        self.avg_rental_duration_hours = avg_rental_duration_hours
        self.most_frequent_user_id = most_frequent_user_id
        self.total_revenue = total_revenue
# ============================================================================
# NEW MODELS FOR ACCOUNTS & PRICING SYSTEM
# ============================================================================

class PUEType(Base):
    """PUE equipment types for categorization and pricing"""
    __tablename__ = 'pue_types'
    
    type_id = Column(Integer, primary_key=True, autoincrement=True)
    type_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    hub_id = Column(BigInteger, ForeignKey('solarhub.hub_id', ondelete='CASCADE'), nullable=True)
    created_by = Column(BigInteger, ForeignKey('user.user_id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    hub = relationship("SolarHub", foreign_keys=[hub_id])
    creator = relationship("User", foreign_keys=[created_by])
    pue_items = relationship("ProductiveUseEquipment", back_populates="pue_type")


class PricingConfig(Base):
    """Flexible pricing configurations for batteries and PUE"""
    __tablename__ = 'pricing_configs'

    pricing_id = Column(Integer, primary_key=True, autoincrement=True)
    hub_id = Column(BigInteger, ForeignKey('solarhub.hub_id', ondelete='CASCADE'), nullable=True)
    item_type = Column(String(50), nullable=False)  # 'battery_capacity', 'pue_item', 'pue_type', 'standing_charge'
    item_reference = Column(String(100), nullable=False)  # e.g., "1000" for 1000Wh, or pue_id, or type_id
    unit_type = Column(String(50), nullable=False)  # 'per_day', 'per_hour', 'per_kg', 'per_month', 'per_kwh', 'per_rental'
    price = Column(Float, nullable=False)
    currency = Column(String(3), server_default='USD', nullable=False)
    is_active = Column(Boolean, server_default='true', nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    hub = relationship("SolarHub", foreign_keys=[hub_id])


class DepositPreset(Base):
    """Preset deposit amounts for different item types"""
    __tablename__ = 'deposit_presets'

    preset_id = Column(Integer, primary_key=True, autoincrement=True)
    hub_id = Column(BigInteger, ForeignKey('solarhub.hub_id', ondelete='CASCADE'), nullable=True)
    item_type = Column(String(50), nullable=False)  # 'battery_capacity', 'pue_item', 'pue_type'
    item_reference = Column(String(100), nullable=False)  # e.g., "1000" for 1000Wh, or pue_id, or type_id
    deposit_amount = Column(Float, nullable=False)
    currency = Column(String(3), server_default='USD', nullable=False)
    is_active = Column(Boolean, server_default='true', nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    hub = relationship("SolarHub", foreign_keys=[hub_id])


class PaymentType(Base):
    """Payment type options (cash, mobile money, etc.)"""
    __tablename__ = 'payment_types'

    type_id = Column(Integer, primary_key=True, autoincrement=True)
    hub_id = Column(BigInteger, ForeignKey('solarhub.hub_id', ondelete='CASCADE'), nullable=True)
    type_name = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, server_default='true', nullable=False)
    sort_order = Column(Integer, server_default='0', nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    hub = relationship("SolarHub", foreign_keys=[hub_id])


class CostStructure(Base):
    """Named cost structure templates (e.g., 'Standard Battery Rental', 'Premium with kWh')"""
    __tablename__ = 'cost_structures'

    structure_id = Column(Integer, primary_key=True, autoincrement=True)
    hub_id = Column(BigInteger, ForeignKey('solarhub.hub_id', ondelete='CASCADE'), nullable=True)
    name = Column(String(100), nullable=False)  # e.g., "Standard Battery Rental"
    description = Column(Text, nullable=True)
    item_type = Column(String(50), nullable=False)  # 'battery_capacity', 'pue_item', 'pue_type'
    item_reference = Column(String(100), nullable=False)  # e.g., "1000" for 1000Wh, or pue_id
    deposit_amount = Column(Float, server_default='0', nullable=False)  # Required deposit for this cost structure
    count_initial_checkout_as_recharge = Column(Boolean, server_default='false', nullable=False)  # If true, initial checkout counts as first recharge
    is_active = Column(Boolean, server_default='true', nullable=False)

    # Pay-to-own fields
    is_pay_to_own = Column(Boolean, server_default='false', nullable=False)  # Is this a pay-to-own structure
    item_total_cost = Column(Numeric(10, 2), nullable=True)  # Total cost of item for pay-to-own
    allow_multiple_items = Column(Boolean, server_default='true', nullable=False)  # False for pay-to-own

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    hub = relationship("SolarHub", foreign_keys=[hub_id])
    components = relationship("CostComponent", back_populates="structure", cascade="all, delete-orphan")
    duration_options = relationship("CostStructureDurationOption", back_populates="structure", cascade="all, delete-orphan")


class CostComponent(Base):
    """Individual cost components within a cost structure"""
    __tablename__ = 'cost_components'

    component_id = Column(Integer, primary_key=True, autoincrement=True)
    structure_id = Column(Integer, ForeignKey('cost_structures.structure_id', ondelete='CASCADE'), nullable=False)
    component_name = Column(String(100), nullable=False)  # e.g., "Daily Rate", "kWh Usage", "Admin Fee"
    unit_type = Column(String(50), nullable=False)  # 'per_day', 'per_hour', 'per_kwh', 'per_kg', 'fixed'
    rate = Column(Float, nullable=False)  # Rate per unit
    is_calculated_on_return = Column(Boolean, default=False)  # True for kWh (calculated on actual usage)
    sort_order = Column(Integer, server_default='0', nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Late fee configuration - What happens to this component when rental is overdue
    late_fee_action = Column(String(50), server_default='continue', nullable=False)  # 'continue', 'stop', 'daily_fine', 'weekly_fine'
    late_fee_rate = Column(Float, nullable=True)  # Rate for fines (only applicable for daily_fine/weekly_fine)
    late_fee_grace_days = Column(Integer, server_default='0', nullable=False)  # Grace period before late fees apply to this component

    # Pay-to-own ownership tracking
    contributes_to_ownership = Column(Boolean, server_default='true', nullable=False)  # Does payment build equity?
    is_percentage_of_remaining = Column(Boolean, server_default='false', nullable=False)  # Calculate as % of remaining balance
    percentage_value = Column(Numeric(5, 2), nullable=True)  # If percentage-based, what %

    # Recurring payment configuration
    is_recurring_payment = Column(Boolean, server_default='false', nullable=False)  # Should this component be charged recursively
    recurring_interval = Column(Numeric(5, 2), nullable=True)  # e.g., 1.0, 2.0, 0.5 (custom frequency multiplier)

    # Relationships
    structure = relationship("CostStructure", back_populates="components")


class CostStructureDurationOption(Base):
    """Duration input options for a specific cost structure"""
    __tablename__ = 'cost_structure_duration_options'

    option_id = Column(Integer, primary_key=True, autoincrement=True)
    structure_id = Column(Integer, ForeignKey('cost_structures.structure_id', ondelete='CASCADE'), nullable=False)
    input_type = Column(String(50), nullable=False)  # 'custom', 'dropdown'
    label = Column(String(100), nullable=False)  # e.g., "Rental Duration", "Select Period"

    # For custom input type
    default_value = Column(Integer, nullable=True)  # Default value for custom inputs
    min_value = Column(Integer, nullable=True)  # Minimum value for custom inputs (e.g., 1)
    max_value = Column(Integer, nullable=True)  # Maximum value for custom inputs (e.g., 90)
    custom_unit = Column(String(20), nullable=True)  # 'days', 'weeks', 'months' - for custom input

    # For dropdown type - JSON array of objects: [{"value": 1, "unit": "days", "label": "1 Day"}, ...]
    dropdown_options = Column(Text, nullable=True)

    sort_order = Column(Integer, server_default='0', nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    structure = relationship("CostStructure", back_populates="duration_options")


class RentalDurationPreset(Base):
    """Configurable rental duration presets"""
    __tablename__ = 'rental_duration_presets'

    preset_id = Column(Integer, primary_key=True, autoincrement=True)
    hub_id = Column(BigInteger, ForeignKey('solarhub.hub_id', ondelete='CASCADE'), nullable=True)
    label = Column(String(50), nullable=False)
    duration_value = Column(Integer, nullable=False)
    duration_unit = Column(String(20), nullable=False)  # 'hours', 'days', 'weeks'
    sort_order = Column(Integer, server_default='0', nullable=False)
    is_active = Column(Boolean, server_default='true', nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    hub = relationship("SolarHub", foreign_keys=[hub_id])


class SubscriptionPackage(Base):
    """Subscription packages for recurring battery/PUE rentals"""
    __tablename__ = 'subscription_packages'

    package_id = Column(Integer, primary_key=True, autoincrement=True)
    hub_id = Column(BigInteger, ForeignKey('solarhub.hub_id', ondelete='CASCADE'), nullable=True)
    package_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    billing_period = Column(String(20), nullable=False)  # 'daily', 'weekly', 'monthly', 'yearly'
    price = Column(Float, nullable=False)
    currency = Column(String(3), server_default='USD', nullable=False)
    max_concurrent_batteries = Column(Integer, nullable=True)  # Max batteries at once (null = unlimited)
    max_concurrent_pue = Column(Integer, nullable=True)  # Max PUE items at once (null = unlimited)
    included_kwh = Column(Float, nullable=True)  # Included kWh per billing period (null = unlimited)
    overage_rate_kwh = Column(Float, nullable=True)  # Rate per kWh over included amount
    auto_renew = Column(Boolean, server_default='true', nullable=False)
    is_active = Column(Boolean, server_default='true', nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    hub = relationship("SolarHub", foreign_keys=[hub_id])
    items = relationship("SubscriptionPackageItem", back_populates="package", cascade="all, delete-orphan")
    user_subscriptions = relationship("UserSubscription", back_populates="package")


class SubscriptionPackageItem(Base):
    """Items included in a subscription package"""
    __tablename__ = 'subscription_package_items'

    item_id = Column(Integer, primary_key=True, autoincrement=True)
    package_id = Column(Integer, ForeignKey('subscription_packages.package_id', ondelete='CASCADE'), nullable=False)
    item_type = Column(String(50), nullable=False)  # 'battery', 'battery_capacity', 'pue', 'pue_type', 'pue_item'
    item_reference = Column(String(100), nullable=False)  # 'all' or specific ID
    quantity_limit = Column(Integer, nullable=True)  # How many of this type (null = unlimited)
    sort_order = Column(Integer, server_default='0', nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    package = relationship("SubscriptionPackage", back_populates="items")


class UserSubscription(Base):
    """Active subscriptions for users"""
    __tablename__ = 'user_subscriptions'

    subscription_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('user.user_id', ondelete='CASCADE'), nullable=False)
    package_id = Column(Integer, ForeignKey('subscription_packages.package_id', ondelete='RESTRICT'), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)  # null = active indefinitely
    next_billing_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False)  # 'active', 'paused', 'cancelled', 'expired'
    auto_renew = Column(Boolean, server_default='true', nullable=False)
    kwh_used_current_period = Column(Float, server_default='0', nullable=False)
    period_start_date = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    package = relationship("SubscriptionPackage", back_populates="user_subscriptions")
    rentals = relationship("Rental", back_populates="subscription")


class UserAccount(Base):
    """Financial account for each user"""
    __tablename__ = 'user_accounts'
    
    account_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('user.user_id', ondelete='CASCADE'), nullable=False, unique=True)
    balance = Column(Float, server_default='0.00', nullable=False)
    total_spent = Column(Float, server_default='0.00', nullable=False)
    total_owed = Column(Float, server_default='0.00', nullable=False)
    currency = Column(String(3), server_default='USD', nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="account")
    transactions = relationship("AccountTransaction", back_populates="account", cascade="all, delete-orphan")


class AccountTransaction(Base):
    """All financial transactions"""
    __tablename__ = 'account_transactions'

    transaction_id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('user_accounts.account_id', ondelete='CASCADE'), nullable=False)
    rental_id = Column(BigInteger, ForeignKey('rental.rentral_id', ondelete='SET NULL'), nullable=True)
    transaction_type = Column(String(50), nullable=False)  # 'rental_charge', 'payment', 'credit_adjustment', 'debt_settlement'
    amount = Column(Float, nullable=False)
    balance_after = Column(Float, nullable=False)
    description = Column(Text, nullable=True)

    # Payment tracking fields
    payment_type = Column(String(50), nullable=True)  # 'Cash', 'Mobile Money', 'Bank Transfer', 'Card'
    payment_method = Column(String(50), nullable=True)  # 'upfront', 'on_return', 'partial', 'deposit_only'

    created_by = Column(BigInteger, ForeignKey('user.user_id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    account = relationship("UserAccount", back_populates="transactions")
    rental = relationship("Rental", foreign_keys=[rental_id])
    creator = relationship("User", foreign_keys=[created_by])
    ledger_entries = relationship("LedgerEntry", back_populates="transaction")


# Enhanced Transaction Type Enum
class TransactionType:
    """Specific transaction types for better tracking"""
    RENTAL_CHARGE = 'rental_charge'           # Charge for rental service
    DEPOSIT_COLLECTED = 'deposit_collected'   # Security deposit received
    DEPOSIT_REFUNDED = 'deposit_refunded'     # Deposit returned to customer
    PAYMENT_RECEIVED = 'payment_received'     # Payment for outstanding balance
    CREDIT_ADDED = 'credit_added'            # Admin adds credit to account
    LATE_FEE = 'late_fee'                    # Late return penalty
    SUBSCRIPTION_FEE = 'subscription_fee'     # Monthly subscription charge
    REFUND_ISSUED = 'refund_issued'          # Refund to customer
    ADJUSTMENT_DEBIT = 'adjustment_debit'     # Correction (decrease balance)
    ADJUSTMENT_CREDIT = 'adjustment_credit'   # Correction (increase balance)

    # Legacy support
    PAYMENT = 'payment'
    CREDIT = 'credit'
    CHARGE = 'charge'
    REFUND = 'refund'


class AccountType:
    """Chart of Accounts - Account Types"""
    # Assets (what the business owns)
    CASH = 'cash'
    ACCOUNTS_RECEIVABLE = 'accounts_receivable'
    CUSTOMER_DEPOSITS = 'customer_deposits'

    # Liabilities (what the business owes)
    CUSTOMER_CREDIT_BALANCE = 'customer_credit_balance'
    DEPOSITS_PAYABLE = 'deposits_payable'

    # Revenue (income)
    RENTAL_REVENUE = 'rental_revenue'
    LATE_FEE_REVENUE = 'late_fee_revenue'
    SUBSCRIPTION_REVENUE = 'subscription_revenue'

    # Expenses (costs)
    REFUNDS_EXPENSE = 'refunds_expense'


class LedgerEntry(Base):
    """Double-entry ledger for proper accounting"""
    __tablename__ = 'ledger_entries'

    entry_id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey('account_transactions.transaction_id', ondelete='CASCADE'), nullable=False)

    # Account classification
    account_type = Column(String(50), nullable=False)  # 'asset', 'liability', 'revenue', 'expense'
    account_name = Column(String(100), nullable=False)  # Specific account (e.g., 'cash', 'rental_revenue')

    # Double-entry amounts
    debit = Column(Float, nullable=True)   # Increase in assets/expenses, decrease in liabilities/revenue
    credit = Column(Float, nullable=True)  # Decrease in assets/expenses, increase in liabilities/revenue

    # Tracking
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    transaction = relationship("AccountTransaction", back_populates="ledger_entries")


class AccountReconciliation(Base):
    """Track account reconciliation history"""
    __tablename__ = 'account_reconciliations'

    reconciliation_id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('user_accounts.account_id', ondelete='CASCADE'), nullable=False)

    # Reconciliation details
    expected_balance = Column(Float, nullable=False)   # Calculated from transactions
    actual_balance = Column(Float, nullable=False)     # What's in the account record
    difference = Column(Float, nullable=False)         # Discrepancy

    # Resolution
    status = Column(String(50), default='pending', nullable=False)  # 'pending', 'resolved', 'ignored'
    resolution_notes = Column(Text, nullable=True)
    resolved_by = Column(BigInteger, ForeignKey('user.user_id', ondelete='SET NULL'), nullable=True)

    # Timestamps
    reconciliation_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    account = relationship("UserAccount")
    resolver = relationship("User", foreign_keys=[resolved_by])


class HubSettings(Base):
    """Hub-specific settings"""
    __tablename__ = 'hub_settings'

    setting_id = Column(Integer, primary_key=True, autoincrement=True)
    hub_id = Column(BigInteger, ForeignKey('solarhub.hub_id', ondelete='CASCADE'), nullable=True, unique=True)
    debt_notification_threshold = Column(Float, server_default='-100.00', nullable=False)
    default_currency = Column(String(3), server_default='USD', nullable=False)
    currency_symbol = Column(String(10), nullable=True)  # Custom currency symbol (e.g., 'MK', 'KSh', '$')
    overdue_notification_hours = Column(Integer, server_default='24', nullable=False)  # Hours after due time to send notification
    vat_percentage = Column(Float, server_default='0.00', nullable=False)  # VAT/Tax percentage (e.g., 15.0 for 15%)
    timezone = Column(String(50), server_default='UTC', nullable=False)  # Timezone (e.g., 'Africa/Nairobi', 'Europe/London')
    default_table_rows_per_page = Column(Integer, server_default='50', nullable=False)  # Default rows per page in tables
    battery_status_green_hours = Column(Integer, server_default='3', nullable=False)  # Hours threshold for green status (data received recently)
    battery_status_orange_hours = Column(Integer, server_default='8', nullable=False)  # Hours threshold for orange status (data getting old)
    other_settings = Column(Text, nullable=True)  # JSON string for flexibility
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    hub = relationship("SolarHub", foreign_keys=[hub_id])


class Notification(Base):
    """System notifications for users"""
    __tablename__ = 'notifications'

    notification_id = Column(Integer, primary_key=True, autoincrement=True)
    hub_id = Column(BigInteger, ForeignKey('solarhub.hub_id', ondelete='CASCADE'), nullable=False)
    user_id = Column(BigInteger, nullable=True)  # Null for hub-wide notifications
    notification_type = Column(String(50), nullable=False)  # 'overdue_rental', 'low_battery', 'payment_overdue', etc.
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False)  # 'info', 'warning', 'error', 'success'
    is_read = Column(Boolean, server_default='false', nullable=False)
    link_type = Column(String(50), nullable=True)  # 'rental', 'battery', 'user', 'account'
    link_id = Column(String(100), nullable=True)  # ID of the related entity
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    hub = relationship("SolarHub", foreign_keys=[hub_id])

class WebhookLog(Base):
    """Webhook request/response logging for debugging in production"""
    __tablename__ = 'webhook_logs'

    log_id = Column(BigInteger, primary_key=True, autoincrement=True)
    battery_id = Column(BigInteger, ForeignKey('bepppbattery.battery_id'), nullable=True)
    endpoint = Column(String(255), nullable=False)  # /webhook/live-data, etc.
    method = Column(String(10), nullable=False)  # POST, GET, etc.
    request_headers = Column(Text, nullable=True)  # JSON string of headers
    request_body = Column(Text, nullable=True)  # Full request body
    response_status = Column(Integer, nullable=True)  # HTTP status code
    response_body = Column(Text, nullable=True)  # Full response body
    error_message = Column(Text, nullable=True)  # Error if request failed
    processing_time_ms = Column(Integer, nullable=True)  # Time to process request
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    battery = relationship("BEPPPBattery", foreign_keys=[battery_id])


# ============================================================================
# RENTAL SYSTEM RESTRUCTURE - NEW MODELS
# ============================================================================

class CostStructureBatteryConfig(Base):
    """Battery-specific configuration for cost structures"""
    __tablename__ = 'cost_structure_battery_config'

    config_id = Column(Integer, primary_key=True, autoincrement=True)
    structure_id = Column(Integer, ForeignKey('cost_structures.structure_id', ondelete='CASCADE'), nullable=False, unique=True)

    # Rental period settings
    max_retention_days = Column(Integer, nullable=True)  # Max days before MUST return (soft limit)
    allow_extensions = Column(Boolean, server_default='true', nullable=False)

    # Overdue handling (combinable options)
    grace_period_days = Column(Integer, nullable=True)  # Days of grace before penalties
    daily_fine_after_grace = Column(Float, nullable=True)  # Per-day fine after grace
    auto_rollover_to_next_period = Column(Boolean, server_default='false', nullable=False)  # Auto-extend to next rental period
    rollover_discount_percentage = Column(Float, nullable=True)  # Discount on auto-rollover (e.g., 10%)

    # Recharge settings
    max_recharges = Column(Integer, nullable=True)  # NULL = unlimited
    recharge_fee_per_occurrence = Column(Float, nullable=True)  # Fee per recharge (if per_recharge component not used)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    cost_structure = relationship("CostStructure", foreign_keys=[structure_id])


class CostStructurePUEConfig(Base):
    """PUE-specific configuration for cost structures"""
    __tablename__ = 'cost_structure_pue_config'

    config_id = Column(Integer, primary_key=True, autoincrement=True)
    structure_id = Column(Integer, ForeignKey('cost_structures.structure_id', ondelete='CASCADE'), nullable=False, unique=True)

    # Pay-to-own settings
    supports_pay_to_own = Column(Boolean, server_default='false', nullable=False)
    default_pay_to_own_price = Column(Float, nullable=True)  # Default price to own
    pay_to_own_conversion_formula = Column(String(50), nullable=True)  # 'fixed_price', 'cumulative_rental', 'percentage_based'

    # Inspection settings
    requires_inspections = Column(Boolean, server_default='false', nullable=False)
    inspection_interval_days = Column(Integer, nullable=True)  # Days between required inspections
    inspection_reminder_days = Column(Integer, server_default='7', nullable=False)  # Days before inspection to send reminder

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    cost_structure = relationship("CostStructure", foreign_keys=[structure_id])


class BatteryRental(Base):
    """Battery rentals - separate from PUE rentals"""
    __tablename__ = 'battery_rentals'

    rental_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('user.user_id', ondelete='CASCADE'), nullable=False)
    hub_id = Column(BigInteger, ForeignKey('solarhub.hub_id', ondelete='CASCADE'), nullable=False)

    # Rental period
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)  # Original due date
    actual_return_date = Column(DateTime(timezone=True), nullable=True)

    # Status
    status = Column(String(20), server_default='active', nullable=False)  # active, returned, overdue, cancelled

    # Cost structure tracking
    cost_structure_id = Column(Integer, ForeignKey('cost_structures.structure_id', ondelete='SET NULL'), nullable=True)
    cost_structure_snapshot = Column(Text, nullable=True)  # JSON snapshot

    # Payment tracking
    estimated_cost_before_vat = Column(Float, nullable=True)
    estimated_vat = Column(Float, nullable=True)
    estimated_cost_total = Column(Float, nullable=True)
    final_cost_before_vat = Column(Float, nullable=True)
    final_vat = Column(Float, nullable=True)
    final_cost_total = Column(Float, nullable=True)
    amount_paid = Column(Float, server_default='0', nullable=False)
    amount_owed = Column(Float, server_default='0', nullable=False)
    deposit_amount = Column(Float, server_default='0', nullable=False)
    deposit_returned = Column(Boolean, server_default='false', nullable=False)
    deposit_returned_date = Column(DateTime(timezone=True), nullable=True)
    payment_method = Column(String(50), nullable=True)
    payment_type = Column(String(50), nullable=True)
    payment_status = Column(String(50), nullable=True)

    # Overdue handling
    max_retention_days = Column(Integer, nullable=True)  # From cost structure
    grace_period_days = Column(Integer, nullable=True)
    grace_period_end_date = Column(DateTime(timezone=True), nullable=True)  # Calculated
    daily_fine_after_grace = Column(Float, nullable=True)
    auto_rollover_enabled = Column(Boolean, server_default='false', nullable=False)

    # Recharge tracking
    max_recharges = Column(Integer, nullable=True)  # NULL = unlimited
    recharges_used = Column(Integer, server_default='0', nullable=False)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by = Column(BigInteger, ForeignKey('user.user_id', ondelete='SET NULL'), nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    hub = relationship("SolarHub", foreign_keys=[hub_id])
    cost_structure = relationship("CostStructure", foreign_keys=[cost_structure_id])
    creator = relationship("User", foreign_keys=[created_by])
    battery_items = relationship("BatteryRentalItem", back_populates="rental", cascade="all, delete-orphan")
    notes = relationship("Note", secondary=battery_rental_notes, back_populates="battery_rentals")


class BatteryRentalItem(Base):
    """Individual batteries in a battery rental"""
    __tablename__ = 'battery_rental_items'

    item_id = Column(BigInteger, primary_key=True, autoincrement=True)
    rental_id = Column(BigInteger, ForeignKey('battery_rentals.rental_id', ondelete='CASCADE'), nullable=False)
    battery_id = Column(BigInteger, ForeignKey('bepppbattery.battery_id', ondelete='CASCADE'), nullable=False)

    # Item-specific tracking
    condition_at_checkout = Column(String(50), nullable=True)  # good, fair, damaged
    condition_at_return = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)

    # kWh tracking (if cost structure uses kWh)
    kwh_at_checkout = Column(Float, nullable=True)
    kwh_at_return = Column(Float, nullable=True)
    kwh_used = Column(Float, nullable=True)

    # Timestamps
    added_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    returned_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    rental = relationship("BatteryRental", back_populates="battery_items")
    battery = relationship("BEPPPBattery")


class PUEPayToOwnLedger(Base):
    """Separate tracking for pay-to-own progress"""
    __tablename__ = 'pue_pay_to_own_ledger'

    ledger_id = Column(BigInteger, primary_key=True, autoincrement=True)
    pue_rental_id = Column(BigInteger, ForeignKey('puerental.pue_rental_id', ondelete='CASCADE'), nullable=False)
    user_id = Column(BigInteger, ForeignKey('user.user_id', ondelete='CASCADE'), nullable=False)

    # Pay-to-own tracking
    total_price = Column(Float, nullable=False)  # Original price to own
    amount_paid_to_date = Column(Float, server_default='0', nullable=False)
    amount_remaining = Column(Float, nullable=False)
    # percent_paid calculated as GENERATED column - would need to add in migration if needed

    # Status
    status = Column(String(20), server_default='active', nullable=False)  # active, paid_off, converted_to_rental, defaulted

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    pue_rental = relationship("PUERental", back_populates="pay_to_own_ledger")
    user = relationship("User")
    transactions = relationship("PUEPayToOwnTransaction", back_populates="ledger", cascade="all, delete-orphan")

    # Computed property for percent paid
    @property
    def percent_paid(self):
        if self.total_price > 0:
            return (self.amount_paid_to_date / self.total_price) * 100
        return 0


class PUEPayToOwnTransaction(Base):
    """Individual payments toward PUE ownership"""
    __tablename__ = 'pue_pay_to_own_transactions'

    transaction_id = Column(BigInteger, primary_key=True, autoincrement=True)
    ledger_id = Column(BigInteger, ForeignKey('pue_pay_to_own_ledger.ledger_id', ondelete='CASCADE'), nullable=False)
    account_transaction_id = Column(Integer, ForeignKey('account_transactions.transaction_id', ondelete='SET NULL'), nullable=True)

    amount = Column(Float, nullable=False)
    payment_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    description = Column(Text, nullable=True)

    # Balance tracking
    balance_before = Column(Float, nullable=True)
    balance_after = Column(Float, nullable=True)

    created_by = Column(BigInteger, ForeignKey('user.user_id', ondelete='SET NULL'), nullable=True)

    # Relationships
    ledger = relationship("PUEPayToOwnLedger", back_populates="transactions")
    account_transaction = relationship("AccountTransaction")
    creator = relationship("User", foreign_keys=[created_by])


class PUEInspection(Base):
    """PUE inspection tracking"""
    __tablename__ = 'pue_inspections'

    inspection_id = Column(BigInteger, primary_key=True, autoincrement=True)
    pue_id = Column(BigInteger, ForeignKey('productiveuseequipment.pue_id', ondelete='CASCADE'), nullable=False)
    pue_rental_id = Column(BigInteger, ForeignKey('puerental.pue_rental_id', ondelete='SET NULL'), nullable=True)

    inspection_date = Column(DateTime(timezone=True), nullable=False)
    inspector_id = Column(BigInteger, ForeignKey('user.user_id', ondelete='SET NULL'), nullable=True)

    # Inspection details
    condition = Column(String(50), nullable=True)  # excellent, good, fair, poor, damaged
    issues_found = Column(Text, nullable=True)
    actions_taken = Column(Text, nullable=True)
    next_inspection_due = Column(DateTime(timezone=True), nullable=True)

    # Optional link to notes system
    note_id = Column(BigInteger, ForeignKey('note.id', ondelete='SET NULL'), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    pue = relationship("ProductiveUseEquipment", back_populates="inspections")
    pue_rental = relationship("PUERental")
    inspector = relationship("User", foreign_keys=[inspector_id])
    note = relationship("Note")
