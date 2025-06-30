from fastapi import FastAPI, HTTPException, Depends, status, Query, Request
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
import logging

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import get_db, init_db
from models import *
from config import SECRET_KEY, ALGORITHM, DEBUG

# Configure logging based on DEBUG flag
def setup_webhook_logging():
    """Setup logging configuration for webhook events based on DEBUG flag"""
    
    # Only create logs if DEBUG is True
    if not DEBUG:
        # Create a null logger that doesn't write anything
        webhook_logger = logging.getLogger('webhook')
        webhook_logger.addHandler(logging.NullHandler())
        return webhook_logger
    
    # Create logs directory if it doesn't exist (only in DEBUG mode)
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create webhook-specific logger
    webhook_logger = logging.getLogger('webhook')
    webhook_logger.setLevel(logging.DEBUG if DEBUG else logging.WARNING)
    
    # Create file handler (only in DEBUG mode)
    webhook_handler = logging.FileHandler(f'{log_dir}/webhook.log')
    webhook_handler.setLevel(logging.DEBUG if DEBUG else logging.WARNING)
    
    # Create console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO if DEBUG else logging.ERROR)
    
    # Create formatter
    if DEBUG:
        # Detailed formatter for debug mode
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
    else:
        # Simple formatter for production
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
    
    webhook_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    webhook_logger.addHandler(webhook_handler)
    webhook_logger.addHandler(console_handler)
    
    return webhook_logger

def log_webhook_event(
    event_type: str,
    user_info: dict,
    battery_id: Optional[int] = None,
    data_id: Optional[int] = None,
    status: str = "success",
    error_message: Optional[str] = None,
    summary: Optional[dict] = None,
    request_data: Optional[dict] = None
):
    """
    Log webhook events with conditional logging based on DEBUG flag
    
    Args:
        event_type: Type of event (e.g., 'data_received', 'authentication_failed')
        user_info: User information from token
        battery_id: Battery ID involved
        data_id: Generated data ID
        status: Status of the operation
        error_message: Error message if any
        summary: Summary of data processing
        request_data: Sample of request data (for debugging)
    """
    
    # Always log errors and warnings, regardless of DEBUG flag
    if status == "error" or status == "warning":
        should_log = True
    # Only log info/success events if DEBUG is True
    elif DEBUG:
        should_log = True
    else:
        should_log = False
    
    if not should_log:
        return
    
    # Create basic log message
    log_message = f"[{event_type}] User: {user_info.get('sub') if user_info else 'Unknown'}"
    
    if battery_id:
        log_message += f" | Battery: {battery_id}"
    
    log_message += f" | Status: {status}"
    
    if error_message:
        log_message += f" | Error: {error_message}"
    
    if summary and DEBUG:  # Only add detailed summary in DEBUG mode
        log_message += f" | Parsed: {summary.get('fields_parsed', 0)} fields"
        if summary.get('processing_time_seconds'):
            log_message += f" | Time: {summary.get('processing_time_seconds'):.3f}s"
    
    # Log based on status
    if status == "success":
        webhook_logger.info(log_message)
    elif status == "error":
        webhook_logger.error(log_message)
    elif status == "warning":
        webhook_logger.warning(log_message)
    else:
        webhook_logger.info(log_message)
    
    # Only log detailed JSON in DEBUG mode
    if DEBUG and status in ["error", "warning"]:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "status": status,
            "user": {
                "username": user_info.get('sub') if user_info else None,
                "user_id": user_info.get('user_id') if user_info else None,
                "role": user_info.get('role') if user_info else None
            },
            "battery_id": battery_id,
            "data_id": data_id,
            "summary": summary,
            "error": error_message
        }
        
        # Add sample request data for debugging (limit size)
        if request_data:
            # Only log first few fields to avoid huge logs
            sample_data = {k: v for i, (k, v) in enumerate(request_data.items()) if i < 5}
            log_entry["sample_data"] = sample_data
        
        webhook_logger.debug(f"Full event data: {json.dumps(log_entry, indent=2)}")

# Initialize webhook logger
webhook_logger = setup_webhook_logging()

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

class LiveDataPayload(BaseModel):
    data: str  # JSON string that needs to be parsed
    battery_id: Optional[int] = None  # Optional if ID is in the data itself

class DirectLiveDataPayload(BaseModel):
    """For direct JSON data submission (your current format)"""
    # Allow any additional fields
    class Config:
        extra = "allow"

