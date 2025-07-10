from fastapi import FastAPI, HTTPException, Depends, status, Query, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text, func, and_, or_, desc
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import json
import pandas as pd
import numpy as np
import io
from passlib.context import CryptContext
import jwt
from jwt.exceptions import InvalidTokenError
from enum import Enum
import logging
from functools import wraps
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import get_db, init_db
from models import *
from sqlalchemy import Table

# Import configuration with safe defaults
try:
    from config import SECRET_KEY, ALGORITHM, DEBUG
    
    try:
        from config import BATTERY_SECRET_KEY
    except ImportError:
        BATTERY_SECRET_KEY = SECRET_KEY + "_battery"
    
    try:
        from config import USER_TOKEN_EXPIRE_HOURS
    except ImportError:
        USER_TOKEN_EXPIRE_HOURS = 24
    
    try:
        from config import BATTERY_TOKEN_EXPIRE_HOURS
    except ImportError:
        BATTERY_TOKEN_EXPIRE_HOURS = 24
        
except ImportError as e:
    raise ImportError(
        "Missing required configuration. Please ensure config.py exists with SECRET_KEY, ALGORITHM, and DEBUG defined."
    ) from e

# ============================================================================
# ENUMS - Define all enums first
# ============================================================================

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"
    BATTERY = "battery"
    DATA_ADMIN = "data_admin"

class ExportFormat(str, Enum):
    json = "json"
    csv = "csv"
    # dataframe = "dataframe"

class PUEUsageLocation(str, Enum):
    HUB_ONLY = "hub_only"
    BATTERY_ONLY = "battery_only"
    BOTH = "both"

class AggregationPeriod(str, Enum):
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"

class AggregationFunction(str, Enum):
    SUM = "sum"
    MEAN = "mean"
    MEDIAN = "median"
    MIN = "min"
    MAX = "max"

class TimePeriod(str, Enum):
    LAST_24_HOURS = "last_24_hours"
    LAST_WEEK = "last_week"
    LAST_2_WEEKS = "last_2_weeks"
    LAST_MONTH = "last_month"
    LAST_2_MONTHS = "last_2_months"
    LAST_3_MONTHS = "last_3_months"
    LAST_6_MONTHS = "last_6_months"
    LAST_YEAR = "last_year"
    THIS_WEEK = "this_week"
    THIS_MONTH = "this_month"
    THIS_YEAR = "this_year"

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

def setup_webhook_logging():
    if not DEBUG:
        webhook_logger = logging.getLogger('webhook')
        webhook_logger.addHandler(logging.NullHandler())
        return webhook_logger
    
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    webhook_logger = logging.getLogger('webhook')
    webhook_logger.setLevel(logging.DEBUG if DEBUG else logging.WARNING)
    
    webhook_handler = logging.FileHandler(f'{log_dir}/webhook.log')
    webhook_handler.setLevel(logging.DEBUG if DEBUG else logging.WARNING)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO if DEBUG else logging.ERROR)
    
    if DEBUG:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
    
    webhook_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
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
    if status == "error" or status == "warning":
        should_log = True
    elif DEBUG:
        should_log = True
    else:
        should_log = False
    
    if not should_log:
        return
    
    log_message = f"[{event_type}] User: {user_info.get('sub') if user_info else 'Unknown'}"
    
    if battery_id:
        log_message += f" | Battery: {battery_id}"
    
    log_message += f" | Status: {status}"
    
    if error_message:
        log_message += f" | Error: {error_message}"
    
    if summary and DEBUG:
        log_message += f" | Parsed: {summary.get('fields_parsed', 0)} fields"
        if summary.get('processing_time_seconds'):
            log_message += f" | Time: {summary.get('processing_time_seconds'):.3f}s"
    
    if status == "success":
        webhook_logger.info(log_message)
    elif status == "error":
        webhook_logger.error(log_message)
    elif status == "warning":
        webhook_logger.warning(log_message)
    else:
        webhook_logger.info(log_message)
    
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
        
        if request_data:
            sample_data = {k: v for i, (k, v) in enumerate(request_data.items()) if i < 5}
            log_entry["sample_data"] = sample_data
        
        webhook_logger.debug(f"Full event data: {json.dumps(log_entry, indent=2)}")

webhook_logger = setup_webhook_logging()

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class SolarHubCreate(BaseModel):
    hub_id: int
    what_three_word_location: Optional[str] = None
    solar_capacity_kw: Optional[int] = None
    country: Optional[str] = None
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
    battery_secret: Optional[str] = None

class BatteryUpdate(BaseModel):
    battery_capacity_wh: Optional[int] = None
    status: Optional[str] = None
    battery_secret: Optional[str] = None

class BatteryAuth(BaseModel):
    battery_id: int
    battery_secret: str

class BatteryLogin(BaseModel):
    battery_id: int
    battery_secret: str

class BatterySecretUpdate(BaseModel):
    new_secret: str

class PUECreate(BaseModel):
    model_config = {'arbitrary_types_allowed': True}

    pue_id: int
    hub_id: int
    name: str
    description: Optional[str] = None
    power_rating_watts: Optional[float] = None
    usage_location: PUEUsageLocation = PUEUsageLocation.BOTH
    storage_location: Optional[str] = None
    suggested_cost_per_day: Optional[float] = None
    rental_cost: Optional[float] = None
    status: Optional[str] = "available"
    


class PUEUpdate(BaseModel):
    model_config = {'arbitrary_types_allowed': True}

    name: Optional[str] = None
    description: Optional[str] = None
    power_rating_watts: Optional[float] = None
    usage_location: Optional[PUEUsageLocation] = None
    storage_location: Optional[str] = None
    suggested_cost_per_day: Optional[float] = None
    rental_cost: Optional[float] = None
    status: Optional[str] = None
    
    

class RentalCreate(BaseModel):
    rentral_id: int
    battery_id: int
    user_id: int
    timestamp_taken: datetime
    due_back: Optional[datetime] = None
    pue_item_ids: Optional[List[int]] = []
    total_cost: Optional[float] = None
    deposit_amount: Optional[float] = None

class RentalUpdate(BaseModel):
    due_back: Optional[datetime] = None
    date_returned: Optional[datetime] = None
    pue_item_ids: Optional[List[int]] = None
    total_cost: Optional[float] = None

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

class LiveDataPayload(BaseModel):
    data: str
    battery_id: Optional[int] = None

class DirectLiveDataPayload(BaseModel):
    class Config:
        extra = "allow"

class BatterySelectionCriteria(BaseModel):
    battery_ids: Optional[List[int]] = None
    hub_ids: Optional[List[int]] = None
    pue_ids: Optional[List[int]] = None
    all_batteries: bool = False

class DataAggregationRequest(BaseModel):
    model_config = {'arbitrary_types_allowed': True}

    battery_selection: BatterySelectionCriteria
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    time_period: Optional[TimePeriod] = None
    aggregation_period: AggregationPeriod
    aggregation_function: AggregationFunction
    metric: str

