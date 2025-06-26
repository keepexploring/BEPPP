from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel, Field
from prisma import Prisma
from typing import Optional, List, Dict, Any, Union, Literal
from datetime import datetime, timezone
import asyncio
import json
import pandas as pd
import io
import os
from passlib.context import CryptContext
import jwt
from jwt.exceptions import InvalidTokenError
from enum import Enum

import pdb

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

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "mySuperSecret123")

# Database connection
prisma = Prisma()

# Enums
class ExportFormat(str, Enum):
    json = "json"
    dataframe = "dataframe"
    csv = "csv"

# Pydantic models for API requests/responses
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
    rentral_id: int  # Note: This matches the typo in the schema
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

# Startup and shutdown events
@app.on_event("startup")
async def startup():
    try:
        await prisma.connect()
        print("✅ Connected to PostgreSQL database")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        raise e

@app.on_event("shutdown")
async def shutdown():
    try:
        await prisma.disconnect()
        print("✅ Disconnected from database")
    except Exception as e:
        print(f"⚠️  Error during shutdown: {e}")

# === WEBHOOK ENDPOINT FOR LIVE DATA ===
@app.post("/webhook/live-data")
async def receive_live_data(webhook_data: WebhookData):
    """Receive live data from Arduino Cloud webhook"""
    try:
        # Find the 'data' property in the values array
        data_property = None
        for value in webhook_data.values:
            if value.get("name") == "data":
                data_property = value
                break
        
        if not data_property:
            raise HTTPException(status_code=400, detail="No 'data' property found in webhook")
        
        # Parse the JSON data
        battery_data = json.loads(data_property["value"])
        
        # Map device_id to battery_id (you'll need to adjust this based on your device mapping)
        # For now, we'll try to extract from the device_id or use a lookup table
        device_to_battery_mapping = {
            "0291f60a-cfaf-462d-9e82-5ce662fb3823": 1  # Add your device->battery mappings here
        }
        
        battery_id = device_to_battery_mapping.get(webhook_data.device_id)
        if not battery_id:
            raise HTTPException(status_code=400, detail=f"Unknown device_id: {webhook_data.device_id}")
        
        # Generate unique ID for this data point
        unique_id = int(datetime.now().timestamp() * 1000000)
        
        # Parse timestamp
        timestamp = None
        if battery_data.get("timestamp"):
            try:
                timestamp = datetime.fromisoformat(battery_data["timestamp"].replace('Z', '+00:00'))
            except:
                timestamp = datetime.now(timezone.utc)
        else:
            timestamp = datetime.now(timezone.utc)
        
        # Create LiveData record
        live_data = await prisma.livedata.create(
            data={
                "id": unique_id,
                "battery_id": battery_id,
                "state_of_charge": battery_data.get("state_of_charge"),
                "voltage": battery_data.get("voltage"),
                "current_amps": battery_data.get("current_amps"),
                "power_watts": battery_data.get("power_watts"),
                "time_remaining": battery_data.get("time_remaining"),
                "temp_battery": battery_data.get("temp_battery"),
                "amp_hours_consumed": battery_data.get("amp_hours_consumed"),
                "charging_current": battery_data.get("charging_current"),
                "timestamp": timestamp,
                "usb_voltage": battery_data.get("usb_voltage"),
                "usb_power": battery_data.get("usb_power"),
                "usb_current": battery_data.get("usb_current"),
                "latitude": battery_data.get("latitude"),
                "longitude": battery_data.get("longitude"),
                "altitude": battery_data.get("altitude"),
                "SD_card_storage_remaining": battery_data.get("SD_card_storage_remaining"),
                "battery_orientation": battery_data.get("battery_orientation"),
                "number_GPS_satellites_for_fix": battery_data.get("number_GPS_satellites_for_fix"),
                "mobile_signal_strength": battery_data.get("mobile_signal_strength"),
                "event_type": battery_data.get("event_type"),
                "new_battery_cycle": battery_data.get("new_battery_cycle")
            }
        )
        
        return {"status": "success", "data_id": live_data.id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing live data: {str(e)}")

# === SOLAR HUB ENDPOINTS ===
@app.post("/hubs/", dependencies=[Depends(verify_token)])
async def create_hub(hub: SolarHubCreate):
    """Create a new solar hub"""
    try:
        result = await prisma.solarhub.create(data=hub.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/hubs/{hub_id}", dependencies=[Depends(verify_token)])
async def get_hub(hub_id: int):
    """Get a solar hub by ID"""
    hub = await prisma.solarhub.find_unique(where={"hub_id": hub_id})
    if not hub:
        raise HTTPException(status_code=404, detail="Hub not found")
    return hub

@app.put("/hubs/{hub_id}", dependencies=[Depends(verify_token)])
async def update_hub(hub_id: int, hub_update: SolarHubUpdate):
    """Update a solar hub"""
    try:
        result = await prisma.solarhub.update(
            where={"hub_id": hub_id},
            data=hub_update.dict(exclude_unset=True)
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/hubs/{hub_id}", dependencies=[Depends(verify_token)])
async def delete_hub(hub_id: int):
    """Delete a solar hub"""
    try:
        await prisma.solarhub.delete(where={"hub_id": hub_id})
        return {"message": "Hub deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/hubs/", dependencies=[Depends(verify_token)])
async def list_hubs():
    """List all solar hubs"""
    return await prisma.solarhub.find_many()

# === USER ENDPOINTS ===
@app.post("/users/", dependencies=[Depends(verify_token)])
async def create_user(user: UserCreate):
    """Create a new user"""
    try:
        # Hash the password
        user_data = user.dict()
        user_data["password_hash"] = hash_password(user_data.pop("password"))
        # Fix field name to match schema
        user_data["Name"] = user_data.pop("name")
        
        result = await prisma.user.create(data=user_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/users/{user_id}", dependencies=[Depends(verify_token)])
async def get_user(user_id: int):
    """Get a user by ID"""
    user = await prisma.user.find_unique(where={"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/users/{user_id}", dependencies=[Depends(verify_token)])
async def update_user(user_id: int, user_update: UserUpdate):
    """Update a user"""
    try:
        update_data = user_update.dict(exclude_unset=True)
        if "password" in update_data:
            update_data["password_hash"] = hash_password(update_data.pop("password"))
        if "name" in update_data:
            update_data["Name"] = update_data.pop("name")
        
        result = await prisma.user.update(
            where={"user_id": user_id},
            data=update_data
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/users/{user_id}", dependencies=[Depends(verify_token)])
async def delete_user(user_id: int):
    """Delete a user"""
    try:
        await prisma.user.delete(where={"user_id": user_id})
        return {"message": "User deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/hubs/{hub_id}/users", dependencies=[Depends(verify_token)])
async def list_hub_users(hub_id: int):
    """List all users for a hub"""
    return await prisma.user.find_many(where={"hub_id": hub_id})

# === BATTERY ENDPOINTS ===
@app.post("/batteries/", dependencies=[Depends(verify_token)])
async def create_battery(battery: BatteryCreate):
    """Create a new battery"""
    try:
        result = await prisma.bepppbattery.create(data=battery.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/batteries/{battery_id}", dependencies=[Depends(verify_token)])
async def get_battery(battery_id: int):
    """Get a battery by ID"""
    battery = await prisma.bepppbattery.find_unique(where={"battery_id": battery_id})
    if not battery:
        raise HTTPException(status_code=404, detail="Battery not found")
    return battery

@app.put("/batteries/{battery_id}", dependencies=[Depends(verify_token)])
async def update_battery(battery_id: int, battery_update: BatteryUpdate):
    """Update a battery"""
    try:
        result = await prisma.bepppbattery.update(
            where={"battery_id": battery_id},
            data=battery_update.dict(exclude_unset=True)
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/batteries/{battery_id}", dependencies=[Depends(verify_token)])
async def delete_battery(battery_id: int):
    """Delete a battery"""
    try:
        await prisma.bepppbattery.delete(where={"battery_id": battery_id})
        return {"message": "Battery deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/hubs/{hub_id}/batteries", dependencies=[Depends(verify_token)])
async def list_hub_batteries(hub_id: int):
    """List all batteries for a hub"""
    return await prisma.bepppbattery.find_many(where={"hub_id": hub_id})

# === BATTERY RENTAL ENDPOINTS ===
@app.post("/rentals/", dependencies=[Depends(verify_token)])
async def create_rental(rental: RentalCreate):
    """Create a new battery rental"""
    try:
        result = await prisma.rental.create(data=rental.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/rentals/{rental_id}", dependencies=[Depends(verify_token)])
async def get_rental(rental_id: int):
    """Get rental by ID"""
    rental = await prisma.rental.find_unique(where={"rentral_id": rental_id})
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")
    return rental

@app.put("/rentals/{rental_id}", dependencies=[Depends(verify_token)])
async def update_rental(rental_id: int, rental_update: RentalUpdate):
    """Update rental"""
    try:
        result = await prisma.rental.update(
            where={"rentral_id": rental_id},
            data=rental_update.dict(exclude_unset=True)
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/rentals/{rental_id}", dependencies=[Depends(verify_token)])
async def delete_rental(rental_id: int):
    """Delete rental"""
    try:
        await prisma.rental.delete(where={"rentral_id": rental_id})
        return {"message": "Rental deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/users/{user_id}/rentals", dependencies=[Depends(verify_token)])
async def list_user_rentals(user_id: int):
    """List all rentals for a user"""
    return await prisma.rental.find_many(where={"user_id": user_id})

@app.get("/batteries/{battery_id}/rentals", dependencies=[Depends(verify_token)])
async def list_battery_rentals(battery_id: int):
    """List all rentals for a battery"""
    return await prisma.rental.find_many(where={"battery_id": battery_id})

# === PRODUCTIVE USE EQUIPMENT ENDPOINTS ===
@app.post("/pue/", dependencies=[Depends(verify_token)])
async def create_pue(pue: PUECreate):
    """Create new productive use equipment"""
    try:
        result = await prisma.productiveuseequipment.create(data=pue.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/pue/{pue_id}", dependencies=[Depends(verify_token)])
async def get_pue(pue_id: int):
    """Get PUE by ID"""
    pue = await prisma.productiveuseequipment.find_unique(where={"pue_id": pue_id})
    if not pue:
        raise HTTPException(status_code=404, detail="PUE not found")
    return pue

@app.put("/pue/{pue_id}", dependencies=[Depends(verify_token)])
async def update_pue(pue_id: int, pue_update: PUEUpdate):
    """Update PUE"""
    try:
        result = await prisma.productiveuseequipment.update(
            where={"pue_id": pue_id},
            data=pue_update.dict(exclude_unset=True)
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/pue/{pue_id}", dependencies=[Depends(verify_token)])
async def delete_pue(pue_id: int):
    """Delete PUE"""
    try:
        await prisma.productiveuseequipment.delete(where={"pue_id": pue_id})
        return {"message": "PUE deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/hubs/{hub_id}/pue", dependencies=[Depends(verify_token)])
async def list_hub_pue(hub_id: int):
    """List all PUE for a hub"""
    return await prisma.productiveuseequipment.find_many(where={"hub_id": hub_id})

# === PUE RENTAL ENDPOINTS ===
@app.post("/pue-rentals/", dependencies=[Depends(verify_token)])
async def create_pue_rental(rental: PUERentalCreate):
    """Create a new PUE rental"""
    try:
        result = await prisma.puerental.create(data=rental.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/pue-rentals/{rental_id}", dependencies=[Depends(verify_token)])
async def get_pue_rental(rental_id: int):
    """Get PUE rental by ID"""
    rental = await prisma.puerental.find_unique(where={"pue_rental_id": rental_id})
    if not rental:
        raise HTTPException(status_code=404, detail="PUE rental not found")
    return rental

@app.put("/pue-rentals/{rental_id}", dependencies=[Depends(verify_token)])
async def update_pue_rental(rental_id: int, rental_update: PUERentalUpdate):
    """Update PUE rental"""
    try:
        result = await prisma.puerental.update(
            where={"pue_rental_id": rental_id},
            data=rental_update.dict(exclude_unset=True)
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/pue-rentals/{rental_id}", dependencies=[Depends(verify_token)])
async def delete_pue_rental(rental_id: int):
    """Delete PUE rental"""
    try:
        await prisma.puerental.delete(where={"pue_rental_id": rental_id})
        return {"message": "PUE rental deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# === NOTES ENDPOINTS ===
@app.post("/notes/", dependencies=[Depends(verify_token)])
async def create_note(note: NoteCreate):
    """Create a new note"""
    try:
        result = await prisma.note.create(data=note.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/notes/{note_id}", dependencies=[Depends(verify_token)])
async def get_note(note_id: int):
    """Get note by ID"""
    note = await prisma.note.find_unique(where={"id": note_id})
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

@app.put("/notes/{note_id}", dependencies=[Depends(verify_token)])
async def update_note(note_id: int, note_update: NoteUpdate):
    """Update note"""
    try:
        result = await prisma.note.update(
            where={"id": note_id},
            data=note_update.dict(exclude_unset=True)
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/notes/{note_id}", dependencies=[Depends(verify_token)])
async def delete_note(note_id: int):
    """Delete note"""
    try:
        await prisma.note.delete(where={"id": note_id})
        return {"message": "Note deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# === DATA QUERY ENDPOINTS ===
@app.get("/data/battery/{battery_id}", dependencies=[Depends(verify_token)])
async def get_battery_data(
    battery_id: int,
    start_timestamp: Optional[datetime] = Query(None, description="Start timestamp (ISO format)"),
    end_timestamp: Optional[datetime] = Query(None, description="End timestamp (ISO format)"),
    limit: Optional[int] = Query(1000, description="Maximum number of records to return"),
    format: ExportFormat = Query(ExportFormat.json, description="Export format")
):
    """Get live data for a specific battery between timestamps"""
    try:
        # Build where clause
        where_clause = {"battery_id": battery_id}
        
        if start_timestamp or end_timestamp:
            timestamp_filter = {}
            if start_timestamp:
                timestamp_filter["gte"] = start_timestamp
            if end_timestamp:
                timestamp_filter["lte"] = end_timestamp
            where_clause["timestamp"] = timestamp_filter
        
        # Query data with limit
        data = await prisma.livedata.find_many(
            where=where_clause,
            order={"timestamp": "desc"},
            take=limit
        )
        
        if not data:
            raise HTTPException(status_code=404, detail=f"No data found for battery {battery_id}")
        
        # Convert to dict for processing
        data_dicts = [item.dict() for item in data]
        
        # Return based on format
        if format == ExportFormat.json:
            return {
                "battery_id": battery_id,
                "data": data_dicts,
                "count": len(data_dicts),
                "start_timestamp": start_timestamp,
                "end_timestamp": end_timestamp
            }
        
        elif format == ExportFormat.dataframe:
            # Return dataframe info
            df = pd.DataFrame(data_dicts)
            return {
                "battery_id": battery_id,
                "dataframe_info": {
                    "shape": df.shape,
                    "columns": df.columns.tolist(),
                    "dtypes": df.dtypes.astype(str).to_dict(),
                    "sample": df.head().to_dict(orient="records") if not df.empty else []
                },
                "data": data_dicts,
                "count": len(data_dicts)
            }
        
        elif format == ExportFormat.csv:
            # Return CSV data
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

@app.post("/data/query", dependencies=[Depends(verify_token)])
async def query_live_data(query: DataQuery):
    """Query live data with flexible filtering and export options"""
    try:
        # Build where clause
        where_clause = {}
        
        if query.battery_ids:
            where_clause["battery_id"] = {"in": query.battery_ids}
        
        if query.start_timestamp or query.end_timestamp:
            timestamp_filter = {}
            if query.start_timestamp:
                timestamp_filter["gte"] = query.start_timestamp
            if query.end_timestamp:
                timestamp_filter["lte"] = query.end_timestamp
            where_clause["timestamp"] = timestamp_filter
        
        # Query data
        data = await prisma.livedata.find_many(
            where=where_clause,
            order={"timestamp": "desc"}
        )
        
        # Convert to dict for processing
        data_dicts = [item.dict() for item in data]
        
        # Filter fields if specified
        if query.fields:
            filtered_data = []
            for item in data_dicts:
                filtered_item = {field: item.get(field) for field in query.fields if field in item}
                filtered_data.append(filtered_item)
            data_dicts = filtered_data
        
        # Return based on format
        if query.format == ExportFormat.json:
            return {"data": data_dicts, "count": len(data_dicts)}
        
        elif query.format == ExportFormat.dataframe:
            # Return dataframe info (since we can't send actual DataFrame via JSON)
            df = pd.DataFrame(data_dicts)
            return {
                "dataframe_info": {
                    "shape": df.shape,
                    "columns": df.columns.tolist(),
                    "dtypes": df.dtypes.astype(str).to_dict(),
                    "sample": df.head().to_dict(orient="records") if not df.empty else []
                },
                "data": data_dicts,
                "count": len(data_dicts)
            }
        
        elif query.format == ExportFormat.csv:
            # Return CSV data
            df = pd.DataFrame(data_dicts)
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_content = csv_buffer.getvalue()
            
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=live_data.csv"}
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying data: {str(e)}")

@app.get("/data/latest/{battery_id}", dependencies=[Depends(verify_token)])
async def get_latest_data(battery_id: int):
    """Get the latest data point for a battery"""
    data = await prisma.livedata.find_first(
        where={"battery_id": battery_id},
        order={"timestamp": "desc"}
    )
    if not data:
        raise HTTPException(status_code=404, detail="No data found for this battery")
    return data

@app.get("/data/summary/{battery_id}", dependencies=[Depends(verify_token)])
async def get_battery_summary(
    battery_id: int,
    hours: int = Query(24, description="Hours to look back for summary")
):
    """Get summary statistics for a battery over the specified time period"""
    try:
        # Calculate start time
        start_time = datetime.now(timezone.utc) - pd.Timedelta(hours=hours)
        
        # Query data
        data = await prisma.livedata.find_many(
            where={
                "battery_id": battery_id,
                "timestamp": {"gte": start_time}
            },
            order={"timestamp": "desc"}
        )
        
        if not data:
            raise HTTPException(status_code=404, detail="No data found for this battery")
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame([item.dict() for item in data])
        
        # Calculate summary statistics
        numeric_columns = ['state_of_charge', 'voltage', 'current_amps', 'power_watts', 'temp_battery']
        summary = {}
        
        for col in numeric_columns:
            if col in df.columns and not df[col].isna().all():
                summary[col] = {
                    "current": float(df[col].iloc[0]) if not pd.isna(df[col].iloc[0]) else None,
                    "average": float(df[col].mean()),
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    "std": float(df[col].std())
                }
        
        return {
            "battery_id": battery_id,
            "period_hours": hours,
            "data_points": len(data),
            "latest_timestamp": data[0].timestamp if data else None,
            "summary": summary
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")

# === AUTHENTICATION ENDPOINTS ===
@app.post("/auth/token")
async def create_token(user_login: UserLogin):
    """Create authentication token"""
    try:
        # Verify username/password against database
        user = await prisma.user.find_unique(where={"username": user_login.username})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Verify password
        if not verify_password(user_login.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Create token
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
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        await prisma.connect()
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