# Field mapping for the actual JSON format received
LIVE_DATA_FIELD_MAPPING = {
    # Core battery metrics (using actual abbreviated field names)
    'soc': ('state_of_charge', float),      # state of charge in %
    'v': ('voltage', float),                # voltage in V
    'i': ('current_amps', float),           # current in A
    'p': ('power_watts', float),            # power in W
    'tr': ('time_remaining', float),        # time remaining (-1 means infinite)
    't': ('temp_battery', float),           # temperature
    'cc': ('amp_hours_consumed', float),    # charge consumed since last full charge in Ah
    'ci': ('charging_current', float),      # charger current in A
    
    # USB metrics
    'uv': ('usb_voltage', float),           # USB voltage in V
    'up': ('usb_power', float),             # USB power in W
    'ui': ('usb_current', float),           # USB current in A
    
    # Location data
    'lat': ('latitude', float),             # GPS latitude
    'lon': ('longitude', float),            # GPS longitude
    'alt': ('altitude', float),             # altitude in m
    
    # GPS and system metrics
    'gs': ('number_GPS_satellites_for_fix', int),  # number of GPS satellites
    'nc': ('new_battery_cycle', int),       # number of battery charge cycles
    
    # Additional fields (now stored in database after migration)
    'cp': ('charger_power', float),         # charger power in W
    'cv': ('charger_voltage', float),       # charger voltage in V
    'gf': ('gps_fix_quality', int),         # GPS fix quality
    'ec': ('charging_enabled', int),        # charging enabled flag
    'ef': ('fan_enabled', int),             # fan enabled flag
    'ei': ('inverter_enabled', int),        # inverter enabled flag
    'eu': ('usb_enabled', int),             # USB enabled flag
    'sa': ('stay_awake_state', int),        # state of stay awake line
    'ts': ('tilt_sensor_state', int),       # state of tilt sensor
    'tcc': ('total_charge_consumed', float), # total charge consumed over lifetime

}

def safe_convert_value(value, target_type, field_name):
    """Safely convert a value to the target type with error handling"""
    # Handle null values explicitly
    if value is None or value == "null" or value == "":
        return None
    
    # Handle special invalid date/time values
    if isinstance(value, str) and value in ["00-00-00", "00:00:00"]:
        return None
    
    try:
        if target_type == int:
            if isinstance(value, str):
                # Handle string numbers, remove any non-numeric characters except decimal point
                value = ''.join(c for c in value if c.isdigit() or c == '.' or c == '-')
                if not value or value == '.' or value == '-':
                    return None
                return int(float(value))  # Convert through float to handle decimals
            return int(value)
        
        elif target_type == float:
            if isinstance(value, str):
                # Handle string numbers
                value = ''.join(c for c in value if c.isdigit() or c == '.' or c == '-')
                if not value or value == '.' or value == '-':
                    return None
            return float(value)
        
        elif target_type == str:
            return str(value).strip() if str(value).strip() else None
        
        else:
            return value
            
    except (ValueError, TypeError, AttributeError) as e:
        print(f"Warning: Could not convert field '{field_name}' with value '{value}' to {target_type}: {e}")
        return None
    
def create_timestamp_from_fields(battery_data):
    """Create a timestamp from date and time fields in the JSON data"""
    try:
        # Try to combine date and time fields
        date_str = battery_data.get('d') or battery_data.get('gd')  # RTC date or GPS date
        time_str = battery_data.get('tm') or battery_data.get('gt')  # RTC time or GPS time
        
        if date_str and time_str and date_str != "00-00-00" and time_str != "00:00:00":
            # Try different date formats
            for date_fmt in ['%Y-%m-%d', '%d-%m-%Y', '%m-%d-%Y']:
                try:
                    datetime_str = f"{date_str} {time_str}"
                    timestamp = datetime.strptime(datetime_str, f"{date_fmt} %H:%M:%S")
                    return timestamp.replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
        
        # If we can't parse the date/time, use current time
        return datetime.now(timezone.utc)
        
    except Exception as e:
        print(f"Warning: Could not create timestamp from date/time fields: {e}")
        return datetime.now(timezone.utc)
    