class RentalAnalyticsRequest(BaseModel):
    model_config = {'arbitrary_types_allowed': True}

    hub_ids: Optional[List[int]] = None
    pue_ids: Optional[List[int]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    time_period: Optional[TimePeriod] = None
    group_by: Optional[str] = "pue_id"

class RentalReturnRequest(BaseModel):
    """Request model for returning battery and/or PUE items"""
    return_battery: bool = Field(True, description="Whether to return the battery")
    return_pue_items: Optional[List[int]] = Field(None, description="List of PUE item IDs to return (if None, returns all)")
    add_pue_items: Optional[List[int]] = Field(None, description="List of PUE item IDs to add to the rental")
    battery_condition: Optional[str] = Field(None, description="Condition of returned battery")
    battery_notes: Optional[str] = Field(None, description="Notes about battery return")
    return_notes: Optional[str] = Field(None, description="General return notes")

class AddPUEToRentalRequest(BaseModel):
    """Request model for adding PUE items to an existing rental"""
    pue_item_ids: List[int] = Field(..., description="List of PUE item IDs to add")
    rental_cost: Optional[float] = Field(None, description="Additional cost for new PUE items")
    due_back: Optional[datetime] = Field(None, description="Due date for new PUE items")

class DataQuery(BaseModel):
    model_config = {'arbitrary_types_allowed': True}

    battery_ids: Optional[List[int]] = None
    start_timestamp: Optional[datetime] = None
    end_timestamp: Optional[datetime] = None
    fields: Optional[List[str]] = None
    format: ExportFormat = ExportFormat.json

# ============================================================================
# FASTAPI APP INITIALIZATION
# ============================================================================

app = FastAPI(
    title="Solar Hub Management API with PUE & Analytics",
    description="""
## Solar Hub Management System API

A comprehensive API for managing solar hubs, batteries, productive use equipment (PUE), and analytics.

### User Roles & Permissions:
- **SUPERADMIN**: Full system access including user management
- **ADMIN**: Hub management, users, batteries, PUE, rentals
- **DATA_ADMIN**: Read-only access to analytics and statistics
- **USER**: Limited access to own hub's operations
- **BATTERY**: Data submission only (for IoT devices)

### Key Features:
- **User Management**: Create and manage users with role-based access
- **Hub Operations**: CRUD operations for solar hubs
- **Battery Management**: Track battery status, data, and rentals
- **PUE Equipment**: Manage productive use equipment with type-based aggregation
- **Rental System**: Complete rental lifecycle with notes and tracking
- **Analytics**: Power usage analytics and aggregated data queries
- **CLI Integration**: Command-line interface for system administration

### Authentication:
- JWT-based authentication with role-based permissions
- Battery-specific authentication for IoT devices
- Token refresh capabilities
    """,
    version="2.0.0",
    contact={
        "name": "Solar Hub Management System",
        "email": "admin@solarhub.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    tags_metadata=[
        {
            "name": "Authentication",
            "description": "User and battery authentication endpoints",
        },
        {
            "name": "Hubs",
            "description": "Solar hub management operations",
        },
        {
            "name": "Users",
            "description": "User management and administration",
        },
        {
            "name": "Batteries",
            "description": "Battery management and data submission",
        },
        {
            "name": "PUE",
            "description": "Productive Use Equipment management",
        },
        {
            "name": "Rentals",
            "description": "Rental system and tracking",
        },
        {
            "name": "Data & Analytics",
            "description": "Battery data retrieval and analytics",
        },
        {
            "name": "System",
            "description": "System health and administration",
        },
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ============================================================================
# FIELD MAPPING AND HELPER FUNCTIONS
# ============================================================================

LIVE_DATA_FIELD_MAPPING = {
    'soc': ('state_of_charge', float),
    'v': ('voltage', float),
    'i': ('current_amps', float),
    'p': ('power_watts', float),
    'tr': ('time_remaining', float),
    't': ('temp_battery', float),
    'cc': ('amp_hours_consumed', float),
    'ci': ('charging_current', float),
    'uv': ('usb_voltage', float),
    'up': ('usb_power', float),
    'ui': ('usb_current', float),
    'lat': ('latitude', float),
    'lon': ('longitude', float),
    'alt': ('altitude', float),
    'gs': ('number_GPS_satellites_for_fix', int),
    'nc': ('new_battery_cycle', int),
    'cp': ('charger_power', float),
    'cv': ('charger_voltage', float),
    'gf': ('gps_fix_quality', int),
    'ec': ('charging_enabled', int),
    'ef': ('fan_enabled', int),
    'ei': ('inverter_enabled', int),
    'eu': ('usb_enabled', int),
    'sa': ('stay_awake_state', int),
    'ts': ('tilt_sensor_state', int),
    'tcc': ('total_charge_consumed', float),
}

def safe_convert_value(value, target_type, field_name):
    if value is None or value == "null" or value == "":
        return None
    
    if isinstance(value, str) and value in ["00-00-00", "00:00:00"]:
        return None
    
    try:
        if target_type == int:
            if isinstance(value, str):
                value = ''.join(c for c in value if c.isdigit() or c == '.' or c == '-')
                if not value or value == '.' or value == '-':
                    return None
                return int(float(value))
            return int(value)
        
        elif target_type == float:
            if isinstance(value, str):
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
    try:
        date_str = battery_data.get('d') or battery_data.get('gd')
        time_str = battery_data.get('tm') or battery_data.get('gt')
        
        if date_str and time_str and date_str != "00-00-00" and time_str != "00:00:00":
            for date_fmt in ['%Y-%m-%d', '%d-%m-%Y', '%m-%d-%Y']:
                try:
                    datetime_str = f"{date_str} {time_str}"
                    timestamp = datetime.strptime(datetime_str, f"{date_fmt} %H:%M:%S")
                    return timestamp.replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
        
        return datetime.now(timezone.utc)
        
    except Exception as e:
        print(f"Warning: Could not create timestamp from date/time fields: {e}")
        return datetime.now(timezone.utc)

def calculate_time_period(time_period: TimePeriod) -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    
    if time_period == TimePeriod.LAST_24_HOURS:
        start_time = now - timedelta(hours=24)
        end_time = now
    elif time_period == TimePeriod.LAST_WEEK:
        start_time = now - timedelta(weeks=1)
        end_time = now
    elif time_period == TimePeriod.LAST_2_WEEKS:
        start_time = now - timedelta(weeks=2)
        end_time = now
    elif time_period == TimePeriod.LAST_MONTH:
        start_time = now - timedelta(days=30)
        end_time = now
    elif time_period == TimePeriod.LAST_2_MONTHS:
        start_time = now - timedelta(days=60)
        end_time = now
    elif time_period == TimePeriod.LAST_3_MONTHS:
        start_time = now - timedelta(days=90)
        end_time = now
    elif time_period == TimePeriod.LAST_6_MONTHS:
        start_time = now - timedelta(days=180)
        end_time = now
    elif time_period == TimePeriod.LAST_YEAR:
        start_time = now - timedelta(days=365)
        end_time = now
    elif time_period == TimePeriod.THIS_WEEK:
        days_since_monday = now.weekday()
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days_since_monday)
        end_time = now
    elif time_period == TimePeriod.THIS_MONTH:
        start_time = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_time = now
    elif time_period == TimePeriod.THIS_YEAR:
        start_time = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end_time = now
    else:
        raise ValueError(f"Unsupported time period: {time_period}")
    
    return start_time, end_time

# ============================================================================
# AUTHENTICATION AND AUTHORIZATION
# ============================================================================

def create_access_token(data: dict, expires_hours: Optional[int] = None):
    to_encode = data.copy()
    expire_hours = expires_hours or USER_TOKEN_EXPIRE_HOURS
    expire = datetime.now(timezone.utc) + timedelta(hours=expire_hours)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_battery_token(battery_id: int, expires_hours: Optional[int] = None):
    expire_hours = expires_hours or BATTERY_TOKEN_EXPIRE_HOURS
    expiry = datetime.now(timezone.utc) + timedelta(hours=expire_hours)
    
    token_data = {
        "sub": f"battery_{battery_id}",
        "battery_id": battery_id,
        "role": UserRole.BATTERY,
        "type": "battery",
        "exp": expiry
    }
    return jwt.encode(token_data, BATTERY_SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def verify_battery_or_superadmin_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        try:
            payload = jwt.decode(credentials.credentials, BATTERY_SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") == "battery":
                return payload
        except:
            pass
        
        try:
            payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("role") == UserRole.SUPERADMIN:
                return payload
        except:
            pass
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Only batteries or superadmins can access this endpoint"
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def get_current_user(token_data: dict = Depends(verify_token), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == token_data.get('sub')).first()
    if user:
        token_data['hub_id'] = user.hub_id
        # For DATA_ADMIN users, also get their accessible hubs
        if user.user_access_level == UserRole.DATA_ADMIN:
            accessible_hub_ids = [hub.hub_id for hub in user.accessible_hubs]
            token_data['accessible_hub_ids'] = accessible_hub_ids
    return token_data

def user_has_hub_access(current_user: dict, hub_id: int) -> bool:
    """Check if user has access to a specific hub"""
    role = current_user.get('role')
    
    if role == UserRole.SUPERADMIN:
        return True
    elif role == UserRole.DATA_ADMIN:
        accessible_hubs = current_user.get('accessible_hub_ids', [])
        return hub_id in accessible_hubs
    else:
        # ADMIN, USER roles are restricted to their own hub
        return current_user.get('hub_id') == hub_id

# ============================================================================
# WEBHOOK HANDLERS
# ============================================================================

async def handle_direct_format(battery_data: dict, db: Session, current_user: dict):
    battery_data.pop('access_token', None)
    
    battery_id = None
    if 'id' in battery_data:
        try:
            battery_id = int(battery_data['id'])
        except (ValueError, TypeError):
            log_webhook_event(
                event_type="invalid_battery_id",
                user_info=current_user,
                status="error",
                error_message=f"Invalid battery ID: {battery_data.get('id')}"
            )
            raise HTTPException(status_code=400, detail="Invalid battery ID in data")
    
    if not battery_id:
        log_webhook_event(
            event_type="missing_battery_id",
            user_info=current_user,
            status="error",
            error_message="No battery ID found in request data"
        )
        raise HTTPException(status_code=400, detail="Battery ID not found in data")
    
    if current_user.get('role') == UserRole.BATTERY:
        token_battery_id = current_user.get('battery_id')
        if token_battery_id != battery_id:
            log_webhook_event(
                event_type="battery_id_mismatch",
                user_info=current_user,
                battery_id=battery_id,
                status="error",
                error_message=f"Battery {token_battery_id} cannot submit data for battery {battery_id}"
            )
            raise HTTPException(
                status_code=403, 
                detail="Battery can only submit data for itself"
            )
    
    battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == battery_id).first()
    if not battery:
        log_webhook_event(
            event_type="battery_not_found",
            user_info=current_user,
            battery_id=battery_id,
            status="error",
            error_message=f"Battery {battery_id} does not exist in database"
        )
        raise HTTPException(status_code=404, detail=f"Battery {battery_id} not found")
    
    if DEBUG:
        log_webhook_event(
            event_type="battery_validated",
            user_info=current_user,
            battery_id=battery_id,
            status="success"
        )
    
    unique_id = int(datetime.now().timestamp() * 1000000)
    timestamp = create_timestamp_from_fields(battery_data)
    
    parsed_data = {
        'id': unique_id,
        'battery_id': battery_id,
        'timestamp': timestamp,
        'created_at': datetime.now(timezone.utc)
    }
    
    parsed_fields = []
    skipped_fields = []
    unmapped_fields = []
    
    for json_key, json_value in battery_data.items():
        if json_key in ['id', 'd', 'gd', 'tm', 'gt']:
            continue
            
        if json_key in LIVE_DATA_FIELD_MAPPING:
            db_field, target_type = LIVE_DATA_FIELD_MAPPING[json_key]
            
            if hasattr(LiveData, db_field):
                converted_value = safe_convert_value(json_value, target_type, json_key)
                
                if converted_value is not None:
                    parsed_data[db_field] = converted_value
                    parsed_fields.append(f"{json_key} -> {db_field}")
                else:
                    skipped_fields.append(f"{json_key}: {json_value} (null/invalid)")
            else:
                unmapped_fields.append(f"{json_key} -> {db_field} (field not in schema)")
        else:
            unmapped_fields.append(f"{json_key}: {json_value} (unknown field)")
    
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
    
    try:
        live_data = LiveData(**parsed_data)
    except TypeError as e:
        valid_fields = {k: v for k, v in parsed_data.items() if hasattr(LiveData, k)}
        live_data = LiveData(**valid_fields)
        
        log_webhook_event(
            event_type="livedata_creation_fallback",
            user_info=current_user,
            battery_id=battery_id,
            status="warning",
            error_message=f"Had to filter fields due to: {str(e)}"
        )
    
    try:
        db.add(live_data)
        db.commit()
        db.refresh(live_data)
        
        if DEBUG:
            log_webhook_event(
                event_type="database_save_success",
                user_info=current_user,
                battery_id=battery_id,
                data_id=live_data.id,
                status="success"
            )
        
    except Exception as e:
        log_webhook_event(
            event_type="database_save_failed",
            user_info=current_user,
            battery_id=battery_id,
            status="error",
            error_message=f"Database error: {str(e)}"
        )
        raise
    
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
    
    if DEBUG:
        response["debug"] = {
            "parsed_fields": parsed_fields,
            "skipped_fields": skipped_fields,
            "unmapped_fields": unmapped_fields,
            "raw_data_keys": list(battery_data.keys())
        }
    
    return response

async def handle_webhook_format(webhook_data: dict, db: Session, current_user: dict):
    data_property = None
    for value in webhook_data.get('values', []):
        if value.get("name") == "data":
            data_property = value
            break
    
    if not data_property:
        log_webhook_event(
            event_type="webhook_data_property_missing",
            user_info=current_user,
            status="error",
            error_message="No 'data' property found in webhook values"
        )
        raise HTTPException(status_code=400, detail="No 'data' property found in webhook")
    
    try:
        battery_data = json.loads(data_property["value"])
    except json.JSONDecodeError as e:
        log_webhook_event(
            event_type="webhook_json_parse_error",
            user_info=current_user,
            status="error",
            error_message=f"Failed to parse JSON from webhook data property: {str(e)}"
        )
        raise HTTPException(status_code=400, detail=f"Invalid JSON in webhook data property: {str(e)}")
    
    if DEBUG:
        log_webhook_event(
            event_type="webhook_json_parsed",
            user_info=current_user,
            status="success",
            summary={"data_fields": len(battery_data)}
        )
    
    device_to_battery_mapping = {
        "0291f60a-cfaf-462d-9e82-5ce662fb3823": 1
    }
    
    device_id = webhook_data.get('device_id')
    battery_id = device_to_battery_mapping.get(device_id)
    
    if not battery_id:
        log_webhook_event(
            event_type="unknown_device_id",
            user_info=current_user,
            status="error",
            error_message=f"Unknown device_id: {device_id}"
        )
        raise HTTPException(status_code=400, detail=f"Unknown device_id: {device_id}")
    
    if DEBUG:
        log_webhook_event(
            event_type="device_mapped_to_battery",
            user_info=current_user,
            battery_id=battery_id,
            status="success",
            summary={"device_id": device_id}
        )
    
    battery_data['id'] = str(battery_id)
    
    if DEBUG:
        log_webhook_event(
            event_type="forwarding_to_direct_handler",
            user_info=current_user,
            battery_id=battery_id,
            status="info"
        )
    
    return await handle_direct_format(battery_data, db, current_user)

# ============================================================================
# WEBHOOK ENDPOINT FOR LIVE DATA
# ============================================================================

@app.post("/webhook/live-data",
    tags=["Batteries"],
    summary="Battery Data Submission",
    description="""
    ## Battery Data Submission Endpoint

    Endpoint for battery IoT devices to submit live data.
    
    ### Permissions:
    - **BATTERY**: Battery devices can submit data
    - **SUPERADMIN**: For testing and administration
    
    ### Features:
    - Accepts multiple data formats (webhook format and direct format)
    - Automatic field mapping and validation
    - Real-time data processing
    - Comprehensive error handling and logging
    
    ### Data Fields:
    - **State of charge, voltage, current, power**
    - **GPS coordinates and fix quality**
    - **Temperature and environmental data**
    - **USB port usage and charging status**
    - **System status and diagnostics**
    
    ### Usage:
    Battery devices authenticate using their device token and submit data in JSON format.
    """,
    response_description="Data submission confirmation and metadata")
async def receive_live_data(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_battery_or_superadmin_token)
):
    """Receive live data - ONLY for batteries and superadmins"""
    
    request_start_time = datetime.now()
    battery_id = None
    data_id = None
    
    try:
        if DEBUG:
            log_webhook_event(
                event_type="request_received",
                user_info=current_user,
                status="info"
            )
        
        battery_data = await request.json()
        
        if 'id' in battery_data:
            try:
                battery_id = int(battery_data['id'])
            except (ValueError, TypeError):
                pass
        
        if DEBUG:
            log_webhook_event(
                event_type="authentication_success",
                user_info=current_user,
                battery_id=battery_id,
                status="success"
            )
        
        if 'values' in battery_data and 'device_id' in battery_data:
            if DEBUG:
                log_webhook_event(
                    event_type="webhook_format_detected",
                    user_info=current_user,
                    battery_id=battery_id,
                    status="info"
                )
            result = await handle_webhook_format(battery_data, db, current_user)
        else:
            if DEBUG:
                log_webhook_event(
                    event_type="direct_format_detected",
                    user_info=current_user,
                    battery_id=battery_id,
                    status="info"
                )
            result = await handle_direct_format(battery_data, db, current_user)
        
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
        error_message = f"Unexpected error: {str(e)}"
        
        log_webhook_event(
            event_type="server_error",
            user_info=current_user,
            battery_id=battery_id,
            status="error",
            error_message=error_message
        )
        
        db.rollback()
        
        if DEBUG:
            webhook_logger.exception("Full exception details:")
        
        raise HTTPException(status_code=500, detail=f"Error processing live data: {str(e)}")

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/auth/token", 
    tags=["Authentication"],
    summary="User Login",
    description="""
    ## User Authentication

    Login endpoint for all user types (SUPERADMIN, ADMIN, DATA_ADMIN, USER).
    
    ### Permissions:
    - **Public**: No authentication required
    
    ### Returns:
    - JWT access token
    - Token type and expiration
    - User information and role
    
    ### Usage:
    ```
    POST /auth/token
    {
        "username": "your_username",
        "password": "your_password"
    }
    ```
    """,
    response_description="JWT token and user information")
async def create_token(
    request: Request,
    db: Session = Depends(get_db),
    user_login: UserLogin = None
):
    try:
        if user_login is None:
            try:
                body = await request.json()
                username = body.get("username")
                password = body.get("password")
            except:
                form_data = await request.form()
                username = form_data.get("username")
                password = form_data.get("password")
        else:
            username = user_login.username
            password = user_login.password
        
        if not username or not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username and password are required"
            )
        
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        if not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        token_data = {
            "sub": user.username,
            "user_id": user.user_id,
            "role": user.user_access_level,
            "hub_id": user.hub_id
        }
        token = create_access_token(token_data)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": USER_TOKEN_EXPIRE_HOURS * 3600,
            "expires_in_hours": USER_TOKEN_EXPIRE_HOURS,
            "user_id": user.user_id,
            "role": user.user_access_level,
            "hub_id": user.hub_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )

