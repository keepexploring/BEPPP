from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import json
import pandas as pd
import io
from passlib.context import CryptContext
import jwt
from jwt.exceptions import InvalidTokenError
from enum import Enum

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import get_db, init_db
from models import *
from config import SECRET_KEY, ALGORITHM, DEBUG

# Initialize FastAPI app
app = FastAPI(
    title="Solar Hub Management API",
    description="API for managing solar hubs, batteries, users, and live data",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Enums
class ExportFormat(str, Enum):
    json = "json"
    dataframe = "dataframe"
    csv = "csv"

# Pydantic models remain the same
class SolarHubCreate(BaseModel):
    hub_id: int
    what_three_word_location: Optional[str] = None
    solar_capacity_kw: Optional[int] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class SolarHubUpdate(BaseModel):
    what_three_word_location: Optional[str] = None
    solar_capacity_kw: Optional[int] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class UserCreate(BaseModel):
    user_id: int
    name: str
    users_identification_document_number: Optional[str] = None
    mobile_number: Optional[str] = None
    address: Optional[str] = None
    hub_id: int
    user_access_level: str
    username: str
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    users_identification_document_number: Optional[str] = None
    mobile_number: Optional[str] = None
    address: Optional[str] = None
    user_access_level: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class BatteryCreate(BaseModel):
    battery_id: int
    hub_id: int
    battery_capacity_wh: Optional[int] = None
    status: Optional[str] = "available"

class BatteryUpdate(BaseModel):
    battery_capacity_wh: Optional[int] = None
    status: Optional[str] = None

class RentalCreate(BaseModel):
    rentral_id: int
    battery_id: int
    user_id: int
    timestamp_taken: datetime
    due_back: Optional[datetime] = None

class RentalUpdate(BaseModel):
    due_back: Optional[datetime] = None
    date_returned: Optional[datetime] = None

class PUECreate(BaseModel):
    pue_id: int
    hub_id: int
    name: str
    description: Optional[str] = None
    rental_cost: Optional[float] = None
    status: Optional[str] = "available"

class PUEUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    rental_cost: Optional[float] = None
    status: Optional[str] = None

class PUERentalCreate(BaseModel):
    pue_rental_id: int
    pue_id: int
    user_id: int
    timestamp_taken: datetime
    due_back: Optional[datetime] = None

class PUERentalUpdate(BaseModel):
    due_back: Optional[datetime] = None
    date_returned: Optional[datetime] = None

class NoteCreate(BaseModel):
    id: int
    content: str

class NoteUpdate(BaseModel):
    content: str

class WebhookData(BaseModel):
    event_id: str
    webhook_id: str
    device_id: str
    thing_id: str
    values: List[Dict[str, Any]]

class DataQuery(BaseModel):
    battery_ids: Optional[List[int]] = None
    start_timestamp: Optional[datetime] = None
    end_timestamp: Optional[datetime] = None
    fields: Optional[List[str]] = None
    format: ExportFormat = ExportFormat.json

# Authentication functions
def create_access_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Startup event
@app.on_event("startup")
async def startup():
    try:
        init_db()
        print("✅ Database tables created/verified")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise e

# === WEBHOOK ENDPOINT FOR LIVE DATA ===
@app.post("/webhook/live-data")
async def receive_live_data(webhook_data: WebhookData, db: Session = Depends(get_db)):
    """Receive live data from Arduino Cloud webhook"""
    try:
        data_property = None
        for value in webhook_data.values:
            if value.get("name") == "data":
                data_property = value
                break
        
        if not data_property:
            raise HTTPException(status_code=400, detail="No 'data' property found in webhook")
        
        battery_data = json.loads(data_property["value"])
        
        device_to_battery_mapping = {
            "0291f60a-cfaf-462d-9e82-5ce662fb3823": 1
        }
        
        battery_id = device_to_battery_mapping.get(webhook_data.device_id)
        if not battery_id:
            raise HTTPException(status_code=400, detail=f"Unknown device_id: {webhook_data.device_id}")
        
        unique_id = int(datetime.now().timestamp() * 1000000)
        
        timestamp = None
        if battery_data.get("timestamp"):
            try:
                timestamp = datetime.fromisoformat(battery_data["timestamp"].replace('Z', '+00:00'))
            except:
                timestamp = datetime.now(timezone.utc)
        else:
            timestamp = datetime.now(timezone.utc)
        
        live_data = LiveData(
            id=unique_id,
            battery_id=battery_id,
            state_of_charge=battery_data.get("state_of_charge"),
            voltage=battery_data.get("voltage"),
            current_amps=battery_data.get("current_amps"),
            power_watts=battery_data.get("power_watts"),
            time_remaining=battery_data.get("time_remaining"),
            temp_battery=battery_data.get("temp_battery"),
            amp_hours_consumed=battery_data.get("amp_hours_consumed"),
            charging_current=battery_data.get("charging_current"),
            timestamp=timestamp,
            usb_voltage=battery_data.get("usb_voltage"),
            usb_power=battery_data.get("usb_power"),
            usb_current=battery_data.get("usb_current"),
            latitude=battery_data.get("latitude"),
            longitude=battery_data.get("longitude"),
            altitude=battery_data.get("altitude"),
            SD_card_storage_remaining=battery_data.get("SD_card_storage_remaining"),
            battery_orientation=battery_data.get("battery_orientation"),
            number_GPS_satellites_for_fix=battery_data.get("number_GPS_satellites_for_fix"),
            mobile_signal_strength=battery_data.get("mobile_signal_strength"),
            event_type=battery_data.get("event_type"),
            new_battery_cycle=battery_data.get("new_battery_cycle")
        )
        
        db.add(live_data)
        db.commit()
        db.refresh(live_data)
        
        return {"status": "success", "data_id": live_data.id}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing live data: {str(e)}")

# === SOLAR HUB ENDPOINTS ===
@app.post("/hubs/", dependencies=[Depends(verify_token)])
async def create_hub(hub: SolarHubCreate, db: Session = Depends(get_db)):
    """Create a new solar hub"""
    try:
        db_hub = SolarHub(**hub.dict())
        db.add(db_hub)
        db.commit()
        db.refresh(db_hub)
        return db_hub
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/hubs/{hub_id}", dependencies=[Depends(verify_token)])
async def get_hub(hub_id: int, db: Session = Depends(get_db)):
    """Get a solar hub by ID"""
    hub = db.query(SolarHub).filter(SolarHub.hub_id == hub_id).first()
    if not hub:
        raise HTTPException(status_code=404, detail="Hub not found")
    return hub

@app.put("/hubs/{hub_id}", dependencies=[Depends(verify_token)])
async def update_hub(hub_id: int, hub_update: SolarHubUpdate, db: Session = Depends(get_db)):
    """Update a solar hub"""
    try:
        hub = db.query(SolarHub).filter(SolarHub.hub_id == hub_id).first()
        if not hub:
            raise HTTPException(status_code=404, detail="Hub not found")
        
        for key, value in hub_update.dict(exclude_unset=True).items():
            setattr(hub, key, value)
        
        db.commit()
        db.refresh(hub)
        return hub
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/hubs/{hub_id}", dependencies=[Depends(verify_token)])
async def delete_hub(hub_id: int, db: Session = Depends(get_db)):
    """Delete a solar hub"""
    try:
        hub = db.query(SolarHub).filter(SolarHub.hub_id == hub_id).first()
        if not hub:
            raise HTTPException(status_code=404, detail="Hub not found")
        
        db.delete(hub)
        db.commit()
        return {"message": "Hub deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/hubs/", dependencies=[Depends(verify_token)])
async def list_hubs(db: Session = Depends(get_db)):
    """List all solar hubs"""
    return db.query(SolarHub).all()

# === USER ENDPOINTS ===
@app.post("/users/", dependencies=[Depends(verify_token)])
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    try:
        user_data = user.dict()
        user_data["password_hash"] = hash_password(user_data.pop("password"))
        user_data["Name"] = user_data.pop("name")
        
        db_user = User(**user_data)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/users/{user_id}", dependencies=[Depends(verify_token)])
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get a user by ID"""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/users/{user_id}", dependencies=[Depends(verify_token)])
async def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    """Update a user"""
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        update_data = user_update.dict(exclude_unset=True)
        if "password" in update_data:
            update_data["password_hash"] = hash_password(update_data.pop("password"))
        if "name" in update_data:
            update_data["Name"] = update_data.pop("name")
        
        for key, value in update_data.items():
            setattr(user, key, value)
        
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/users/{user_id}", dependencies=[Depends(verify_token)])
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete a user"""
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        db.delete(user)
        db.commit()
        return {"message": "User deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/hubs/{hub_id}/users", dependencies=[Depends(verify_token)])
async def list_hub_users(hub_id: int, db: Session = Depends(get_db)):
    """List all users for a hub"""
    return db.query(User).filter(User.hub_id == hub_id).all()

# === BATTERY ENDPOINTS ===
@app.post("/batteries/", dependencies=[Depends(verify_token)])
async def create_battery(battery: BatteryCreate, db: Session = Depends(get_db)):
    """Create a new battery"""
    try:
        db_battery = BEPPPBattery(**battery.dict())
        db.add(db_battery)
        db.commit()
        db.refresh(db_battery)
        return db_battery
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/batteries/{battery_id}", dependencies=[Depends(verify_token)])
async def get_battery(battery_id: int, db: Session = Depends(get_db)):
    """Get a battery by ID"""
    battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == battery_id).first()
    if not battery:
        raise HTTPException(status_code=404, detail="Battery not found")
    return battery