# Authentication function that handles optional token
def optional_verify_token(authorization: str = None):
    """Verify token if provided, otherwise allow anonymous access"""
    if not authorization:
        return None
    
    try:
        if authorization.startswith('Bearer '):
            token = authorization[7:]
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        else:
            return None
    except:
        return None
    
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
        # Initialize webhook logging
        setup_webhook_logging()
        
        if DEBUG:
            webhook_logger.info("🚀 Webhook logging system initialized (DEBUG MODE)")
            print("🔍 DEBUG MODE: Detailed webhook logging enabled")
        else:
            print("🚀 Production mode: Minimal logging enabled (errors/warnings only)")
        
        # Initialize database
        init_db()
        
        if DEBUG:
            webhook_logger.info("✅ Database tables created/verified")
        
        print("✅ Database tables created/verified")
        
    except Exception as e:
        if DEBUG:
            webhook_logger.error(f"❌ Startup failed: {e}")
        print(f"❌ Database initialization failed: {e}")
        raise e

# === WEBHOOK ENDPOINT FOR LIVE DATA ===
@app.post("/webhook/live-data", dependencies=[Depends(verify_token)])
async def receive_live_data(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Receive live data - REQUIRES AUTHENTICATION
    Events are logged based on DEBUG flag in .env
    """
    
    request_start_time = datetime.now()
    battery_id = None
    data_id = None
    
    try:
        # Only log request received in DEBUG mode
        if DEBUG:
            log_webhook_event(
                event_type="request_received",
                user_info=current_user,
                status="info"
            )
        
        # Get the raw JSON data
        battery_data = await request.json()
        
        # Extract battery ID early for logging
        if 'id' in battery_data:
            try:
                battery_id = int(battery_data['id'])
            except (ValueError, TypeError):
                pass
        
        # Only log authentication success in DEBUG mode (since it's already verified by dependency)
        if DEBUG:
            log_webhook_event(
                event_type="authentication_success",
                user_info=current_user,
                battery_id=battery_id,
                status="success"
            )
        
        # Check if this is the old webhook format or direct data
        if 'values' in battery_data and 'device_id' in battery_data:
            # Old Arduino Cloud webhook format
            if DEBUG:
                log_webhook_event(
                    event_type="webhook_format_detected",
                    user_info=current_user,
                    battery_id=battery_id,
                    status="info"
                )
            result = await handle_webhook_format(battery_data, db, current_user)
        else:
            # Direct JSON format (your current approach)
            if DEBUG:
                log_webhook_event(
                    event_type="direct_format_detected",
                    user_info=current_user,
                    battery_id=battery_id,
                    status="info"
                )
            result = await handle_direct_format(battery_data, db, current_user)
        
        # Always log successful data processing (but with different detail levels)
        data_id = result.get('data_id')
        battery_id = result.get('battery_id')
        
        processing_time = (datetime.now() - request_start_time).total_seconds()
        
        summary = {
            **result.get('summary', {}),
            "processing_time_seconds": processing_time
        } if DEBUG else {"fields_parsed": result.get('summary', {}).get('fields_parsed', 0)}
        
        log_webhook_event(
            event_type="data_processed_successfully",
            user_info=current_user,
            battery_id=battery_id,
            data_id=data_id,
            status="success",
            summary=summary,
            request_data=battery_data if DEBUG else None
        )
        
        return result
        
    except HTTPException as he:
        # Always log HTTP exceptions (client errors)
        log_webhook_event(
            event_type="client_error",
            user_info=current_user,
            battery_id=battery_id,
            status="error",
            error_message=f"HTTP {he.status_code}: {he.detail}"
        )
        db.rollback()
        raise he
        
    except Exception as e:
        # Always log unexpected server errors
        error_message = f"Unexpected error: {str(e)}"
        
        log_webhook_event(
            event_type="server_error",
            user_info=current_user,
            battery_id=battery_id,
            status="error",
            error_message=error_message
        )
        
        db.rollback()
        
        # Only log full exception details in DEBUG mode
        if DEBUG:
            webhook_logger.exception("Full exception details:")
        
        raise HTTPException(status_code=500, detail=f"Error processing live data: {str(e)}")

async def handle_direct_format(battery_data: dict, db: Session, current_user: dict):
    """Handle direct JSON data format with conditional logging based on DEBUG flag"""
    
    # Remove access_token from data if it exists (we already have authentication)
    battery_data.pop('access_token', None)
    
    # Extract battery ID from data
    battery_id = None
    if 'id' in battery_data:
        try:
            battery_id = int(battery_data['id'])
        except (ValueError, TypeError):
            # Always log validation errors
            log_webhook_event(
                event_type="invalid_battery_id",
                user_info=current_user,
                status="error",
                error_message=f"Invalid battery ID: {battery_data.get('id')}"
            )
            raise HTTPException(status_code=400, detail="Invalid battery ID in data")
    
    if not battery_id:
        # Always log missing battery ID
        log_webhook_event(
            event_type="missing_battery_id",
            user_info=current_user,
            status="error",
            error_message="No battery ID found in request data"
        )
        raise HTTPException(status_code=400, detail="Battery ID not found in data")
    
    # Verify battery exists
    battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == battery_id).first()
    if not battery:
        # Always log battery not found errors
        log_webhook_event(
            event_type="battery_not_found",
            user_info=current_user,
            battery_id=battery_id,
            status="error",
            error_message=f"Battery {battery_id} does not exist in database"
        )
        raise HTTPException(status_code=404, detail=f"Battery {battery_id} not found")
    
    # Only log battery validation success in DEBUG mode
    if DEBUG:
        log_webhook_event(
            event_type="battery_validated",
            user_info=current_user,
            battery_id=battery_id,
            status="success"
        )
    
    # Generate unique ID for this data point
    unique_id = int(datetime.now().timestamp() * 1000000)
    
    # Create timestamp from date/time fields or use current time
    timestamp = create_timestamp_from_fields(battery_data)
    
    # Parse and convert fields safely
    parsed_data = {
        'id': unique_id,
        'battery_id': battery_id,
        'timestamp': timestamp,
        'created_at': datetime.now(timezone.utc)
    }
    
    # Track which fields were successfully parsed
    parsed_fields = []
    skipped_fields = []
    unmapped_fields = []
    
    # Process each field in the incoming data
    for json_key, json_value in battery_data.items():
        # Skip special fields that we handle separately
        if json_key in ['id', 'd', 'gd', 'tm', 'gt']:
            continue
            
        if json_key in LIVE_DATA_FIELD_MAPPING:
            db_field, target_type = LIVE_DATA_FIELD_MAPPING[json_key]
            
            # Only process fields that exist in our current database schema
            if hasattr(LiveData, db_field):
                converted_value = safe_convert_value(json_value, target_type, json_key)
                
                if converted_value is not None:
                    parsed_data[db_field] = converted_value
                    parsed_fields.append(f"{json_key} -> {db_field}")
                else:
                    skipped_fields.append(f"{json_key}: {json_value} (null/invalid)")
            else:
                # Field is mapped but doesn't exist in current schema
                unmapped_fields.append(f"{json_key} -> {db_field} (field not in schema)")
        else:
            # Log unknown fields for debugging
            unmapped_fields.append(f"{json_key}: {json_value} (unknown field)")
    
    # Only log field parsing summary in DEBUG mode
    if DEBUG:
        log_webhook_event(
            event_type="field_parsing_completed",
            user_info=current_user,
            battery_id=battery_id,
            status="info",
            summary={
                "fields_parsed": len(parsed_fields),
                "fields_skipped": len(skipped_fields),
                "fields_unmapped": len(unmapped_fields),
                "total_fields": len(battery_data)
            }
        )
    
    # Create the LiveData object with only the fields that exist in the schema
    try:
        live_data = LiveData(**parsed_data)
    except TypeError as e:
        # If there's an issue with field names, filter to only valid fields
        valid_fields = {k: v for k, v in parsed_data.items() if hasattr(LiveData, k)}
        live_data = LiveData(**valid_fields)
        
        # Always log creation fallback warnings
        log_webhook_event(
            event_type="livedata_creation_fallback",
            user_info=current_user,
            battery_id=battery_id,
            status="warning",
            error_message=f"Had to filter fields due to: {str(e)}"
        )
    
    # Save to database
    try:
        db.add(live_data)
        db.commit()
        db.refresh(live_data)
        
        # Only log database save success in DEBUG mode
        if DEBUG:
            log_webhook_event(
                event_type="database_save_success",
                user_info=current_user,
                battery_id=battery_id,
                data_id=live_data.id,
                status="success"
            )
        
    except Exception as e:
        # Always log database save failures
        log_webhook_event(
            event_type="database_save_failed",
            user_info=current_user,
            battery_id=battery_id,
            status="error",
            error_message=f"Database error: {str(e)}"
        )
        raise
    
    # Return detailed response about what was processed
    response = {
        "status": "success",
        "data_id": live_data.id,
        "battery_id": battery_id,
        "timestamp": live_data.timestamp.isoformat(),
        "submitted_by": current_user.get('sub'),
        "user_id": current_user.get('user_id'),
        "summary": {
            "fields_parsed": len(parsed_fields),
            "fields_skipped": len(skipped_fields),
            "fields_unmapped": len(unmapped_fields),
            "total_fields_in_payload": len(battery_data)
        }
    }
    
    # Add debug details only if DEBUG is True
    if DEBUG:
        response["debug"] = {
            "parsed_fields": parsed_fields,
            "skipped_fields": skipped_fields,
            "unmapped_fields": unmapped_fields,
            "raw_data_keys": list(battery_data.keys())
        }
    
    return response

async def handle_webhook_format(webhook_data: dict, db: Session, current_user: dict):
    """Handle the old Arduino Cloud webhook format (for backward compatibility) with conditional logging"""
    
    data_property = None
    for value in webhook_data.get('values', []):
        if value.get("name") == "data":
            data_property = value
            break
    
    if not data_property:
        # Always log missing data property error
        log_webhook_event(
            event_type="webhook_data_property_missing",
            user_info=current_user,
            status="error",
            error_message="No 'data' property found in webhook values"
        )
        raise HTTPException(status_code=400, detail="No 'data' property found in webhook")
    
    # Parse the JSON data from the webhook
    try:
        battery_data = json.loads(data_property["value"])
    except json.JSONDecodeError as e:
        # Always log JSON parsing errors
        log_webhook_event(
            event_type="webhook_json_parse_error",
            user_info=current_user,
            status="error",
            error_message=f"Failed to parse JSON from webhook data property: {str(e)}"
        )
        raise HTTPException(status_code=400, detail=f"Invalid JSON in webhook data property: {str(e)}")
    
    # Only log successful JSON parsing in DEBUG mode
    if DEBUG:
        log_webhook_event(
            event_type="webhook_json_parsed",
            user_info=current_user,
            status="success",
            summary={"data_fields": len(battery_data)}
        )
    
    # Map device ID to battery ID
    device_to_battery_mapping = {
        "0291f60a-cfaf-462d-9e82-5ce662fb3823": 1
        # Add more device mappings as needed
    }
    
    device_id = webhook_data.get('device_id')
    battery_id = device_to_battery_mapping.get(device_id)
    
    if not battery_id:
        # Always log unknown device ID errors
        log_webhook_event(
            event_type="unknown_device_id",
            user_info=current_user,
            status="error",
            error_message=f"Unknown device_id: {device_id}"
        )
        raise HTTPException(status_code=400, detail=f"Unknown device_id: {device_id}")
    
    # Only log device mapping success in DEBUG mode
    if DEBUG:
        log_webhook_event(
            event_type="device_mapped_to_battery",
            user_info=current_user,
            battery_id=battery_id,
            status="success",
            summary={"device_id": device_id}
        )
    
    # Add battery_id to the data and process it using the direct format handler
    battery_data['id'] = str(battery_id)
    
    # Only log forwarding to direct handler in DEBUG mode
    if DEBUG:
        log_webhook_event(
            event_type="forwarding_to_direct_handler",
            user_info=current_user,
            battery_id=battery_id,
            status="info"
        )
    
    return await handle_direct_format(battery_data, db, current_user)

# Add endpoint to view recent webhook logs (only available in DEBUG mode)
@app.get("/admin/webhook-logs", dependencies=[Depends(verify_token)])
async def get_webhook_logs(
    lines: int = Query(100, description="Number of recent log lines to return"),
    current_user: dict = Depends(verify_token)
):
    """
    Get recent webhook logs (admin only, DEBUG mode only)
    """
    # Check if DEBUG mode is enabled
    if not DEBUG:
        raise HTTPException(
            status_code=404, 
            detail="Webhook logs are only available in DEBUG mode"
        )
    
    # Check if user is admin
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        log_file_path = "logs/webhook.log"
        
        if not os.path.exists(log_file_path):
            return {"logs": [], "message": "No log file found"}
        
        with open(log_file_path, 'r') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        return {
            "logs": [line.strip() for line in recent_lines],
            "total_lines": len(all_lines),
            "showing_lines": len(recent_lines),
            "debug_mode": DEBUG
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading logs: {str(e)}")

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