@app.post("/auth/battery-login",
    tags=["Authentication"],
    summary="Battery Device Login",
    description="""
    ## Battery Device Authentication

    Login endpoint specifically for battery IoT devices to obtain authentication tokens.
    
    ### Permissions:
    - **Public**: No authentication required
    
    ### Returns:
    - JWT access token for battery device
    - Token type and expiration
    
    ### Usage:
    ```
    POST /auth/battery-login
    {
        "battery_id": 123,
        "battery_secret": "device_secret_key"
    }
    ```
    """,
    response_description="JWT token for battery device")
async def battery_login(
    battery_login: BatteryLogin,
    db: Session = Depends(get_db)
):
    """Battery self-authentication"""
    try:
        battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == battery_login.battery_id).first()
        if not battery:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid battery credentials"
            )
        
        if not battery.battery_secret:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Battery not configured for authentication"
            )
        
        if battery.battery_secret != battery_login.battery_secret:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid battery credentials"
            )
        
        token = create_battery_token(battery_login.battery_id)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "battery_id": battery_login.battery_id,
            "expires_in": BATTERY_TOKEN_EXPIRE_HOURS * 3600,
            "expires_in_hours": BATTERY_TOKEN_EXPIRE_HOURS,
            "scope": "webhook_write"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Battery authentication error: {str(e)}"
        )

@app.post("/auth/battery-refresh")
async def battery_refresh_token(
    db: Session = Depends(get_db),
    current_battery: dict = Depends(verify_battery_or_superadmin_token)
):
    """Refresh battery token"""
    try:
        if current_battery.get('type') != 'battery':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only batteries can refresh battery tokens"
            )
        
        battery_id = current_battery.get('battery_id')
        if not battery_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid battery token"
            )
        
        battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == battery_id).first()
        if not battery:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Battery not found"
            )
        
        token = create_battery_token(battery_id)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "battery_id": battery_id,
            "expires_in": BATTERY_TOKEN_EXPIRE_HOURS * 3600,
            "expires_in_hours": BATTERY_TOKEN_EXPIRE_HOURS,
            "scope": "webhook_write"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh error: {str(e)}"
        )

