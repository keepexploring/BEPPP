from sqlalchemy import create_engine, Column, BigInteger, String, Float, DateTime, ForeignKey, Table, Integer, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime

Base = declarative_base()

# Junction tables for many-to-many relationships
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

battery_pue_rental = Table('batterypuerental', Base.metadata,
    Column('battery_rental_id', BigInteger, ForeignKey('rental.rentral_id'), primary_key=True),
    Column('pue_rental_id', BigInteger, ForeignKey('puerental.pue_rental_id'), primary_key=True)
)

class SolarHub(Base):
    __tablename__ = 'solarhub'
    
    hub_id = Column(BigInteger, primary_key=True)
    what_three_word_location = Column(String(255))
    solar_capacity_kw = Column(BigInteger)
    country = Column(String(255))
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Relations
    users = relationship("User", back_populates="hub")
    batteries = relationship("BEPPPBattery", back_populates="hub")
    pue_items = relationship("ProductiveUseEquipment", back_populates="hub")

class User(Base):
    __tablename__ = 'user'
    
    user_id = Column(BigInteger, primary_key=True)
    Name = Column(String(255))
    users_identification_document_number = Column(String)
    mobile_number = Column(String(255))
    address = Column(String)
    hub_id = Column(BigInteger, ForeignKey('solarhub.hub_id'))
    user_access_level = Column(String(255))
    username = Column(String(255), unique=True)
    password_hash = Column(String(255))
    
    # Relations
    hub = relationship("SolarHub", back_populates="users")
    battery_rentals = relationship("Rental", back_populates="user")
    pue_rentals = relationship("PUERental", back_populates="user")

class Note(Base):
    __tablename__ = 'note'
    
    id = Column(BigInteger, primary_key=True)
    content = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
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
    
    # Relations
    hub = relationship("SolarHub", back_populates="batteries")
    live_data = relationship("LiveData", back_populates="battery")
    rentals = relationship("Rental", back_populates="battery")
    notes = relationship("Note", secondary=battery_notes, back_populates="batteries")

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
    
    # Relations
    battery = relationship("BEPPPBattery", back_populates="live_data")

class Rental(Base):
    __tablename__ = 'rental'
    
    rentral_id = Column(BigInteger, primary_key=True)  # Note: keeping the typo to match schema
    battery_id = Column(BigInteger, ForeignKey('bepppbattery.battery_id'))
    user_id = Column(BigInteger, ForeignKey('user.user_id'))
    timestamp_taken = Column(DateTime)
    due_back = Column(DateTime)
    date_returned = Column(DateTime)
    
    # Relations
    battery = relationship("BEPPPBattery", back_populates="rentals")
    user = relationship("User", back_populates="battery_rentals")
    notes = relationship("Note", secondary=rental_notes, back_populates="rentals")
    pue_rentals = relationship("PUERental", secondary=battery_pue_rental, back_populates="battery_rentals")

class ProductiveUseEquipment(Base):
    __tablename__ = 'productiveuseequipment'
    
    pue_id = Column(BigInteger, primary_key=True)
    hub_id = Column(BigInteger, ForeignKey('solarhub.hub_id'))
    name = Column(String(255))
    description = Column(String)
    rental_cost = Column(Float)
    status = Column(String, default="available")
    rental_count = Column(Integer, default=0)
    
    # Relations
    hub = relationship("SolarHub", back_populates="pue_items")
    notes = relationship("Note", secondary=pue_notes, back_populates="pue_items")
    pue_rentals = relationship("PUERental", back_populates="pue")

class PUERental(Base):
    __tablename__ = 'puerental'
    
    pue_rental_id = Column(BigInteger, primary_key=True)
    pue_id = Column(BigInteger, ForeignKey('productiveuseequipment.pue_id'))
    user_id = Column(BigInteger, ForeignKey('user.user_id'))
    timestamp_taken = Column(DateTime)
    due_back = Column(DateTime)
    date_returned = Column(DateTime)
    
    # Relations
    pue = relationship("ProductiveUseEquipment", back_populates="pue_rentals")
    user = relationship("User", back_populates="pue_rentals")
    notes = relationship("Note", secondary=pue_rental_notes, back_populates="pue_rentals")
    battery_rentals = relationship("Rental", secondary=battery_pue_rental, back_populates="pue_rentals")