from sqlalchemy import create_engine, Column, BigInteger, String, Float, DateTime, ForeignKey, Table, Integer, func, Boolean, Text
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
    users = relationship("User", back_populates="hub")
    batteries = relationship("BEPPPBattery", back_populates="hub")
    pue_items = relationship("ProductiveUseEquipment", back_populates="hub")
    data_admin_users = relationship("User", secondary=user_hub_access, back_populates="accessible_hubs")

class User(Base):
    __tablename__ = 'user'
    
    user_id = Column(BigInteger, primary_key=True)
    Name = Column(String(255))
    users_identification_document_number = Column(String)
    mobile_number = Column(String(255))
    address = Column(String)
    hub_id = Column(BigInteger, ForeignKey('solarhub.hub_id'))
    user_access_level = Column(String(255))  # Will store UserRole enum values
    username = Column(String(255), unique=True)
    password_hash = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relations
    hub = relationship("SolarHub", back_populates="users")
    battery_rentals = relationship("Rental", back_populates="user")
    pue_rentals = relationship("PUERental", back_populates="user")
    accessible_hubs = relationship("SolarHub", secondary=user_hub_access, back_populates="data_admin_users")

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

class BEPPPBattery(Base):
    __tablename__ = 'bepppbattery'
    
    battery_id = Column(BigInteger, primary_key=True)
    hub_id = Column(BigInteger, ForeignKey('solarhub.hub_id'))
    battery_capacity_wh = Column(BigInteger)
    status = Column(String, default="available")
    battery_secret = Column(String(255), nullable=True)  # Secret for battery self-authentication
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
    usage_location = Column(String(50), default="both")  # Where it can be used: hub_only, battery_only, both
    storage_location = Column(String(255), nullable=True)  # Physical storage location
    suggested_cost_per_day = Column(Float, nullable=True)  # Suggested daily rental cost
    
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
    notes = relationship("Note", secondary=pue_notes, back_populates="pue_items")
    pue_rentals = relationship("PUERental", back_populates="pue")
    rental_items = relationship("RentalPUEItem", back_populates="pue")

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
    is_active = Column(Boolean, default=True)  # Whether rental is currently active
    created_at = Column(DateTime, default=datetime.utcnow)
    
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
    
    # Relations
    pue = relationship("ProductiveUseEquipment", back_populates="pue_rentals")
    user = relationship("User", back_populates="pue_rentals")
    notes = relationship("Note", secondary=pue_rental_notes, back_populates="pue_rentals")

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