@app.post("/auth/battery-token")
async def create_battery_token_endpoint(
    battery_auth: BatteryAuth,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create authentication token for a battery (admin/superadmin only)"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == battery_auth.battery_id).first()
        if not battery:
            raise HTTPException(status_code=404, detail="Battery not found")
        
        if not battery.battery_secret or battery.battery_secret != battery_auth.battery_secret:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid battery secret"
            )
        
        token = create_battery_token(battery_auth.battery_id)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "battery_id": battery_auth.battery_id,
            "expires_in": BATTERY_TOKEN_EXPIRE_HOURS * 3600,
            "expires_in_hours": BATTERY_TOKEN_EXPIRE_HOURS,
            "scope": "webhook_write"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Battery authentication error: {str(e)}"
        )

@app.post("/admin/battery-secret/{battery_id}")
async def set_battery_secret(
    battery_id: int,
    secret_update: BatterySecretUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Set or update battery secret (admin/superadmin only)"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == battery_id).first()
        if not battery:
            raise HTTPException(status_code=404, detail="Battery not found")
        
        battery.battery_secret = secret_update.new_secret
        db.commit()
        
        return {
            "message": f"Battery secret updated for battery {battery_id}",
            "battery_id": battery_id,
            "updated_by": current_user.get('sub'),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating battery secret: {str(e)}"
        )

@app.get("/admin/token-config")
async def get_token_config(
    current_user: dict = Depends(get_current_user)
):
    """Get current token configuration (admin/superadmin only)"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return {
        "user_token_expire_hours": USER_TOKEN_EXPIRE_HOURS,
        "battery_token_expire_hours": BATTERY_TOKEN_EXPIRE_HOURS,
        "note": "Token expiration times are configured in config.py"
    }

# ============================================================================
# HUB ENDPOINTS
# ============================================================================

@app.post("/hubs/",
    tags=["Hubs"],
    summary="Create Solar Hub",
    description="""
    ## Create a New Solar Hub

    Creates a new solar hub in the system.
    
    ### Permissions:
    - **ADMIN**: Can create hubs
    - **SUPERADMIN**: Can create hubs
    
    ### Parameters:
    - **hub_id**: Unique identifier for the hub
    - **what_three_word_location**: Location using what3words format
    - **solar_capacity_kw**: Solar capacity in kilowatts
    - **country**: Country where hub is located
    - **latitude/longitude**: GPS coordinates
    
    ### Returns:
    - Created hub information
    """,
    response_description="Created solar hub details")
async def create_hub(
    hub: SolarHubCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new solar hub (admin/superadmin only)"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        db_hub = SolarHub(**hub.dict())
        db.add(db_hub)
        db.commit()
        db.refresh(db_hub)
        return db_hub
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/hubs/{hub_id}",
    tags=["Hubs"],
    summary="Get Solar Hub",
    description="""
    ## Get Solar Hub Details

    Get details of a specific solar hub.
    
    ### Permissions:
    - **SUPERADMIN**: Can access any hub
    - **ADMIN**: Can access their own hub only
    - **DATA_ADMIN**: Can access hubs they have been granted access to
    - **USER**: Can access their own hub only
    
    ### Returns:
    - Solar hub details
    """,
    response_description="Solar hub details")
async def get_hub(
    hub_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a solar hub by ID"""
    if not user_has_hub_access(current_user, hub_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    hub = db.query(SolarHub).filter(SolarHub.hub_id == hub_id).first()
    if not hub:
        raise HTTPException(status_code=404, detail="Hub not found")
    return hub

@app.put("/hubs/{hub_id}")
async def update_hub(
    hub_id: int,
    hub_update: SolarHubUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a solar hub (admin/superadmin only)"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
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

@app.delete("/hubs/{hub_id}")
async def delete_hub(
    hub_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a solar hub (superadmin only)"""
    if current_user.get('role') != UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Superadmin access required")
    
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

@app.get("/hubs/",
    tags=["Hubs"],
    summary="List Solar Hubs",
    description="""
    ## List Solar Hubs

    List hubs based on user permissions.
    
    ### Permissions:
    - **SUPERADMIN**: Can see all hubs
    - **ADMIN**: Can see their own hub only
    - **DATA_ADMIN**: Can see hubs they have been granted access to
    - **USER**: Can see their own hub only
    
    ### Returns:
    - List of accessible hubs
    """,
    response_description="List of accessible solar hubs")
async def list_hubs(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all solar hubs"""
    role = current_user.get('role')
    
    if role == UserRole.SUPERADMIN:
        return db.query(SolarHub).all()
    elif role == UserRole.DATA_ADMIN:
        accessible_hub_ids = current_user.get('accessible_hub_ids', [])
        if accessible_hub_ids:
            return db.query(SolarHub).filter(SolarHub.hub_id.in_(accessible_hub_ids)).all()
        else:
            return []
    else:
        # ADMIN and USER roles see only their own hub
        return db.query(SolarHub).filter(SolarHub.hub_id == current_user.get('hub_id')).all()

@app.post("/admin/user-hub-access/{user_id}/{hub_id}",
    tags=["Users"],
    summary="Grant Hub Access to DATA_ADMIN",
    description="""
    ## Grant Hub Access to DATA_ADMIN User

    Grant a DATA_ADMIN user access to a specific hub.
    
    ### Permissions:
    - **SUPERADMIN**: Can grant hub access to any DATA_ADMIN user
    
    ### Parameters:
    - **user_id**: ID of the DATA_ADMIN user
    - **hub_id**: ID of the hub to grant access to
    
    ### Returns:
    - Success confirmation
    """,
    response_description="Access grant confirmation")
async def grant_hub_access(
    user_id: int,
    hub_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Grant hub access to a DATA_ADMIN user (superadmin only)"""
    if current_user.get('role') != UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Superadmin access required")
    
    # Check if user exists and is DATA_ADMIN
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.user_access_level != UserRole.DATA_ADMIN:
        raise HTTPException(status_code=400, detail="User must be DATA_ADMIN to grant hub access")
    
    # Check if hub exists
    hub = db.query(SolarHub).filter(SolarHub.hub_id == hub_id).first()
    if not hub:
        raise HTTPException(status_code=404, detail="Hub not found")
    
    # Check if access already exists
    if hub in user.accessible_hubs:
        raise HTTPException(status_code=400, detail="User already has access to this hub")
    
    # Grant access
    user.accessible_hubs.append(hub)
    db.commit()
    
    return {"message": f"Hub access granted to user {user_id} for hub {hub_id}"}

@app.delete("/admin/user-hub-access/{user_id}/{hub_id}",
    tags=["Users"],
    summary="Revoke Hub Access from DATA_ADMIN",
    description="""
    ## Revoke Hub Access from DATA_ADMIN User

    Revoke a DATA_ADMIN user's access to a specific hub.
    
    ### Permissions:
    - **SUPERADMIN**: Can revoke hub access from any DATA_ADMIN user
    
    ### Parameters:
    - **user_id**: ID of the DATA_ADMIN user
    - **hub_id**: ID of the hub to revoke access from
    
    ### Returns:
    - Success confirmation
    """,
    response_description="Access revoke confirmation")
async def revoke_hub_access(
    user_id: int,
    hub_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Revoke hub access from a DATA_ADMIN user (superadmin only)"""
    if current_user.get('role') != UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Superadmin access required")
    
    # Check if user exists and is DATA_ADMIN
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.user_access_level != UserRole.DATA_ADMIN:
        raise HTTPException(status_code=400, detail="User must be DATA_ADMIN to revoke hub access")
    
    # Check if hub exists
    hub = db.query(SolarHub).filter(SolarHub.hub_id == hub_id).first()
    if not hub:
        raise HTTPException(status_code=404, detail="Hub not found")
    
    # Check if access exists
    if hub not in user.accessible_hubs:
        raise HTTPException(status_code=400, detail="User does not have access to this hub")
    
    # Revoke access
    user.accessible_hubs.remove(hub)
    db.commit()
    
    return {"message": f"Hub access revoked from user {user_id} for hub {hub_id}"}

# ============================================================================
# USER ENDPOINTS
# ============================================================================

@app.post("/users/")
async def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new user"""
    if current_user.get('role') == UserRole.DATA_ADMIN:
        raise HTTPException(status_code=403, detail="Data admins cannot create users")
    
    if current_user.get('role') == UserRole.USER:
        if user.hub_id != current_user.get('hub_id'):
            raise HTTPException(status_code=403, detail="Can only create users in your own hub")
        if user.user_access_level in [UserRole.ADMIN, UserRole.SUPERADMIN]:
            raise HTTPException(status_code=403, detail="Cannot create admin or superadmin users")
    elif current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Access denied")
    
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

@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a user by ID"""
    if current_user.get('role') == UserRole.DATA_ADMIN:
        raise HTTPException(status_code=403, detail="Data admins cannot access user information")
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        if user.hub_id != current_user.get('hub_id'):
            raise HTTPException(status_code=403, detail="Access denied")
    
    return user

@app.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a user"""
    if current_user.get('role') == UserRole.DATA_ADMIN:
        raise HTTPException(status_code=403, detail="Data admins cannot modify users")
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if current_user.get('role') == UserRole.USER:
        if user.hub_id != current_user.get('hub_id'):
            raise HTTPException(status_code=403, detail="Access denied")
        if user_update.user_access_level in [UserRole.ADMIN, UserRole.SUPERADMIN]:
            raise HTTPException(status_code=403, detail="Cannot set admin roles")
    elif current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
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

@app.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a user (admin/superadmin only)"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
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

@app.get("/hubs/{hub_id}/users")
async def list_hub_users(
    hub_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all users for a hub"""
    if current_user.get('role') == UserRole.DATA_ADMIN:
        raise HTTPException(status_code=403, detail="Data admins cannot access user information")
    
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        if current_user.get('hub_id') != hub_id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    return db.query(User).filter(User.hub_id == hub_id).all()

# ============================================================================
# BATTERY ENDPOINTS
# ============================================================================

@app.post("/batteries/")
async def create_battery(
    battery: BatteryCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new battery"""
    if current_user.get('role') == UserRole.DATA_ADMIN:
        raise HTTPException(status_code=403, detail="Data admins cannot create batteries")
    
    if current_user.get('role') == UserRole.USER:
        if battery.hub_id != current_user.get('hub_id'):
            raise HTTPException(status_code=403, detail="Can only add batteries to your own hub")
    elif current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        battery_data = battery.dict()
        db_battery = BEPPPBattery(**battery_data)
        db.add(db_battery)
        db.commit()
        db.refresh(db_battery)
        
        result = {**battery_data}
        result.pop('battery_secret', None)
        result['id'] = db_battery.battery_id
        
        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/batteries/{battery_id}")
async def get_battery(
    battery_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a battery by ID"""
    battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == battery_id).first()
    if not battery:
        raise HTTPException(status_code=404, detail="Battery not found")
    
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.DATA_ADMIN]:
        if battery.hub_id != current_user.get('hub_id'):
            raise HTTPException(status_code=403, detail="Access denied")
    
    return battery

@app.put("/batteries/{battery_id}")
async def update_battery(
    battery_id: int,
    battery_update: BatteryUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a battery"""
    if current_user.get('role') == UserRole.DATA_ADMIN:
        raise HTTPException(status_code=403, detail="Data admins cannot modify batteries")
    
    battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == battery_id).first()
    if not battery:
        raise HTTPException(status_code=404, detail="Battery not found")
    
    if current_user.get('role') == UserRole.USER:
        if battery.hub_id != current_user.get('hub_id'):
            raise HTTPException(status_code=403, detail="Access denied")
        if battery_update.battery_secret is not None:
            raise HTTPException(status_code=403, detail="Cannot update battery secret")
    elif current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        update_data = battery_update.dict(exclude_unset=True)
        
        for key, value in update_data.items():
            setattr(battery, key, value)
        
        db.commit()
        db.refresh(battery)
        
        result = {c.name: getattr(battery, c.name) for c in battery.__table__.columns}
        result.pop('battery_secret', None)
        
        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/batteries/{battery_id}")
async def delete_battery(
    battery_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a battery (admin/superadmin only)"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
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

@app.get("/hubs/{hub_id}/batteries")
async def list_hub_batteries(
    hub_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all batteries for a hub"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.DATA_ADMIN]:
        if current_user.get('hub_id') != hub_id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    return db.query(BEPPPBattery).filter(BEPPPBattery.hub_id == hub_id).all()

# ============================================================================
# PUE ENDPOINTS
# ============================================================================

@app.post("/pue/",
    tags=["PUE"],
    summary="Create PUE Equipment",
    description="""
    ## Create Productive Use Equipment

    Add new PUE equipment to a hub with detailed specifications.
    
    ### Permissions:
    - **ADMIN**: Can create PUE equipment
    - **SUPERADMIN**: Can create PUE equipment
    
    ### Features:
    - **Equipment Types**: Different usage locations (hub only, battery only, both)
    - **Power Ratings**: Specify power consumption in watts
    - **Pricing**: Set suggested and actual rental costs
    - **Location Tracking**: Storage location and usage restrictions
    - **Notes System**: Detailed equipment history and comments
    
    ### Parameters:
    - **pue_id**: Unique identifier for the equipment
    - **hub_id**: Hub where equipment is located
    - **name**: Equipment name/model
    - **power_rating_watts**: Power consumption specification
    - **usage_location**: Where equipment can be used
    - **rental_cost**: Daily rental cost
    
    ### Returns:
    - Created PUE equipment details
    """,
    response_description="Created PUE equipment information")
async def create_pue_item(
    pue: PUECreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new PUE item (admin/superadmin only)"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        pue_data = pue.dict()
        if 'usage_location' in pue_data and pue_data['usage_location']:
            pue_data['usage_location'] = pue_data['usage_location'].value
        
        db_pue = ProductiveUseEquipment(**pue_data)
        db.add(db_pue)
        db.commit()
        db.refresh(db_pue)
        return db_pue
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/pue/{pue_id}")
async def get_pue_item(
    pue_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a PUE item by ID"""
    pue = db.query(ProductiveUseEquipment).filter(ProductiveUseEquipment.pue_id == pue_id).first()
    if not pue:
        raise HTTPException(status_code=404, detail="PUE item not found")
    
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        if current_user.get('role') == UserRole.DATA_ADMIN:
            pass
        else:
            if pue.hub_id != current_user.get('hub_id'):
                raise HTTPException(status_code=403, detail="Access denied")
    
    return pue

@app.put("/pue/{pue_id}")
async def update_pue_item(
    pue_id: int,
    pue_update: PUEUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a PUE item (admin/superadmin only)"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        pue = db.query(ProductiveUseEquipment).filter(ProductiveUseEquipment.pue_id == pue_id).first()
        if not pue:
            raise HTTPException(status_code=404, detail="PUE item not found")
        
        update_data = pue_update.dict(exclude_unset=True)
        
        if 'usage_location' in update_data and update_data['usage_location']:
            update_data['usage_location'] = update_data['usage_location'].value
        
        for key, value in update_data.items():
            setattr(pue, key, value)
        
        pue.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(pue)
        return pue
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/pue/{pue_id}")
async def delete_pue_item(
    pue_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Soft delete a PUE item (superadmin only)"""
    if current_user.get('role') != UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Superadmin access required")
    
    try:
        pue = db.query(ProductiveUseEquipment).filter(ProductiveUseEquipment.pue_id == pue_id).first()
        if not pue:
            raise HTTPException(status_code=404, detail="PUE item not found")
        
        pue.is_active = False
        pue.updated_at = datetime.utcnow()
        db.commit()
        return {"message": "PUE item deactivated successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/hubs/{hub_id}/pue")
async def list_hub_pue_items(
    hub_id: int,
    include_inactive: bool = Query(False, description="Include inactive PUE items"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all PUE items for a hub"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.DATA_ADMIN]:
        if current_user.get('hub_id') != hub_id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    query = db.query(ProductiveUseEquipment).filter(ProductiveUseEquipment.hub_id == hub_id)
    
    if not include_inactive:
        query = query.filter(ProductiveUseEquipment.is_active == True)
    
    return query.all()

@app.get("/hubs/{hub_id}/pue/available")
async def list_hub_available_pue_items(
    hub_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List all available PUE items for a hub that can be rented.
    
    Returns only PUE items that are:
    - Active (not soft-deleted)
    - Available for rental (status = "available")
    
    This endpoint is specifically designed for rental interfaces to show
    which PUE items can be added to a rental.
    """
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.DATA_ADMIN]:
        if current_user.get('hub_id') != hub_id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    available_pue_items = db.query(ProductiveUseEquipment).filter(
        ProductiveUseEquipment.hub_id == hub_id,
        ProductiveUseEquipment.is_active == True,
        ProductiveUseEquipment.status == "available"
    ).all()
    
    return available_pue_items

# ============================================================================
# RENTAL ENDPOINTS
# ============================================================================

@app.post("/rentals/",
    tags=["Rentals"],
    summary="Create Battery Rental",
    description="""
    ## Create a New Battery Rental

    Creates a new battery rental with optional PUE equipment.
    
    ### Permissions:
    - **ADMIN**: Can create rentals
    - **SUPERADMIN**: Can create rentals
    - **USER**: Can create rentals for their own hub
    
    ### Features:
    - Automatic battery availability checking
    - PUE equipment can be added during rental creation
    - Automatic due date calculation
    - Cost calculation with deposits
    - Notes system for additional information
    
    ### Returns:
    - Created rental information
    - Associated battery and PUE details
    - Cost breakdown and due dates
    """,
    response_description="Created rental with battery and PUE details")
async def create_rental(
    rental: RentalCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new battery rental with optional PUE items.
    
    ## Usage Examples:
    
    ### 1. Rent just a battery:
    ```json
    {
        "rentral_id": 1,
        "battery_id": 5,
        "user_id": 123,
        "timestamp_taken": "2024-07-09T10:00:00Z",
        "due_back": "2024-07-16T10:00:00Z",
        "pue_item_ids": []
    }
    ```
    
    ### 2. Rent battery with PUE items:
    ```json
    {
        "rentral_id": 2,
        "battery_id": 6,
        "user_id": 123,
        "timestamp_taken": "2024-07-09T10:00:00Z",
        "due_back": "2024-07-16T10:00:00Z",
        "pue_item_ids": [1, 3, 5],
        "total_cost": 25.00,
        "deposit_amount": 50.00
    }
    ```
    
    **Note**: PUE items are automatically marked as 'rented' when added to a rental.
    """
    if current_user.get('role') == UserRole.DATA_ADMIN:
        raise HTTPException(status_code=403, detail="Data admins cannot create rentals")
    
    try:
        battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == rental.battery_id).first()
        if not battery:
            raise HTTPException(status_code=404, detail="Battery not found")
        
        user = db.query(User).filter(User.user_id == rental.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if current_user.get('role') == UserRole.USER:
            if battery.hub_id != current_user.get('hub_id') or user.hub_id != current_user.get('hub_id'):
                raise HTTPException(status_code=403, detail="Access denied")
        
        pue_items = []
        if rental.pue_item_ids:
            pue_items = db.query(ProductiveUseEquipment).filter(
                ProductiveUseEquipment.pue_id.in_(rental.pue_item_ids),
                ProductiveUseEquipment.is_active == True
            ).all()
            
            if len(pue_items) != len(rental.pue_item_ids):
                raise HTTPException(status_code=400, detail="Some PUE items not found or inactive")
        
        rental_data = rental.dict(exclude={'pue_item_ids'})
        db_rental = Rental(**rental_data)
        db.add(db_rental)
        db.flush()
        
        for pue_item in pue_items:
            rental_pue_item = RentalPUEItem(
                rental_id=db_rental.rentral_id,
                pue_id=pue_item.pue_id,
                rental_cost=pue_item.rental_cost,
                due_back=rental.due_back
            )
            db.add(rental_pue_item)
        
        db.commit()
        db.refresh(db_rental)
        return db_rental
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/rentals/{rental_id}")
async def get_rental_with_pue(
    rental_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get rental with complete details including PUE items.
    
    Returns a comprehensive view of the rental including:
    - Rental information (dates, status, costs)
    - Battery details
    - User information (if not DATA_ADMIN)
    - All PUE items with their individual return status
    
    **Response includes:**
    - `rental`: Main rental object
    - `pue_items`: List of PUE items with return status
    - `battery`: Battery information
    - `user`: User details (null for DATA_ADMIN role)
    """
    rental = db.query(Rental).filter(Rental.rentral_id == rental_id).first()
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")
    
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        if current_user.get('role') == UserRole.DATA_ADMIN:
            pass
        else:
            battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == rental.battery_id).first()
            if not battery or battery.hub_id != current_user.get('hub_id'):
                raise HTTPException(status_code=403, detail="Access denied")
    
    rental_dict = {
        "rental": rental,
        "pue_items": rental.pue_items,
        "battery": rental.battery,
        "user": rental.user if current_user.get('role') != UserRole.DATA_ADMIN else None
    }
    
    return rental_dict

@app.put("/rentals/{rental_id}")
async def update_rental(
    rental_id: int,
    rental_update: RentalUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update rental details (legacy endpoint - use POST /rentals/{id}/return for returns).
    
    ## Usage Examples:
    
    ### 1. Update due date:
    ```json
    {
        "due_back": "2024-07-20T10:00:00Z"
    }
    ```
    
    ### 2. Record return (basic):
    ```json
    {
        "date_returned": "2024-07-15T14:30:00Z"
    }
    ```
    
    ### 3. Replace all PUE items:
    ```json
    {
        "pue_item_ids": [2, 4, 6]
    }
    ```
    
    **Recommendation**: Use the dedicated endpoints instead:
    - `POST /rentals/{id}/return` for returning items
    - `POST /rentals/{id}/add-pue` for adding PUE items
    """
    if current_user.get('role') == UserRole.DATA_ADMIN:
        raise HTTPException(status_code=403, detail="Data admins cannot modify rentals")
    
    rental = db.query(Rental).filter(Rental.rentral_id == rental_id).first()
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")
    
    if current_user.get('role') == UserRole.USER:
        battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == rental.battery_id).first()
        if not battery or battery.hub_id != current_user.get('hub_id'):
            raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        update_data = rental_update.dict(exclude_unset=True)
        
        if 'pue_item_ids' in update_data:
            pue_item_ids = update_data.pop('pue_item_ids')
            if pue_item_ids is not None:
                # Delete existing PUE items
                db.query(RentalPUEItem).filter(
                    RentalPUEItem.rental_id == rental.rentral_id
                ).delete()
                
                if pue_item_ids:
                    pue_items = db.query(ProductiveUseEquipment).filter(
                        ProductiveUseEquipment.pue_id.in_(pue_item_ids),
                        ProductiveUseEquipment.is_active == True
                    ).all()
                    
                    if len(pue_items) != len(pue_item_ids):
                        raise HTTPException(status_code=400, detail="Some PUE items not found or inactive")
                    
                    for pue_item in pue_items:
                        rental_pue_item = RentalPUEItem(
                            rental_id=rental.rentral_id,
                            pue_id=pue_item.pue_id,
                            rental_cost=pue_item.rental_cost,
                            due_back=rental.due_back
                        )
                        db.add(rental_pue_item)
        
        for key, value in update_data.items():
            setattr(rental, key, value)
        
        db.commit()
        db.refresh(rental)
        return rental
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/rentals/{rental_id}")
async def delete_rental(
    rental_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete rental (admin/superadmin only)"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
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

@app.post("/rentals/{rental_id}/return",
    tags=["Rentals"],
    summary="Return Battery Rental",
    description="""
    ## Return Battery Rental

    Process the return of a battery rental with condition assessment.
    
    ### Permissions:
    - **ADMIN**: Can process returns
    - **SUPERADMIN**: Can process returns
    - **USER**: Can return rentals from their hub
    
    ### Features:
    - Condition assessment and notes
    - Automatic status updates
    - PUE equipment return handling
    - Cost calculations and refunds
    
    ### Parameters:
    - **rental_id**: ID of the rental to return
    - **return_request**: Return details including condition and notes
    
    ### Returns:
    - Updated rental information
    - Return confirmation details
    """,
    response_description="Return confirmation and updated rental details")
async def return_rental(
    rental_id: int,
    return_request: RentalReturnRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Return battery and/or PUE items for a rental with comprehensive options.
    
    ## Usage Examples:
    
    ### 1. Return everything (battery + all PUE items):
    ```json
    {
        "return_battery": true,
        "return_pue_items": null,
        "battery_condition": "good",
        "return_notes": "All items returned in good condition"
    }
    ```
    
    ### 2. Return only battery, keep PUE items:
    ```json
    {
        "return_battery": true,
        "return_pue_items": [],
        "battery_condition": "good",
        "return_notes": "Battery returned, user keeping PUE items"
    }
    ```
    
    ### 3. Return specific PUE items only:
    ```json
    {
        "return_battery": false,
        "return_pue_items": [1, 3, 5],
        "return_notes": "Returned drill, lamp, and radio"
    }
    ```
    
    ### 4. Partial return + add new PUE items:
    ```json
    {
        "return_battery": false,
        "return_pue_items": [1, 2],
        "add_pue_items": [6, 7],
        "return_notes": "Returned drill and saw, added phone charger and speaker"
    }
    ```
    
    ### 5. Exchange PUE items (return some, add others):
    ```json
    {
        "return_battery": false,
        "return_pue_items": [1, 3],
        "add_pue_items": [8, 9],
        "return_notes": "Exchanged tools for different equipment"
    }
    ```
    
    **Parameters:**
    - `return_battery`: Whether to return the battery (default: true)
    - `return_pue_items`: List of PUE IDs to return (null = all, [] = none, [1,2,3] = specific items)
    - `add_pue_items`: List of PUE IDs to add to the rental
    - `battery_condition`: Condition of returned battery
    - `battery_notes`: Notes about battery return
    - `return_notes`: General notes about the return
    """
    if current_user.get('role') == UserRole.DATA_ADMIN:
        raise HTTPException(status_code=403, detail="Data admins cannot process returns")
    
    rental = db.query(Rental).filter(Rental.rentral_id == rental_id).first()
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")
    
    # Authorization check
    if current_user.get('role') == UserRole.USER:
        battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == rental.battery_id).first()
        if not battery or battery.hub_id != current_user.get('hub_id'):
            raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        return_summary = {
            "battery_returned": False,
            "pue_items_returned": [],
            "pue_items_added": [],
            "still_rented": {
                "battery": False,
                "pue_items": []
            }
        }
        
        # Handle battery return
        if return_request.return_battery:
            rental.battery_returned_date = datetime.now(timezone.utc)
            if return_request.battery_condition:
                rental.battery_return_condition = return_request.battery_condition
            if return_request.battery_notes:
                rental.battery_return_notes = return_request.battery_notes
            
            # Update battery status to available
            battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == rental.battery_id).first()
            if battery:
                battery.status = "available"
            
            return_summary["battery_returned"] = True
        else:
            return_summary["still_rented"]["battery"] = True
        
        # Handle PUE item returns
        current_pue_items = db.query(RentalPUEItem).filter(
            RentalPUEItem.rental_id == rental.rentral_id,
            RentalPUEItem.is_returned == False
        ).all()
        
        if return_request.return_pue_items is None:
            # Return all PUE items
            for pue_item in current_pue_items:
                pue_item.is_returned = True
                pue_item.returned_date = datetime.now(timezone.utc)
                
                # Update PUE status to available
                pue = db.query(ProductiveUseEquipment).filter(
                    ProductiveUseEquipment.pue_id == pue_item.pue_id
                ).first()
                if pue:
                    pue.status = "available"
                
                return_summary["pue_items_returned"].append(pue_item.pue_id)
        
        elif return_request.return_pue_items:
            # Return specific PUE items
            for pue_id in return_request.return_pue_items:
                pue_item = next((item for item in current_pue_items if item.pue_id == pue_id), None)
                if pue_item:
                    pue_item.is_returned = True
                    pue_item.returned_date = datetime.now(timezone.utc)
                    
                    # Update PUE status to available
                    pue = db.query(ProductiveUseEquipment).filter(
                        ProductiveUseEquipment.pue_id == pue_id
                    ).first()
                    if pue:
                        pue.status = "available"
                    
                    return_summary["pue_items_returned"].append(pue_id)
        
        # Find still rented PUE items
        still_rented_pue = db.query(RentalPUEItem).filter(
            RentalPUEItem.rental_id == rental.rentral_id,
            RentalPUEItem.is_returned == False
        ).all()
        return_summary["still_rented"]["pue_items"] = [item.pue_id for item in still_rented_pue]
        
        # Handle adding new PUE items
        if return_request.add_pue_items:
            new_pue_items = db.query(ProductiveUseEquipment).filter(
                ProductiveUseEquipment.pue_id.in_(return_request.add_pue_items),
                ProductiveUseEquipment.is_active == True,
                ProductiveUseEquipment.status == "available"
            ).all()
            
            if len(new_pue_items) != len(return_request.add_pue_items):
                raise HTTPException(status_code=400, detail="Some PUE items not found or not available")
            
            for pue_item in new_pue_items:
                rental_pue_item = RentalPUEItem(
                    rental_id=rental.rentral_id,
                    pue_id=pue_item.pue_id,
                    rental_cost=pue_item.rental_cost,
                    due_back=rental.due_back
                )
                db.add(rental_pue_item)
                
                # Update PUE status to rented
                pue_item.status = "rented"
                
                return_summary["pue_items_added"].append(pue_item.pue_id)
                return_summary["still_rented"]["pue_items"].append(pue_item.pue_id)
        
        # Add general return notes
        if return_request.return_notes:
            rental.battery_return_notes = (rental.battery_return_notes or "") + f"\n{return_request.return_notes}"
        
        # Update rental status if everything is returned
        if (return_request.return_battery and 
            not return_summary["still_rented"]["pue_items"]):
            rental.is_active = False
            rental.status = "completed"
        
        db.commit()
        
        return {
            "message": "Return processed successfully",
            "rental_id": rental_id,
            "return_summary": return_summary,
            "rental_status": rental.status,
            "is_active": rental.is_active,
            "processed_by": current_user.get('sub'),
            "processed_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/rentals/{rental_id}/add-pue")
async def add_pue_to_rental(
    rental_id: int,
    add_request: AddPUEToRentalRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Add PUE items to an existing rental.
    
    ## Usage Examples:
    
    ### 1. Add PUE items with default due date:
    ```json
    {
        "pue_item_ids": [4, 5, 6]
    }
    ```
    
    ### 2. Add PUE items with custom due date and cost:
    ```json
    {
        "pue_item_ids": [7, 8],
        "rental_cost": 15.50,
        "due_back": "2024-07-15T10:00:00Z"
    }
    ```
    
    This endpoint allows you to add more equipment to an ongoing rental 
    without affecting existing items.
    """
    if current_user.get('role') == UserRole.DATA_ADMIN:
        raise HTTPException(status_code=403, detail="Data admins cannot modify rentals")
    
    rental = db.query(Rental).filter(Rental.rentral_id == rental_id).first()
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")
    
    if not rental.is_active:
        raise HTTPException(status_code=400, detail="Cannot add items to inactive rental")
    
    # Authorization check
    if current_user.get('role') == UserRole.USER:
        battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == rental.battery_id).first()
        if not battery or battery.hub_id != current_user.get('hub_id'):
            raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Validate PUE items are available
        pue_items = db.query(ProductiveUseEquipment).filter(
            ProductiveUseEquipment.pue_id.in_(add_request.pue_item_ids),
            ProductiveUseEquipment.is_active == True,
            ProductiveUseEquipment.status == "available"
        ).all()
        
        if len(pue_items) != len(add_request.pue_item_ids):
            raise HTTPException(status_code=400, detail="Some PUE items not found or not available")
        
        added_items = []
        for pue_item in pue_items:
            rental_pue_item = RentalPUEItem(
                rental_id=rental.rentral_id,
                pue_id=pue_item.pue_id,
                rental_cost=add_request.rental_cost or pue_item.rental_cost,
                due_back=add_request.due_back or rental.due_back
            )
            db.add(rental_pue_item)
            
            # Update PUE status to rented
            pue_item.status = "rented"
            
            added_items.append({
                "pue_id": pue_item.pue_id,
                "name": pue_item.name,
                "rental_cost": rental_pue_item.rental_cost,
                "due_back": rental_pue_item.due_back.isoformat() if rental_pue_item.due_back else None
            })
        
        db.commit()
        
        return {
            "message": "PUE items added successfully",
            "rental_id": rental_id,
            "added_items": added_items,
            "total_pue_items": len(rental.pue_items) + len(added_items),
            "added_by": current_user.get('sub'),
            "added_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# DATA QUERY ENDPOINTS
# ============================================================================

@app.get("/data/battery/{battery_id}",
    tags=["Data & Analytics"],
    summary="Get Battery Data",
    description="""
    ## Retrieve Battery Data

    Get historical data for a specific battery with filtering options.
    
    ### Permissions:
    - **ADMIN**: Can view all battery data
    - **SUPERADMIN**: Can view all battery data  
    - **DATA_ADMIN**: Can view all battery data
    
    ### Features:
    - Date range filtering
    - Export in JSON or CSV format
    - Pagination with limit controls
    - Real-time and historical data access
    
    ### Parameters:
    - **battery_id**: ID of the battery to retrieve data for
    - **start_timestamp**: Start date for data range (optional)
    - **end_timestamp**: End date for data range (optional)
    - **limit**: Maximum number of records (default: 1000)
    - **format**: Export format (json/csv)
    
    ### Returns:
    - Battery data records
    - Metadata about the query
    """,
    response_description="Battery data records and metadata")
async def get_battery_data(
    battery_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    start_timestamp: Optional[datetime] = None,
    end_timestamp: Optional[datetime] = None,
    limit: int = 1000,
    format: str = Query("json", description="Output format: json or csv")
):
    """
    Get battery data in specified format (json or csv)
    """
    # Input validation
    if format not in ["json", "csv"]:
        raise HTTPException(status_code=400, detail="Format must be either 'json' or 'csv'")

    # Your existing query logic
    battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == battery_id).first()
    if not battery:
        raise HTTPException(status_code=404, detail="Battery not found")
    
    # Authorization check
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.DATA_ADMIN]:
        if battery.hub_id != current_user.get('hub_id'):
            raise HTTPException(status_code=403, detail="Access denied")

    # Query construction
    query = db.query(LiveData).filter(LiveData.battery_id == battery_id)
    
    if start_timestamp:
        query = query.filter(LiveData.timestamp >= start_timestamp)
    if end_timestamp:
        query = query.filter(LiveData.timestamp <= end_timestamp)
    
    data = query.order_by(LiveData.timestamp.desc()).limit(limit).all()
    
    if not data:
        raise HTTPException(status_code=404, detail=f"No data found for battery {battery_id}")
    
    # Convert to dicts
    data_dicts = [
        {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
        for obj in data
    ]

    # Format response
    if format == "json":
        return JSONResponse(content={
            "battery_id": battery_id,
            "data": data_dicts,
            "count": len(data_dicts)
        })
    else:  # csv
        df = pd.DataFrame(data_dicts)
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        return Response(
            content=csv_buffer.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=battery_{battery_id}_data.csv"}
        )

@app.get("/data/latest/{battery_id}")
async def get_latest_data(
    battery_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get the latest data point for a battery"""
    battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == battery_id).first()
    if not battery:
        raise HTTPException(status_code=404, detail="Battery not found")
    
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.DATA_ADMIN]:
        if battery.hub_id != current_user.get('hub_id'):
            raise HTTPException(status_code=403, detail="Access denied")
    
    data = db.query(LiveData).filter(LiveData.battery_id == battery_id).order_by(LiveData.timestamp.desc()).first()
    if not data:
        raise HTTPException(status_code=404, detail="No data found for this battery")
    return data

# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@app.get("/analytics/hub-summary",
    tags=["Data & Analytics"],
    summary="Hub Summary Analytics",
    description="""
    ## Hub Summary Analytics

    Get comprehensive statistics for one or more hubs.
    
    ### Permissions:
    - **ADMIN**: Can view all hubs
    - **SUPERADMIN**: Can view all hubs
    - **DATA_ADMIN**: Can view all hubs (anonymized user data)
    
    ### Features:
    - Total batteries and PUE equipment per hub
    - Active rental counts
    - Overdue rental tracking
    - Revenue summaries
    - Equipment utilization rates
    
    ### Parameters:
    - **hub_ids**: Optional list of specific hub IDs to analyze
    
    ### Returns:
    - Hub statistics and summaries
    - Rental analytics
    - Equipment status overview
    """,
    response_description="Hub summary statistics and analytics")
async def get_hub_summary(
    hub_ids: Optional[List[int]] = Query(None, description="Specific hub IDs"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get summary statistics for hubs"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.DATA_ADMIN]:
        raise HTTPException(status_code=403, detail="Data access required")
    
    # Filter hubs based on user access
    if current_user.get('role') == UserRole.SUPERADMIN:
        # Superadmin can access any hubs
        pass
    elif current_user.get('role') == UserRole.DATA_ADMIN:
        # DATA_ADMIN can only access their assigned hubs
        accessible_hub_ids = current_user.get('accessible_hub_ids', [])
        if hub_ids:
            # Filter requested hubs to only those the user has access to
            hub_ids = [h for h in hub_ids if h in accessible_hub_ids]
        else:
            # If no specific hubs requested, use all accessible hubs
            hub_ids = accessible_hub_ids
        
        if not hub_ids:
            return {"message": "No accessible hubs found", "hubs": []}
    else:
        # ADMIN users can only access their own hub
        user_hub_id = current_user.get('hub_id')
        if hub_ids and user_hub_id not in hub_ids:
            raise HTTPException(status_code=403, detail="Access denied to requested hubs")
        hub_ids = [user_hub_id]
    
    if hub_ids is None:
        if current_user.get('role') == UserRole.DATA_ADMIN:
            hubs = db.query(SolarHub).all()
        elif current_user.get('role') in [UserRole.ADMIN, UserRole.SUPERADMIN]:
            hubs = db.query(SolarHub).all()
        else:
            hubs = db.query(SolarHub).filter(SolarHub.hub_id == current_user.get('hub_id')).all()
    else:
        hubs = db.query(SolarHub).filter(SolarHub.hub_id.in_(hub_ids)).all()
    
    hub_summaries = []
    for hub in hubs:
        battery_stats = db.query(
            BEPPPBattery.status,
            func.count(BEPPPBattery.battery_id).label('count')
        ).filter(BEPPPBattery.hub_id == hub.hub_id).group_by(BEPPPBattery.status).all()
        
        pue_count = db.query(ProductiveUseEquipment).filter(
            ProductiveUseEquipment.hub_id == hub.hub_id,
            ProductiveUseEquipment.is_active == True
        ).count()
        
        active_rentals = db.query(Rental).filter(
            Rental.battery_id.in_(
                db.query(BEPPPBattery.battery_id).filter(BEPPPBattery.hub_id == hub.hub_id)
            ),
            Rental.is_active == True,
            Rental.date_returned.is_(None)
        ).count()
        
        hub_summaries.append({
            "hub_id": hub.hub_id,
            "hub_name": hub.what_three_word_location,
            "country": hub.country,
            "solar_capacity_kw": hub.solar_capacity_kw,
            "battery_stats": {stat.status: stat.count for stat in battery_stats},
            "total_batteries": sum(stat.count for stat in battery_stats),
            "pue_count": pue_count,
            "active_rentals": active_rentals
        })
    
    return hub_summaries

@app.post("/analytics/power-usage")
async def get_power_usage_analytics(
    request: DataAggregationRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get aggregated power usage analytics"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.DATA_ADMIN]:
        raise HTTPException(status_code=403, detail="Data access required")
    
    try:
        if request.time_period and (request.start_time or request.end_time):
            raise HTTPException(
                status_code=400, 
                detail="Cannot specify both time_period and start_time/end_time"
            )
        
        if (request.start_time and not request.end_time) or (request.end_time and not request.start_time):
            raise HTTPException(
                status_code=400,
                detail="When using custom dates, both start_time and end_time must be provided"
            )
        
        if request.time_period:
            start_time, end_time = calculate_time_period(request.time_period)
            time_period_description = f"Predefined period: {request.time_period.value}"
        elif request.start_time and request.end_time:
            start_time, end_time = request.start_time, request.end_time
            time_period_description = f"Custom period: {start_time.isoformat()} to {end_time.isoformat()}"
        else:
            start_time, end_time = calculate_time_period(TimePeriod.LAST_WEEK)
            time_period_description = f"Default period: {TimePeriod.LAST_WEEK.value}"
        
        battery_ids = []
        
        if request.battery_selection.all_batteries:
            if request.battery_selection.hub_ids:
                batteries = db.query(BEPPPBattery.battery_id).filter(
                    BEPPPBattery.hub_id.in_(request.battery_selection.hub_ids)
                ).all()
            else:
                batteries = db.query(BEPPPBattery.battery_id).all()
            battery_ids = [b.battery_id for b in batteries]
        
        elif request.battery_selection.battery_ids:
            battery_ids = request.battery_selection.battery_ids
        
        elif request.battery_selection.hub_ids:
            batteries = db.query(BEPPPBattery.battery_id).filter(
                BEPPPBattery.hub_id.in_(request.battery_selection.hub_ids)
            ).all()
            battery_ids = [b.battery_id for b in batteries]
        
        if not battery_ids:
            return {"error": "No batteries found matching criteria"}
        
        live_data_query = db.query(LiveData).filter(
            LiveData.battery_id.in_(battery_ids),
            LiveData.timestamp >= start_time,
            LiveData.timestamp <= end_time
        )
        
        live_data = live_data_query.all()
        if not live_data:
            return {"error": "No data found for the specified criteria"}
        
        data_dicts = []
        for data_point in live_data:
            data_dicts.append({
                'battery_id': data_point.battery_id,
                'timestamp': data_point.timestamp,
                'power_watts': data_point.power_watts,
                'state_of_charge': data_point.state_of_charge,
                'voltage': data_point.voltage,
                'current_amps': data_point.current_amps
            })
        
        df = pd.DataFrame(data_dicts)
        
        if request.aggregation_period == AggregationPeriod.HOUR:
            df['time_group'] = df['timestamp'].dt.floor('H')
        elif request.aggregation_period == AggregationPeriod.DAY:
            df['time_group'] = df['timestamp'].dt.floor('D')
        elif request.aggregation_period == AggregationPeriod.WEEK:
            df['time_group'] = df['timestamp'].dt.to_period('W').dt.start_time
        elif request.aggregation_period == AggregationPeriod.MONTH:
            df['time_group'] = df['timestamp'].dt.to_period('M').dt.start_time
        
        if request.aggregation_function == AggregationFunction.SUM:
            agg_func = 'sum'
        elif request.aggregation_function == AggregationFunction.MEAN:
            agg_func = 'mean'
        elif request.aggregation_function == AggregationFunction.MEDIAN:
            agg_func = 'median'
        elif request.aggregation_function == AggregationFunction.MIN:
            agg_func = 'min'
        elif request.aggregation_function == AggregationFunction.MAX:
            agg_func = 'max'
        
        if request.metric in df.columns:
            result = df.groupby(['time_group', 'battery_id'])[request.metric].agg(agg_func).reset_index()
            
            result['time_group'] = result['time_group'].astype(str)
            result_dict = result.to_dict('records')
            
            summary = {
                'total_data_points': len(df),
                'battery_count': df['battery_id'].nunique(),
                'time_periods': len(result['time_group'].unique()),
                'metric_summary': {
                    'min': float(result[request.metric].min()),
                    'max': float(result[request.metric].max()),
                    'mean': float(result[request.metric].mean()),
                    'median': float(result[request.metric].median())
                }
            }
            
            return {
                'time_period': {
                    'description': time_period_description,
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'days_analyzed': (end_time - start_time).days
                },
                'data': result_dict,
                'summary': summary,
                'request_parameters': {
                    'metric': request.metric,
                    'aggregation_period': request.aggregation_period,
                    'aggregation_function': request.aggregation_function,
                    'time_period': request.time_period.value if request.time_period else None
                }
            }
        else:
            raise HTTPException(status_code=400, detail=f"Metric '{request.metric}' not available")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")

# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

@app.get("/admin/webhook-logs")
async def get_webhook_logs(
    lines: int = Query(100, description="Number of recent log lines to return"),
    current_user: dict = Depends(get_current_user)
):
    """Get recent webhook logs (admin/superadmin only, DEBUG mode only)"""
    if not DEBUG:
        raise HTTPException(
            status_code=404, 
            detail="Webhook logs are only available in DEBUG mode"
        )
    
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
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

# ============================================================================
# HEALTH CHECK AND ROOT ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        result = db.execute(text("SELECT 1")).fetchone()
        db_status = "connected" if result else "disconnected"
    except Exception as e:
        db_status = "disconnected"
        print(f"Database health check failed: {e}")
    
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "database": db_status
    }

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Solar Hub Management API with PUE & Analytics",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health",
        "features": {
            "pue_management": "Productive Use Equipment tracking and rental",
            "data_analytics": "Power usage analytics and rental statistics", 
            "enhanced_rentals": "Battery rentals with PUE equipment",
            "flexible_returns": "Comprehensive return system with partial returns and item exchanges",
            "role_based_access": "Fine-grained permission system"
        },
        "key_endpoints": {
            "rentals": {
                "create": "POST /rentals/ - Start a new rental",
                "get": "GET /rentals/{id} - Get rental details",
                "return": "POST /rentals/{id}/return - Return battery/PUE items",
                "add_pue": "POST /rentals/{id}/add-pue - Add PUE items to rental"
            },
            "examples": {
                "full_return": "POST /rentals/1/return with return_battery=true, return_pue_items=null",
                "partial_return": "POST /rentals/1/return with return_battery=true, return_pue_items=[1,2]",
                "exchange_pue": "POST /rentals/1/return with return_pue_items=[1,2], add_pue_items=[3,4]"
            }
        },
        "roles": {
            "user": "Kiosk operator - can manage users/batteries in their hub",
            "admin": "Full access except webhook data submission",
            "superadmin": "Full access to everything",
            "battery": "Can only submit data to webhook endpoint",
            "data_admin": "Read-only access to analytics and data"
        },
        "authentication": {
            "users": {
                "login": "POST /auth/token",
                "credentials": "username and password",
                "token_expires_hours": USER_TOKEN_EXPIRE_HOURS
            },
            "batteries": {
                "login": "POST /auth/battery-login",
                "refresh": "POST /auth/battery-refresh",
                "credentials": "battery_id and battery_secret",
                "token_expires_hours": BATTERY_TOKEN_EXPIRE_HOURS
            }
        }
    }

# ============================================================================
# STARTUP EVENT
# ============================================================================

@app.on_event("startup")
async def startup():
    try:
        setup_webhook_logging()
        
        if DEBUG:
            webhook_logger.info("🚀 Enhanced API with PUE & Analytics initialized (DEBUG MODE)")
            print("🔍 DEBUG MODE: Detailed webhook logging enabled")
        else:
            print("🚀 Production mode: Minimal logging enabled (errors/warnings only)")
        
        init_db()
        
        if DEBUG:
            webhook_logger.info("✅ Database tables created/verified")
        
        print("✅ Enhanced API ready with PUE management and data analytics")
        
    except Exception as e:
        if DEBUG:
            webhook_logger.error(f"❌ Startup failed: {e}")
        print(f"❌ Database initialization failed: {e}")
        raise e

# ============================================================================
# RUN THE APP
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)