@app.put("/batteries/{battery_id}", dependencies=[Depends(verify_token)])
async def update_battery(battery_id: int, battery_update: BatteryUpdate, db: Session = Depends(get_db)):
    """Update a battery"""
    try:
        battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == battery_id).first()
        if not battery:
            raise HTTPException(status_code=404, detail="Battery not found")
        
        for key, value in battery_update.dict(exclude_unset=True).items():
            setattr(battery, key, value)
        
        db.commit()
        db.refresh(battery)
        return battery
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/batteries/{battery_id}", dependencies=[Depends(verify_token)])
async def delete_battery(battery_id: int, db: Session = Depends(get_db)):
    """Delete a battery"""
    try:
        battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == battery_id).first()
        if not battery:
            raise HTTPException(status_code=404, detail="Battery not found")
        
        db.delete(battery)
        db.commit()
        return {"message": "Battery deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/hubs/{hub_id}/batteries", dependencies=[Depends(verify_token)])
async def list_hub_batteries(hub_id: int, db: Session = Depends(get_db)):
    """List all batteries for a hub"""
    return db.query(BEPPPBattery).filter(BEPPPBattery.hub_id == hub_id).all()

# === RENTAL ENDPOINTS ===
@app.post("/rentals/", dependencies=[Depends(verify_token)])
async def create_rental(rental: RentalCreate, db: Session = Depends(get_db)):
    """Create a new battery rental"""
    try:
        db_rental = Rental(**rental.dict())
        db.add(db_rental)
        db.commit()
        db.refresh(db_rental)
        return db_rental
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/rentals/{rental_id}", dependencies=[Depends(verify_token)])
async def get_rental(rental_id: int, db: Session = Depends(get_db)):
    """Get rental by ID"""
    rental = db.query(Rental).filter(Rental.rentral_id == rental_id).first()
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")
    return rental

@app.put("/rentals/{rental_id}", dependencies=[Depends(verify_token)])
async def update_rental(rental_id: int, rental_update: RentalUpdate, db: Session = Depends(get_db)):
    """Update rental"""
    try:
        rental = db.query(Rental).filter(Rental.rentral_id == rental_id).first()
        if not rental:
            raise HTTPException(status_code=404, detail="Rental not found")
        
        for key, value in rental_update.dict(exclude_unset=True).items():
            setattr(rental, key, value)
        
        db.commit()
        db.refresh(rental)
        return rental
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/rentals/{rental_id}", dependencies=[Depends(verify_token)])
async def delete_rental(rental_id: int, db: Session = Depends(get_db)):
    """Delete rental"""
    try:
        rental = db.query(Rental).filter(Rental.rentral_id == rental_id).first()
        if not rental:
            raise HTTPException(status_code=404, detail="Rental not found")
        
        db.delete(rental)
        db.commit()
        return {"message": "Rental deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

# === DATA QUERY ENDPOINTS ===
@app.get("/data/battery/{battery_id}", dependencies=[Depends(verify_token)])
async def get_battery_data(
    battery_id: int,
    db: Session = Depends(get_db),
    start_timestamp: Optional[datetime] = Query(None),
    end_timestamp: Optional[datetime] = Query(None),
    limit: Optional[int] = Query(1000),
    format: ExportFormat = Query(ExportFormat.json)
):
    """Get live data for a specific battery between timestamps"""
    try:
        query = db.query(LiveData).filter(LiveData.battery_id == battery_id)
        
        if start_timestamp:
            query = query.filter(LiveData.timestamp >= start_timestamp)
        if end_timestamp:
            query = query.filter(LiveData.timestamp <= end_timestamp)
        
        data = query.order_by(LiveData.timestamp.desc()).limit(limit).all()
        
        if not data:
            raise HTTPException(status_code=404, detail=f"No data found for battery {battery_id}")
        
        # Convert to dict
        data_dicts = [
            {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
            for obj in data
        ]
        
        if format == ExportFormat.json:
            return {
                "battery_id": battery_id,
                "data": data_dicts,
                "count": len(data_dicts)
            }
        elif format == ExportFormat.csv:
            df = pd.DataFrame(data_dicts)
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_content = csv_buffer.getvalue()
            
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=battery_{battery_id}_data.csv"}
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving battery data: {str(e)}")

@app.get("/data/latest/{battery_id}", dependencies=[Depends(verify_token)])
async def get_latest_data(battery_id: int, db: Session = Depends(get_db)):
    """Get the latest data point for a battery"""
    data = db.query(LiveData).filter(LiveData.battery_id == battery_id).order_by(LiveData.timestamp.desc()).first()
    if not data:
        raise HTTPException(status_code=404, detail="No data found for this battery")
    return data

# === AUTHENTICATION ENDPOINTS ===
@app.post("/auth/token")
async def create_token(user_login: UserLogin, db: Session = Depends(get_db)):
    """Create authentication token"""
    try:
        user = db.query(User).filter(User.username == user_login.username).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        if not verify_password(user_login.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        token_data = {
            "sub": user.username,
            "user_id": user.user_id,
            "role": user.user_access_level
        }
        token = create_access_token(token_data)
        
        return {"access_token": token, "token_type": "bearer"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )

# === HEALTH CHECK ===
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        db.execute("SELECT 1")
        db_status = "connected"
    except:
        db_status = "disconnected"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "database": db_status
    }

# === ROOT ENDPOINT ===
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Solar Hub Management API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)