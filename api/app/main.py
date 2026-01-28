from fastapi import FastAPI, HTTPException, Depends, status, Query, Request, File, UploadFile, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse, FileResponse
from pydantic import BaseModel, Field, ConfigDict, field_validator
from sqlalchemy.orm import Session
from sqlalchemy import text, func, and_, or_, desc
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timezone, timedelta, date
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
import shutil
from pathlib import Path
import uuid

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import get_db, init_db
from models import *
from sqlalchemy import Table
from api.app.utils.rental_id_generator import generate_rental_id
from api.app.services.pay_to_own_service import PayToOwnService

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

    try:
        from config import WEBHOOK_LOG_LIMIT
    except ImportError:
        WEBHOOK_LOG_LIMIT = 100

except ImportError as e:
    raise ImportError(
        "Missing required configuration. Please ensure config.py exists with SECRET_KEY, ALGORITHM, and DEBUG defined."
    ) from e

###############################################################################
# WEBHOOK LOGGING CONFIGURATION
# Set to True to log authentication events to database (visible in frontend)
# Set to False to log only to file
###############################################################################
ENABLE_DATABASE_LOGGING = True  # Change to False to disable database logging

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
    # IMPORTANT: Always set up logging in production AND debug mode
    # We need authentication logs visible in production for security monitoring

    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    webhook_logger = logging.getLogger('webhook')
    # Use INFO level in production (not WARNING) so we can see login events
    webhook_logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)

    webhook_handler = logging.FileHandler(f'{log_dir}/webhook.log')
    # Use INFO level in production so authentication events are logged
    webhook_handler.setLevel(logging.DEBUG if DEBUG else logging.INFO)

    console_handler = logging.StreamHandler()
    # Keep console at INFO in production for visibility
    console_handler.setLevel(logging.INFO)
    
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
    user_info: dict = None,
    battery_id: Optional[int] = None,
    data_id: Optional[int] = None,
    status: str = "success",
    error_message: Optional[str] = None,
    summary: Optional[dict] = None,
    request_data: Optional[dict] = None,
    additional_info: Optional[dict] = None,
    db: Session = None  # NEW: Optional database session for saving to DB
):
    # Always log errors, warnings, and info events (expanded logging for debugging)
    if status == "error" or status == "warning":
        should_log = True
    elif DEBUG:
        should_log = True
    else:
        # Log all authentication and token-related events even in production
        if "token" in event_type.lower() or "auth" in event_type.lower() or "login" in event_type.lower():
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

    if additional_info:
        for key, value in additional_info.items():
            log_message += f" | {key}: {value}"

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

    ###########################################################################
    # NEW: Also save to database for frontend Webhook Logs page visibility
    # This makes authentication and token events visible in the UI
    # Controlled by ENABLE_DATABASE_LOGGING constant (line ~67)
    ###########################################################################
    if db is not None and ENABLE_DATABASE_LOGGING:
        try:
            # Build request/response info from event data
            request_body = {}
            response_body = {"event_type": event_type, "status": status}

            if additional_info:
                request_body.update(additional_info)

            if error_message:
                response_body["error"] = error_message

            if summary:
                response_body["summary"] = summary

            # Determine response status code based on event status
            if status == "success":
                response_status = 200
            elif status == "error":
                response_status = 400 if "failed" in event_type else 500
            elif status == "warning":
                response_status = 200
            else:
                response_status = 200

            # Create webhook log entry for database
            webhook_log = WebhookLog(
                battery_id=str(battery_id) if battery_id else None,
                endpoint=event_type,  # Use event_type as endpoint
                method="EVENT",  # Special method to distinguish from HTTP methods
                request_headers={},
                request_body=request_body,
                response_status=response_status,
                response_body=response_body,
                error_message=error_message,
                processing_time_ms=0  # Events don't have processing time
            )

            db.add(webhook_log)
            db.commit()
        except Exception as e:
            # Don't fail the main operation if logging fails
            webhook_logger.error(f"Failed to save webhook event to database: {str(e)}")
            try:
                db.rollback()
            except:
                pass

def log_webhook_to_db(
    db: Session,
    battery_id: Optional[int],
    endpoint: str,
    method: str,
    request_headers: Optional[dict],
    request_body: Optional[dict],
    response_status: Optional[int],
    response_body: Optional[dict],
    error_message: Optional[str],
    processing_time_ms: Optional[int]
):
    """
    Log webhook request/response to database for production debugging.
    All logs are preserved for historical analysis and troubleshooting.
    """
    try:
        # Create webhook log entry
        webhook_log = WebhookLog(
            battery_id=battery_id,
            endpoint=endpoint,
            method=method,
            request_headers=json.dumps(request_headers) if request_headers else None,
            request_body=json.dumps(request_body) if request_body else None,
            response_status=response_status,
            response_body=json.dumps(response_body) if response_body else None,
            error_message=error_message,
            processing_time_ms=processing_time_ms
        )
        db.add(webhook_log)
        db.commit()

        # NOTE: All logs are now preserved. No automatic cleanup.
        # If database grows too large, implement manual cleanup or archival strategy.

    except Exception as e:
        # Don't let logging failures break the webhook
        print(f"Failed to log webhook to database: {e}")
        db.rollback()

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
    return_survey_required: Optional[bool] = None

class UserCreate(BaseModel):
    user_id: Optional[int] = None  # Auto-generated by database
    # New name fields (preferred)
    first_names: Optional[str] = None
    last_name: Optional[str] = None
    # Legacy name field (for backward compatibility)
    name: Optional[str] = None

    users_identification_document_number: Optional[str] = None
    mobile_number: Optional[str] = None

    # Address fields
    physical_address: Optional[str] = None
    address: Optional[str] = None  # Legacy field for backward compatibility

    # New customer demographic fields
    date_of_birth: Optional[datetime] = None
    gesi_status: Optional[str] = None
    business_category: Optional[str] = None
    monthly_energy_expenditure: Optional[float] = None
    main_reason_for_signup: Optional[str] = None

    hub_id: int
    user_access_level: str
    username: Optional[str] = None  # Auto-generated from name if not provided
    password: Optional[str] = None  # Auto-generated if not provided
    id_document_photo_url: Optional[str] = None

class UserUpdate(BaseModel):
    # New name fields (preferred)
    first_names: Optional[str] = None
    last_name: Optional[str] = None
    # Legacy name field (for backward compatibility)
    name: Optional[str] = None

    users_identification_document_number: Optional[str] = None
    mobile_number: Optional[str] = None

    # Address fields
    physical_address: Optional[str] = None
    address: Optional[str] = None  # Legacy field for backward compatibility

    # New customer demographic fields
    date_of_birth: Optional[datetime] = None
    gesi_status: Optional[str] = None
    business_category: Optional[str] = None
    monthly_energy_expenditure: Optional[float] = None
    main_reason_for_signup: Optional[str] = None

    user_access_level: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    id_document_photo_url: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class BatteryCreate(BaseModel):
    battery_id: str
    hub_id: int
    battery_capacity_wh: Optional[int] = None
    status: Optional[str] = "available"
    battery_secret: Optional[str] = None

class BatteryUpdate(BaseModel):
    battery_capacity_wh: Optional[int] = None
    status: Optional[str] = None
    battery_secret: Optional[str] = None

class BatteryAuth(BaseModel):
    battery_id: str
    battery_secret: str

class BatteryLogin(BaseModel):
    battery_id: str
    battery_secret: str

class BatterySecretUpdate(BaseModel):
    new_secret: str

class PUECreate(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    pue_id: str
    hub_id: int
    name: str
    description: Optional[str] = None
    power_rating_watts: Optional[float] = None
    usage_location: str = Field(default="both", description="Usage location: hub_only, battery_only, or both")
    storage_location: Optional[str] = None
    suggested_cost_per_day: Optional[float] = None
    rental_cost: Optional[float] = None
    status: Optional[str] = "available"
    


class PUEUpdate(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: Optional[str] = None
    description: Optional[str] = None
    power_rating_watts: Optional[float] = None
    usage_location: Optional[str] = Field(default=None, description="Usage location: hub_only, battery_only, or both")
    storage_location: Optional[str] = None
    suggested_cost_per_day: Optional[float] = None
    rental_cost: Optional[float] = None
    status: Optional[str] = None
    
    

class RentalCreateUserFriendly(BaseModel):
    """User-friendly rental creation model"""
    user_name: str
    user_mobile: str
    battery_id: Union[int, str]  # Support both int and string battery IDs
    rental_cost: Optional[float] = None
    due_back: Optional[datetime] = None
    pue_item_ids: Optional[List[int]] = []
    deposit_amount: Optional[float] = None
    rental_notes: Optional[str] = None

    @field_validator('battery_id', mode='before')
    @classmethod
    def convert_battery_id_to_str(cls, v):
        """Convert battery_id to string if it's an integer"""
        return str(v) if v is not None else v

class RentalCreate(BaseModel):
    rentral_id: Optional[int] = None
    battery_id: Union[int, str]  # Support both int and string battery IDs
    user_id: int
    timestamp_taken: datetime
    due_back: Optional[datetime] = None
    pue_item_ids: Optional[List[int]] = []
    total_cost: Optional[float] = None
    deposit_amount: Optional[float] = None

    @field_validator('battery_id', mode='before')
    @classmethod
    def convert_battery_id_to_str(cls, v):
        """Convert battery_id to string if it's an integer"""
        return str(v) if v is not None else v

class RentalUpdate(BaseModel):
    due_back: Optional[datetime] = None
    date_returned: Optional[datetime] = None
    battery_returned_date: Optional[datetime] = None
    pue_item_ids: Optional[List[int]] = None
    total_cost: Optional[float] = None

class PUERentalCreate(BaseModel):
    pue_rental_id: int
    pue_id: str
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
    battery_ids: Optional[List[str]] = None
    hub_ids: Optional[List[int]] = None
    pue_ids: Optional[List[str]] = None
    all_batteries: bool = False

class DataAggregationRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    battery_selection: BatterySelectionCriteria
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    time_period: Optional[str] = Field(default=None, description="Time period: last_24_hours, last_week, etc.")
    aggregation_period: str = Field(..., description="Period: hour, day, week, month")
    aggregation_function: str = Field(..., description="Function: sum, mean, median, min, max")
    metric: str

class RentalAnalyticsRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    hub_ids: Optional[List[int]] = None
    pue_ids: Optional[List[str]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    time_period: Optional[str] = Field(default=None, description="Time period: last_24_hours, last_week, etc.")
    group_by: Optional[str] = "pue_id"

class RentalReturnRequest(BaseModel):
    """Request model for returning battery and/or PUE items"""
    return_battery: bool = Field(True, description="Whether to return the battery")
    return_pue_items: Optional[List[int]] = Field(None, description="List of PUE item IDs to return (if None, returns all)")
    add_pue_items: Optional[List[int]] = Field(None, description="List of PUE item IDs to add to the rental")
    battery_condition: Optional[str] = Field(None, description="Condition of returned battery")
    battery_notes: Optional[str] = Field(None, description="Notes about battery return")
    return_notes: Optional[str] = Field(None, description="General return notes")
    actual_return_date: Optional[datetime] = Field(None, description="Actual return date (defaults to now)")

    # Usage data for final cost calculation
    kwh_usage_end: Optional[float] = Field(None, description="kWh reading at return (for kWh-based billing)")

    # Payment on return
    payment_amount: Optional[float] = Field(None, description="Payment amount if collecting payment on return")
    payment_type: Optional[str] = Field(None, description="Payment type: Cash, Mobile Money, Bank Transfer, Card")
    payment_method: Optional[str] = Field(None, description="Payment method: upfront, on_return, partial, deposit_only")
    payment_notes: Optional[str] = Field(None, description="Notes about the payment")

class AddPUEToRentalRequest(BaseModel):
    """Request model for adding PUE items to an existing rental"""
    pue_item_ids: List[int] = Field(..., description="List of PUE item IDs to add")
    rental_cost: Optional[float] = Field(None, description="Additional cost for new PUE items")
    due_back: Optional[datetime] = Field(None, description="Due date for new PUE items")

# ============================================================================
# NEW RENTAL SYSTEM PYDANTIC MODELS
# ============================================================================

class BatteryRentalCreate(BaseModel):
    """Create a new battery rental"""
    user_id: int = Field(..., description="User ID renting the batteries")
    battery_ids: List[str] = Field(..., description="List of battery IDs to rent")
    cost_structure_id: int = Field(..., description="Cost structure to apply")
    rental_start_date: Optional[datetime] = Field(None, description="Rental start date (defaults to now)")
    due_date: Optional[datetime] = Field(None, description="Expected return date")
    deposit_amount: Optional[float] = Field(None, description="Deposit collected")
    notes: Optional[List[str]] = Field(None, description="Notes about the rental")

    @field_validator('battery_ids', mode='before')
    @classmethod
    def convert_battery_ids_to_str(cls, v):
        """Convert all battery_ids to strings if they are integers"""
        if isinstance(v, list):
            return [str(item) if isinstance(item, int) else item for item in v]
        return v

class BatteryRentalUpdate(BaseModel):
    """Update battery rental details"""
    due_date: Optional[datetime] = Field(None, description="Update expected return date")
    notes: Optional[List[str]] = Field(None, description="Add notes to rental")

class BatteryRentalReturn(BaseModel):
    """Return batteries from a rental"""
    battery_ids: Optional[List[str]] = Field(None, description="Battery IDs to return (if None, return all)")
    return_date: Optional[datetime] = Field(None, description="Return date (defaults to now)")
    actual_return_date: Optional[datetime] = Field(None, description="Actual return date (alias for return_date)")
    condition_notes: Optional[str] = Field(None, description="Notes about battery condition")
    return_notes: Optional[str] = Field(None, description="Return notes (alias for condition_notes)")
    collect_payment: Optional[bool] = Field(False, description="Whether to collect payment")
    payment_amount: Optional[float] = Field(None, description="Cash payment collected on return")
    payment_type: Optional[str] = Field('cash', description="Payment type: cash, mobile_money, bank_transfer, card")
    payment_notes: Optional[str] = Field(None, description="Payment notes")
    credit_applied: Optional[float] = Field(None, description="Account credit applied to payment")
    kwh_usage_end: Optional[float] = Field(None, description="Ending kWh reading")

    @field_validator('battery_ids', mode='before')
    @classmethod
    def convert_battery_ids_to_str(cls, v):
        """Convert all battery_ids to strings if they are integers"""
        if v is None:
            return v
        if isinstance(v, list):
            return [str(item) if isinstance(item, int) else item for item in v]
        return v

class BatteryRentalAddBattery(BaseModel):
    """Add batteries to existing rental"""
    battery_ids: List[str] = Field(..., description="Battery IDs to add")
    additional_cost: Optional[float] = Field(None, description="Additional cost for new batteries")

    @field_validator('battery_ids', mode='before')
    @classmethod
    def convert_battery_ids_to_str(cls, v):
        """Convert all battery_ids to strings if they are integers"""
        if isinstance(v, list):
            return [str(item) if isinstance(item, int) else item for item in v]
        return v

class BatteryRentalPayment(BaseModel):
    """Record payment for a battery rental"""
    payment_amount: float = Field(..., description="Payment amount", ge=0)
    payment_type: str = Field('cash', description="Payment type: cash, mobile_money, bank_transfer, card")
    payment_notes: Optional[str] = Field(None, description="Payment notes")
    credit_applied: Optional[float] = Field(None, description="Account credit applied to payment", ge=0)

class BatteryRentalRecharge(BaseModel):
    """Record a battery recharge"""
    battery_id: str = Field(..., description="Battery ID that was recharged")
    recharge_date: Optional[datetime] = Field(None, description="Recharge date (defaults to now)")
    recharge_cost: Optional[float] = Field(None, description="Cost of recharge")
    notes: Optional[str] = Field(None, description="Recharge notes")

class PUERentalCreateNew(BaseModel):
    """Create a new PUE rental with pay-to-own support"""
    user_id: int = Field(..., description="User ID renting the PUE")
    pue_id: str = Field(..., description="PUE item ID")
    cost_structure_id: int = Field(..., description="Cost structure to apply")
    rental_start_date: Optional[datetime] = Field(None, description="Rental start date (defaults to now)")
    is_pay_to_own: bool = Field(False, description="Is this a pay-to-own rental")
    pay_to_own_price: Optional[float] = Field(None, description="Total price for pay-to-own")
    initial_payment: Optional[float] = Field(None, description="Initial payment amount")
    deposit_amount: Optional[float] = Field(None, description="Deposit amount collected")
    payment_type: Optional[str] = Field(None, description="Payment type: cash, mobile_money, etc.")
    notes: Optional[List[str]] = Field(None, description="Notes about the rental")
    has_recurring_payment: bool = Field(False, description="Enable recurring payments")
    recurring_payment_frequency: Optional[str] = Field(None, description="Payment frequency: monthly, weekly, daily")

class PUERentalPayment(BaseModel):
    """Record payment for PUE rental"""
    payment_amount: float = Field(..., description="Payment amount", ge=0)
    payment_date: Optional[datetime] = Field(None, description="Payment date (defaults to now)")
    payment_type: str = Field("Cash", description="Payment type: Cash, Mobile Money, etc.")
    notes: Optional[str] = Field(None, description="Payment notes")
    credit_applied: Optional[float] = Field(None, description="Account credit applied to payment", ge=0)

class PayToOwnPaymentRequest(BaseModel):
    """Process a pay-to-own payment"""
    payment_amount: float = Field(..., description="Cash/card payment amount", ge=0)
    payment_type: str = Field("cash", description="Payment type: cash, mobile_money, etc.")
    notes: Optional[str] = Field(None, description="Payment notes")
    credit_applied: float = Field(0, description="Amount of credit applied from user account", ge=0)

class PUERentalConvertToRental(BaseModel):
    """Convert pay-to-own back to regular rental"""
    new_cost_structure_id: int = Field(..., description="New cost structure for rental")
    refund_amount: Optional[float] = Field(None, description="Amount to refund")
    notes: Optional[str] = Field(None, description="Conversion notes")

class PUEInspectionCreate(BaseModel):
    """Create PUE inspection record"""
    inspection_date: Optional[datetime] = Field(None, description="Inspection date (defaults to now)")
    condition: str = Field(..., description="Condition: Excellent, Good, Fair, Poor, Damaged")
    notes: Optional[str] = Field(None, description="Issues found during inspection")
    maintenance_notes: Optional[str] = Field(None, description="Actions taken during inspection")

class DataQuery(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    battery_ids: Optional[List[int]] = None
    start_timestamp: Optional[datetime] = None
    end_timestamp: Optional[datetime] = None
    fields: Optional[List[str]] = None
    format: ExportFormat = ExportFormat.json

# Job Cards / Maintenance Board Schemas

class JobCardCreate(BaseModel):
    """Create a new job card"""
    title: str = Field(..., description="Job card title", max_length=255)
    description: Optional[str] = Field(None, description="Detailed description")
    status: str = Field("todo", description="Status: todo, in_progress, blocked, done, cancelled")
    priority: str = Field("medium", description="Priority: low, medium, high, urgent")
    assigned_to: Optional[int] = Field(None, description="User ID to assign this card to")
    linked_entity_type: Optional[str] = Field(None, description="Entity type: battery, pue, user, rental")
    linked_battery_id: Optional[str] = Field(None, description="Linked battery ID")
    linked_pue_id: Optional[str] = Field(None, description="Linked PUE ID")
    linked_user_id: Optional[int] = Field(None, description="Linked user ID")
    linked_rental_id: Optional[int] = Field(None, description="Linked rental ID")
    due_date: Optional[str] = Field(None, description="Due date for completion (YYYY-MM-DD or full datetime)")

class JobCardUpdate(BaseModel):
    """Update job card details"""
    title: Optional[str] = Field(None, description="Job card title", max_length=255)
    description: Optional[str] = Field(None, description="Detailed description")
    status: Optional[str] = Field(None, description="Status: todo, in_progress, blocked, done, cancelled")
    priority: Optional[str] = Field(None, description="Priority: low, medium, high, urgent")
    due_date: Optional[str] = Field(None, description="Due date for completion (YYYY-MM-DD or full datetime)")
    assigned_to: Optional[int] = Field(None, description="User ID to assign this card to")
    sort_order: Optional[int] = Field(None, description="Sort order within column")

class JobCardActivityCreate(BaseModel):
    """Add activity/comment to job card"""
    activity_type: str = Field("comment", description="Activity type: created, status_changed, comment, assigned, updated, due_date_changed")
    description: str = Field(..., description="Activity description")
    metadata: Optional[str] = Field(None, description="Additional metadata as JSON")

class JobCardReorder(BaseModel):
    """Batch reorder job cards for drag-and-drop"""
    card_id: int = Field(..., description="Card ID to reorder")
    status: str = Field(..., description="New status column")
    sort_order: int = Field(..., description="New sort order within column")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def record_rental_payment(
    rental: "BatteryRental",
    user_account: "UserAccount",
    payment_amount: Optional[float],
    credit_applied: Optional[float],
    payment_type: str,
    payment_notes: Optional[str],
    db: Session
) -> tuple[float, list[dict]]:
    """
    Helper function to record payment for a rental.
    Updates user account and returns payment info.

    Returns:
        tuple: (total_payment_collected, payment_transactions_list)
    """
    total_payment_collected = 0
    payment_transactions = []

    # Apply account credit if specified
    if credit_applied and credit_applied > 0:
        # Create debit transaction (reduces account balance)
        credit_description = f"Account credit applied to Battery Rental #{rental.rental_id}"
        if payment_notes:
            credit_description += f" - {payment_notes}"

        user_account.balance -= credit_applied
        credit_transaction = AccountTransaction(
            account_id=user_account.account_id,
            rental_id=None,
            transaction_type='debit',
            amount=credit_applied,
            balance_after=user_account.balance,
            description=credit_description
        )
        db.add(credit_transaction)
        total_payment_collected += credit_applied
        payment_transactions.append({
            "type": "credit",
            "amount": credit_applied,
            "description": "Account credit applied"
        })

    # Record cash payment if specified
    if payment_amount and payment_amount > 0:
        # Create credit transaction (increases account balance when customer pays)
        payment_description = f"Payment for Battery Rental #{rental.rental_id} ({payment_type})"
        if payment_notes:
            payment_description += f" - {payment_notes}"

        user_account.balance += payment_amount
        payment_transaction = AccountTransaction(
            account_id=user_account.account_id,
            rental_id=None,
            transaction_type='credit',
            amount=payment_amount,
            balance_after=user_account.balance,
            description=payment_description,
            payment_type=payment_type
        )
        db.add(payment_transaction)
        total_payment_collected += payment_amount
        payment_transactions.append({
            "type": "cash",
            "amount": payment_amount,
            "payment_type": payment_type,
            "description": f"Cash payment ({payment_type})"
        })

    return total_payment_collected, payment_transactions

def update_rental_payment_status(rental: "BatteryRental", payment_collected: float = 0):
    """
    Helper function to update rental payment fields and status.
    Call this after recording payment or calculating final cost.
    """
    # Update amount paid if payment was collected
    if payment_collected > 0:
        rental.amount_paid = (rental.amount_paid or 0) + payment_collected

    # Calculate amount owed if final cost is available
    if rental.final_cost_total is not None:
        total_paid = (rental.amount_paid or 0) + (rental.deposit_amount or 0)
        rental.amount_owed = max(0, rental.final_cost_total - total_paid)

        # Update payment status
        if rental.amount_owed == 0:
            rental.payment_status = 'paid'
        elif rental.amount_paid > 0:
            rental.payment_status = 'partial'
        else:
            rental.payment_status = 'unpaid'

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
- **JWT-based authentication** with role-based permissions
- **Battery-specific authentication** for IoT devices with separate token system
- **Token refresh capabilities** for both user and battery tokens
- **Secure token management** with configurable expiration times

### Battery Token System:
- **Separate Authentication**: Battery devices use dedicated endpoints (`/auth/battery-login`, `/auth/battery-refresh`)
- **Limited Scope**: Battery tokens are restricted to data submission operations (`webhook_write`)
- **Secure Design**: Uses separate secret keys and token validation for enhanced security
- **Auto-Refresh**: Tokens can be refreshed before expiration to maintain continuous connectivity
- **IoT Optimized**: Designed specifically for battery management IoT devices
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
            "description": "User and battery authentication endpoints. Includes battery-specific login and token refresh for IoT devices.",
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

# CORS Configuration - Allow frontend and panel to access API
# In production, set CORS_ORIGINS env var to your domains (comma-separated)
cors_origins_str = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:8000,http://localhost:5100,http://localhost:9000,http://localhost:9001"
)
cors_origins = [origin.strip() for origin in cors_origins_str.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
    max_age=600,  # Cache preflight requests for 10 minutes
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
    'err': ('err', str),
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

def calculate_time_period(time_period: str) -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    
    if time_period == "last_24_hours":
        start_time = now - timedelta(hours=24)
        end_time = now
    elif time_period == "last_week":
        start_time = now - timedelta(weeks=1)
        end_time = now
    elif time_period == "last_2_weeks":
        start_time = now - timedelta(weeks=2)
        end_time = now
    elif time_period == "last_month":
        start_time = now - timedelta(days=30)
        end_time = now
    elif time_period == "last_2_months":
        start_time = now - timedelta(days=60)
        end_time = now
    elif time_period == "last_3_months":
        start_time = now - timedelta(days=90)
        end_time = now
    elif time_period == "last_6_months":
        start_time = now - timedelta(days=180)
        end_time = now
    elif time_period == "last_year":
        start_time = now - timedelta(days=365)
        end_time = now
    elif time_period == "this_week":
        days_since_monday = now.weekday()
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days_since_monday)
        end_time = now
    elif time_period == "this_month":
        start_time = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_time = now
    elif time_period == "this_year":
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

def create_battery_token(battery_id: str, expires_hours: Optional[int] = None):
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
        log_webhook_event(
            event_type="token_verification_attempt",
            status="info",
            additional_info={"token_prefix": credentials.credentials[:20] + "..."}
        )
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        log_webhook_event(
            event_type="token_verification_success",
            user_info=payload,
            status="success",
            additional_info={"user_id": payload.get("user_id"), "role": payload.get("role")}
        )
        return payload
    except InvalidTokenError as e:
        log_webhook_event(
            event_type="token_verification_failed",
            status="error",
            error_message=f"Invalid token: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def verify_battery_or_superadmin_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        log_webhook_event(
            event_type="battery_token_verification_attempt",
            status="info",
            additional_info={"token_prefix": credentials.credentials[:20] + "..."}
        )

        # Try battery token first
        try:
            payload = jwt.decode(credentials.credentials, BATTERY_SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") == "battery":
                log_webhook_event(
                    event_type="battery_token_verified",
                    user_info=payload,
                    battery_id=payload.get("battery_id"),
                    status="success",
                    additional_info={"token_type": "battery", "battery_id": payload.get("battery_id")}
                )
                return payload
        except Exception as e:
            log_webhook_event(
                event_type="battery_token_decode_failed",
                status="warning",
                error_message=f"Not a battery token: {str(e)}"
            )

        # Try superadmin token
        try:
            payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("role") == UserRole.SUPERADMIN:
                log_webhook_event(
                    event_type="superadmin_token_verified",
                    user_info=payload,
                    status="success",
                    additional_info={"token_type": "superadmin", "user_id": payload.get("user_id")}
                )
                return payload
        except Exception as e:
            log_webhook_event(
                event_type="superadmin_token_decode_failed",
                status="warning",
                error_message=f"Not a superadmin token: {str(e)}"
            )

        log_webhook_event(
            event_type="token_verification_rejected",
            status="error",
            error_message="Token is neither battery nor superadmin"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Only batteries or superadmins can access this endpoint"
        )
    except HTTPException:
        raise
    except Exception as e:
        log_webhook_event(
            event_type="token_verification_exception",
            status="error",
            error_message=f"Unexpected error: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def validate_password_policy(password: str) -> None:
    """
    Enforce password policy requirements.
    Raises HTTPException if password doesn't meet requirements.

    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )

    if not any(c.isupper() for c in password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one uppercase letter"
        )

    if not any(c.islower() for c in password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one lowercase letter"
        )

    if not any(c.isdigit() for c in password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one digit"
        )

    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)"
        )

def hash_password(password: str) -> str:
    # Validate password before hashing
    validate_password_policy(password)
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
# BATTERY ERROR PROCESSING AND SMART NOTIFICATIONS
# ============================================================================

# Error code mapping for battery diagnostics
BATTERY_ERROR_CODES = {
    'R': {'name': 'rtcError', 'description': 'Real-time clock error', 'severity': 'warning'},
    'C': {'name': 'powerSensorChargeError', 'description': 'Power sensor charge error', 'severity': 'error'},
    'U': {'name': 'powerSensorUsbError', 'description': 'Power sensor USB error', 'severity': 'warning'},
    'T': {'name': 'tempSensorError', 'description': 'Temperature sensor error', 'severity': 'warning'},
    'B': {'name': 'batteryMonitorError', 'description': 'Battery monitor error', 'severity': 'error'},
    'G': {'name': 'gpsError', 'description': 'GPS error', 'severity': 'warning'},
    'S': {'name': 'sdError', 'description': 'SD card error', 'severity': 'warning'},
    'L': {'name': 'lteError', 'description': 'LTE connection error', 'severity': 'error'},
    'D': {'name': 'displayError', 'description': 'Display error', 'severity': 'info'},
}

def decode_error_string(error_string: str) -> list[dict]:
    """
    Decode battery error string into list of errors

    Args:
        error_string: String containing error codes (e.g., "TG", "RCB")

    Returns:
        List of error dictionaries with code, name, description, and severity
        Unknown codes are still included with a generic description
    """
    errors = []
    for char in error_string.strip().upper():
        if char in BATTERY_ERROR_CODES:
            error_info = BATTERY_ERROR_CODES[char].copy()
            error_info['code'] = char
            errors.append(error_info)
        else:
            # Handle unknown error codes - still record them
            errors.append({
                'code': char,
                'name': f'unknownError_{char}',
                'description': f'Unknown error code: {char}',
                'severity': 'warning'
            })
    return errors

def process_battery_errors(db: Session, battery_id: str, error_string: str, hub_id: int):
    """
    Process battery error codes and create smart notifications

    Features:
    - Decodes error string into human-readable errors
    - Creates notifications for NEW errors only (no flooding)
    - Tracks which errors have active notifications
    - Only creates new notification if old one was dismissed and error persists

    Args:
        db: Database session
        battery_id: Battery ID
        error_string: Error codes string (e.g., "TG", "RCB")
        hub_id: Hub ID for the notification
    """
    from models import Notification, BEPPPBattery

    # Decode error string
    errors = decode_error_string(error_string)

    if not errors:
        return  # No errors, nothing to do

    # Get battery name for notification message
    battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == battery_id).first()
    battery_name = (battery.short_id if battery and battery.short_id else f"Battery #{battery_id}")

    # For each error, check if we already have an active notification
    for error in errors:
        error_code = error['code']
        error_name = error['name']
        error_desc = error['description']
        severity = error['severity']

        # Check for existing UNREAD notification with this exact error for this battery
        # This prevents flooding - we only have one notification per error type per battery
        notification_type = f"battery_error_{error_code}"

        existing_notification = db.query(Notification).filter(
            Notification.hub_id == hub_id,
            Notification.link_type == 'battery',
            Notification.link_id == str(battery_id),
            Notification.notification_type == notification_type,
            Notification.is_read == False  # Only unread notifications matter
        ).first()

        if existing_notification:
            # We already have an active notification for this error
            # Don't create a new one (prevents flooding)
            continue

        # No active notification exists - create a new one
        # This will show even if a previous notification was dismissed
        # (allowing users to be re-notified if they dismissed it but problem persists)

        notification = Notification(
            hub_id=hub_id,
            user_id=None,  # Hub-wide notification
            notification_type=notification_type,
            title=f"{battery_name}: {error_desc}",
            message=f"Error code '{error_code}' detected on {battery_name}. {error_desc}. Please check the battery error log for more details.",
            severity=severity,
            is_read=False,
            link_type='battery',
            link_id=str(battery_id)
        )

        db.add(notification)

    # Commit all new notifications
    try:
        db.commit()
    except Exception as e:
        print(f"Failed to create error notifications: {e}")
        db.rollback()

# ============================================================================
# WEBHOOK HANDLERS
# ============================================================================

async def handle_direct_format(battery_data: dict, db: Session, current_user: dict):
    battery_data.pop('access_token', None)
    
    battery_id = None
    if 'id' in battery_data:
        # Keep battery_id as string to match database schema (converted in ff7c9c33882f migration)
        battery_id = str(battery_data['id'])
        if not battery_id:
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
    special_fields = []  # Fields used for timestamp/metadata processing

    for json_key, json_value in battery_data.items():
        if json_key in ['id', 'd', 'gd', 'tm', 'gt']:
            special_fields.append(json_key)
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

        # Update battery's last_data_received timestamp
        battery.last_data_received = datetime.now(timezone.utc)
        db.commit()

        if DEBUG:
            log_webhook_event(
                event_type="database_save_success",
                user_info=current_user,
                battery_id=battery_id,
                data_id=live_data.id,
                status="success"
            )

        # Process error codes and create smart notifications if needed
        if live_data.err and live_data.err.strip():
            process_battery_errors(
                db=db,
                battery_id=battery_id,
                error_string=live_data.err,
                hub_id=battery.hub_id
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
            "status": "success",
            "fields_stored": parsed_fields,
            "timestamp_fields": special_fields,
            "fields_skipped": skipped_fields,
            "unknown_fields": unmapped_fields,
            "counts": {
                "stored": len(parsed_fields),
                "timestamp": len(special_fields),
                "skipped": len(skipped_fields),
                "unknown": len(unmapped_fields),
                "total_in_payload": len(battery_data)
            }
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

    Endpoint for battery IoT devices to submit live data including power metrics, GPS location, environmental data, and system status.
    
    ### Authentication:
    1. **Login**: Use `/auth/battery-login` with `battery_id` and `battery_secret`
    2. **Submit Data**: Use returned token in `Authorization: Bearer {token}` header
    3. **Refresh**: Use `/auth/battery-refresh` to refresh token before expiration
    
    ### Permissions:
    - **BATTERY**: Battery devices can submit data
    - **SUPERADMIN**: For testing and administration
    
    ### Features:
    - Accepts multiple data formats (webhook format and direct format)
    - Automatic field mapping and validation
    - Real-time data processing
    - Comprehensive error handling and logging
    
    ### Data Fields Mapping:
    
    **Power & Battery Status:**
    - `soc`: State of charge (0-100%)
    - `v`: Voltage (V)
    - `i`: Current (A)
    - `p`: Power (W)
    - `t`: Temperature (°C)
    - `tr`: Time remaining (-1 = infinite)
    - `nc`: Number of charge cycles
    - `cc`: Charge consumed since last full charge (Ah)
    - `tcc`: Total charge consumed over lifetime (Ah)
    
    **Charging System:**
    - `ci`: Charger current (A)
    - `cv`: Charger voltage (V)
    - `cp`: Charger power (W)
    - `ec`: Charging enabled (1/0)
    
    **USB Port:**
    - `ui`: USB current (A)
    - `uv`: USB voltage (V)
    - `up`: USB power (W)
    - `eu`: USB enabled (1/0)
    
    **GPS & Location:**
    - `lat`: GPS latitude (decimal degrees)
    - `lon`: GPS longitude (decimal degrees)
    - `alt`: Altitude (m)
    - `gs`: Number of GPS satellites
    - `gf`: GPS fix quality (0-9)
    - `gd`: GPS date (YYYY-MM-DD)
    - `gt`: GPS time (HH:MM:SS)
    
    **System Status:**
    - `ef`: Fan enabled (1/0)
    - `ei`: Inverter enabled (1/0)
    - `sa`: Stay awake state (1/0)
    - `ts`: Tilt sensor state (0-9)
    - `err`: Error codes (string) - See error codes below
    
    **Error Codes (err field):**
    - `R`: rtcError - Real-time clock error
    - `C`: powerSensorChargeError - Power sensor charge error
    - `U`: powerSensorUsbError - Power sensor USB error
    - `T`: tempSensorError - Temperature sensor error
    - `B`: batteryMonitorError - Battery monitor error
    - `G`: gpsError - GPS error
    - `S`: sdError - SD card error
    - `L`: lteError - LTE connection error
    - `D`: displayError - Display error
    
    **Timing & Identification:**
    - `id`: Battery ID (string or number)
    - `d`: RTC date (YYYY-MM-DD)
    - `tm`: RTC time (HH:MM:SS)
    
    ### Example Data:
    ```json
    {
        "id": "123",
        "soc": 85.5,
        "v": 12.4,
        "i": 2.1,
        "p": 25.6,
        "t": 21.5,
        "lat": 55.6227,
        "lon": -3.52763,
        "alt": 226.9,
        "gs": 11,
        "gf": 1,
        "ci": 0.5,
        "cv": 14.2,
        "cp": 7.1,
        "ec": 1,
        "ui": 0.0,
        "uv": 0.0,
        "up": 0.0,
        "eu": 0,
        "ef": 1,
        "ei": 0,
        "sa": 1,
        "ts": 0,
        "nc": 15,
        "cc": 2.5,
        "tcc": 150.0,
        "tr": -1.0,
        "gd": "2025-07-11",
        "gt": "14:30:15",
        "d": "2025-07-11",
        "tm": "14:30:20",
        "err": "TG"
    }
    ```
    
    ### Response Format:
    ```json
    {
        "status": "success",
        "data_id": 12345,
        "battery_id": 123,
        "timestamp": "2025-07-11T14:30:20Z",
        "fields_processed": 25
    }
    ```
    
    ### Error Handling:
    - **401**: Invalid or expired token
    - **403**: Insufficient permissions 
    - **400**: Invalid data format or missing required fields
    - **500**: Server processing error
    
    ### Best Practices:
    - Submit data regularly (every 1-5 minutes recommended)
    - Include GPS coordinates when available for location tracking
    - Monitor token expiration and refresh proactively
    - Handle network failures gracefully with retry logic
    - Validate data locally before submission
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
    request_headers = dict(request.headers)
    battery_data = None
    result = None
    error_msg = None
    response_status = None

    try:
        log_webhook_event(
            event_type="webhook_request_received",
            user_info=current_user,
            status="info",
            additional_info={
                "endpoint": "/live-data",
                "method": request.method,
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown")[:100]
            }
        )

        battery_data = await request.json()

        log_webhook_event(
            event_type="webhook_data_received",
            user_info=current_user,
            status="info",
            additional_info={
                "data_size_bytes": len(str(battery_data)),
                "has_id": 'id' in battery_data,
                "has_values": 'values' in battery_data,
                "has_device_id": 'device_id' in battery_data,
                "keys_count": len(battery_data.keys())
            }
        )

        if 'id' in battery_data:
            # Keep battery_id as string to match database schema (converted in ff7c9c33882f migration)
            battery_id = str(battery_data['id']) if battery_data['id'] else None

        log_webhook_event(
            event_type="webhook_authentication_validated",
            user_info=current_user,
            battery_id=battery_id,
            status="success",
            additional_info={
                "token_battery_id": current_user.get('battery_id'),
                "payload_battery_id": battery_id,
                "user_type": current_user.get('type') or current_user.get('role'),
                "match": str(current_user.get('battery_id')) == str(battery_id) if battery_id else "N/A"
            }
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

        # Log to database for production debugging
        processing_time_ms = int((datetime.now() - request_start_time).total_seconds() * 1000)
        response_status = 200
        log_webhook_to_db(
            db=db,
            battery_id=battery_id,
            endpoint="/webhook/live-data",
            method="POST",
            request_headers=request_headers,
            request_body=battery_data,
            response_status=response_status,
            response_body=result,
            error_message=None,
            processing_time_ms=processing_time_ms
        )

        return result
        
    except HTTPException as he:
        error_msg = f"HTTP {he.status_code}: {he.detail}"
        log_webhook_event(
            event_type="client_error",
            user_info=current_user,
            battery_id=battery_id,
            status="error",
            error_message=error_msg
        )

        # Log to database for production debugging
        processing_time_ms = int((datetime.now() - request_start_time).total_seconds() * 1000)
        log_webhook_to_db(
            db=db,
            battery_id=battery_id,
            endpoint="/webhook/live-data",
            method="POST",
            request_headers=request_headers,
            request_body=battery_data,
            response_status=he.status_code,
            response_body={"detail": he.detail},
            error_message=error_msg,
            processing_time_ms=processing_time_ms
        )

        db.rollback()
        raise he

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"

        log_webhook_event(
            event_type="server_error",
            user_info=current_user,
            battery_id=battery_id,
            status="error",
            error_message=error_msg
        )

        # Log to database for production debugging
        processing_time_ms = int((datetime.now() - request_start_time).total_seconds() * 1000)
        log_webhook_to_db(
            db=db,
            battery_id=battery_id,
            endpoint="/webhook/live-data",
            method="POST",
            request_headers=request_headers,
            request_body=battery_data,
            response_status=500,
            response_body={"detail": f"Error processing live data: {str(e)}"},
            error_message=error_msg,
            processing_time_ms=processing_time_ms
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
        log_webhook_event(
            event_type="user_login_attempt",
            status="info",
            additional_info={"endpoint": "/auth/token", "client_ip": request.client.host if request.client else "unknown"},
            db=db  # NEW: Pass db for database logging
        )

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

        log_webhook_event(
            event_type="user_login_credentials_received",
            status="info",
            additional_info={"username": username},
            db=db  # NEW: Pass db for database logging
        )

        if not username or not password:
            log_webhook_event(
                event_type="user_login_failed_missing_credentials",
                status="error",
                error_message="Username or password missing",
                db=db  # NEW: Pass db for database logging
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username and password are required"
            )

        user = db.query(User).filter(User.username == username).first()

        if not user:
            log_webhook_event(
                event_type="user_login_failed_user_not_found",
                status="error",
                additional_info={"username": username},
                error_message=f"User not found: {username}",
                db=db  # NEW: Pass db for database logging
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        if not verify_password(password, user.password_hash):
            log_webhook_event(
                event_type="user_login_failed_invalid_password",
                status="error",
                additional_info={"username": username, "user_id": user.user_id},
                error_message=f"Invalid password for user: {username}",
                db=db  # NEW: Pass db for database logging
            )
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

        log_webhook_event(
            event_type="user_login_success",
            user_info=token_data,
            status="success",
            additional_info={
                "username": username,
                "user_id": user.user_id,
                "role": user.user_access_level,
                "hub_id": user.hub_id,
                "token_prefix": token[:20] + "..."
            },
            db=db  # NEW: Pass db for database logging
        )

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
    Battery devices use this endpoint to authenticate and receive JWT tokens for data submission.
    
    ### Permissions:
    - **Public**: No authentication required for this endpoint
    
    ### Prerequisites:
    - Battery must be registered in the system with a valid `battery_id`
    - Battery must have a configured `battery_secret` for authentication
    - Battery must be associated with a valid solar hub
    
    ### Returns:
    - JWT access token for battery device (expires in 24 hours by default)
    - Token type and expiration information
    - Battery ID and scope details
    
    ### Token Features:
    - **Scope**: `webhook_write` (limited to data submission)
    - **Expiration**: Configurable (default 24 hours)
    - **Security**: Uses separate secret key from user tokens
    - **Refresh**: Can be refreshed using `/auth/battery-refresh` endpoint
    
    ### Usage:
    ```
    POST /auth/battery-login
    {
        "battery_id": 123,
        "battery_secret": "device_secret_key"
    }
    ```
    
    ### Response Example:
    ```json
    {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "token_type": "bearer",
        "battery_id": 123,
        "expires_in": 86400,
        "expires_in_hours": 24,
        "scope": "webhook_write"
    }
    ```
    
    ### Using the Token:
    After authentication, include the token in the Authorization header:
    ```
    Authorization: Bearer {access_token}
    ```
    
    ### Error Handling:
    - 401: Invalid battery credentials or battery not found
    - 401: Battery not configured for authentication
    - 422: Invalid request format
    - 500: Internal server error
    
    ### Best Practices:
    - Store tokens securely on the device
    - Implement token refresh before expiration
    - Use HTTPS for all authentication requests
    - Handle authentication failures gracefully
    """,
    response_description="JWT token for battery device with expiration and scope information")
async def battery_login(
    battery_login: BatteryLogin,
    db: Session = Depends(get_db)
):
    """Battery self-authentication"""
    try:
        # Log battery login attempt (to file AND database)
        log_webhook_event(
            event_type="battery_login_attempt",
            battery_id=battery_login.battery_id,
            status="info",
            additional_info={"battery_id": str(battery_login.battery_id)},
            db=db  # NEW: Pass db to save to database
        )

        battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == battery_login.battery_id).first()
        if not battery:
            log_webhook_event(
                event_type="battery_login_failed",
                battery_id=battery_login.battery_id,
                status="error",
                error_message="Battery not found",
                db=db  # NEW: Pass db to save to database
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid battery credentials"
            )

        if not battery.battery_secret:
            log_webhook_event(
                event_type="battery_login_failed",
                battery_id=battery_login.battery_id,
                status="error",
                error_message="Battery not configured for authentication",
                db=db  # NEW: Pass db to save to database
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Battery not configured for authentication"
            )

        if battery.battery_secret != battery_login.battery_secret:
            log_webhook_event(
                event_type="battery_login_failed",
                battery_id=battery_login.battery_id,
                status="error",
                error_message="Invalid battery secret",
                db=db  # NEW: Pass db to save to database
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid battery credentials"
            )

        token = create_battery_token(battery_login.battery_id)

        # Log successful battery login (to file AND database)
        log_webhook_event(
            event_type="battery_login_success",
            battery_id=battery_login.battery_id,
            status="success",
            additional_info={
                "battery_id": str(battery_login.battery_id),
                "token_expires_in_hours": BATTERY_TOKEN_EXPIRE_HOURS,
                "scope": "webhook_write"
            },
            db=db  # NEW: Pass db to save to database
        )

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
        log_webhook_event(
            event_type="battery_login_error",
            battery_id=battery_login.battery_id,
            status="error",
            error_message=str(e),
            db=db  # NEW: Pass db to save to database
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Battery authentication error: {str(e)}"
        )

@app.post("/auth/battery-refresh",
    tags=["Authentication"],
    summary="Refresh Battery Token",
    description="""
    ## Battery Token Refresh
    
    Refresh an existing battery authentication token before it expires to maintain continuous connectivity for IoT devices.
    
    ### Permissions:
    - **Battery Device**: Must have valid battery token
    - **Superadmin**: Can refresh any battery token
    
    ### Authentication:
    - Requires valid battery token in Authorization header
    - Token must be of type 'battery' with `webhook_write` scope
    - Token must not be expired (within valid time window)
    
    ### Token Information:
    - **Default Expiration**: 24 hours
    - **Refresh Window**: Can be refreshed anytime before expiration
    - **New Token Duration**: Full duration from refresh time (24 hours)
    - **Scope**: `webhook_write` (data submission only)
    
    ### Usage Example:
    ```bash
    # Refresh token
    curl -X POST "https://your-api.com/auth/battery-refresh" \
         -H "Authorization: Bearer {current_battery_token}" \
         -H "Content-Type: application/json"
    ```
    
    ### Response Format:
    ```json
    {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "token_type": "bearer",
        "battery_id": 123,
        "expires_in": 86400,
        "expires_in_hours": 24,
        "scope": "webhook_write",
        "refresh_time": "2025-07-11T14:30:20Z"
    }
    ```
    
    ### Implementation Best Practices:
    
    **Proactive Refresh:**
    - Refresh tokens 5-10 minutes before expiration
    - Monitor token expiration timestamps
    - Implement automatic refresh logic in your IoT device
    
    **Error Handling:**
    - Implement exponential backoff for failed refresh attempts
    - Fall back to full authentication if refresh fails
    - Log refresh attempts for monitoring
    
    **Security:**
    - Replace old token immediately after successful refresh
    - Store tokens securely (encrypted if possible)
    - Clear expired tokens from memory
    
    ### Sample Implementation:
    ```python
    import requests
    from datetime import datetime, timedelta
    
    def refresh_battery_token(current_token):
        headers = {
            'Authorization': f'Bearer {current_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            'https://your-api.com/auth/battery-refresh',
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()['access_token']
        else:
            raise Exception(f"Token refresh failed: {response.text}")
    ```
    
    ### Error Handling:
    - **401**: Invalid or expired token - perform full authentication
    - **403**: Token is not a battery token - check token type
    - **404**: Battery not found in database - verify battery registration
    - **422**: Invalid request format - check request headers
    - **500**: Server error - retry with exponential backoff
    """,
    response_description="New JWT token for battery device")
async def battery_refresh_token(
    db: Session = Depends(get_db),
    current_battery: dict = Depends(verify_battery_or_superadmin_token)
):
    """Refresh battery token with extended expiration"""
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
    log_webhook_event(
        event_type="battery_token_creation_attempt",
        user_info=current_user,
        battery_id=battery_auth.battery_id,
        status="info",
        additional_info={"requested_by": current_user.get("sub"), "battery_id": battery_auth.battery_id}
    )

    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        log_webhook_event(
            event_type="battery_token_creation_rejected",
            user_info=current_user,
            battery_id=battery_auth.battery_id,
            status="error",
            error_message=f"User role {current_user.get('role')} not authorized"
        )
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == battery_auth.battery_id).first()
        if not battery:
            log_webhook_event(
                event_type="battery_token_creation_failed_not_found",
                user_info=current_user,
                battery_id=battery_auth.battery_id,
                status="error",
                error_message=f"Battery {battery_auth.battery_id} not found"
            )
            raise HTTPException(status_code=404, detail="Battery not found")

        if not battery.battery_secret or battery.battery_secret != battery_auth.battery_secret:
            log_webhook_event(
                event_type="battery_token_creation_failed_invalid_secret",
                user_info=current_user,
                battery_id=battery_auth.battery_id,
                status="error",
                error_message=f"Invalid secret for battery {battery_auth.battery_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid battery secret"
            )

        token = create_battery_token(battery_auth.battery_id)

        log_webhook_event(
            event_type="battery_token_created",
            user_info=current_user,
            battery_id=battery_auth.battery_id,
            status="success",
            additional_info={
                "battery_id": battery_auth.battery_id,
                "created_by": current_user.get("sub"),
                "token_prefix": token[:20] + "...",
                "expires_in_hours": BATTERY_TOKEN_EXPIRE_HOURS
            }
        )

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
        log_webhook_event(
            event_type="battery_token_creation_exception",
            user_info=current_user,
            battery_id=battery_auth.battery_id,
            status="error",
            error_message=f"Unexpected error: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Battery authentication error: {str(e)}"
        )

@app.post("/admin/battery-secret/{battery_id}")
async def set_battery_secret(
    battery_id: str,
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
    summary="Grant Hub Access to User",
    description="""
    ## Grant Hub Access to User

    Grant a user access to a specific hub. This changes the user's primary hub_id.

    ### Permissions:
    - **SUPERADMIN**: Can change hub access for any user

    ### Parameters:
    - **user_id**: ID of the user
    - **hub_id**: ID of the hub to grant access to

    ### Returns:
    - Success confirmation

    ### Note:
    For DATA_ADMIN users, this grants additional hub access without changing their primary hub.
    For other users, this changes their primary hub assignment.
    """,
    response_description="Access grant confirmation")
async def grant_hub_access(
    user_id: int,
    hub_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Grant hub access to a user (superadmin only)"""
    if current_user.get('role') != UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Superadmin access required")

    # Check if user exists
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if hub exists
    hub = db.query(SolarHub).filter(SolarHub.hub_id == hub_id).first()
    if not hub:
        raise HTTPException(status_code=404, detail="Hub not found")

    # For DATA_ADMIN users, add to accessible_hubs for multi-hub access
    if user.user_access_level == UserRole.DATA_ADMIN:
        # Check if access already exists
        if hub in user.accessible_hubs:
            raise HTTPException(status_code=400, detail="User already has access to this hub")

        # Grant additional hub access
        user.accessible_hubs.append(hub)
        db.commit()
        return {"message": f"Additional hub access granted to DATA_ADMIN user {user_id} for hub {hub_id}"}
    else:
        # For other users, change their primary hub assignment
        user.hub_id = hub_id
        db.commit()
        return {"message": f"User {user_id} hub changed to {hub_id}"}

@app.delete("/admin/user-hub-access/{user_id}/{hub_id}",
    tags=["Users"],
    summary="Revoke Hub Access from User",
    description="""
    ## Revoke Hub Access from User

    Revoke a DATA_ADMIN user's access to a specific hub.
    This only applies to DATA_ADMIN users with multi-hub access.

    ### Permissions:
    - **SUPERADMIN**: Can revoke hub access from any DATA_ADMIN user

    ### Parameters:
    - **user_id**: ID of the DATA_ADMIN user
    - **hub_id**: ID of the hub to revoke access from

    ### Returns:
    - Success confirmation

    ### Note:
    This endpoint only works for DATA_ADMIN users who have multiple hub access.
    For other users, use the grant endpoint to change their primary hub.
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

    # Check if user exists
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Only DATA_ADMIN users can have multi-hub access revoked
    if user.user_access_level != UserRole.DATA_ADMIN:
        raise HTTPException(status_code=400, detail="Only DATA_ADMIN users have multi-hub access that can be revoked")

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

    # Role-based restrictions
    current_role = current_user.get('role')

    # Hub admins can only create customers in their own hub
    if current_role == 'hub_admin':
        if user.hub_id != current_user.get('hub_id'):
            raise HTTPException(status_code=403, detail="Can only create users in your own hub")
        if user.user_access_level != 'user':
            raise HTTPException(status_code=403, detail="Hub admins can only create customers")

    # Regular users have limited permissions
    elif current_role == UserRole.USER:
        if user.hub_id != current_user.get('hub_id'):
            raise HTTPException(status_code=403, detail="Can only create users in your own hub")
        if user.user_access_level in [UserRole.ADMIN, UserRole.SUPERADMIN]:
            raise HTTPException(status_code=403, detail="Cannot create admin or superadmin users")

    # Admins cannot create superadmins or data_admins
    elif current_role == UserRole.ADMIN:
        if user.user_access_level in [UserRole.SUPERADMIN, UserRole.DATA_ADMIN]:
            raise HTTPException(status_code=403, detail="Admins cannot create superadmins or data admins")

    # Only superadmins and admins (with restrictions above) can create users
    elif current_role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        user_data = user.dict(exclude_none=True)

        # Remove user_id if present (database will auto-generate it)
        user_data.pop("user_id", None)

        # Handle name fields - compute full name from first_names + last_name OR use legacy 'name' field
        full_name = None
        if user_data.get("first_names") or user_data.get("last_name"):
            # New approach: use first_names and last_name
            first = user_data.get("first_names", "").strip()
            last = user_data.get("last_name", "").strip()
            full_name = f"{first} {last}".strip()
        elif user_data.get("name"):
            # Legacy approach: use 'name' field
            full_name = user_data["name"]
            # Try to split into first_names and last_name if not already provided
            if " " in full_name and not user_data.get("first_names"):
                parts = full_name.rsplit(" ", 1)  # Split on last space
                user_data["first_names"] = parts[0] if len(parts) > 0 else ""
                user_data["last_name"] = parts[1] if len(parts) > 1 else ""

        # Set the legacy Name field for backward compatibility
        if full_name:
            user_data["Name"] = full_name

        # Remove the 'name' field from user_data as it's not in the database
        user_data.pop("name", None)

        # Handle address fields - sync physical_address with address for backward compatibility
        if user_data.get("physical_address"):
            user_data["address"] = user_data["physical_address"]
        elif user_data.get("address"):
            user_data["physical_address"] = user_data["address"]

        # Auto-generate username from name if not provided
        generated_username = None
        if not user_data.get("username"):
            # Create username from name + number
            base_username = full_name.lower().replace(" ", "") if full_name else "user"
            # Check for existing usernames and find next available number
            counter = 1
            test_username = base_username
            while db.query(User).filter(User.username == test_username).first():
                test_username = f"{base_username}{counter}"
                counter += 1
            user_data["username"] = test_username
            generated_username = test_username

        # Auto-generate password if not provided
        generated_password = None
        if not user_data.get("password"):
            import secrets
            import string
            # Generate a random 12-character password
            alphabet = string.ascii_letters + string.digits
            generated_password = ''.join(secrets.choice(alphabet) for _ in range(12))
            user_data["password"] = generated_password

        user_data["password_hash"] = hash_password(user_data.pop("password"))

        db_user = User(**user_data)
        db.add(db_user)
        db.flush()  # Flush to get the ID before committing

        # Generate short_id for QR codes
        db_user.short_id = f"BH-{str(db_user.user_id).zfill(4)}"

        db.commit()
        db.refresh(db_user)

        # Return user with generated credentials if they were auto-generated
        response_data = {
            "user": db_user,
            "generated_credentials": {}
        }
        if generated_username:
            response_data["generated_credentials"]["username"] = generated_username
        if generated_password:
            response_data["generated_credentials"]["password"] = generated_password

        return response_data
    except Exception as e:
        db.rollback()
        import traceback
        error_msg = str(e) if str(e) else f"{type(e).__name__}: {repr(e)}"
        print(f"User creation error: {error_msg}")
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=error_msg or "Failed to create user")

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

        # Handle password update
        if "password" in update_data:
            update_data["password_hash"] = hash_password(update_data.pop("password"))

        # Handle name fields - compute full name from first_names + last_name OR use legacy 'name' field
        full_name = None
        if "first_names" in update_data or "last_name" in update_data:
            # New approach: use first_names and last_name
            first = update_data.get("first_names", user.first_names or "").strip()
            last = update_data.get("last_name", user.last_name or "").strip()
            full_name = f"{first} {last}".strip()
        elif "name" in update_data:
            # Legacy approach: use 'name' field
            full_name = update_data["name"]
            # Try to split into first_names and last_name if not already provided
            if " " in full_name:
                parts = full_name.rsplit(" ", 1)  # Split on last space
                if "first_names" not in update_data:
                    update_data["first_names"] = parts[0] if len(parts) > 0 else ""
                if "last_name" not in update_data:
                    update_data["last_name"] = parts[1] if len(parts) > 1 else ""

        # Set the legacy Name field for backward compatibility
        if full_name:
            update_data["Name"] = full_name

        # Remove the 'name' field from update_data as it's not in the database
        update_data.pop("name", None)

        # Handle address fields - sync physical_address with address for backward compatibility
        if "physical_address" in update_data:
            update_data["address"] = update_data["physical_address"]
        elif "address" in update_data:
            update_data["physical_address"] = update_data["address"]

        for key, value in update_data.items():
            setattr(user, key, value)

        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

class PasswordReset(BaseModel):
    password: Optional[str] = None  # If not provided, auto-generate

@app.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    password_data: Optional[PasswordReset] = Body(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Reset a user's password (superadmin only)"""
    if current_user.get('role') != UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Superadmin access required")

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        import secrets
        import string

        # Use provided password or generate random one
        if password_data and password_data.password:
            new_password = password_data.password
        else:
            # Generate a random 12-character password that meets policy requirements
            uppercase = string.ascii_uppercase
            lowercase = string.ascii_lowercase
            digits = string.digits
            special = '!@#$%^&*()_+-=[]{}|;:,.<>?'

            # Ensure at least one of each required type
            new_password = (
                secrets.choice(uppercase) +
                secrets.choice(lowercase) +
                secrets.choice(digits) +
                secrets.choice(special)
            )

            # Fill the rest randomly
            all_chars = uppercase + lowercase + digits + special
            for _ in range(8):  # 4 already added + 8 more = 12 total
                new_password += secrets.choice(all_chars)

            # Shuffle to randomize position of required characters
            new_password_list = list(new_password)
            secrets.SystemRandom().shuffle(new_password_list)
            new_password = ''.join(new_password_list)

        # Update password (hash_password validates password policy)
        user.password_hash = hash_password(new_password)
        db.commit()

        return {
            "message": "Password reset successfully",
            "new_password": new_password
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

@app.post("/users/me/change-password")
async def change_own_password(
    password_data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Change your own password (requires current password)"""
    user_id = current_user.get('user_id')
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        # Verify current password
        if not verify_password(password_data.current_password, user.password_hash):
            raise HTTPException(status_code=400, detail="Current password is incorrect")

        # Update to new password (hash_password validates password policy)
        user.password_hash = hash_password(password_data.new_password)
        db.commit()

        return {
            "message": "Password changed successfully"
        }
    except HTTPException:
        raise
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

@app.get("/users/by-short-id/{short_id}")
async def get_user_by_short_id(
    short_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get user by their short ID from QR code (e.g., BH-0001)"""
    if current_user.get('role') == UserRole.DATA_ADMIN:
        raise HTTPException(status_code=403, detail="Data admins cannot access user information")

    user = db.query(User).filter(User.short_id == short_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User with short ID '{short_id}' not found")

    # Check access rights
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        if user.hub_id != current_user.get('hub_id'):
            raise HTTPException(status_code=403, detail="Access denied")

    return user

# ============================================================================
# USER ID DOCUMENT PHOTO ENDPOINTS
# ============================================================================

UPLOAD_DIR = Path("/app/uploads/id_documents")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@app.post("/users/{user_id}/upload-id-photo")
async def upload_id_document_photo(
    user_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Upload ID document photo for a user"""
    # Check access rights
    if current_user.get('role') == UserRole.DATA_ADMIN:
        raise HTTPException(status_code=403, detail="Data admins cannot upload photos")

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check hub access
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        if user.hub_id != current_user.get('hub_id'):
            raise HTTPException(status_code=403, detail="Access denied")

    # Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
        )

    # Validate file size (max 5MB)
    file_content = await file.read()
    if len(file_content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be less than 5MB")

    # Generate unique filename
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
    unique_filename = f"{user_id}_{uuid.uuid4()}.{file_extension}"
    file_path = UPLOAD_DIR / unique_filename

    # Save file
    with open(file_path, "wb") as buffer:
        buffer.write(file_content)

    # Update user record with photo URL
    photo_url = f"/uploads/id_documents/{unique_filename}"
    db.execute(
        text("UPDATE \"user\" SET id_document_photo_url = :photo_url WHERE user_id = :user_id"),
        {"photo_url": photo_url, "user_id": user_id}
    )
    db.commit()

    return {"message": "Photo uploaded successfully", "photo_url": photo_url}

@app.get("/uploads/id_documents/{filename}")
async def get_id_document_photo(
    filename: str,
    current_user: dict = Depends(get_current_user)
):
    """Serve ID document photo"""
    file_path = UPLOAD_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Photo not found")

    return FileResponse(file_path)

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
        db.flush()  # Flush to get the ID before committing

        # Generate short_id for QR codes
        db_battery.short_id = f"BAT-{str(db_battery.battery_id).zfill(4)}"

        db.commit()
        db.refresh(db_battery)

        result = {**battery_data}
        result.pop('battery_secret', None)
        result['id'] = db_battery.battery_id
        result['short_id'] = db_battery.short_id

        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/batteries/")
async def list_batteries(
    hub_id: Optional[int] = Query(None, description="Filter by hub ID"),
    status: Optional[str] = Query(None, description="Filter by battery status (available, rented, maintenance, retired)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all batteries (with optional hub and status filters)"""
    query = db.query(BEPPPBattery)

    # Apply hub filter based on user role and parameters
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.DATA_ADMIN]:
        # Regular users can only see batteries from their hub
        query = query.filter(BEPPPBattery.hub_id == current_user.get('hub_id'))
    elif hub_id is not None:
        # Admin/superadmin can filter by specific hub
        query = query.filter(BEPPPBattery.hub_id == hub_id)

    # Apply status filter
    if status is not None:
        query = query.filter(BEPPPBattery.status == status)

    batteries = query.offset(skip).limit(limit).all()
    return batteries

@app.get("/batteries/{battery_id}")
async def get_battery(
    battery_id: str,
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
    battery_id: str,
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
    battery_id: str,
    force: bool = Query(False, description="Force delete with all related data (superadmin only)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a battery with data integrity protection
    
    - Normal deletion: Only allowed if no live data or rentals exist
    - Force deletion: Superadmin can delete everything (battery + all related data)
    """
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Force deletion requires superadmin
    if force and current_user.get('role') != UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Force deletion requires superadmin access")
    
    battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == battery_id).first()
    if not battery:
        raise HTTPException(status_code=404, detail="Battery not found")
    
    # Check for associated data
    live_data_count = db.query(LiveData).filter(LiveData.battery_id == battery_id).count()
    rental_count = db.query(Rental).filter(Rental.battery_id == battery_id).count()
    
    # If there's associated data and not forcing, reject the deletion
    if (live_data_count > 0 or rental_count > 0) and not force:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot delete battery: has {live_data_count} live data records and {rental_count} rentals. Data must be removed first, or use force=true (superadmin only)"
        )
    
    try:
        if force:
            # Superadmin force deletion - remove all related data first
            # Order matters for foreign key constraints
            
            # 1. Delete rental PUE items for rentals with this battery
            rental_ids = [r.rentral_id for r in db.query(Rental).filter(Rental.battery_id == battery_id).all()]
            deleted_pue_items = 0
            if rental_ids:
                deleted_pue_items = db.query(RentalPUEItem).filter(RentalPUEItem.rental_id.in_(rental_ids)).delete(synchronize_session=False)
            
            # 2. Delete rentals
            deleted_rentals = db.query(Rental).filter(Rental.battery_id == battery_id).delete(synchronize_session=False)
            
            # 3. Delete live data
            deleted_live_data = db.query(LiveData).filter(LiveData.battery_id == battery_id).delete(synchronize_session=False)
            
            # 4. Finally delete the battery
            db.delete(battery)
            db.commit()
            
            return {
                "message": "Battery and all related data force deleted",
                "deleted": {
                    "battery_id": battery_id,
                    "live_data_records": deleted_live_data,
                    "rentals": deleted_rentals,
                    "rental_pue_items": deleted_pue_items
                }
            }
        else:
            # Safe deletion - no associated data
            db.delete(battery)
            db.commit()
            return {"message": f"Battery {battery_id} deleted successfully"}
            
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

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

@app.get("/batteries/by-short-id/{short_id}")
async def get_battery_by_short_id(
    short_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get battery by their short ID from QR code (e.g., BAT-0001)"""
    battery = db.query(BEPPPBattery).filter(BEPPPBattery.short_id == short_id).first()
    if not battery:
        raise HTTPException(status_code=404, detail=f"Battery with short ID '{short_id}' not found")

    # Check access rights
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.DATA_ADMIN]:
        if battery.hub_id != current_user.get('hub_id'):
            raise HTTPException(status_code=403, detail="Access denied")

    return battery

# ============================================================================
# BATTERY NOTES ENDPOINTS
# ============================================================================

@app.get("/batteries/{battery_id}/notes", tags=["Batteries"])
async def get_battery_notes(
    battery_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all notes for a battery"""
    # Check battery exists and user has access
    battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == battery_id).first()
    if not battery:
        raise HTTPException(status_code=404, detail="Battery not found")

    # Check access
    if current_user.get('role') not in [UserRole.SUPERADMIN, UserRole.DATA_ADMIN]:
        if battery.hub_id != current_user.get('hub_id'):
            raise HTTPException(status_code=403, detail="Access denied")

    # Get notes - they are linked via the battery_notes junction table
    notes = battery.notes

    return {
        "battery_id": battery_id,
        "notes": [
            {
                "id": note.id,
                "content": note.content,
                "created_at": note.created_at.isoformat() if note.created_at else None,
                "created_by": note.created_by,
                "creator": {
                    "user_id": note.creator.user_id if note.creator else None,
                    "username": note.creator.username if note.creator else None,
                    "Name": note.creator.Name if note.creator else None
                } if note.creator else None
            }
            for note in notes
        ]
    }


@app.get("/batteries/{battery_id}/errors", tags=["Batteries"])
async def get_battery_errors(
    battery_id: str,
    limit: int = 50,
    time_period: str = "last_week",
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get error history for a battery

    Returns all live data records that contain error codes for the specified battery.
    Errors are decoded into human-readable format with severity levels.

    Args:
        battery_id: Battery ID
        limit: Maximum number of error records to return (default: 50)
        time_period: Time range - last_24_hours, last_week, last_month, last_year (default: last_week)

    Returns:
        Error history with decoded error information and metrics at time of error
    """
    # Check battery exists and user has access
    battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == battery_id).first()
    if not battery:
        raise HTTPException(status_code=404, detail="Battery not found")

    # Check access
    if current_user.get('role') not in [UserRole.SUPERADMIN, UserRole.DATA_ADMIN]:
        if battery.hub_id != current_user.get('hub_id'):
            raise HTTPException(status_code=403, detail="Access denied")

    # Calculate time range
    start_time, end_time = calculate_time_period(time_period)

    # Query live data with errors
    error_records = db.query(LiveData).filter(
        LiveData.battery_id == battery_id,
        LiveData.err.isnot(None),
        LiveData.err != '',
        LiveData.timestamp >= start_time,
        LiveData.timestamp <= end_time
    ).order_by(LiveData.timestamp.desc()).limit(limit).all()

    # Format response
    errors = []
    for record in error_records:
        decoded = decode_error_string(record.err) if record.err else []
        errors.append({
            "id": record.id,
            "timestamp": record.timestamp.isoformat() if record.timestamp else None,
            "error_codes": record.err,
            "decoded_errors": decoded,
            "other_metrics": {
                "soc": record.state_of_charge,
                "voltage": record.voltage,
                "current": record.current_amps,
                "temperature": record.temp_battery,
                "power": record.power_watts,
                "latitude": record.latitude,
                "longitude": record.longitude
            }
        })

    return {
        "battery_id": battery_id,
        "battery_name": battery.short_id or f"Battery #{battery_id}",
        "errors": errors,
        "total_errors": len(errors),
        "time_period": time_period,
        "time_range": {
            "start": start_time.isoformat(),
            "end": end_time.isoformat()
        }
    }


@app.post("/batteries/{battery_id}/notes", tags=["Batteries"])
async def create_battery_note(
    battery_id: str,
    note_data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a note for a battery.

    Required fields:
    - content: str (note text)

    Optional fields:
    - condition: str (battery condition: 'excellent', 'good', 'fair', 'poor', 'needs_repair')
    """
    # Check permissions
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Check battery exists and user has access
    battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == battery_id).first()
    if not battery:
        raise HTTPException(status_code=404, detail="Battery not found")

    # Check access
    if current_user.get('role') != UserRole.SUPERADMIN:
        if battery.hub_id != current_user.get('hub_id'):
            raise HTTPException(status_code=403, detail="Access denied")

    # Validate required fields
    if not note_data.get('content'):
        raise HTTPException(status_code=400, detail="Note content is required")

    try:
        # Create note
        new_note = Note(
            content=note_data['content'],
            created_by=current_user.get('sub')
        )
        db.add(new_note)
        db.flush()  # Get the note ID

        # Link note to battery
        battery.notes.append(new_note)

        # Update battery condition if provided
        if note_data.get('condition'):
            # Store condition in a custom way since it's not in the model
            # You might want to add a 'condition' column to BEPPPBattery model
            pass

        db.commit()
        db.refresh(new_note)

        return {
            "note_id": new_note.id,
            "battery_id": battery_id,
            "message": "Note created successfully"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create note: {str(e)}")


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
        pue_data = pue.model_dump()

        # Validate usage_location against enum values
        if 'usage_location' in pue_data and pue_data['usage_location']:
            # Convert to uppercase to match database enum
            if pue_data['usage_location'].upper() in ["HUB_ONLY", "BATTERY_ONLY", "BOTH"]:
                pue_data['usage_location'] = pue_data['usage_location'].upper()
            elif pue_data['usage_location'].lower() in ["hub_only", "battery_only", "both"]:
                pue_data['usage_location'] = pue_data['usage_location'].upper()

            if pue_data['usage_location'] not in ["HUB_ONLY", "BATTERY_ONLY", "BOTH"]:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid usage_location. Must be one of: hub_only, battery_only, both"
                )

        db_pue = ProductiveUseEquipment(**pue_data)
        db.add(db_pue)
        db.flush()  # Flush to get the ID before committing

        # Generate short_id for QR codes
        db_pue.short_id = f"PUE-{str(db_pue.pue_id).zfill(4)}"

        db.commit()
        db.refresh(db_pue)
        return db_pue
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/pue/{pue_id}")
async def get_pue_item(
    pue_id: str,
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
    pue_id: str,
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
        
        update_data = pue_update.model_dump(exclude_unset=True)
        
        # Validate usage_location against enum values
        if 'usage_location' in update_data and update_data['usage_location']:
            # Convert to uppercase to match database enum
            if update_data['usage_location'].upper() in ["HUB_ONLY", "BATTERY_ONLY", "BOTH"]:
                update_data['usage_location'] = update_data['usage_location'].upper()
            elif update_data['usage_location'].lower() in ["hub_only", "battery_only", "both"]:
                update_data['usage_location'] = update_data['usage_location'].upper()
            
            if update_data['usage_location'] not in ["HUB_ONLY", "BATTERY_ONLY", "BOTH"]:
                raise HTTPException(
                    status_code=400, 
                    detail="Invalid usage_location. Must be one of: hub_only, battery_only, both"
                )
        
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
    pue_id: str,
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
    except HTTPException:
        db.rollback()
        raise
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

    pue_items = query.all()

    # Convert to dicts to ensure proper serialization
    return [{
        "pue_id": pue.pue_id,
        "hub_id": pue.hub_id,
        "name": pue.name,
        "description": pue.description,
        "power_rating_watts": pue.power_rating_watts,
        "usage_location": pue.usage_location.value if pue.usage_location else None,
        "storage_location": pue.storage_location,
        "suggested_cost_per_day": pue.suggested_cost_per_day,
        "pue_type_id": pue.pue_type_id,
        "short_id": pue.short_id,
        "rental_cost": pue.rental_cost,
        "status": pue.status,
        "rental_count": pue.rental_count,
        "created_at": pue.created_at,
        "updated_at": pue.updated_at,
        "is_active": pue.is_active
    } for pue in pue_items]

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

@app.get("/rentals/",
    tags=["Rentals"],
    summary="List All Rentals",
    description="""
    ## Get All Rentals

    Retrieves all rentals with filtering by status and user.

    ### Permissions:
    - **SUPERADMIN/DATA_ADMIN**: Can see all rentals across all hubs
    - **ADMIN/USER**: Can only see rentals from their assigned hub

    ### Query Parameters:
    - **status**: Filter by rental status (active, returned, all)
    - **user_id**: Filter by specific user ID (optional)

    ### Returns:
    - List of rentals with user, battery, and hub information
    """,
    response_description="List of rentals")
async def list_rentals(
    status: str = "all",
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all battery and PUE rentals with optional status filtering"""
    try:
        now = datetime.now(timezone.utc)
        result = []

        # Query Battery Rentals
        battery_query = db.query(BatteryRental)

        # Filter by user_id if provided
        if user_id is not None:
            battery_query = battery_query.filter(BatteryRental.user_id == user_id)

        # Filter by status
        if status == "active":
            battery_query = battery_query.filter(
                BatteryRental.status.in_(['active', 'overdue']),
                BatteryRental.actual_return_date.is_(None)
            )
        elif status == "returned":
            battery_query = battery_query.filter(
                BatteryRental.actual_return_date.isnot(None)
            )
        elif status == "overdue":
            battery_query = battery_query.filter(
                BatteryRental.status == 'overdue',
                BatteryRental.actual_return_date.is_(None)
            )

        # For non-superadmins, filter by their hub
        if current_user.get('role') not in [UserRole.SUPERADMIN, UserRole.DATA_ADMIN]:
            user_hub_id = current_user.get('hub_id')
            if user_hub_id:
                battery_query = battery_query.filter(BatteryRental.hub_id == user_hub_id)

        battery_rentals = battery_query.order_by(BatteryRental.start_date.desc()).all()

        # Process battery rentals
        for rental in battery_rentals:
            user = db.query(User).filter(User.user_id == rental.user_id).first()
            hub = db.query(SolarHub).filter(SolarHub.hub_id == rental.hub_id).first()

            # Get battery items for this rental
            battery_items = db.query(BatteryRentalItem).filter(
                BatteryRentalItem.rental_id == rental.rental_id
            ).all()

            # Determine status
            rental_status = "returned" if rental.actual_return_date else rental.status
            if rental_status in ['active', 'overdue'] and rental.end_date:
                end_date = rental.end_date
                if end_date.tzinfo is None:
                    end_date = end_date.replace(tzinfo=timezone.utc)
                if end_date < now:
                    rental_status = "overdue"

            # Get battery info for display
            battery_info = None
            if battery_items:
                first_battery = db.query(BEPPPBattery).filter(
                    BEPPPBattery.battery_id == battery_items[0].battery_id
                ).first()
                if first_battery:
                    battery_info = {
                        "battery_id": first_battery.battery_id,
                        "short_id": first_battery.short_id,
                        "status": first_battery.status,
                        "battery_capacity_wh": first_battery.battery_capacity_wh
                    }

            result.append({
                "rentral_id": rental.rental_id,
                "rental_type": "battery",
                "battery_id": battery_items[0].battery_id if battery_items else None,
                "item_name": f"{len(battery_items)} Battery(ies)" if len(battery_items) > 1 else (battery_items[0].battery_id if battery_items else "Battery"),
                "user_id": rental.user_id,
                "timestamp_taken": rental.start_date.isoformat() if rental.start_date else None,
                "due_back": rental.end_date.isoformat() if rental.end_date else None,
                "battery_returned_date": rental.actual_return_date.isoformat() if rental.actual_return_date else None,
                "total_cost": float(rental.final_cost_total or rental.estimated_cost_total or 0.0),
                "deposit_amount": float(rental.deposit_amount or 0.0),
                "status": rental_status,
                "rental_status": rental_status,
                "user": {
                    "user_id": user.user_id,
                    "username": user.username if hasattr(user, 'username') else None,
                    "Name": user.Name if hasattr(user, 'Name') else None,
                    "mobile_number": user.mobile_number if hasattr(user, 'mobile_number') else None
                } if user else None,
                "battery": battery_info,
                "hub": {
                    "hub_id": hub.hub_id,
                    "what_three_word_location": hub.what_three_word_location
                } if hub else None
            })

        # Query PUE Rentals
        pue_query = db.query(PUERental)

        # Filter by user_id if provided
        if user_id is not None:
            pue_query = pue_query.filter(PUERental.user_id == user_id)

        # Filter by status
        if status == "active":
            pue_query = pue_query.filter(
                PUERental.is_active == True,
                PUERental.date_returned.is_(None)
            )
        elif status == "returned":
            pue_query = pue_query.filter(
                PUERental.date_returned.isnot(None)
            )
        elif status == "overdue":
            pue_query = pue_query.filter(
                PUERental.is_active == True,
                PUERental.date_returned.is_(None),
                PUERental.due_back < now
            )

        # For non-superadmins, filter by their hub
        if current_user.get('role') not in [UserRole.SUPERADMIN, UserRole.DATA_ADMIN]:
            user_hub_id = current_user.get('hub_id')
            if user_hub_id:
                pue_query = pue_query.join(
                    ProductiveUseEquipment,
                    PUERental.pue_id == ProductiveUseEquipment.pue_id
                ).filter(ProductiveUseEquipment.hub_id == user_hub_id)

        pue_rentals = pue_query.order_by(PUERental.timestamp_taken.desc()).all()

        # Process PUE rentals
        for rental in pue_rentals:
            user = db.query(User).filter(User.user_id == rental.user_id).first()
            pue = db.query(ProductiveUseEquipment).filter(
                ProductiveUseEquipment.pue_id == rental.pue_id
            ).first()
            hub = db.query(SolarHub).filter(SolarHub.hub_id == pue.hub_id).first() if pue else None

            # Determine status
            rental_status = "returned" if rental.date_returned else "active"
            if rental_status == "active" and rental.due_back:
                due_back = rental.due_back
                if due_back.tzinfo is None:
                    due_back = due_back.replace(tzinfo=timezone.utc)
                if due_back < now:
                    rental_status = "overdue"

            result.append({
                "rentral_id": rental.pue_rental_id,
                "rental_type": "pue",
                "pue_id": rental.pue_id,
                "item_name": pue.name if pue else "PUE Item",
                "user_id": rental.user_id,
                "timestamp_taken": rental.timestamp_taken.isoformat() if rental.timestamp_taken else None,
                "due_back": rental.due_back.isoformat() if rental.due_back else None,
                "battery_returned_date": rental.date_returned.isoformat() if rental.date_returned else None,
                "total_cost": float(rental.rental_cost or 0.0),
                "deposit_amount": float(rental.deposit_amount or 0.0),
                "status": rental_status,
                "rental_status": rental_status,
                "user": {
                    "user_id": user.user_id,
                    "username": user.username if hasattr(user, 'username') else None,
                    "Name": user.Name if hasattr(user, 'Name') else None,
                    "mobile_number": user.mobile_number if hasattr(user, 'mobile_number') else None
                } if user else None,
                "pue": {
                    "pue_id": pue.pue_id,
                    "name": pue.name,
                    "status": pue.status
                } if pue else None,
                "hub": {
                    "hub_id": hub.hub_id,
                    "what_three_word_location": hub.what_three_word_location
                } if hub else None
            })

        # Sort combined results by timestamp_taken (most recent first)
        result.sort(key=lambda x: x['timestamp_taken'] if x['timestamp_taken'] else '', reverse=True)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list rentals: {str(e)}")

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
    request: Request,
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
        # Parse request body
        rental_data_raw = await request.json()
        
        # Determine which format to use based on the fields present
        if 'user_name' in rental_data_raw or 'user_mobile' in rental_data_raw:
            # User-friendly format
            try:
                rental = RentalCreateUserFriendly(**rental_data_raw)
            except Exception as e:
                raise HTTPException(status_code=422, detail=f"Invalid user-friendly rental data: {str(e)}")
        else:
            # Standard format
            try:
                rental = RentalCreate(**rental_data_raw)
            except Exception as e:
                raise HTTPException(status_code=422, detail=f"Invalid rental data: {str(e)}")
        
        # Handle different rental creation formats
        if isinstance(rental, RentalCreateUserFriendly):
            # User-friendly format: create or find user by name/mobile
            # Convert battery_id to string if it's an integer
            battery_id_str = str(rental.battery_id)
            battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == battery_id_str).first()
            if not battery:
                raise HTTPException(status_code=404, detail="Battery not found")

            # Check if battery is already rented
            existing_rental = db.query(Rental).filter(
                Rental.battery_id == battery_id_str,
                Rental.battery_returned_date.is_(None)
            ).first()
            if existing_rental:
                raise HTTPException(status_code=409, detail="Battery is already rented")

            # Find or create user
            user = db.query(User).filter(User.mobile_number == rental.user_mobile).first()
            if not user:
                # Create new user
                new_user_id = int(datetime.now().timestamp() * 1000) % 1000000
                user = User(
                    user_id=new_user_id,
                    Name=rental.user_name,
                    mobile_number=rental.user_mobile,
                    hub_id=battery.hub_id,
                    user_access_level=UserRole.USER
                )
                db.add(user)
                db.flush()

            # Convert to standard rental format (ignore notes since they're not in the model)
            rental_data = {
                "rentral_id": int(datetime.now().timestamp() * 1000) % 1000000,
                "battery_id": battery_id_str,
                "user_id": user.user_id,
                "timestamp_taken": datetime.now(timezone.utc),
                "due_back": rental.due_back or (datetime.now(timezone.utc) + timedelta(days=7)),
                "pue_item_ids": rental.pue_item_ids or [],
                "total_cost": rental.rental_cost,
                "deposit_amount": rental.deposit_amount
            }
            # Create a proper RentalCreate object
            from types import SimpleNamespace
            rental = SimpleNamespace(**rental_data)

        # Convert battery_id to string if it's an integer (for standard format)
        battery_id_str = str(rental.battery_id)
        battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == battery_id_str).first()
        if not battery:
            raise HTTPException(status_code=404, detail="Battery not found")
        
        user = db.query(User).filter(User.user_id == rental.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if current_user.get('role') == UserRole.USER:
            if battery.hub_id != current_user.get('hub_id') or user.hub_id != current_user.get('hub_id'):
                raise HTTPException(status_code=403, detail="Access denied")
        
        pue_items = []
        pue_item_ids = getattr(rental, 'pue_item_ids', []) or []
        if pue_item_ids:
            pue_items = db.query(ProductiveUseEquipment).filter(
                ProductiveUseEquipment.pue_id.in_(pue_item_ids),
                ProductiveUseEquipment.is_active == True
            ).all()
            
            if len(pue_items) != len(pue_item_ids):
                raise HTTPException(status_code=400, detail="Some PUE items not found or inactive")
        
        # Handle both Pydantic models and SimpleNamespace objects
        if hasattr(rental, 'dict'):
            rental_data = rental.dict(exclude={'pue_item_ids'})
        else:
            rental_data = {k: v for k, v in rental.__dict__.items() if k != 'pue_item_ids'}

        # Ensure battery_id is a string
        if 'battery_id' in rental_data:
            rental_data['battery_id'] = str(rental_data['battery_id'])

        # Generate unique rental ID (will be used in rentral_id)
        rental_unique_id = generate_rental_id(db)
        # Note: rental_unique_id is just for transaction descriptions,
        # the actual ID is auto-generated as rentral_id

        # Remove auto-generated fields that shouldn't be set during creation
        rental_data.pop('rentral_id', None)
        rental_data.pop('rental_unique_id', None)

        # Handle payment fields
        payment_status = rental_data.get('payment_status', 'unpaid')
        amount_paid = rental_data.get('amount_paid', 0)
        total_cost = rental_data.get('total_cost', 0)

        rental_data['payment_status'] = payment_status
        rental_data['amount_paid'] = amount_paid
        rental_data['amount_owed'] = max(0, total_cost - amount_paid)

        # Create cost breakdown if battery_cost or pue_cost provided
        battery_cost = rental_data.get('battery_cost', 0)
        pue_cost = rental_data.get('pue_cost', 0)
        if battery_cost or pue_cost:
            rental_data['total_cost_breakdown'] = {
                'battery_cost': battery_cost,
                'pue_cost': pue_cost,
                'total': battery_cost + pue_cost
            }

        # Debug: Check all keys in rental_data before creating Rental
        print(f"DEBUG: rental_data keys before Rental creation: {list(rental_data.keys())}")
        print(f"DEBUG: rentral_id in rental_data: {'rentral_id' in rental_data}")
        if 'rentral_id' in rental_data:
            print(f"DEBUG: rentral_id value: {rental_data['rentral_id']} (type: {type(rental_data['rentral_id'])})")

        db_rental = Rental(**rental_data)
        db.add(db_rental)
        db.flush()

        # Debug: Log the rental ID after flush
        print(f"DEBUG: After flush, db_rental.rentral_id = {db_rental.rentral_id} (type: {type(db_rental.rentral_id)})")

        # If rentral_id is not set, use a generated numeric ID
        if db_rental.rentral_id is None:
            db_rental.rentral_id = int(datetime.now().timestamp() * 1000) % 1000000000
            db.flush()
            print(f"DEBUG: Set rentral_id to {db_rental.rentral_id}")

        # Update battery status to rented
        battery.status = "rented"

        # Create or update user account and record transaction
        user_account = db.query(UserAccount).filter(UserAccount.user_id == user.user_id).first()
        if not user_account:
            # Auto-create user account
            user_account = UserAccount(
                user_id=user.user_id,
                balance=0,
                total_spent=0,
                total_owed=0
            )
            db.add(user_account)
            db.flush()

        # Record rental charge transaction
        if total_cost > 0:
            # Update account balances first to calculate balance_after
            user_account.balance -= total_cost  # Debit (negative balance = debt)
            user_account.total_spent += total_cost
            user_account.total_owed += rental_data['amount_owed']

            charge_transaction = AccountTransaction(
                account_id=user_account.account_id,
                rental_id=db_rental.rentral_id,
                transaction_type='rental_charge',
                amount=-total_cost,  # Negative for charges (debit)
                balance_after=user_account.balance,
                description=f'Rental charge for {rental_unique_id}',
                payment_method=rental_data.get('payment_method'),
                payment_type=rental_data.get('payment_type'),
                created_by=current_user.get('user_id') if hasattr(current_user, 'get') else None
            )
            db.add(charge_transaction)

        # Record payment transaction if paid upfront
        if amount_paid > 0:
            # Credit the payment
            user_account.balance += amount_paid
            user_account.total_owed = max(0, user_account.total_owed - amount_paid)

            payment_transaction = AccountTransaction(
                account_id=user_account.account_id,
                rental_id=db_rental.rentral_id,
                transaction_type='payment',
                amount=amount_paid,  # Positive for payments (credit)
                balance_after=user_account.balance,
                description=f'Payment for rental {rental_unique_id}',
                payment_method=rental_data.get('payment_method'),
                payment_type=rental_data.get('payment_type'),
                created_by=current_user.get('user_id') if hasattr(current_user, 'get') else None
            )
            db.add(payment_transaction)
        
        for pue_item in pue_items:
            rental_pue_item = RentalPUEItem(
                rental_id=db_rental.rentral_id,
                pue_id=pue_item.pue_id,
                rental_cost=pue_item.rental_cost,
                due_back=getattr(rental, 'due_back', None)
            )
            db.add(rental_pue_item)
        
        db.commit()
        db.refresh(db_rental)
        return db_rental
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Rental creation failed: {str(e)}")

@app.get("/rentals/overdue-upcoming",
    tags=["Rentals"],
    summary="Get Overdue and Upcoming Rentals",
    description="Get rentals that are overdue or due soon (within 3 days)")
async def get_overdue_upcoming_rentals(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get battery and PUE rentals that are overdue or due within 3 days"""
    try:
        now = datetime.now(timezone.utc)
        upcoming_threshold = now + timedelta(days=3)

        overdue = []
        upcoming = []

        # Get active battery rentals
        battery_rentals_query = db.query(BatteryRental).filter(
            BatteryRental.status.in_(['active', 'overdue']),
            BatteryRental.actual_return_date.is_(None)
        )

        # For non-superadmins, filter by their hub
        if current_user.get('role') not in [UserRole.SUPERADMIN, UserRole.DATA_ADMIN]:
            user_hub_id = current_user.get('hub_id')
            if user_hub_id:
                battery_rentals_query = battery_rentals_query.filter(BatteryRental.hub_id == user_hub_id)

        battery_rentals = battery_rentals_query.all()

        for rental in battery_rentals:
            # Use end_date as the due date
            due_date = rental.end_date
            if due_date.tzinfo is None:
                due_date = due_date.replace(tzinfo=timezone.utc)

            # Get user and hub info
            user = db.query(User).filter(User.user_id == rental.user_id).first()
            hub = db.query(SolarHub).filter(SolarHub.hub_id == rental.hub_id).first()

            # Get battery items for this rental
            battery_items = db.query(BatteryRentalItem).filter(
                BatteryRentalItem.rental_id == rental.rental_id
            ).all()
            battery_ids = [item.battery_id for item in battery_items]

            days_diff = (due_date - now).days
            hours_diff = (due_date - now).total_seconds() / 3600

            rental_info = {
                "rentral_id": rental.rental_id,
                "rental_type": "battery",
                "battery_id": battery_ids[0] if battery_ids else None,
                "item_name": f"{len(battery_ids)} Battery(ies)" if len(battery_ids) > 1 else battery_ids[0] if battery_ids else "Battery",
                "user_id": rental.user_id,
                "user_name": user.Name if user else "Unknown",
                "username": user.username if user else "Unknown",
                "mobile_number": user.mobile_number if user else None,
                "address": user.address if user else None,
                "hub_id": rental.hub_id,
                "hub_name": hub.what_three_word_location if hub else "Unknown",
                "due_back": due_date.isoformat(),
                "timestamp_taken": rental.start_date.isoformat() if rental.start_date else None,
                "days_overdue": abs(days_diff) if days_diff < 0 else 0,
                "hours_overdue": abs(hours_diff) if hours_diff < 0 else 0,
                "days_until_due": days_diff if days_diff > 0 else 0,
                "status": "overdue" if due_date < now else "upcoming",
                "total_cost": rental.final_cost_total or rental.estimated_cost_total,
                "deposit_amount": rental.deposit_amount
            }

            if due_date < now:
                overdue.append(rental_info)
            elif due_date <= upcoming_threshold:
                upcoming.append(rental_info)

        # Get active PUE rentals
        pue_rentals_query = db.query(PUERental).filter(
            PUERental.is_active == True,
            PUERental.date_returned.is_(None)
        )

        # For non-superadmins, filter by their hub
        if current_user.get('role') not in [UserRole.SUPERADMIN, UserRole.DATA_ADMIN]:
            user_hub_id = current_user.get('hub_id')
            if user_hub_id:
                # PUE rentals link through ProductiveUseEquipment to get hub_id
                pue_rentals_query = pue_rentals_query.join(
                    ProductiveUseEquipment,
                    PUERental.pue_id == ProductiveUseEquipment.pue_id
                ).filter(ProductiveUseEquipment.hub_id == user_hub_id)

        pue_rentals = pue_rentals_query.all()

        for rental in pue_rentals:
            # Use due_back as the due date
            due_date = rental.due_back
            if not due_date:
                continue  # Skip rentals without due date
            if due_date.tzinfo is None:
                due_date = due_date.replace(tzinfo=timezone.utc)

            # Get user, PUE item, and hub info
            user = db.query(User).filter(User.user_id == rental.user_id).first()
            pue = db.query(ProductiveUseEquipment).filter(ProductiveUseEquipment.pue_id == rental.pue_id).first()
            hub = db.query(SolarHub).filter(SolarHub.hub_id == pue.hub_id).first() if pue else None

            days_diff = (due_date - now).days
            hours_diff = (due_date - now).total_seconds() / 3600

            rental_info = {
                "rentral_id": rental.pue_rental_id,
                "rental_type": "pue",
                "pue_id": rental.pue_id,
                "item_name": pue.name if pue else "PUE Item",
                "user_id": rental.user_id,
                "user_name": user.Name if user else "Unknown",
                "username": user.username if user else "Unknown",
                "mobile_number": user.mobile_number if user else None,
                "address": user.address if user else None,
                "hub_id": pue.hub_id if pue else None,
                "hub_name": hub.what_three_word_location if hub else "Unknown",
                "due_back": due_date.isoformat(),
                "timestamp_taken": rental.timestamp_taken.isoformat() if rental.timestamp_taken else None,
                "days_overdue": abs(days_diff) if days_diff < 0 else 0,
                "hours_overdue": abs(hours_diff) if hours_diff < 0 else 0,
                "days_until_due": days_diff if days_diff > 0 else 0,
                "status": "overdue" if due_date < now else "upcoming",
                "total_cost": rental.rental_cost,
                "deposit_amount": rental.deposit_amount
            }

            if due_date < now:
                overdue.append(rental_info)
            elif due_date <= upcoming_threshold:
                upcoming.append(rental_info)

        # Sort by urgency
        overdue.sort(key=lambda x: x['days_overdue'], reverse=True)
        upcoming.sort(key=lambda x: x['days_until_due'])

        return {
            "overdue": overdue,
            "upcoming": upcoming,
            "total_overdue": len(overdue),
            "total_upcoming": len(upcoming)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting overdue/upcoming rentals: {str(e)}")

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
    
    # Calculate summary statistics
    pue_items = rental.pue_items if rental.pue_items else []
    total_pue_items = len(pue_items)
    returned_pue_items = len([item for item in pue_items if item.returned_date])
    battery_returned = bool(rental.date_returned or rental.battery_returned_date)
    rental_complete = battery_returned and (returned_pue_items == total_pue_items)

    # Get battery and user details
    battery = rental.battery
    user = rental.user if current_user.get('role') != UserRole.DATA_ADMIN else None

    rental_dict = {
        "rental": rental,
        "pue_items": pue_items,
        "battery": {
            "battery_id": battery.battery_id,
            "short_id": battery.short_id,
            "battery_capacity_wh": battery.battery_capacity_wh,
            "status": battery.status
        } if battery else None,
        "user": {
            "user_id": user.user_id,
            "Name": user.Name,
            "username": user.username,
            "mobile_number": user.mobile_number,
            "email": user.email if hasattr(user, 'email') else None
        } if user else None,
        "summary": {
            "total_pue_items": total_pue_items,
            "returned_pue_items": returned_pue_items,
            "battery_returned": battery_returned,
            "rental_complete": rental_complete
        }
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
    except HTTPException:
        db.rollback()
        raise
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

        # Handle payment on return
        if return_request.payment_amount and return_request.payment_amount > 0:
            user_account = db.query(UserAccount).filter(UserAccount.user_id == rental.user_id).first()
            if not user_account:
                # Create user account if it doesn't exist
                user_account = UserAccount(
                    user_id=rental.user_id,
                    balance=0,
                    total_spent=0,
                    total_owed=0
                )
                db.add(user_account)
                db.flush()

            # Record payment transaction
            payment_transaction = AccountTransaction(
                user_id=rental.user_id,
                transaction_type='payment',
                amount=return_request.payment_amount,
                description=return_request.payment_notes or f'Payment on return of rental {rental.rentral_id}',
                related_rental_id=rental.rentral_id
            )
            db.add(payment_transaction)

            # Update rental payment status
            rental.amount_paid = (rental.amount_paid or 0) + return_request.payment_amount
            rental.amount_owed = max(0, (rental.total_cost or 0) - rental.amount_paid)

            if rental.amount_owed == 0:
                rental.payment_status = 'paid'
            elif rental.amount_paid > 0:
                rental.payment_status = 'partial'

            # Update user account balance
            user_account.balance += return_request.payment_amount
            user_account.total_owed = max(0, user_account.total_owed - return_request.payment_amount)

            return_summary["payment_recorded"] = {
                "amount": return_request.payment_amount,
                "new_balance": rental.amount_owed
            }

        # Update rental status if everything is returned
        if (return_request.return_battery and
            not return_summary["still_rented"]["pue_items"]):
            rental.is_active = False
            rental.status = "completed"

        # Use actual_return_date if provided, otherwise use current time
        if return_request.actual_return_date and return_request.return_battery:
            rental.battery_returned_date = return_request.actual_return_date

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

@app.get("/rentals/{rental_id}/calculate-return-cost",
    tags=["Rentals"],
    summary="Calculate Final Cost at Return",
    description="Calculate the final cost for a rental based on actual usage (days, kWh, etc.)")
async def calculate_return_cost(
    rental_id: int,
    actual_return_date: Optional[str] = Query(None, description="Actual return date (ISO format)"),
    kwh_usage: Optional[float] = Query(None, description="Actual kWh used"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Calculate final cost for a rental at return time based on:
    - Actual duration (rental start to return date)
    - Actual kWh usage (if provided)
    - Cost structure components (per_day, per_hour, per_kwh, fixed, etc.)
    - Early return credits or late return penalties

    Returns breakdown of all cost components and final total.
    """
    rental = db.query(Rental).filter(Rental.rentral_id == rental_id).first()
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")

    # Authorization check
    if current_user.get('role') == UserRole.USER:
        battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == rental.battery_id).first()
        if not battery or battery.hub_id != current_user.get('hub_id'):
            raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.get('role') == UserRole.DATA_ADMIN:
        raise HTTPException(status_code=403, detail="Data admins cannot access rental details")

    # Parse actual return date or use now
    if actual_return_date:
        try:
            return_date = datetime.fromisoformat(actual_return_date.replace('Z', '+00:00'))
        except:
            return_date = datetime.now(timezone.utc)
    else:
        return_date = datetime.now(timezone.utc)

    # Calculate actual duration
    start_date = rental.timestamp_taken
    if isinstance(start_date, str):
        start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
    elif start_date and not start_date.tzinfo:
        # If start_date is naive (no timezone), assume UTC
        start_date = start_date.replace(tzinfo=timezone.utc)

    duration_delta = return_date - start_date
    actual_hours = duration_delta.total_seconds() / 3600
    actual_days = duration_delta.total_seconds() / 86400
    actual_weeks = actual_days / 7
    actual_months = actual_days / 30  # Approximate

    # Get cost structure and calculate costs
    cost_breakdown = []
    subtotal = 0
    has_cost_structure = False

    if rental.cost_structure_id:
        cost_structure = db.query(CostStructure).filter(
            CostStructure.structure_id == rental.cost_structure_id
        ).first()

        if cost_structure:
            has_cost_structure = True
            components = db.query(CostComponent).filter(
                CostComponent.structure_id == cost_structure.structure_id
            ).all()

            for component in components:
                component_cost = 0
                quantity = 0

                if component.unit_type == 'per_hour':
                    quantity = actual_hours
                    component_cost = component.rate * actual_hours
                elif component.unit_type == 'per_day':
                    quantity = actual_days
                    component_cost = component.rate * actual_days
                elif component.unit_type == 'per_week':
                    quantity = actual_weeks
                    component_cost = component.rate * actual_weeks
                elif component.unit_type == 'per_month':
                    quantity = actual_months
                    component_cost = component.rate * actual_months
                elif component.unit_type == 'per_kwh':
                    # Calculate kWh usage from multiple sources
                    kwh_used = None

                    if kwh_usage is not None:
                        # Use provided kWh usage
                        kwh_used = kwh_usage
                    elif getattr(rental, 'kwh_usage_start', None) and getattr(rental, 'kwh_usage_end', None):
                        # Use stored rental kWh readings
                        kwh_used = rental.kwh_usage_end - rental.kwh_usage_start
                    else:
                        # Automatically fetch latest kWh from battery's live data
                        latest_data = db.query(LiveData).filter(
                            LiveData.battery_id == rental.battery_id
                        ).order_by(LiveData.timestamp.desc()).first()

                        if latest_data and latest_data.amp_hours_consumed:
                            # Use amp_hours_consumed as kWh estimate
                            # Convert Ah to kWh: Ah * V / 1000
                            voltage = latest_data.voltage or 48  # Default to 48V if not available
                            kwh_used = (latest_data.amp_hours_consumed * voltage) / 1000
                        elif getattr(rental, 'kwh_usage_start', None):
                            # If we have start reading, try to get current reading
                            if latest_data:
                                # Estimate based on SOC change if available
                                pass  # Could add SOC-based estimation here

                    if kwh_used is not None and kwh_used > 0:
                        quantity = kwh_used
                        component_cost = component.rate * kwh_used
                elif component.unit_type == 'fixed':
                    quantity = 1
                    component_cost = component.rate

                cost_breakdown.append({
                    "component_name": component.component_name,
                    "unit_type": component.unit_type,
                    "rate": float(component.rate),
                    "quantity": round(quantity, 2),
                    "amount": round(component_cost, 2)
                })

                subtotal += component_cost

    # If no cost structure, use rental's total cost as fallback
    if not has_cost_structure and rental.total_cost:
        subtotal = rental.total_cost
        cost_breakdown.append({
            "component_name": "Total Cost (Estimate)",
            "unit_type": "fixed",
            "rate": float(rental.total_cost),
            "quantity": 1,
            "amount": float(rental.total_cost)
        })

    # Get hub VAT (default to 15% if not set)
    battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == rental.battery_id).first()
    vat_percentage = 15.0  # Default VAT percentage
    if battery and battery.hub_id:
        hub = db.query(SolarHub).filter(SolarHub.hub_id == battery.hub_id).first()
        if hub and hasattr(hub, 'vat_percentage') and hub.vat_percentage is not None:
            vat_percentage = hub.vat_percentage

    vat_amount = subtotal * (vat_percentage / 100)
    total = subtotal + vat_amount

    # Calculate difference from original estimate (use getattr for safety)
    original_total = getattr(rental, 'estimated_cost_total', None) or rental.total_cost or 0
    cost_difference = total - original_total

    # Get user account balance
    user_account = db.query(UserAccount).filter(UserAccount.user_id == rental.user_id).first()
    account_balance = user_account.balance if user_account else 0

    # Calculate amounts (use getattr for fields that may not exist in DB)
    amount_paid_so_far = getattr(rental, 'amount_paid', 0) or 0
    amount_still_owed = max(0, total - amount_paid_so_far)
    amount_after_credit = max(0, amount_still_owed - account_balance)

    # Check subscription coverage
    subscription_info = None
    subscription_covered_amount = 0
    if rental.subscription_id:
        user_subscription = db.query(UserSubscription).filter(
            UserSubscription.subscription_id == rental.subscription_id
        ).first()

        if user_subscription and user_subscription.status == 'active':
            subscription_package = db.query(SubscriptionPackage).filter(
                SubscriptionPackage.package_id == user_subscription.package_id
            ).first()

            if subscription_package:
                # Check if this rental type is covered by subscription
                package_items = db.query(SubscriptionPackageItem).filter(
                    SubscriptionPackageItem.package_id == subscription_package.package_id
                ).all()

                # Check if battery is covered
                battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == rental.battery_id).first()
                is_covered = False

                for item in package_items:
                    if item.item_type == 'battery' and item.item_reference == 'all':
                        is_covered = True
                        break
                    elif item.item_type == 'battery_capacity' and battery and str(battery.capacity) == item.item_reference:
                        is_covered = True
                        break
                    elif item.item_type == 'battery_item' and str(battery.battery_id) == item.item_reference:
                        is_covered = True
                        break

                # Calculate subscription coverage
                if is_covered:
                    # Base rental cost is covered by subscription
                    # Check kWh usage against subscription limits
                    kwh_included = subscription_package.included_kwh_per_period or 0
                    kwh_used_this_period = user_subscription.kwh_used_current_period or 0
                    kwh_for_this_rental = kwh_usage or 0

                    overage_kwh = max(0, (kwh_used_this_period + kwh_for_this_rental) - kwh_included)
                    overage_cost = overage_kwh * (subscription_package.kwh_overage_rate or 0)

                    # Subscription covers base cost, but not overages or late fees
                    subscription_covered_amount = total - overage_cost

                    subscription_info = {
                        "is_covered": True,
                        "subscription_name": subscription_package.package_name,
                        "subscription_id": rental.subscription_id,
                        "package_id": subscription_package.package_id,
                        "billing_period": subscription_package.billing_period,
                        "covered_amount": round(subscription_covered_amount, 2),
                        "kwh_included": kwh_included,
                        "kwh_used_this_period": kwh_used_this_period,
                        "kwh_for_this_rental": kwh_for_this_rental,
                        "kwh_overage": round(overage_kwh, 2),
                        "kwh_overage_cost": round(overage_cost, 2),
                        "remaining_cost_after_subscription": round(max(0, total - subscription_covered_amount), 2)
                    }
                else:
                    subscription_info = {
                        "is_covered": False,
                        "subscription_name": subscription_package.package_name,
                        "message": "This rental is not covered by your subscription package"
                    }

    # Recalculate amount owed considering subscription coverage
    if subscription_covered_amount > 0:
        amount_still_owed = max(0, total - subscription_covered_amount - amount_paid_so_far)
        amount_after_credit = max(0, amount_still_owed - account_balance)

    # Ensure due_back is timezone-aware for comparison
    due_back_aware = rental.due_back
    if due_back_aware and not due_back_aware.tzinfo:
        due_back_aware = due_back_aware.replace(tzinfo=timezone.utc)

    return {
        "rental_id": rental_id,
        "rental_unique_id": rental.rentral_id,  # Use rentral_id as the unique identifier
        "duration": {
            "start_date": start_date.isoformat(),
            "return_date": return_date.isoformat(),
            "actual_hours": round(actual_hours, 2),
            "actual_days": round(actual_days, 2),
            "scheduled_return_date": due_back_aware.isoformat() if due_back_aware else None,
            "is_late": return_date > due_back_aware if due_back_aware else False
        },
        "kwh_usage": {
            "start_reading": rental.kwh_usage_start,
            "end_reading": kwh_usage or rental.kwh_usage_end,
            "total_used": kwh_usage or (rental.kwh_usage_end - rental.kwh_usage_start if rental.kwh_usage_end and rental.kwh_usage_start else None)
        },
        "cost_breakdown": cost_breakdown,
        "subtotal": round(subtotal, 2),
        "vat_percentage": vat_percentage,
        "vat_amount": round(vat_amount, 2),
        "total": round(total, 2),
        "original_estimate": round(original_total, 2),
        "cost_difference": round(cost_difference, 2),
        "payment_status": {
            "amount_paid_so_far": round(amount_paid_so_far, 2),
            "amount_still_owed": round(amount_still_owed, 2),
            "user_account_balance": round(account_balance, 2),
            "amount_after_credit": round(amount_after_credit, 2),
            "can_pay_with_credit": account_balance >= amount_still_owed
        },
        "subscription": subscription_info
    }

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

@app.put("/rentals/{rental_id}/pue-items/{pue_id}/return",
    tags=["Rentals"],
    summary="Return Individual PUE Item",
    description="Return a specific PUE item from a rental")
async def return_individual_pue_item(
    rental_id: int,
    pue_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Return a specific PUE item from a rental"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.USER]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get the rental
    rental = db.query(Rental).filter(Rental.rentral_id == rental_id).first()
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")
    
    # Check access permissions
    if current_user.get('role') == UserRole.USER:
        battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == rental.battery_id).first()
        if not battery or battery.hub_id != current_user.get('hub_id'):
            raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Find the PUE item in this rental
        pue_item = db.query(RentalPUEItem).filter(
            RentalPUEItem.rental_id == rental_id,
            RentalPUEItem.pue_id == pue_id,
            RentalPUEItem.is_returned == False
        ).first()
        
        if not pue_item:
            raise HTTPException(status_code=404, detail="PUE item not found in this rental or already returned")
        
        # Mark the PUE item as returned
        pue_item.is_returned = True
        pue_item.returned_date = datetime.now(timezone.utc)
        
        # Update PUE equipment status to available
        pue_equipment = db.query(ProductiveUseEquipment).filter(
            ProductiveUseEquipment.pue_id == pue_id
        ).first()
        
        if pue_equipment:
            pue_equipment.status = "available"
        
        db.commit()
        
        return {
            "message": "PUE item returned successfully",
            "rental_id": rental_id,
            "pue_id": pue_id,
            "returned_date": pue_item.returned_date.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error returning PUE item: {str(e)}")

# ============================================================================
# NEW BATTERY RENTAL ENDPOINTS
# ============================================================================

@app.post("/battery-rentals",
    tags=["Battery Rentals"],
    summary="Create Battery Rental",
    description="""
    ## Create a New Battery Rental

    Creates a new battery rental using the restructured rental system.
    Supports multiple batteries in a single rental.

    ### Permissions:
    - **ADMIN**: Can create rentals
    - **SUPERADMIN**: Can create rentals
    - **USER**: Can create rentals for their own hub

    ### Features:
    - Multiple batteries in one rental
    - Automatic availability checking
    - Cost structure application
    - Overdue handling with grace periods
    - Recharge tracking

    ### Returns:
    - Created rental information with all batteries
    """,
    response_description="Created battery rental details")
async def create_battery_rental(
    rental: BatteryRentalCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new battery rental"""
    if current_user.get('role') == UserRole.DATA_ADMIN:
        raise HTTPException(status_code=403, detail="Data admins cannot create rentals")

    try:
        # Verify user exists
        user = db.query(User).filter(User.user_id == rental.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Authorization check
        if current_user.get('role') == UserRole.USER:
            if user.hub_id != current_user.get('hub_id'):
                raise HTTPException(status_code=403, detail="Access denied")

        # Verify cost structure exists
        cost_structure = db.query(CostStructure).filter(
            CostStructure.structure_id == rental.cost_structure_id
        ).first()
        if not cost_structure:
            raise HTTPException(status_code=404, detail="Cost structure not found")

        # Determine initial recharge count based on cost structure setting
        initial_recharges = 1 if cost_structure.count_initial_checkout_as_recharge else 0

        # ENFORCE SINGLE BATTERY ONLY (for multi-battery support, remove this validation)
        if len(rental.battery_ids) != 1:
            raise HTTPException(
                status_code=400,
                detail="Currently only single battery rentals are supported. Please select exactly one battery."
            )

        # Check all batteries exist and are available
        batteries = []
        for battery_id in rental.battery_ids:
            battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == battery_id).first()
            if not battery:
                raise HTTPException(status_code=404, detail=f"Battery {battery_id} not found")

            # Check if battery is already in an active rental
            existing_rental = db.query(BatteryRentalItem).join(BatteryRental).filter(
                BatteryRentalItem.battery_id == battery_id,
                BatteryRentalItem.returned_at.is_(None),
                BatteryRental.status == 'active'
            ).first()
            if existing_rental:
                raise HTTPException(status_code=409, detail=f"Battery {battery_id} is already rented")

            batteries.append(battery)

        # Create rental
        rental_start = rental.rental_start_date or datetime.now(timezone.utc)
        new_rental = BatteryRental(
            user_id=rental.user_id,
            hub_id=user.hub_id,
            cost_structure_id=rental.cost_structure_id,
            start_date=rental_start,
            end_date=rental.due_date,
            deposit_amount=rental.deposit_amount or 0.0,
            status='active',
            recharges_used=initial_recharges  # Set based on cost structure setting
        )
        db.add(new_rental)
        db.flush()  # Get rental_id

        # Create rental items for each battery
        rental_items = []
        for battery in batteries:
            item = BatteryRentalItem(
                rental_id=new_rental.rental_id,
                battery_id=battery.battery_id
                # added_at will be set automatically by server default
            )
            db.add(item)
            rental_items.append(item)

            # Mark battery as rented
            battery.status = 'rented'

        # Add notes if provided
        if rental.notes:
            for note_content in rental.notes:
                note = Note(content=note_content)
                db.add(note)
                db.flush()
                new_rental.notes.append(note)

        # Calculate estimated cost
        estimated_subtotal = 0
        estimated_breakdown = []

        # Get cost components
        components = db.query(CostComponent).filter(
            CostComponent.structure_id == rental.cost_structure_id
        ).order_by(CostComponent.sort_order).all()

        # Calculate duration if we have an end date
        if rental.due_date:
            duration_delta = rental.due_date - rental_start
            hours = duration_delta.total_seconds() / 3600
            days = duration_delta.total_seconds() / 86400
            weeks = days / 7
            months = days / 30
            years = days / 365

            for component in components:
                component_cost = 0
                quantity = 0

                if component.unit_type == 'flat':
                    quantity = 1
                    component_cost = component.rate
                elif component.unit_type == 'per_hour':
                    quantity = hours
                    component_cost = component.rate * hours
                elif component.unit_type == 'per_day':
                    quantity = days
                    component_cost = component.rate * days
                elif component.unit_type == 'per_week':
                    quantity = weeks
                    component_cost = component.rate * weeks
                elif component.unit_type == 'per_month':
                    quantity = months
                    component_cost = component.rate * months
                elif component.unit_type == 'per_year':
                    quantity = years
                    component_cost = component.rate * years
                elif component.unit_type == 'per_recharge':
                    # Use initial recharge count
                    quantity = initial_recharges
                    component_cost = component.rate * initial_recharges
                # per_kwh and per_charge can't be estimated

                if component_cost > 0:
                    estimated_breakdown.append({
                        "component_name": component.component_name,
                        "unit_type": component.unit_type,
                        "rate": float(component.rate),
                        "quantity": round(quantity, 2),
                        "amount": round(component_cost, 2)
                    })
                    estimated_subtotal += component_cost

            # Apply VAT
            hub = db.query(SolarHub).filter(SolarHub.hub_id == user.hub_id).first()
            vat_percentage = hub.vat_percentage if (hub and hasattr(hub, 'vat_percentage') and hub.vat_percentage is not None) else 0.0
            estimated_vat = estimated_subtotal * (vat_percentage / 100)
            estimated_total = estimated_subtotal + estimated_vat

            # Save estimated costs to rental
            new_rental.estimated_cost_before_vat = estimated_subtotal
            new_rental.estimated_vat = estimated_vat
            new_rental.estimated_cost_total = estimated_total

        # Note: Upfront cost charging feature removed - costs are now calculated on return
        # This can be re-implemented at the cost structure level if needed

        upfront_total = 0
        upfront_charges = []

        if False:  # Disabled for now
            # Calculate and charge known costs upfront
            upfront_subtotal = 0

            # Get cost components
            components = db.query(CostComponent).filter(
                CostComponent.structure_id == rental.cost_structure_id
            ).all()

            # Calculate duration if we have an end date
            duration_known = rental.due_date is not None
            if duration_known:
                duration_delta = rental.due_date - rental_start
                hours = duration_delta.total_seconds() / 3600
                days = duration_delta.total_seconds() / 86400
                weeks = days / 7
                months = days / 30

            for component in components:
                component_cost = 0
                quantity = 0
                can_charge_now = False

                if component.unit_type == 'fixed':
                    # Fixed costs are always known
                    quantity = 1
                    component_cost = component.rate
                    can_charge_now = True
                elif duration_known:
                    # Time-based costs can be charged if duration is known
                    if component.unit_type == 'per_hour':
                        quantity = hours
                        component_cost = component.rate * hours
                        can_charge_now = True
                    elif component.unit_type == 'per_day':
                        quantity = days
                        component_cost = component.rate * days
                        can_charge_now = True
                    elif component.unit_type == 'per_week':
                        quantity = weeks
                        component_cost = component.rate * weeks
                        can_charge_now = True
                    elif component.unit_type == 'per_month':
                        quantity = months
                        component_cost = component.rate * months
                        can_charge_now = True

                # Per-recharge and per-kwh costs cannot be charged upfront
                # They will be charged at return time

                if can_charge_now and component_cost > 0:
                    upfront_charges.append({
                        "component_name": component.component_name,
                        "unit_type": component.unit_type,
                        "rate": float(component.rate),
                        "quantity": round(quantity, 2),
                        "amount": round(component_cost, 2)
                    })
                    upfront_subtotal += component_cost

            # Apply VAT to upfront charges
            hub = db.query(SolarHub).filter(SolarHub.hub_id == user.hub_id).first()
            vat_percentage = hub.vat_percentage if (hub and hasattr(hub, 'vat_percentage') and hub.vat_percentage is not None) else 15.0
            upfront_vat = upfront_subtotal * (vat_percentage / 100)
            upfront_total = upfront_subtotal + upfront_vat

            # Create charge transaction if there are upfront costs
            if upfront_total > 0:
                # Get or create user account
                user_account = db.query(UserAccount).filter(UserAccount.user_id == rental.user_id).first()
                if not user_account:
                    user_account = UserAccount(user_id=rental.user_id, balance=0)
                    db.add(user_account)
                    db.flush()

                # Create charge description
                charge_description = f"Battery Rental #{new_rental.rental_id} - Upfront charges"
                if upfront_charges:
                    charge_description += f" ({', '.join([c['component_name'] for c in upfront_charges])})"

                # Create charge transaction (credit to account = debt owed)
                user_account.balance += upfront_total  # Increase balance = increase debt
                charge_transaction = AccountTransaction(
                    account_id=user_account.account_id,
                    rental_id=None,  # This is for old Rental model, not BatteryRental
                    transaction_type='credit',
                    amount=upfront_total,
                    balance_after=user_account.balance,
                    description=charge_description
                )
                db.add(charge_transaction)

        db.commit()
        db.refresh(new_rental)

        return {
            "message": "Battery rental created successfully",
            "rental_id": new_rental.rental_id,
            "user_id": new_rental.user_id,
            "hub_id": new_rental.hub_id,
            "battery_ids": rental.battery_ids,
            "rental_start_date": new_rental.start_date.isoformat(),
            "rental_end_date": new_rental.end_date.isoformat() if new_rental.end_date else None,
            "status": new_rental.status,
            "deposit_paid": float(new_rental.deposit_amount),
            "cost_structure_id": new_rental.cost_structure_id,
            "upfront_charges": None  # Upfront charging disabled
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error creating battery rental: {str(e)}")

@app.get("/battery-rentals",
    tags=["Battery Rentals"],
    summary="List Battery Rentals")
async def list_battery_rentals(
    user_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    hub_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List battery rentals with optional filters"""
    query = db.query(BatteryRental)

    # Hub-based filtering (BatteryRental has hub_id directly)
    if current_user.get('role') == UserRole.USER:
        query = query.filter(BatteryRental.hub_id == current_user.get('hub_id'))
    elif hub_id:
        query = query.filter(BatteryRental.hub_id == hub_id)

    # User filter
    if user_id:
        query = query.filter(BatteryRental.user_id == user_id)

    # Status filter
    if status:
        query = query.filter(BatteryRental.status == status)

    rentals = query.order_by(BatteryRental.start_date.desc()).all()

    result = []
    for rental in rentals:
        user = db.query(User).filter(User.user_id == rental.user_id).first()
        items = db.query(BatteryRentalItem).filter(BatteryRentalItem.rental_id == rental.rental_id).all()

        # Build user object for frontend
        user_data = None
        if user:
            # Get account balance from UserAccount table
            account_balance = 0.0
            if hasattr(user, 'account') and user.account:
                account_balance = float(user.account.balance) if user.account.balance is not None else 0.0

            user_data = {
                "user_id": user.user_id,
                "Name": user.Name,
                "username": user.username,
                "short_id": user.short_id,
                "account_balance": account_balance
            }

        result.append({
            "rental_id": rental.rental_id,
            "rentral_id": rental.rental_id,  # Legacy typo field for frontend compatibility
            "user_id": rental.user_id,
            "user_name": user.Name if user else None,  # Keep for backward compatibility
            "user": user_data,  # Add full user object for frontend
            "hub_id": rental.hub_id,
            "cost_structure_id": rental.cost_structure_id,
            "rental_start_date": rental.start_date.isoformat(),
            "rental_end_date": rental.end_date.isoformat() if rental.end_date else None,
            "actual_return_date": rental.actual_return_date.isoformat() if rental.actual_return_date else None,
            "timestamp_taken": rental.start_date.isoformat(),  # Legacy field mapping
            "due_back": rental.end_date.isoformat() if rental.end_date else None,  # Legacy field mapping
            "deposit_paid": float(rental.deposit_amount),
            "total_cost_calculated": float(rental.final_cost_total) if rental.final_cost_total else (float(rental.estimated_cost_total) if rental.estimated_cost_total else None),
            "total_cost": float(rental.final_cost_total) if rental.final_cost_total else (float(rental.estimated_cost_total) if rental.estimated_cost_total else 0.0),  # Legacy field
            "amount_paid": float(rental.amount_paid) if rental.amount_paid else 0.0,
            "amount_owed": float(rental.amount_owed) if rental.amount_owed is not None else None,
            "payment_status": rental.payment_status if rental.final_cost_total is not None else None,  # Only show payment status for returned rentals with calculated cost
            "rental_status": rental.status,
            "status": rental.status,  # Add status field for frontend
            "battery_id": items[0].battery_id if items else None,  # First battery for list view
            "battery_count": len(items),
            "rental_type": "battery"  # Add type for frontend routing
        })

    return result

@app.get("/battery-rentals/{rental_id}",
    tags=["Battery Rentals"],
    summary="Get Battery Rental Details")
async def get_battery_rental(
    rental_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get details of a specific battery rental"""
    rental = db.query(BatteryRental).filter(BatteryRental.rental_id == rental_id).first()
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")

    # Authorization check
    if current_user.get('role') == UserRole.USER:
        user = db.query(User).filter(User.user_id == rental.user_id).first()
        if user.hub_id != current_user.get('hub_id'):
            raise HTTPException(status_code=403, detail="Access denied")

    # Get rental items (batteries)
    items = db.query(BatteryRentalItem).filter(BatteryRentalItem.rental_id == rental_id).all()
    batteries = []
    for item in items:
        battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == item.battery_id).first()
        batteries.append({
            "battery_id": battery.battery_id,
            "short_id": battery.short_id,
            "capacity_wh": battery.battery_capacity_wh,
            "status": battery.status,
            "added_at": item.added_at.isoformat(),
            "returned_at": item.returned_at.isoformat() if item.returned_at else None
        })

    # Get cost structure details if available
    cost_structure_data = None
    if rental.cost_structure_id:
        cost_structure = db.query(CostStructure).filter(
            CostStructure.structure_id == rental.cost_structure_id
        ).first()

        if cost_structure:
            # Get components for this structure
            components = db.query(CostComponent).filter(
                CostComponent.structure_id == cost_structure.structure_id
            ).order_by(CostComponent.sort_order).all()

            cost_structure_data = {
                "structure_id": cost_structure.structure_id,
                "name": cost_structure.name,
                "description": cost_structure.description,
                "components": [{
                    "component_name": comp.component_name,
                    "unit_type": comp.unit_type,
                    "rate": float(comp.rate),
                    "is_calculated_on_return": comp.is_calculated_on_return,
                    "late_fee_action": comp.late_fee_action,
                    "late_fee_rate": float(comp.late_fee_rate) if comp.late_fee_rate is not None else None,
                    "late_fee_grace_days": comp.late_fee_grace_days
                } for comp in components]
            }

    return {
        "rental_id": rental.rental_id,
        "rentral_id": rental.rental_id,  # Legacy typo field for frontend compatibility
        "user_id": rental.user_id,
        "hub_id": rental.hub_id,
        "cost_structure_id": rental.cost_structure_id,
        "cost_structure": cost_structure_data,
        "rental_start_date": rental.start_date.isoformat(),
        "rental_end_date": rental.end_date.isoformat() if rental.end_date else None,
        "actual_return_date": rental.actual_return_date.isoformat() if rental.actual_return_date else None,
        "deposit_paid": float(rental.deposit_amount),
        "deposit_amount": float(rental.deposit_amount),
        "total_cost_calculated": float(rental.final_cost_total) if rental.final_cost_total else (float(rental.estimated_cost_total) if rental.estimated_cost_total else None),
        "amount_paid": float(rental.amount_paid) if rental.amount_paid else 0.0,
        "amount_owed": float(rental.amount_owed) if rental.amount_owed is not None else None,
        "payment_status": rental.payment_status if rental.final_cost_total is not None else None,  # Only show payment status for returned rentals with calculated cost
        "rental_status": rental.status,
        "rental_type": "battery",
        "batteries": batteries
    }

@app.post("/battery-rentals/{rental_id}/return",
    tags=["Battery Rentals"],
    summary="Return Batteries")
async def return_batteries(
    rental_id: int,
    return_data: BatteryRentalReturn,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Return batteries from a rental"""
    if current_user.get('role') == UserRole.DATA_ADMIN:
        raise HTTPException(status_code=403, detail="Data admins cannot process returns")

    try:
        rental = db.query(BatteryRental).filter(BatteryRental.rental_id == rental_id).first()
        if not rental:
            raise HTTPException(status_code=404, detail="Rental not found")

        # Authorization check
        if current_user.get('role') == UserRole.USER:
            user = db.query(User).filter(User.user_id == rental.user_id).first()
            if user.hub_id != current_user.get('hub_id'):
                raise HTTPException(status_code=403, detail="Access denied")

        # Use actual_return_date if provided, otherwise return_date, otherwise now
        return_date = return_data.actual_return_date or return_data.return_date or datetime.now(timezone.utc)

        # Get items to return
        if return_data.battery_ids:
            items = db.query(BatteryRentalItem).filter(
                BatteryRentalItem.rental_id == rental_id,
                BatteryRentalItem.battery_id.in_(return_data.battery_ids),
                BatteryRentalItem.returned_at.is_(None)
            ).all()
        else:
            # Return all unreturned batteries
            items = db.query(BatteryRentalItem).filter(
                BatteryRentalItem.rental_id == rental_id,
                BatteryRentalItem.returned_at.is_(None)
            ).all()

        if not items:
            # Check if rental has any items at all
            all_items = db.query(BatteryRentalItem).filter(
                BatteryRentalItem.rental_id == rental_id
            ).all()

            if not all_items:
                raise HTTPException(status_code=400, detail="This rental has no batteries associated with it")
            else:
                # All items have been returned
                returned_count = len([item for item in all_items if item.returned_at is not None])
                raise HTTPException(
                    status_code=400,
                    detail=f"All batteries in this rental have already been returned ({returned_count} battery/batteries returned)"
                )

        # Mark batteries as returned and update battery status
        for item in items:
            item.returned_at = return_date

            # Mark battery as available again
            battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == item.battery_id).first()
            if battery:
                battery.status = 'available'

        # Flush changes so the database reflects updated returned_at values
        db.flush()

        # Check if all batteries returned
        remaining = db.query(BatteryRentalItem).filter(
            BatteryRentalItem.rental_id == rental_id,
            BatteryRentalItem.returned_at.is_(None)
        ).count()

        if remaining == 0:
            rental.actual_return_date = return_date
            rental.status = 'returned'

        # Handle payment recording
        total_payment_collected = 0
        payment_transactions = []

        if return_data.collect_payment or return_data.payment_amount or return_data.credit_applied:
            # Get or create user account
            user_account = db.query(UserAccount).filter(UserAccount.user_id == rental.user_id).first()
            if not user_account:
                user_account = UserAccount(user_id=rental.user_id, balance=0)
                db.add(user_account)
                db.flush()

            # Use helper function to record payment
            total_payment_collected, payment_transactions = record_rental_payment(
                rental=rental,
                user_account=user_account,
                payment_amount=return_data.payment_amount,
                credit_applied=return_data.credit_applied,
                payment_type=return_data.payment_type or 'cash',
                payment_notes=return_data.payment_notes,
                db=db
            )

        # Add condition/return notes
        notes_content = return_data.return_notes or return_data.condition_notes
        if notes_content:
            note = Note(content=f"Return notes: {notes_content}")
            db.add(note)
            db.flush()
            rental.notes.append(note)

        # Auto-calculate cost if all batteries returned and cost not yet calculated
        if remaining == 0 and rental.final_cost_total is None:
            # Calculate cost automatically
            cost_structure = db.query(CostStructure).filter(
                CostStructure.structure_id == rental.cost_structure_id
            ).first()

            if cost_structure:
                # Calculate actual duration
                start_date = rental.start_date
                if isinstance(start_date, str):
                    start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                elif start_date and not start_date.tzinfo:
                    start_date = start_date.replace(tzinfo=timezone.utc)

                return_date_for_calc = rental.actual_return_date
                if isinstance(return_date_for_calc, str):
                    return_date_for_calc = datetime.fromisoformat(return_date_for_calc.replace('Z', '+00:00'))
                elif return_date_for_calc and not return_date_for_calc.tzinfo:
                    return_date_for_calc = return_date_for_calc.replace(tzinfo=timezone.utc)

                duration_delta = return_date_for_calc - start_date
                actual_hours = duration_delta.total_seconds() / 3600
                actual_days = duration_delta.total_seconds() / 86400
                actual_weeks = actual_days / 7
                actual_months = actual_days / 30
                actual_years = actual_days / 365

                # Get recharges used
                total_recharges = rental.recharges_used or 0

                # Calculate costs
                subtotal = 0
                components = db.query(CostComponent).filter(
                    CostComponent.structure_id == rental.cost_structure_id
                ).order_by(CostComponent.sort_order).all()

                for comp in components:
                    component_cost = 0

                    if comp.unit_type == 'flat':
                        component_cost = comp.rate
                    elif comp.unit_type == 'per_hour':
                        component_cost = comp.rate * actual_hours
                    elif comp.unit_type == 'per_day':
                        component_cost = comp.rate * actual_days
                    elif comp.unit_type == 'per_week':
                        component_cost = comp.rate * actual_weeks
                    elif comp.unit_type == 'per_month':
                        component_cost = comp.rate * actual_months
                    elif comp.unit_type == 'per_year':
                        component_cost = comp.rate * actual_years
                    elif comp.unit_type == 'per_recharge':
                        component_cost = comp.rate * total_recharges

                    subtotal += component_cost

                # Apply VAT
                hub = db.query(SolarHub).filter(SolarHub.hub_id == rental.hub_id).first()
                vat_percentage = hub.vat_percentage if (hub and hasattr(hub, 'vat_percentage') and hub.vat_percentage is not None) else 0.0
                vat_amount = subtotal * (vat_percentage / 100)
                total_cost = subtotal + vat_amount

                # Save to rental
                rental.final_cost_before_vat = subtotal
                rental.final_vat = vat_amount
                rental.final_cost_total = total_cost

        # Update payment status using helper function
        update_rental_payment_status(rental, total_payment_collected)

        db.commit()

        return {
            "message": "Batteries returned successfully",
            "rental_id": rental_id,
            "returned_battery_ids": [item.battery_id for item in items],
            "return_date": return_date.isoformat(),
            "rental_status": rental.status,
            "remaining_batteries": remaining,
            "payment_collected": total_payment_collected,
            "payment_transactions": payment_transactions
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error returning batteries: {str(e)}")

@app.post("/battery-rentals/{rental_id}/payment",
    tags=["Battery Rentals"],
    summary="Record Payment for Battery Rental")
async def record_battery_rental_payment(
    rental_id: int,
    payment_data: BatteryRentalPayment,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Record a payment for a battery rental (typically after return).
    Updates amount_paid, amount_owed, and payment_status.
    """
    if current_user.get('role') == UserRole.DATA_ADMIN:
        raise HTTPException(status_code=403, detail="Data admins cannot modify rentals")

    try:
        rental = db.query(BatteryRental).filter(BatteryRental.rental_id == rental_id).first()
        if not rental:
            raise HTTPException(status_code=404, detail="Rental not found")

        # Authorization check
        if current_user.get('role') == UserRole.USER:
            user = db.query(User).filter(User.user_id == rental.user_id).first()
            if user.hub_id != current_user.get('hub_id'):
                raise HTTPException(status_code=403, detail="Access denied")

        # Auto-calculate cost if not yet calculated (for rentals returned before this feature was added)
        if rental.final_cost_total is None:
            # Check if all batteries have been returned
            all_items = db.query(BatteryRentalItem).filter(
                BatteryRentalItem.rental_id == rental_id
            ).all()

            unreturned_items = [item for item in all_items if item.returned_at is None]

            if unreturned_items:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot calculate cost: some batteries have not been returned yet"
                )

            # Calculate cost automatically
            cost_structure = db.query(CostStructure).filter(
                CostStructure.structure_id == rental.cost_structure_id
            ).first()

            if not cost_structure:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot calculate cost: no cost structure assigned to rental"
                )

            # Use the actual return date from the last returned item
            return_dates = [item.returned_at for item in all_items if item.returned_at]
            if not return_dates:
                raise HTTPException(status_code=400, detail="No return dates found")

            return_date_for_calc = max(return_dates)  # Use latest return date
            if isinstance(return_date_for_calc, str):
                return_date_for_calc = datetime.fromisoformat(return_date_for_calc.replace('Z', '+00:00'))
            elif return_date_for_calc and not return_date_for_calc.tzinfo:
                return_date_for_calc = return_date_for_calc.replace(tzinfo=timezone.utc)

            # Calculate duration
            start_date = rental.start_date
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            elif start_date and not start_date.tzinfo:
                start_date = start_date.replace(tzinfo=timezone.utc)

            duration_delta = return_date_for_calc - start_date
            actual_hours = duration_delta.total_seconds() / 3600
            actual_days = duration_delta.total_seconds() / 86400
            actual_weeks = actual_days / 7
            actual_months = actual_days / 30
            actual_years = actual_days / 365

            # Get recharges
            total_recharges = rental.recharges_used or 0
            if cost_structure.count_initial_checkout_as_recharge and total_recharges == 0:
                total_recharges = 1

            # Calculate costs
            subtotal = 0
            components = db.query(CostComponent).filter(
                CostComponent.structure_id == rental.cost_structure_id
            ).order_by(CostComponent.sort_order).all()

            for comp in components:
                component_cost = 0
                if comp.unit_type == 'flat':
                    component_cost = comp.rate
                elif comp.unit_type == 'per_hour':
                    component_cost = comp.rate * actual_hours
                elif comp.unit_type == 'per_day':
                    component_cost = comp.rate * actual_days
                elif comp.unit_type == 'per_week':
                    component_cost = comp.rate * actual_weeks
                elif comp.unit_type == 'per_month':
                    component_cost = comp.rate * actual_months
                elif comp.unit_type == 'per_year':
                    component_cost = comp.rate * actual_years
                elif comp.unit_type == 'per_recharge':
                    component_cost = comp.rate * total_recharges
                elif comp.unit_type == 'per_kwh':
                    kwh_used = rental.kwh_usage_end - rental.kwh_usage_start if (rental.kwh_usage_end and rental.kwh_usage_start) else 0
                    component_cost = comp.rate * kwh_used

                subtotal += component_cost

            # Apply VAT
            hub = db.query(SolarHub).filter(SolarHub.hub_id == rental.hub_id).first()
            vat_percentage = hub.vat_percentage if (hub and hasattr(hub, 'vat_percentage') and hub.vat_percentage is not None) else 0.0
            vat_amount = subtotal * (vat_percentage / 100)
            total_cost = subtotal + vat_amount

            # Save to rental
            rental.final_cost_total = total_cost
            rental.final_cost_subtotal = subtotal
            rental.final_cost_vat = vat_amount
            rental.final_cost_calculated_at = datetime.now(timezone.utc)
            rental.actual_return_date = return_date_for_calc

            db.flush()

        # Get or create user account
        user_account = db.query(UserAccount).filter(UserAccount.user_id == rental.user_id).first()
        if not user_account:
            user_account = UserAccount(user_id=rental.user_id, balance=0)
            db.add(user_account)
            db.flush()

        # Check credit balance if applying credit
        if payment_data.credit_applied and payment_data.credit_applied > 0:
            if user_account.balance < payment_data.credit_applied:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient account credit. Available: {user_account.balance}, Requested: {payment_data.credit_applied}"
                )

        # Use helper function to record payment
        total_payment_collected, payment_transactions = record_rental_payment(
            rental=rental,
            user_account=user_account,
            payment_amount=payment_data.payment_amount,
            credit_applied=payment_data.credit_applied,
            payment_type=payment_data.payment_type,
            payment_notes=payment_data.payment_notes,
            db=db
        )

        # Update payment status using helper function
        update_rental_payment_status(rental, total_payment_collected)

        db.commit()
        db.refresh(rental)

        return {
            "message": "Payment recorded successfully",
            "rental_id": rental_id,
            "payment_collected": total_payment_collected,
            "amount_paid": float(rental.amount_paid),
            "amount_owed": float(rental.amount_owed) if rental.amount_owed is not None else None,
            "payment_status": rental.payment_status,
            "payment_transactions": payment_transactions
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error recording payment: {str(e)}")

@app.post("/battery-rentals/{rental_id}/add-battery",
    tags=["Battery Rentals"],
    summary="Add Battery to Rental")
async def add_battery_to_rental(
    rental_id: int,
    add_data: BatteryRentalAddBattery,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Add batteries to an existing rental"""
    if current_user.get('role') == UserRole.DATA_ADMIN:
        raise HTTPException(status_code=403, detail="Data admins cannot modify rentals")

    try:
        rental = db.query(BatteryRental).filter(BatteryRental.rental_id == rental_id).first()
        if not rental:
            raise HTTPException(status_code=404, detail="Rental not found")

        if rental.rental_status != 'active':
            raise HTTPException(status_code=400, detail="Can only add batteries to active rentals")

        # Check batteries
        for battery_id in add_data.battery_ids:
            battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == battery_id).first()
            if not battery:
                raise HTTPException(status_code=404, detail=f"Battery {battery_id} not found")

            # Check availability
            existing = db.query(BatteryRentalItem).join(BatteryRental).filter(
                BatteryRentalItem.battery_id == battery_id,
                BatteryRentalItem.returned_at.is_(None),
                BatteryRental.rental_status == 'active'
            ).first()
            if existing:
                raise HTTPException(status_code=409, detail=f"Battery {battery_id} is already rented")

            # Add to rental
            item = BatteryRentalItem(
                rental_id=rental_id,
                battery_id=battery_id,
                rental_start_date=datetime.now(timezone.utc)
            )
            db.add(item)

        db.commit()

        return {
            "message": "Batteries added successfully",
            "rental_id": rental_id,
            "added_battery_ids": add_data.battery_ids
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error adding batteries: {str(e)}")

@app.post("/battery-rentals/{rental_id}/recharge",
    tags=["Battery Rentals"],
    summary="Record Battery Recharge")
async def record_recharge(
    rental_id: int,
    recharge_data: BatteryRentalRecharge,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Record a battery recharge during rental"""
    if current_user.get('role') == UserRole.DATA_ADMIN:
        raise HTTPException(status_code=403, detail="Data admins cannot record recharges")

    try:
        # Find the rental item
        item = db.query(BatteryRentalItem).filter(
            BatteryRentalItem.rental_id == rental_id,
            BatteryRentalItem.battery_id == recharge_data.battery_id,
            BatteryRentalItem.return_date.is_(None)
        ).first()

        if not item:
            raise HTTPException(status_code=404, detail="Battery not found in active rental")

        # Increment recharge count
        item.recharge_count = (item.recharge_count or 0) + 1
        item.last_recharge_date = recharge_data.recharge_date or datetime.now(timezone.utc)

        # Add note if provided
        if recharge_data.notes:
            rental = db.query(BatteryRental).filter(BatteryRental.rental_id == rental_id).first()
            note = Note(content=f"Recharge #{item.recharge_count}: {recharge_data.notes}")
            db.add(note)
            db.flush()
            rental.notes.append(note)

        db.commit()

        return {
            "message": "Recharge recorded successfully",
            "rental_id": rental_id,
            "battery_id": recharge_data.battery_id,
            "recharge_count": item.recharge_count,
            "recharge_date": item.last_recharge_date.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error recording recharge: {str(e)}")

@app.get("/battery-rentals/{rental_id}/calculate-return-cost",
    tags=["Battery Rentals"],
    summary="Calculate Final Cost at Return",
    description="Calculate the final cost for a battery rental based on actual usage (days, recharges, kWh, etc.)")
async def calculate_battery_rental_return_cost(
    rental_id: int,
    actual_return_date: Optional[str] = Query(None, description="Actual return date (ISO format)"),
    kwh_usage: Optional[float] = Query(None, description="Actual kWh used"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Calculate final cost for a battery rental at return time based on:
    - Actual duration (rental start to return date)
    - Number of recharges
    - Actual kWh usage (if provided)
    - Cost structure components (per_day, per_hour, per_recharge, per_kwh, fixed, etc.)

    Returns breakdown of all cost components and final total.
    """
    rental = db.query(BatteryRental).filter(BatteryRental.rental_id == rental_id).first()
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")

    # Authorization check
    if current_user.get('role') == UserRole.USER:
        if rental.hub_id != current_user.get('hub_id'):
            raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.get('role') == UserRole.DATA_ADMIN:
        raise HTTPException(status_code=403, detail="Data admins cannot access rental details")

    # Parse actual return date or use now
    if actual_return_date:
        try:
            return_date = datetime.fromisoformat(actual_return_date.replace('Z', '+00:00'))
        except:
            return_date = datetime.now(timezone.utc)
    else:
        return_date = datetime.now(timezone.utc)

    # Calculate actual duration
    start_date = rental.start_date
    if isinstance(start_date, str):
        start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
    elif start_date and not start_date.tzinfo:
        start_date = start_date.replace(tzinfo=timezone.utc)

    duration_delta = return_date - start_date
    actual_hours = duration_delta.total_seconds() / 3600
    actual_days = duration_delta.total_seconds() / 86400
    actual_weeks = actual_days / 7
    actual_months = actual_days / 30  # Approximate

    # Get all battery items in this rental
    items = db.query(BatteryRentalItem).filter(
        BatteryRentalItem.rental_id == rental_id
    ).all()

    # Get cost structure first (needed to determine recharge count)
    cost_structure = None
    if rental.cost_structure_id:
        cost_structure = db.query(CostStructure).filter(
            CostStructure.structure_id == rental.cost_structure_id
        ).first()

    # Get total recharges from the rental (tracked at rental level, not per item)
    total_recharges = rental.recharges_used or 0

    # If cost structure counts initial checkout as recharge and there are no recorded recharges,
    # count it as 1 (handles rentals created before this setting was enabled)
    if cost_structure and cost_structure.count_initial_checkout_as_recharge and total_recharges == 0:
        total_recharges = 1

    # Get cost structure and calculate costs
    cost_breakdown = []
    calculation_steps = []  # Detailed step-by-step explanations
    subtotal = 0
    cost_structure_info = None

    if cost_structure:
        # Store cost structure information for display
        cost_structure_info = {
            "structure_id": cost_structure.structure_id,
            "name": cost_structure.name,
            "description": cost_structure.description or "No description available",
            "item_type": cost_structure.item_type,
            "item_reference": cost_structure.item_reference,
            "count_initial_checkout_as_recharge": cost_structure.count_initial_checkout_as_recharge
        }

        components = db.query(CostComponent).filter(
            CostComponent.structure_id == cost_structure.structure_id
        ).all()

        for component in components:
            component_cost = 0
            quantity = 0
            calculation_explanation = ""

            if component.unit_type == 'per_hour':
                quantity = actual_hours
                component_cost = component.rate * actual_hours
                calculation_explanation = f"{component.component_name}: {round(quantity, 2)} hours × R{component.rate:.2f}/hour = R{component_cost:.2f}"
            elif component.unit_type == 'per_day':
                quantity = actual_days
                component_cost = component.rate * actual_days
                calculation_explanation = f"{component.component_name}: {round(quantity, 2)} days × R{component.rate:.2f}/day = R{component_cost:.2f}"
            elif component.unit_type == 'per_week':
                quantity = actual_weeks
                component_cost = component.rate * actual_weeks
                calculation_explanation = f"{component.component_name}: {round(quantity, 2)} weeks × R{component.rate:.2f}/week = R{component_cost:.2f}"
            elif component.unit_type == 'per_month':
                quantity = actual_months
                component_cost = component.rate * actual_months
                calculation_explanation = f"{component.component_name}: {round(quantity, 2)} months × R{component.rate:.2f}/month = R{component_cost:.2f}"
            elif component.unit_type == 'per_recharge':
                quantity = total_recharges
                component_cost = component.rate * total_recharges
                # Add note if initial checkout counted as a recharge
                recharge_note = ""
                if cost_structure.count_initial_checkout_as_recharge and total_recharges >= 1:
                    recharge_note = " (includes initial checkout)"
                calculation_explanation = f"{component.component_name}: {int(quantity)} recharge(s){recharge_note} × R{component.rate:.2f}/recharge = R{component_cost:.2f}"
            elif component.unit_type == 'per_kwh':
                # Use provided kWh or try to calculate from battery data
                kwh_used = kwh_usage
                if kwh_used is None and len(items) > 0:
                    # Try to get from first battery's latest data
                    battery_id = items[0].battery_id
                    latest_data = db.query(LiveData).filter(
                        LiveData.battery_id == battery_id
                    ).order_by(LiveData.timestamp.desc()).first()

                    if latest_data and latest_data.amp_hours_consumed:
                        voltage = latest_data.voltage or 48
                        kwh_used = (latest_data.amp_hours_consumed * voltage) / 1000

                if kwh_used is not None and kwh_used > 0:
                    quantity = kwh_used
                    component_cost = component.rate * kwh_used
                    calculation_explanation = f"{component.component_name}: {round(quantity, 2)} kWh × R{component.rate:.2f}/kWh = R{component_cost:.2f}"
            elif component.unit_type == 'fixed':
                quantity = 1
                component_cost = component.rate
                calculation_explanation = f"{component.component_name}: Fixed charge = R{component_cost:.2f}"

            if quantity > 0 or component.unit_type == 'fixed':
                cost_breakdown.append({
                    "component_name": component.component_name,
                    "unit_type": component.unit_type,
                    "rate": float(component.rate),
                    "quantity": round(quantity, 2),
                    "amount": round(component_cost, 2),
                    "explanation": calculation_explanation
                })

                if calculation_explanation:
                    calculation_steps.append(calculation_explanation)

                subtotal += component_cost

    # Get hub VAT
    vat_percentage = 15.0
    hub = db.query(SolarHub).filter(SolarHub.hub_id == rental.hub_id).first()
    if hub and hasattr(hub, 'vat_percentage') and hub.vat_percentage is not None:
        vat_percentage = hub.vat_percentage

    vat_amount = subtotal * (vat_percentage / 100)
    total = subtotal + vat_amount

    # Get user account balance
    user_account = db.query(UserAccount).filter(UserAccount.user_id == rental.user_id).first()
    account_balance = user_account.balance if user_account else 0

    # Calculate amounts
    deposit_paid = rental.deposit_amount or 0
    amount_still_owed = max(0, total - deposit_paid)
    amount_after_credit = max(0, amount_still_owed - account_balance)

    # Ensure end_date is timezone-aware for comparison
    end_date_aware = rental.end_date
    if end_date_aware and not end_date_aware.tzinfo:
        end_date_aware = end_date_aware.replace(tzinfo=timezone.utc)

    return {
        "rental_id": rental_id,
        "rental_unique_id": rental_id,  # Use rental_id as the unique identifier for battery rentals
        "cost_structure": cost_structure_info,  # Details about which cost structure is being used
        "calculation_steps": calculation_steps,  # Step-by-step breakdown for customer
        "duration": {
            "start_date": start_date.isoformat(),
            "return_date": return_date.isoformat(),
            "actual_hours": round(actual_hours, 2),
            "actual_days": round(actual_days, 2),
            "scheduled_return_date": end_date_aware.isoformat() if end_date_aware else None,
            "is_late": return_date > end_date_aware if end_date_aware else False
        },
        "kwh_usage": {
            "start_reading": None,
            "end_reading": kwh_usage,
            "total_used": kwh_usage
        },
        "usage_stats": {
            "total_recharges": total_recharges,
            "battery_count": len(items)
        },
        "cost_breakdown": cost_breakdown,
        "subtotal": round(subtotal, 2),
        "vat_percentage": vat_percentage,
        "vat_amount": round(vat_amount, 2),
        "total": round(total, 2),
        "original_estimate": 0,  # Not tracked for battery rentals
        "cost_difference": round(total, 2),  # Difference from estimate (0)
        "payment_status": {
            "amount_paid_so_far": round(deposit_paid, 2),
            "amount_still_owed": round(amount_still_owed, 2),
            "user_account_balance": round(account_balance, 2),
            "amount_after_credit": round(amount_after_credit, 2),
            "can_pay_with_credit": account_balance >= amount_still_owed
        },
        "subscription": None  # Subscription support not yet implemented for battery rentals
    }

@app.post("/admin/battery-rentals/{rental_id}/recalculate-cost",
    tags=["Battery Rentals", "Admin"],
    summary="Recalculate Cost for Returned Rental (Admin Only)")
async def recalculate_rental_cost(
    rental_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Admin endpoint to recalculate and save the final cost for an already-returned rental.
    Useful for fixing rentals that were returned before cost calculation was working properly.
    """
    # Only admins can recalculate costs
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can recalculate costs")

    rental = db.query(BatteryRental).filter(BatteryRental.rental_id == rental_id).first()
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")

    # Must be a returned rental
    if rental.status != 'returned' or not rental.actual_return_date:
        raise HTTPException(status_code=400, detail="Rental must be returned to recalculate cost")

    # Get cost structure
    if not rental.cost_structure_id:
        raise HTTPException(status_code=400, detail="Rental has no cost structure")

    cost_structure = db.query(CostStructure).filter(
        CostStructure.structure_id == rental.cost_structure_id
    ).first()
    if not cost_structure:
        raise HTTPException(status_code=404, detail="Cost structure not found")

    # Calculate actual duration
    start_date = rental.start_date
    if isinstance(start_date, str):
        start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
    elif start_date and not start_date.tzinfo:
        start_date = start_date.replace(tzinfo=timezone.utc)

    return_date = rental.actual_return_date
    if isinstance(return_date, str):
        return_date = datetime.fromisoformat(return_date.replace('Z', '+00:00'))
    elif return_date and not return_date.tzinfo:
        return_date = return_date.replace(tzinfo=timezone.utc)

    duration_delta = return_date - start_date
    actual_hours = duration_delta.total_seconds() / 3600
    actual_days = duration_delta.total_seconds() / 86400
    actual_weeks = actual_days / 7
    actual_months = actual_days / 30
    actual_years = actual_days / 365

    # Get recharges used
    total_recharges = rental.recharges_used or 0

    # Calculate costs
    subtotal = 0
    components = db.query(CostComponent).filter(
        CostComponent.structure_id == rental.cost_structure_id
    ).order_by(CostComponent.sort_order).all()

    for comp in components:
        component_cost = 0

        if comp.unit_type == 'flat':
            component_cost = comp.rate
        elif comp.unit_type == 'per_hour':
            component_cost = comp.rate * actual_hours
        elif comp.unit_type == 'per_day':
            component_cost = comp.rate * actual_days
        elif comp.unit_type == 'per_week':
            component_cost = comp.rate * actual_weeks
        elif comp.unit_type == 'per_month':
            component_cost = comp.rate * actual_months
        elif comp.unit_type == 'per_year':
            component_cost = comp.rate * actual_years
        elif comp.unit_type == 'per_recharge':
            component_cost = comp.rate * total_recharges

        subtotal += component_cost

    # Apply VAT
    user = db.query(User).filter(User.user_id == rental.user_id).first()
    hub = db.query(SolarHub).filter(SolarHub.hub_id == rental.hub_id).first()
    vat_percentage = hub.vat_percentage if (hub and hasattr(hub, 'vat_percentage') and hub.vat_percentage is not None) else 0.0
    vat_amount = subtotal * (vat_percentage / 100)
    total = subtotal + vat_amount

    # Save to rental
    rental.final_cost_before_vat = subtotal
    rental.final_vat = vat_amount
    rental.final_cost_total = total

    db.commit()
    db.refresh(rental)

    return {
        "success": True,
        "message": "Cost recalculated successfully",
        "rental_id": rental_id,
        "days_rented": round(actual_days, 2),
        "recharges_used": total_recharges,
        "subtotal": round(subtotal, 2),
        "vat": round(vat_amount, 2),
        "total": round(total, 2),
        "vat_percentage": vat_percentage
    }

# ============================================================================
# NEW PUE RENTAL ENDPOINTS
# ============================================================================

@app.post("/pue-rentals",
    tags=["PUE Rentals"],
    summary="Create PUE Rental",
    description="""
    ## Create a New PUE Rental

    Creates a new PUE rental with optional pay-to-own support.

    ### Permissions:
    - **ADMIN**: Can create rentals
    - **SUPERADMIN**: Can create rentals
    - **USER**: Can create rentals for their own hub

    ### Features:
    - Regular rental or pay-to-own
    - Payment tracking
    - Inspection scheduling
    - Ownership transfer on completion

    ### Returns:
    - Created rental information
    """,
    response_description="Created PUE rental details")
async def create_pue_rental(
    rental: PUERentalCreateNew,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new PUE rental"""
    if current_user.get('role') == UserRole.DATA_ADMIN:
        raise HTTPException(status_code=403, detail="Data admins cannot create rentals")

    try:
        # Verify user and PUE exist
        user = db.query(User).filter(User.user_id == rental.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        pue = db.query(ProductiveUseEquipment).filter(ProductiveUseEquipment.pue_id == rental.pue_id).first()
        if not pue:
            raise HTTPException(status_code=404, detail="PUE not found")

        # Check if PUE is available
        if pue.status != 'available':
            raise HTTPException(status_code=409, detail=f"PUE is not available (status: {pue.status})")

        # Authorization check
        if current_user.get('role') == UserRole.USER:
            if user.hub_id != current_user.get('hub_id'):
                raise HTTPException(status_code=403, detail="Access denied")

        # Create rental
        rental_start = rental.rental_start_date or datetime.now(timezone.utc)

        # Calculate next payment due date if recurring payments are enabled
        next_payment_due = None
        if rental.has_recurring_payment and rental.recurring_payment_frequency:
            from datetime import timedelta
            if rental.recurring_payment_frequency == 'daily':
                next_payment_due = rental_start + timedelta(days=1)
            elif rental.recurring_payment_frequency == 'weekly':
                next_payment_due = rental_start + timedelta(weeks=1)
            elif rental.recurring_payment_frequency == 'monthly':
                next_payment_due = rental_start + timedelta(days=30)

        new_rental = PUERental(
            user_id=rental.user_id,
            pue_id=rental.pue_id,
            timestamp_taken=rental_start,
            cost_structure_id=rental.cost_structure_id,
            is_pay_to_own=rental.is_pay_to_own,
            total_item_cost=rental.pay_to_own_price,
            total_paid_towards_ownership=rental.initial_payment or 0.0,
            deposit_amount=rental.deposit_amount,
            is_active=True,
            has_recurring_payment=rental.has_recurring_payment,
            recurring_payment_frequency=rental.recurring_payment_frequency,
            next_payment_due_date=next_payment_due
        )
        db.add(new_rental)
        db.flush()

        # Create account transactions for deposit and initial payment
        if rental.deposit_amount and rental.deposit_amount > 0:
            # Get or create user account
            user_account = db.query(UserAccount).filter(UserAccount.user_id == rental.user_id).first()
            if not user_account:
                user_account = UserAccount(
                    user_id=rental.user_id,
                    balance=0,
                    total_spent=0,
                    total_owed=0
                )
                db.add(user_account)
                db.flush()

            # Record deposit transaction (deposits are credits held, not spent)
            deposit_transaction = AccountTransaction(
                account_id=user_account.account_id,
                transaction_type='pue_deposit',
                amount=-rental.deposit_amount,  # Negative = money held as deposit
                balance_after=user_account.balance - rental.deposit_amount,
                description=f'Deposit for PUE rental #{new_rental.pue_rental_id}',
                payment_method=rental.payment_type or 'cash',
                created_at=rental_start
            )
            db.add(deposit_transaction)
            user_account.balance -= rental.deposit_amount
            user_account.total_owed += rental.deposit_amount

        # If pay-to-own, create ledger
        if rental.is_pay_to_own and rental.pay_to_own_price:
            ledger = PUEPayToOwnLedger(
                pue_rental_id=new_rental.pue_rental_id,
                total_price=rental.pay_to_own_price,
                amount_paid=rental.initial_payment or 0.0,
                ownership_transferred=False
            )
            db.add(ledger)
            db.flush()

            # Record initial payment transaction
            if rental.initial_payment and rental.initial_payment > 0:
                transaction = PUEPayToOwnTransaction(
                    ledger_id=ledger.ledger_id,
                    payment_date=rental_start,
                    payment_amount=rental.initial_payment,
                    payment_type='Cash',
                    notes='Initial payment'
                )
                db.add(transaction)

        # Update PUE status
        pue.status = 'rented'

        # Add notes if provided
        if rental.notes:
            for note_content in rental.notes:
                note = Note(content=note_content)
                db.add(note)
                db.flush()
                new_rental.notes.append(note)

        db.commit()
        db.refresh(new_rental)

        return {
            "message": "PUE rental created successfully",
            "pue_rental_id": new_rental.pue_rental_id,
            "user_id": new_rental.user_id,
            "pue_id": new_rental.pue_id,
            "rental_start_date": new_rental.timestamp_taken.isoformat(),
            "is_pay_to_own": new_rental.is_pay_to_own,
            "pay_to_own_price": float(new_rental.total_item_cost) if new_rental.total_item_cost else None,
            "amount_paid": float(new_rental.total_paid_towards_ownership) if new_rental.total_paid_towards_ownership else 0.0,
            "deposit_amount": float(new_rental.deposit_amount) if new_rental.deposit_amount else 0.0,
            "status": 'active' if new_rental.is_active else 'inactive'
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error creating PUE rental: {str(e)}")

@app.get("/pue-rentals",
    tags=["PUE Rentals"],
    summary="List PUE Rentals")
async def list_pue_rentals(
    user_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    hub_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List PUE rentals with optional filters"""
    query = db.query(PUERental)

    # Hub-based filtering
    if current_user.get('role') == UserRole.USER:
        query = query.join(User, PUERental.user_id == User.user_id).filter(User.hub_id == current_user.get('hub_id'))
    elif hub_id:
        query = query.join(User, PUERental.user_id == User.user_id).filter(User.hub_id == hub_id)

    # User filter
    if user_id:
        query = query.filter(PUERental.user_id == user_id)

    # Status filter (PUERental uses is_active, not status)
    if status:
        if status == 'active':
            query = query.filter(PUERental.is_active == True)
        elif status == 'returned':
            query = query.filter(PUERental.is_active == False)
        # 'overdue' status not directly supported in PUERental model

    rentals = query.order_by(PUERental.timestamp_taken.desc()).all()

    result = []
    for rental in rentals:
        user = db.query(User).filter(User.user_id == rental.user_id).first()
        pue = db.query(ProductiveUseEquipment).filter(ProductiveUseEquipment.pue_id == rental.pue_id).first()

        # Get pay-to-own progress if applicable
        pay_to_own_progress = None
        if rental.is_pay_to_own:
            ledger = db.query(PUEPayToOwnLedger).filter(
                PUEPayToOwnLedger.pue_rental_id == rental.pue_rental_id
            ).first()
            if ledger:
                pay_to_own_progress = {
                    "total_price": float(ledger.total_price),
                    "amount_paid": float(ledger.amount_paid),
                    "remaining": float(ledger.total_price - ledger.amount_paid),
                    "ownership_transferred": ledger.ownership_transferred
                }

        # Determine status
        if rental.date_returned:
            status = 'returned'
        elif rental.is_active:
            status = 'active'
        else:
            status = 'inactive'

        # Build user object for frontend
        user_data = None
        if user:
            # Get account balance from UserAccount table
            account_balance = 0.0
            if hasattr(user, 'account') and user.account:
                account_balance = float(user.account.balance) if user.account.balance is not None else 0.0

            user_data = {
                "user_id": user.user_id,
                "Name": user.Name,
                "username": user.username,
                "short_id": user.short_id,
                "account_balance": account_balance
            }

        result.append({
            "pue_rental_id": rental.pue_rental_id,
            "user_id": rental.user_id,
            "user_name": user.Name if user else None,  # Keep for backward compatibility
            "user": user_data,  # Add full user object for frontend
            "pue_id": rental.pue_id,
            "pue_name": pue.name if pue else None,
            "timestamp_taken": rental.timestamp_taken.isoformat(),
            "date_returned": rental.date_returned.isoformat() if rental.date_returned else None,
            "is_pay_to_own": rental.is_pay_to_own,
            "total_item_cost": float(rental.total_item_cost) if rental.total_item_cost else None,
            "total_paid_towards_ownership": float(rental.total_paid_towards_ownership) if rental.total_paid_towards_ownership else 0.0,
            "ownership_percentage": float(rental.ownership_percentage) if rental.ownership_percentage else 0.0,
            "deposit_amount": float(rental.deposit_amount) if rental.deposit_amount else 0.0,
            "is_active": rental.is_active,
            "status": status,
            "pay_to_own_progress": pay_to_own_progress
        })

    return result

@app.get("/pue-rentals/{rental_id}",
    tags=["PUE Rentals"],
    summary="Get PUE Rental Details")
async def get_pue_rental(
    rental_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get details of a specific PUE rental"""
    rental = db.query(PUERental).filter(PUERental.pue_rental_id == rental_id).first()
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")

    # Authorization check
    if current_user.get('role') == UserRole.USER:
        user = db.query(User).filter(User.user_id == rental.user_id).first()
        if user.hub_id != current_user.get('hub_id'):
            raise HTTPException(status_code=403, detail="Access denied")

    # Get PUE details
    pue = db.query(ProductiveUseEquipment).filter(ProductiveUseEquipment.pue_id == rental.pue_id).first()

    # Get cost structure if available
    cost_structure_data = None
    if rental.cost_structure_id:
        cost_structure = db.query(CostStructure).filter(CostStructure.structure_id == rental.cost_structure_id).first()
        if cost_structure:
            # Get cost components
            components = db.query(CostComponent).filter(
                CostComponent.structure_id == rental.cost_structure_id
            ).order_by(CostComponent.component_id).all()

            cost_structure_data = {
                "structure_id": cost_structure.structure_id,
                "name": cost_structure.name,
                "description": cost_structure.description,
                "components": [{
                    "component_id": comp.component_id,
                    "component_name": comp.component_name,
                    "rate": float(comp.rate),
                    "unit_type": comp.unit_type,
                    "late_fee_rate": float(comp.late_fee_rate) if comp.late_fee_rate else None,
                    "late_fee_grace_days": comp.late_fee_grace_days,
                    "late_fee_action": comp.late_fee_action
                } for comp in components]
            }

    # Determine status
    if rental.date_returned:
        status = 'returned'
    elif rental.is_active:
        status = 'active'
    else:
        status = 'inactive'

    return {
        "pue_rental_id": rental.pue_rental_id,
        "user_id": rental.user_id,
        "pue_id": rental.pue_id,
        "pue_name": pue.name if pue else None,
        "timestamp_taken": rental.timestamp_taken.isoformat(),
        "date_returned": rental.date_returned.isoformat() if rental.date_returned else None,
        "is_pay_to_own": rental.is_pay_to_own,
        "total_item_cost": float(rental.total_item_cost) if rental.total_item_cost else None,
        "total_paid_towards_ownership": float(rental.total_paid_towards_ownership) if rental.total_paid_towards_ownership else 0.0,
        "ownership_percentage": float(rental.ownership_percentage) if rental.ownership_percentage else 0.0,
        "deposit_amount": float(rental.deposit_amount) if rental.deposit_amount else 0.0,
        "rental_cost": rental.rental_cost,
        "status": status,
        "is_active": rental.is_active,
        "cost_structure": cost_structure_data
    }

@app.post("/pue-rentals/{rental_id}/payment",
    tags=["PUE Rentals"],
    summary="Record PUE Payment")
async def record_pue_payment(
    rental_id: int,
    payment: PUERentalPayment,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Record a payment for PUE rental (applies to pay-to-own if applicable)"""
    if current_user.get('role') == UserRole.DATA_ADMIN:
        raise HTTPException(status_code=403, detail="Data admins cannot record payments")

    try:
        rental = db.query(PUERental).filter(PUERental.pue_rental_id == rental_id).first()
        if not rental:
            raise HTTPException(status_code=404, detail="Rental not found")

        payment_date = payment.payment_date or datetime.now(timezone.utc)

        # Get or create user account for credit handling
        user_account = db.query(UserAccount).filter(UserAccount.user_id == rental.user_id).first()
        if not user_account:
            user_account = UserAccount(user_id=rental.user_id, balance=0)
            db.add(user_account)
            db.flush()

        # Check credit balance if applying credit
        credit_to_apply = payment.credit_applied or 0
        if credit_to_apply > 0:
            if user_account.balance < credit_to_apply:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient account credit. Available: {user_account.balance}, Requested: {credit_to_apply}"
                )

        # Total payment is cash + credit
        total_payment = payment.payment_amount + credit_to_apply

        # If pay-to-own, update ledger
        if rental.is_pay_to_own:
            ledger = db.query(PUEPayToOwnLedger).filter(
                PUEPayToOwnLedger.pue_rental_id == rental_id
            ).first()

            if not ledger:
                raise HTTPException(status_code=404, detail="Pay-to-own ledger not found")

            # Record transaction
            transaction = PUEPayToOwnTransaction(
                ledger_id=ledger.ledger_id,
                payment_date=payment_date,
                payment_amount=total_payment,
                payment_type=payment.payment_type,
                notes=payment.notes
            )
            db.add(transaction)

            # Deduct credit from user account if applicable
            if credit_to_apply > 0:
                user_account.balance -= credit_to_apply

            # Update ledger
            ledger.amount_paid = (ledger.amount_paid or 0) + total_payment
            ledger.remaining_balance = ledger.total_price - ledger.amount_paid

            # Check if fully paid
            if ledger.remaining_balance <= 0:
                ledger.ownership_transferred = True
                ledger.ownership_transfer_date = payment_date
                rental.status = 'completed'

                # Update PUE ownership
                pue = db.query(ProductiveUseEquipment).filter(ProductiveUseEquipment.pue_id == rental.pue_id).first()
                if pue:
                    pue.status = 'owned'
                    pue.owner_user_id = rental.user_id
        else:
            # Regular rental payment
            rental.pay_to_own_paid_amount = (rental.pay_to_own_paid_amount or 0) + total_payment

            # Deduct credit from user account if applicable
            if credit_to_apply > 0:
                user_account.balance -= credit_to_apply

        # Update rental
        rental.pay_to_own_paid_amount = (rental.pay_to_own_paid_amount or 0) + total_payment

        db.commit()

        return {
            "message": "Payment recorded successfully",
            "pue_rental_id": rental_id,
            "payment_amount": float(payment.payment_amount),
            "credit_applied": float(credit_to_apply) if credit_to_apply > 0 else 0,
            "total_payment": float(total_payment),
            "total_paid": float(rental.pay_to_own_paid_amount),
            "payment_date": payment_date.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error recording payment: {str(e)}")

@app.get("/pue-rentals/{rental_id}/pay-to-own-ledger",
    tags=["PUE Rentals"],
    summary="Get Pay-to-Own Progress")
async def get_pay_to_own_ledger(
    rental_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get pay-to-own payment progress and transaction history"""
    rental = db.query(PUERental).filter(PUERental.pue_rental_id == rental_id).first()
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")

    if not rental.is_pay_to_own:
        raise HTTPException(status_code=400, detail="This is not a pay-to-own rental")

    ledger = db.query(PUEPayToOwnLedger).filter(
        PUEPayToOwnLedger.pue_rental_id == rental_id
    ).first()

    if not ledger:
        raise HTTPException(status_code=404, detail="Ledger not found")

    # Get transactions
    transactions = db.query(PUEPayToOwnTransaction).filter(
        PUEPayToOwnTransaction.ledger_id == ledger.ledger_id
    ).order_by(PUEPayToOwnTransaction.payment_date.desc()).all()

    transaction_list = [{
        "transaction_id": t.transaction_id,
        "payment_date": t.payment_date.isoformat(),
        "payment_amount": float(t.payment_amount),
        "payment_type": t.payment_type,
        "notes": t.notes
    } for t in transactions]

    return {
        "ledger_id": ledger.ledger_id,
        "pue_rental_id": rental_id,
        "total_price": float(ledger.total_price),
        "amount_paid": float(ledger.amount_paid),
        "remaining_balance": float(ledger.remaining_balance) if ledger.remaining_balance else 0.0,
        "ownership_transferred": ledger.ownership_transferred,
        "ownership_transfer_date": ledger.ownership_transfer_date.isoformat() if ledger.ownership_transfer_date else None,
        "payment_progress_percentage": (float(ledger.amount_paid) / float(ledger.total_price) * 100) if ledger.total_price > 0 else 0,
        "transactions": transaction_list
    }

@app.get("/pue-rentals/{rental_id}/calculate-return-cost",
    tags=["PUE Rentals"],
    summary="Calculate Final Cost at PUE Return")
async def calculate_pue_rental_return_cost(
    rental_id: int,
    actual_return_date: Optional[str] = Query(None, description="Actual return date (ISO format)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Calculate final cost for a PUE rental at return time based on:
    - Actual duration (rental start to return date)
    - Cost structure components (per_day, per_hour, per_week, per_month, fixed, etc.)

    Returns breakdown of all cost components and final total.
    """
    rental = db.query(PUERental).filter(PUERental.pue_rental_id == rental_id).first()
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")

    # Authorization check
    if current_user.get('role') == UserRole.USER:
        # Get the PUE item to check hub
        pue = db.query(ProductiveUseEquipment).filter(ProductiveUseEquipment.pue_id == rental.pue_id).first()
        if pue and pue.hub_id != current_user.get('hub_id'):
            raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.get('role') == UserRole.DATA_ADMIN:
        raise HTTPException(status_code=403, detail="Data admins cannot access rental details")

    # Parse actual return date or use now
    if actual_return_date:
        try:
            return_date = datetime.fromisoformat(actual_return_date.replace('Z', '+00:00'))
        except:
            return_date = datetime.now(timezone.utc)
    else:
        return_date = datetime.now(timezone.utc)

    # Calculate actual duration
    start_date = rental.timestamp_taken
    if isinstance(start_date, str):
        start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
    elif start_date and not start_date.tzinfo:
        start_date = start_date.replace(tzinfo=timezone.utc)

    duration_delta = return_date - start_date
    actual_hours = duration_delta.total_seconds() / 3600
    actual_days = duration_delta.total_seconds() / 86400
    actual_weeks = actual_days / 7
    actual_months = actual_days / 30

    # Get cost structure
    cost_breakdown = []
    subtotal = 0
    cost_structure_info = None

    if rental.cost_structure_id:
        cost_structure = db.query(CostStructure).filter(
            CostStructure.structure_id == rental.cost_structure_id
        ).first()

        if cost_structure:
            cost_structure_info = {
                "structure_id": cost_structure.structure_id,
                "name": cost_structure.name,
                "description": cost_structure.description or "No description available"
            }

            components = db.query(CostComponent).filter(
                CostComponent.structure_id == cost_structure.structure_id
            ).all()

            for component in components:
                component_cost = 0
                quantity = 0

                if component.unit_type == 'per_hour':
                    quantity = actual_hours
                    component_cost = component.rate * actual_hours
                elif component.unit_type == 'per_day':
                    quantity = actual_days
                    component_cost = component.rate * actual_days
                elif component.unit_type == 'per_week':
                    quantity = actual_weeks
                    component_cost = component.rate * actual_weeks
                elif component.unit_type == 'per_month':
                    quantity = actual_months
                    component_cost = component.rate * actual_months
                elif component.unit_type == 'fixed':
                    quantity = 1
                    component_cost = component.rate

                if quantity > 0 or component.unit_type == 'fixed':
                    cost_breakdown.append({
                        "component_name": component.component_name,
                        "unit_type": component.unit_type,
                        "rate": float(component.rate),
                        "quantity": round(quantity, 2),
                        "amount": round(component_cost, 2)
                    })
                    subtotal += component_cost

    # Get hub VAT
    pue = db.query(ProductiveUseEquipment).filter(ProductiveUseEquipment.pue_id == rental.pue_id).first()
    vat_percentage = 15.0
    if pue and pue.hub_id:
        hub = db.query(SolarHub).filter(SolarHub.hub_id == pue.hub_id).first()
        if hub and hasattr(hub, 'vat_percentage') and hub.vat_percentage is not None:
            vat_percentage = hub.vat_percentage

    vat_amount = subtotal * (vat_percentage / 100)
    total = subtotal + vat_amount

    # Get user account balance
    user_account = db.query(UserAccount).filter(UserAccount.user_id == rental.user_id).first()
    account_balance = user_account.balance if user_account else 0

    # Calculate amounts
    deposit_paid = rental.deposit_amount or 0
    amount_still_owed = max(0, total - deposit_paid)

    return {
        "rental_id": rental_id,
        "cost_structure": cost_structure_info,
        "duration": {
            "start_date": start_date.isoformat(),
            "return_date": return_date.isoformat(),
            "actual_hours": round(actual_hours, 2),
            "actual_days": round(actual_days, 2),
            "is_late": False  # Can add late logic later if needed
        },
        "kwh_usage": {
            "start_reading": None,
            "end_reading": None,
            "total_used": None
        },
        "cost_breakdown": cost_breakdown,
        "subtotal": round(subtotal, 2),
        "vat_percentage": vat_percentage,
        "vat_amount": round(vat_amount, 2),
        "total": round(total, 2),
        "original_estimate": 0,
        "payment_status": {
            "amount_paid_so_far": round(deposit_paid, 2),
            "amount_still_owed": round(amount_still_owed, 2),
            "user_account_balance": round(account_balance, 2),
            "can_pay_with_credit": account_balance >= amount_still_owed
        },
        "subscription": None
    }

@app.post("/pue-rentals/{rental_id}/return",
    tags=["PUE Rentals"],
    summary="Return PUE Item")
async def return_pue_rental(
    rental_id: int,
    return_data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Return PUE item from a rental"""
    if current_user.get('role') == UserRole.DATA_ADMIN:
        raise HTTPException(status_code=403, detail="Data admins cannot process returns")

    try:
        rental = db.query(PUERental).filter(PUERental.pue_rental_id == rental_id).first()
        if not rental:
            raise HTTPException(status_code=404, detail="Rental not found")

        # Authorization check
        if current_user.get('role') == UserRole.USER:
            pue = db.query(ProductiveUseEquipment).filter(ProductiveUseEquipment.pue_id == rental.pue_id).first()
            if pue and pue.hub_id != current_user.get('hub_id'):
                raise HTTPException(status_code=403, detail="Access denied")

        # Check if already returned
        if rental.date_returned:
            raise HTTPException(status_code=400, detail="PUE item has already been returned")

        # Parse return date
        actual_return_date = return_data.get('actual_return_date')
        if actual_return_date:
            if isinstance(actual_return_date, str):
                return_date = datetime.fromisoformat(actual_return_date.replace('Z', '+00:00'))
            else:
                return_date = actual_return_date
        else:
            return_date = datetime.now(timezone.utc)

        # Update rental status
        rental.date_returned = return_date
        rental.is_active = False

        # Mark PUE item as available
        pue = db.query(ProductiveUseEquipment).filter(ProductiveUseEquipment.pue_id == rental.pue_id).first()
        if pue:
            pue.status = 'available'

        # Handle payment if collecting
        if return_data.get('collect_payment'):
            user_account = db.query(UserAccount).filter(UserAccount.user_id == rental.user_id).first()
            if not user_account:
                user_account = UserAccount(user_id=rental.user_id, balance=0)
                db.add(user_account)
                db.flush()

            payment_amount = return_data.get('payment_amount', 0)
            credit_applied = return_data.get('credit_applied', 0)

            if credit_applied > 0:
                if user_account.balance < credit_applied:
                    raise HTTPException(status_code=400, detail="Insufficient account credit")
                user_account.balance -= credit_applied

            if payment_amount > 0:
                user_account.balance += payment_amount

            # Create transaction record
            payment_type = return_data.get('payment_type', 'cash')
            payment_notes = return_data.get('payment_notes', '')

            transaction = AccountTransaction(
                account_id=user_account.account_id,
                transaction_type='pue_rental_payment',
                amount=payment_amount,
                balance_after=user_account.balance,
                description=f'Payment for PUE rental #{rental_id}' + (f' - {payment_notes}' if payment_notes else ''),
                payment_method=payment_type,
                created_at=return_date
            )
            db.add(transaction)

        # Add return notes
        return_notes = return_data.get('return_notes')
        if return_notes:
            note = Note(content=f"Return notes: {return_notes}")
            db.add(note)
            db.flush()
            rental.notes.append(note)

        db.commit()

        return {
            "message": "PUE rental returned successfully",
            "pue_rental_id": rental_id,
            "return_date": return_date.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# PAY-TO-OWN ENDPOINTS (NEW DESIGN)
# ============================================================================

@app.get("/pue-rentals/{rental_id}/ownership-status",
    tags=["PUE Rentals - Pay to Own"],
    summary="Get ownership status for pay-to-own rental")
async def get_rental_ownership_status(
    rental_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get current ownership status for a pay-to-own rental.
    Shows total item cost, amount paid, remaining balance, and ownership percentage.
    """
    if current_user.get('role') == UserRole.DATA_ADMIN:
        raise HTTPException(status_code=403, detail="Data admins cannot access rental ownership status")

    # Fetch rental
    rental = db.query(PUERental).filter(PUERental.pue_rental_id == rental_id).first()
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")

    # Use PayToOwnService to get ownership status
    try:
        ownership_status = PayToOwnService.get_ownership_status(rental)
        return ownership_status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving ownership status: {str(e)}")


@app.post("/pue-rentals/{rental_id}/pay-to-own-payment",
    tags=["PUE Rentals - Pay to Own"],
    summary="Process pay-to-own payment")
async def process_rental_pay_to_own_payment(
    rental_id: int,
    payment_data: PayToOwnPaymentRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Process a payment for a pay-to-own rental.

    Calculates how much of the payment goes toward ownership vs rental fees
    based on the cost structure components. Updates ownership tracking fields
    and marks rental as completed if 100% ownership is reached.
    """
    if current_user.get('role') == UserRole.DATA_ADMIN:
        raise HTTPException(status_code=403, detail="Data admins cannot process payments")

    # Fetch rental
    rental = db.query(PUERental).filter(PUERental.pue_rental_id == rental_id).first()
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")

    # Process payment using PayToOwnService
    try:
        result = PayToOwnService.process_payment(
            db=db,
            rental=rental,
            payment_amount=payment_data.payment_amount,
            payment_type=payment_data.payment_type,
            notes=payment_data.notes,
            credit_applied=payment_data.credit_applied
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing payment: {str(e)}")


@app.get("/users/{user_id}/pay-to-own-items",
    tags=["Users", "PUE Rentals - Pay to Own"],
    summary="Get user's active pay-to-own items")
async def get_user_pay_to_own_items(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all active pay-to-own items for a user.

    Returns list of pay-to-own rentals with ownership progress,
    amount paid, and remaining balance for each item.
    """
    if current_user.get('role') == UserRole.DATA_ADMIN:
        raise HTTPException(status_code=403, detail="Data admins cannot access user pay-to-own items")

    # Verify user exists
    user = db.query(BEPPPUser).filter(BEPPPUser.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Fetch active pay-to-own rentals
    rentals = db.query(PUERental).filter(
        PUERental.user_id == user_id,
        PUERental.is_pay_to_own == True,
        or_(
            PUERental.pay_to_own_status == 'active',
            PUERental.pay_to_own_status == None
        )
    ).all()

    items = []
    for rental in rentals:
        # Get PUE item details
        pue_item = db.query(ProductiveUseEquipment).filter(ProductiveUseEquipment.pue_id == rental.pue_id).first()

        # Calculate remaining balance
        remaining = float(rental.total_item_cost or 0) - float(rental.total_paid_towards_ownership)

        items.append({
            "rental_id": rental.pue_rental_id,
            "rental_unique_id": getattr(rental, 'rental_unique_id', None),
            "pue_id": rental.pue_id,
            "pue_name": pue_item.name if pue_item else "Unknown",
            "total_item_cost": float(rental.total_item_cost) if rental.total_item_cost else 0,
            "total_paid_towards_ownership": float(rental.total_paid_towards_ownership),
            "ownership_percentage": float(rental.ownership_percentage),
            "remaining_balance": max(remaining, 0),
            "pay_to_own_status": rental.pay_to_own_status,
            "rental_start_date": rental.timestamp_taken.isoformat() if rental.timestamp_taken else None
        })

    return {
        "user_id": user_id,
        "total_pay_to_own_items": len(items),
        "items": items
    }

# ============================================================================
# PUE INSPECTION ENDPOINTS
# ============================================================================

@app.post("/pue/{pue_id}/inspections",
    tags=["PUE Inspections"],
    summary="Record PUE Inspection")
async def create_pue_inspection(
    pue_id: str,
    inspection: PUEInspectionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Record a new PUE inspection"""
    if current_user.get('role') == UserRole.DATA_ADMIN:
        raise HTTPException(status_code=403, detail="Data admins cannot record inspections")

    try:
        pue = db.query(ProductiveUseEquipment).filter(ProductiveUseEquipment.pue_id == pue_id).first()
        if not pue:
            raise HTTPException(status_code=404, detail="PUE not found")

        inspection_date = inspection.inspection_date or datetime.now(timezone.utc)

        new_inspection = PUEInspection(
            pue_id=pue_id,
            inspection_date=inspection_date,
            inspector_id=current_user.get('user_id'),
            condition=inspection.condition,
            issues_found=inspection.notes,
            actions_taken=inspection.maintenance_notes if hasattr(inspection, 'maintenance_notes') else None
        )
        db.add(new_inspection)
        db.commit()
        db.refresh(new_inspection)

        return {
            "message": "Inspection recorded successfully",
            "inspection_id": new_inspection.inspection_id,
            "pue_id": pue_id,
            "inspection_date": new_inspection.inspection_date.isoformat(),
            "condition": new_inspection.condition,
            "issues_found": new_inspection.issues_found,
            "next_inspection_due": None
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error recording inspection: {str(e)}")

@app.get("/pue/{pue_id}/inspections",
    tags=["PUE Inspections"],
    summary="Get PUE Inspection History")
async def get_pue_inspections(
    pue_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get inspection history for a specific PUE"""
    pue = db.query(ProductiveUseEquipment).filter(ProductiveUseEquipment.pue_id == pue_id).first()
    if not pue:
        raise HTTPException(status_code=404, detail="PUE not found")

    inspections = db.query(PUEInspection).filter(
        PUEInspection.pue_id == pue_id
    ).order_by(PUEInspection.inspection_date.desc()).all()

    inspection_list = [{
        "inspection_id": i.inspection_id,
        "inspection_date": i.inspection_date.isoformat(),
        "inspector_id": i.inspector_id,
        "condition": i.condition,
        "issues_found": i.issues_found,
        "actions_taken": i.actions_taken,
        "next_inspection_due": i.next_inspection_due.isoformat() if i.next_inspection_due else None
    } for i in inspections]

    # Get last inspection from the list
    last_inspection_date = inspections[0].inspection_date if inspections else None

    return {
        "pue_id": pue_id,
        "pue_name": pue.name,
        "last_inspection_date": last_inspection_date.isoformat() if last_inspection_date else None,
        "next_inspection_due": None,  # Can be calculated from last inspection + interval if needed
        "inspection_count": len(inspections),
        "inspections": inspection_list
    }

@app.get("/inspections/due",
    tags=["PUE Inspections"],
    summary="Get PUE Due for Inspection")
async def get_due_inspections(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all PUE items that are due for inspection"""
    today = datetime.now(timezone.utc).date()

    # PUE with next_inspection_due <= today
    due_pue = db.query(ProductiveUseEquipment).filter(
        ProductiveUseEquipment.next_inspection_due.isnot(None),
        func.date(ProductiveUseEquipment.next_inspection_due) <= today
    ).all()

    result = [{
        "pue_id": p.pue_id,
        "pue_name": p.name,
        "serial_number": p.short_id,
        "status": p.status,
        "last_inspection_date": p.last_inspection_date.isoformat() if p.last_inspection_date else None,
        "next_inspection_due": p.next_inspection_due.isoformat() if p.next_inspection_due else None,
        "days_overdue": (today - p.next_inspection_due.date()).days if p.next_inspection_due else 0
    } for p in due_pue]

    return {
        "count": len(result),
        "due_inspections": result
    }

@app.get("/inspections/overdue",
    tags=["PUE Inspections"],
    summary="Get Overdue Inspections")
async def get_overdue_inspections(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all PUE items with overdue inspections"""
    today = datetime.now(timezone.utc).date()

    # PUE with next_inspection_due < today
    overdue_pue = db.query(ProductiveUseEquipment).filter(
        ProductiveUseEquipment.next_inspection_due.isnot(None),
        func.date(ProductiveUseEquipment.next_inspection_due) < today
    ).all()

    result = [{
        "pue_id": p.pue_id,
        "pue_name": p.name,
        "serial_number": p.short_id,
        "status": p.status,
        "last_inspection_date": p.last_inspection_date.isoformat() if p.last_inspection_date else None,
        "next_inspection_due": p.next_inspection_due.isoformat() if p.next_inspection_due else None,
        "days_overdue": (today - p.next_inspection_due.date()).days
    } for p in overdue_pue]

    return {
        "count": len(result),
        "overdue_inspections": result
    }

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
    battery_id: str,
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
    data_dicts = []
    for obj in data:
        row_dict = {}
        for c in obj.__table__.columns:
            value = getattr(obj, c.name)
            # Convert datetime objects to ISO format strings for JSON serialization
            if isinstance(value, datetime):
                row_dict[c.name] = value.isoformat()
            else:
                row_dict[c.name] = value
        data_dicts.append(row_dict)

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
    battery_id: str,
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
            Rental.battery_returned_date.is_(None)
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
            time_period_description = f"Predefined period: {request.time_period}"
        elif request.start_time and request.end_time:
            start_time, end_time = request.start_time, request.end_time
            time_period_description = f"Custom period: {start_time.isoformat()} to {end_time.isoformat()}"
        else:
            start_time, end_time = calculate_time_period("last_week")
            time_period_description = f"Default period: last_week"
        
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
        
        if request.aggregation_period == "hour":
            df['time_group'] = df['timestamp'].dt.floor('H')
        elif request.aggregation_period == "day":
            df['time_group'] = df['timestamp'].dt.floor('D')
        elif request.aggregation_period == "week":
            df['time_group'] = df['timestamp'].dt.to_period('W').dt.start_time
        elif request.aggregation_period == "month":
            df['time_group'] = df['timestamp'].dt.to_period('M').dt.start_time
        
        if request.aggregation_function == "sum":
            agg_func = 'sum'
        elif request.aggregation_function == "mean":
            agg_func = 'mean'
        elif request.aggregation_function == "median":
            agg_func = 'median'
        elif request.aggregation_function == "min":
            agg_func = 'min'
        elif request.aggregation_function == "max":
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

@app.get("/analytics/battery-performance",
    tags=["Data & Analytics"],
    summary="Battery Performance Analytics",
    description="Get performance analytics for specific batteries over a time period")
async def get_battery_performance_analytics(
    battery_ids: str = Query(..., description="Comma-separated battery IDs"),
    days_back: int = Query(7, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get battery performance analytics"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.DATA_ADMIN]:
        raise HTTPException(status_code=403, detail="Data access required")
    
    try:
        # Parse battery IDs
        battery_id_list = [int(bid.strip()) for bid in battery_ids.split(',')]
        
        # Calculate time range
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days_back)
        
        # Get battery performance data
        performance_data = []
        for battery_id in battery_id_list:
            # Get battery info
            battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == battery_id).first()
            if not battery:
                continue
                
            # Get live data for this battery
            live_data = db.query(LiveData).filter(
                LiveData.battery_id == battery_id,
                LiveData.timestamp >= start_time,
                LiveData.timestamp <= end_time
            ).all()
            
            if live_data:
                voltages = [d.voltage for d in live_data if d.voltage]
                currents = [d.current_amps for d in live_data if d.current_amps]
                soc_values = [d.state_of_charge for d in live_data if d.state_of_charge]
                
                performance_data.append({
                    "battery_id": battery_id,
                    "battery_capacity_wh": battery.battery_capacity_wh,
                    "data_points": len(live_data),
                    "avg_voltage": sum(voltages) / len(voltages) if voltages else 0,
                    "avg_current": sum(currents) / len(currents) if currents else 0,
                    "avg_soc": sum(soc_values) / len(soc_values) if soc_values else 0,
                    "min_soc": min(soc_values) if soc_values else 0,
                    "max_soc": max(soc_values) if soc_values else 0
                })
            else:
                performance_data.append({
                    "battery_id": battery_id,
                    "battery_capacity_wh": battery.battery_capacity_wh,
                    "data_points": 0,
                    "avg_voltage": 0,
                    "avg_current": 0,
                    "avg_soc": 0,
                    "min_soc": 0,
                    "max_soc": 0
                })
        
        return {
            "battery_performance": performance_data,
            "analysis_period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "days_analyzed": days_back
            },
            "summary": {
                "total_batteries_analyzed": len(performance_data),
                "batteries_with_data": len([b for b in performance_data if b["data_points"] > 0])
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Battery performance analytics error: {str(e)}")

@app.post("/analytics/rental-statistics",
    tags=["Data & Analytics"],
    summary="Rental Statistics Analytics",
    description="Get rental statistics for specified hubs and time period")
async def get_rental_statistics_analytics(
    request: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get rental statistics analytics"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.DATA_ADMIN]:
        raise HTTPException(status_code=403, detail="Data access required")
    
    try:
        hub_ids = request.get("hub_ids", [])
        time_period = request.get("time_period", "last_month")
        
        # Calculate time range based on period
        end_time = datetime.now(timezone.utc)
        if time_period == "last_week":
            start_time = end_time - timedelta(days=7)
        elif time_period == "last_month":
            start_time = end_time - timedelta(days=30)
        elif time_period == "last_year":
            start_time = end_time - timedelta(days=365)
        else:
            start_time = end_time - timedelta(days=30)  # Default to month
        
        # Build query
        query = db.query(Rental)
        if hub_ids:
            # Get batteries in specified hubs
            battery_ids = db.query(BEPPPBattery.battery_id).filter(
                BEPPPBattery.hub_id.in_(hub_ids)
            ).all()
            battery_id_list = [b.battery_id for b in battery_ids]
            query = query.filter(Rental.battery_id.in_(battery_id_list))
        
        # Filter by time period
        rentals = query.filter(
            Rental.timestamp_taken >= start_time,
            Rental.timestamp_taken <= end_time
        ).all()
        
        # Calculate statistics
        total_rentals = len(rentals)
        completed_rentals = len([r for r in rentals if r.date_returned or r.battery_returned_date])
        active_rentals = total_rentals - completed_rentals
        
        total_revenue = sum([r.total_cost or 0 for r in rentals])
        avg_rental_duration = 0
        
        if completed_rentals > 0:
            durations = []
            for rental in rentals:
                if rental.date_returned or rental.battery_returned_date:
                    return_date = rental.date_returned or rental.battery_returned_date
                    duration = (return_date - rental.timestamp_taken).days
                    durations.append(duration)
            
            if durations:
                avg_rental_duration = sum(durations) / len(durations)
        
        return {
            "time_period": {
                "description": time_period,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "days_analyzed": (end_time - start_time).days
            },
            "overall_statistics": {
                "total_rentals": total_rentals,
                "completed_rentals": completed_rentals,
                "active_rentals": active_rentals,
                "total_revenue": total_revenue,
                "average_rental_duration_days": avg_rental_duration
            },
            "hub_breakdown": hub_ids if hub_ids else "all_hubs"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rental statistics error: {str(e)}")

@app.get("/analytics/revenue",
    tags=["Data & Analytics"], 
    summary="Revenue Analytics",
    description="Get revenue analytics including rental and PUE income")
async def get_revenue_analytics(
    days_back: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get revenue analytics"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Calculate time range
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days_back)
        
        # Get rental revenue
        rentals = db.query(Rental).filter(
            Rental.timestamp_taken >= start_time,
            Rental.timestamp_taken <= end_time
        ).all()
        
        rental_revenue = sum([r.total_cost or 0 for r in rentals])
        
        # Get PUE revenue (from rental PUE items)
        pue_rentals = db.query(RentalPUEItem).join(Rental).filter(
            Rental.timestamp_taken >= start_time,
            Rental.timestamp_taken <= end_time
        ).all()
        
        pue_revenue = sum([item.rental_cost or 0 for item in pue_rentals])
        
        total_revenue = rental_revenue + pue_revenue
        
        return {
            "time_period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "days_analyzed": days_back
            },
            "total_revenue": total_revenue,
            "rental_revenue": rental_revenue,
            "pue_revenue": pue_revenue,
            "revenue_breakdown": {
                "battery_rentals": rental_revenue,
                "pue_equipment": pue_revenue
            },
            "statistics": {
                "total_rentals": len(rentals),
                "avg_revenue_per_rental": rental_revenue / len(rentals) if rentals else 0,
                "daily_avg_revenue": total_revenue / days_back if days_back > 0 else 0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Revenue analytics error: {str(e)}")

@app.get("/analytics/device-utilization/{hub_id}",
    tags=["Data & Analytics"],
    summary="Device Utilization Analytics", 
    description="Get device utilization rates for a specific hub")
async def get_device_utilization_analytics(
    hub_id: int,
    days_back: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get device utilization analytics for a hub"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.DATA_ADMIN]:
        raise HTTPException(status_code=403, detail="Data access required")
    
    try:
        # Calculate time range
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days_back)
        
        # Get batteries for this hub
        batteries = db.query(BEPPPBattery).filter(BEPPPBattery.hub_id == hub_id).all()
        total_batteries = len(batteries)
        
        # Get battery utilization
        if batteries:
            battery_rentals = db.query(Rental).filter(
                Rental.battery_id.in_([b.battery_id for b in batteries]),
                Rental.timestamp_taken >= start_time,
                Rental.timestamp_taken <= end_time
            ).all()
        else:
            battery_rentals = []
        
        battery_rental_days = 0
        for rental in battery_rentals:
            try:
                if rental.date_returned or rental.battery_returned_date:
                    return_date = rental.date_returned or rental.battery_returned_date
                    if rental.timestamp_taken and return_date:
                        # Ensure both dates are timezone-aware or naive consistently
                        if return_date.tzinfo is None and rental.timestamp_taken.tzinfo is not None:
                            return_date = return_date.replace(tzinfo=timezone.utc)
                        elif return_date.tzinfo is not None and rental.timestamp_taken.tzinfo is None:
                            timestamp_taken = rental.timestamp_taken.replace(tzinfo=timezone.utc)
                        else:
                            timestamp_taken = rental.timestamp_taken
                        
                        duration = (return_date - timestamp_taken).days
                        battery_rental_days += max(duration, 1)  # At least 1 day
                    else:
                        battery_rental_days += 1  # Default if dates are missing
                else:
                    # Still active, count days since start
                    if rental.timestamp_taken:
                        # Ensure timezone consistency
                        timestamp_taken = rental.timestamp_taken
                        if timestamp_taken.tzinfo is None:
                            timestamp_taken = timestamp_taken.replace(tzinfo=timezone.utc)
                        duration = (end_time - timestamp_taken).days
                        battery_rental_days += max(duration, 1)
                    else:
                        battery_rental_days += 1  # Default if timestamp missing
            except Exception as e:
                # Log error but continue processing
                print(f"Error processing battery rental {rental.rentral_id}: {e}")
                battery_rental_days += 1  # Default to 1 day for problematic rentals
        
        battery_utilization_rate = (battery_rental_days / (total_batteries * days_back)) * 100 if total_batteries > 0 else 0
        
        # Get PUE equipment for this hub
        pue_items = db.query(ProductiveUseEquipment).filter(
            ProductiveUseEquipment.hub_id == hub_id
        ).all()
        total_pue = len(pue_items)
        
        # Get PUE utilization
        if pue_items:
            pue_rentals = db.query(RentalPUEItem).join(Rental).filter(
                RentalPUEItem.pue_id.in_([p.pue_id for p in pue_items]),
                Rental.timestamp_taken >= start_time,
                Rental.timestamp_taken <= end_time
            ).all()
        else:
            pue_rentals = []
        
        pue_rental_days = 0
        for item in pue_rentals:
            try:
                if item.returned_date and item.added_at:
                    # Ensure both dates are timezone-aware or naive consistently
                    returned_date = item.returned_date
                    added_at = item.added_at
                    
                    # Handle timezone consistency
                    if returned_date.tzinfo is None and added_at.tzinfo is not None:
                        returned_date = returned_date.replace(tzinfo=timezone.utc)
                    elif returned_date.tzinfo is not None and added_at.tzinfo is None:
                        added_at = added_at.replace(tzinfo=timezone.utc)
                    
                    # Calculate actual rental duration
                    duration_days = (returned_date - added_at).days
                    pue_rental_days += max(duration_days, 1)  # At least 1 day
                else:
                    # Default to 1 day if dates are missing
                    pue_rental_days += 1
            except Exception as e:
                # Log error but continue processing
                print(f"Error processing PUE rental item {item.id}: {e}")
                pue_rental_days += 1  # Default to 1 day for problematic items
        pue_utilization_rate = (pue_rental_days / (total_pue * days_back)) * 100 if total_pue > 0 else 0
        
        overall_utilization = (battery_utilization_rate + pue_utilization_rate) / 2 if (total_batteries > 0 or total_pue > 0) else 0
        
        return {
            "hub_id": hub_id,
            "analysis_period": {
                "start_time": start_time.isoformat(), 
                "end_time": end_time.isoformat(),
                "days_analyzed": days_back
            },
            "battery_utilization": {
                "total_batteries": total_batteries,
                "rental_days": battery_rental_days,
                "utilization_rate": round(battery_utilization_rate, 2)
            },
            "pue_utilization": {
                "total_pue_items": total_pue,
                "rental_days": pue_rental_days,
                "utilization_rate": round(pue_utilization_rate, 2)
            },
            "utilization_rate": round(overall_utilization, 2)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Device utilization error: {str(e)}")

@app.get("/analytics/export/{hub_id}",
    tags=["Data & Analytics"],
    summary="Export Analytics Data",
    description="Export analytics data in CSV or JSON format")
async def export_analytics_data(
    hub_id: int,
    format: str = Query("json", description="Export format: csv or json"),
    days_back: int = Query(30, description="Number of days to include"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Export analytics data for a hub"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.DATA_ADMIN]:
        raise HTTPException(status_code=403, detail="Data access required")
    
    try:
        # Calculate time range
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days_back)
        
        # Get hub data
        hub = db.query(SolarHub).filter(SolarHub.hub_id == hub_id).first()
        if not hub:
            raise HTTPException(status_code=404, detail="Hub not found")
        
        # Get batteries and their data
        batteries = db.query(BEPPPBattery).filter(BEPPPBattery.hub_id == hub_id).all()
        
        # Get rental data
        rentals = db.query(Rental).filter(
            Rental.battery_id.in_([b.battery_id for b in batteries]),
            Rental.timestamp_taken >= start_time,
            Rental.timestamp_taken <= end_time
        ).all()
        
        # Prepare export data
        export_data = {
            "hub_info": {
                "hub_id": hub.hub_id,
                "location": hub.what_three_word_location,
                "solar_capacity_kw": hub.solar_capacity_kw,
                "country": hub.country
            },
            "export_period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "days_included": days_back
            },
            "batteries": [
                {
                    "battery_id": b.battery_id,
                    "capacity_wh": b.battery_capacity_wh,
                    "status": b.status
                } for b in batteries
            ],
            "rentals": [
                {
                    "rental_id": r.rentral_id,
                    "battery_id": r.battery_id,
                    "user_id": r.user_id,
                    "timestamp_taken": r.timestamp_taken.isoformat() if r.timestamp_taken else None,
                    "date_returned": r.battery_returned_date.isoformat() if r.battery_returned_date else None,
                    "rental_cost": r.total_cost
                } for r in rentals
            ]
        }
        
        if format.lower() == "csv":
            # Create CSV response
            from io import StringIO
            import csv
            
            output = StringIO()
            
            # Write rental data as CSV
            if rentals:
                writer = csv.writer(output)
                writer.writerow(["rental_id", "battery_id", "user_id", "timestamp_taken", "date_returned", "rental_cost"])
                for rental in rentals:
                    writer.writerow([
                        rental.rentral_id,
                        rental.battery_id,
                        rental.user_id,
                        rental.timestamp_taken.isoformat() if rental.timestamp_taken else "",
                        rental.battery_returned_date.isoformat() if rental.battery_returned_date else "",
                        rental.total_cost or 0
                    ])
            
            from fastapi.responses import Response
            return Response(
                content=output.getvalue(),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=hub_{hub_id}_analytics.csv"}
            )
        else:
            # Return JSON
            return export_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")

# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

@app.get("/admin/webhook-logs")
async def get_webhook_logs(
    limit: int = Query(100, description="Number of recent webhook logs to return (max: limit from config)"),
    battery_id: Optional[int] = Query(None, description="Filter by battery ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get recent webhook logs from database (admin/superadmin only).
    Shows full request/response data for debugging battery data submissions in production.
    """
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        # Build query
        query = db.query(WebhookLog).order_by(desc(WebhookLog.created_at))

        # Filter by battery_id if specified
        if battery_id:
            query = query.filter(WebhookLog.battery_id == battery_id)

        # Limit results
        logs = query.limit(min(limit, WEBHOOK_LOG_LIMIT)).all()

        # Format logs for response
        formatted_logs = []
        for log in logs:
            formatted_logs.append({
                "log_id": log.log_id,
                "battery_id": log.battery_id,
                "endpoint": log.endpoint,
                "method": log.method,
                "timestamp": log.created_at.isoformat(),
                "request_headers": json.loads(log.request_headers) if log.request_headers else None,
                "request_body": json.loads(log.request_body) if log.request_body else None,
                "status_code": log.response_status,  # Rename for frontend consistency
                "response_body": json.loads(log.response_body) if log.response_body else None,
                "error_message": log.error_message,
                "processing_time_ms": log.processing_time_ms
            })

        total_logs = db.query(WebhookLog).count()

        return {
            "logs": formatted_logs,
            "total_logs": total_logs,
            "showing": len(formatted_logs),
            "limit": WEBHOOK_LOG_LIMIT,
            "filtered_by_battery": battery_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading webhook logs: {str(e)}")

@app.delete("/admin/webhook-logs/cleanup")
async def cleanup_webhook_logs(
    before_date: str = Query(..., description="Delete logs before this date (ISO format: YYYY-MM-DD)"),
    battery_id: Optional[str] = Query(None, description="Optional: only delete logs for specific battery"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete webhook logs before a specified date (superadmin only).

    This helps manage database size by removing old logs while preserving recent history.

    Examples:
    - DELETE /admin/webhook-logs/cleanup?before_date=2026-01-01
    - DELETE /admin/webhook-logs/cleanup?before_date=2025-12-01&battery_id=1
    """
    if current_user.get('role') != UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Superadmin access required")

    try:
        # Parse the date
        try:
            cutoff_date = datetime.strptime(before_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Use YYYY-MM-DD (e.g., 2026-01-01)"
            )

        # Build delete query
        query = db.query(WebhookLog).filter(WebhookLog.created_at < cutoff_date)

        # Filter by battery_id if specified
        if battery_id:
            query = query.filter(WebhookLog.battery_id == battery_id)

        # Count logs to be deleted (for reporting)
        logs_to_delete = query.count()

        if logs_to_delete == 0:
            return {
                "message": "No logs found matching the criteria",
                "deleted_count": 0,
                "cutoff_date": cutoff_date.isoformat(),
                "battery_id": battery_id,
                "total_remaining": db.query(WebhookLog).count()
            }

        # Delete the logs
        query.delete(synchronize_session=False)
        db.commit()

        remaining_logs = db.query(WebhookLog).count()

        log_webhook_event(
            event_type="webhook_logs_cleanup",
            user_info=current_user,
            battery_id=battery_id,
            status="success",
            additional_info={
                "deleted_count": logs_to_delete,
                "cutoff_date": cutoff_date.isoformat(),
                "battery_id_filter": battery_id or "all",
                "performed_by": current_user.get("sub"),
                "remaining_logs": remaining_logs
            }
        )

        return {
            "message": f"Successfully deleted {logs_to_delete} webhook logs",
            "deleted_count": logs_to_delete,
            "cutoff_date": cutoff_date.isoformat(),
            "battery_id": battery_id,
            "total_remaining": remaining_logs,
            "performed_by": current_user.get("sub"),
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        log_webhook_event(
            event_type="webhook_logs_cleanup_failed",
            user_info=current_user,
            status="error",
            error_message=str(e),
            additional_info={
                "cutoff_date": before_date,
                "battery_id": battery_id
            }
        )
        raise HTTPException(status_code=500, detail=f"Error deleting webhook logs: {str(e)}")

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
        "new_endpoints": {
            "pue_management": [
                "POST /pue/ - Create PUE equipment",
                "GET /pue/{id} - Get PUE details",
                "PUT /pue/{id} - Update PUE equipment",
                "GET /hubs/{id}/pue - List hub PUE items"
            ],
            "data_analytics": [
                "GET /analytics/hub-summary - Hub statistics",
                "POST /analytics/power-usage - Power analytics",
                "GET /analytics/battery-performance - Battery performance",
                "POST /analytics/rental-statistics - Rental statistics", 
                "GET /analytics/revenue - Revenue analytics",
                "GET /analytics/device-utilization/{hub_id} - Device utilization",
                "GET /analytics/export/{hub_id} - Export analytics data"
            ]
        },
        "data_admin_capabilities": {
            "analytics_access": "Full access to analytics endpoints",
            "restricted_user_data": "Cannot view individual user information",
            "hub_filtering": "Access only to assigned hubs"
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

        # Note: Database schema is managed by Alembic migrations
        # init_db() is not called here to avoid conflicts with Alembic
        # Run migrations with: alembic upgrade head

        if DEBUG:
            webhook_logger.info("✅ Database schema managed by Alembic migrations")

        print("✅ Enhanced API ready with PUE management and data analytics")

    except Exception as e:
        if DEBUG:
            webhook_logger.error(f"❌ Startup failed: {e}")
        print(f"❌ API startup failed: {e}")
        raise e

# ============================================================================
# SETTINGS ENDPOINTS
# ============================================================================

@app.get("/settings/rental-durations", tags=["Settings"])
async def get_rental_duration_presets(
    hub_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get rental duration presets for a hub (or global)"""
    query = db.query(RentalDurationPreset).filter(RentalDurationPreset.is_active == True)

    if hub_id:
        # Get hub-specific and global presets
        query = query.filter(
            or_(
                RentalDurationPreset.hub_id == hub_id,
                RentalDurationPreset.hub_id.is_(None)
            )
        )
    else:
        # Only global presets
        query = query.filter(RentalDurationPreset.hub_id.is_(None))

    presets = query.order_by(RentalDurationPreset.sort_order).all()

    return {
        "presets": [{
            "preset_id": p.preset_id,
            "hub_id": p.hub_id,
            "label": p.label,
            "duration_value": p.duration_value,
            "duration_unit": p.duration_unit,
            "sort_order": p.sort_order,
            "is_global": p.hub_id is None,
            "is_active": p.is_active
        } for p in presets]
    }

@app.post("/settings/rental-durations", tags=["Settings"])
async def create_rental_duration_preset(
    label: str = Query(...),
    duration_value: int = Query(...),
    duration_unit: str = Query(...),
    hub_id: Optional[int] = Query(None),
    sort_order: int = Query(0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new rental duration preset"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can create presets")

    preset = RentalDurationPreset(
        label=label,
        duration_value=duration_value,
        duration_unit=duration_unit,
        hub_id=hub_id,
        sort_order=sort_order
    )
    db.add(preset)
    db.commit()
    db.refresh(preset)

    return {"message": "Preset created", "preset_id": preset.preset_id}

@app.put("/settings/rental-durations/{preset_id}", tags=["Settings"])
async def update_rental_duration_preset(
    preset_id: int,
    label: Optional[str] = Query(None),
    duration_value: Optional[int] = Query(None),
    duration_unit: Optional[str] = Query(None),
    hub_id: Optional[int] = Query(None),
    sort_order: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a rental duration preset"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can update presets")

    preset = db.query(RentalDurationPreset).filter(RentalDurationPreset.preset_id == preset_id).first()
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")

    if label is not None:
        preset.label = label
    if duration_value is not None:
        preset.duration_value = duration_value
    if duration_unit is not None:
        preset.duration_unit = duration_unit
    if hub_id is not None:
        preset.hub_id = hub_id
    if sort_order is not None:
        preset.sort_order = sort_order

    db.commit()
    db.refresh(preset)

    return {"message": "Preset updated", "preset_id": preset.preset_id}

@app.delete("/settings/rental-durations/{preset_id}", tags=["Settings"])
async def delete_rental_duration_preset(
    preset_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a rental duration preset"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can delete presets")

    preset = db.query(RentalDurationPreset).filter(RentalDurationPreset.preset_id == preset_id).first()
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")

    db.delete(preset)
    db.commit()

    return {"message": "Preset deleted"}

@app.get("/settings/pue-types", tags=["Settings"])
async def get_pue_types(
    hub_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get PUE equipment types"""
    query = db.query(PUEType)

    if hub_id:
        # For specific hub: return hub-specific types + global types
        query = query.filter(
            or_(
                PUEType.hub_id == hub_id,
                PUEType.hub_id.is_(None)
            )
        )
    else:
        # For superadmin (no hub_id): return ALL types from all hubs
        # Don't filter - show everything
        pass

    types = query.all()

    return {
        "pue_types": [{
            "type_id": t.type_id,
            "type_name": t.type_name,
            "description": t.description,
            "hub_id": t.hub_id,
            "is_global": t.hub_id is None,
            "created_at": t.created_at
        } for t in types]
    }

@app.post("/settings/pue-types", tags=["Settings"])
async def create_pue_type(
    type_name: str = Query(...),
    description: Optional[str] = Query(None),
    hub_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new PUE type"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can create PUE types")

    pue_type = PUEType(
        type_name=type_name,
        description=description,
        hub_id=hub_id,
        created_by=current_user.get('user_id')
    )
    db.add(pue_type)
    db.commit()
    db.refresh(pue_type)

    return {"message": "PUE type created", "type_id": pue_type.type_id}

@app.put("/settings/pue-types/{type_id}", tags=["Settings"])
async def update_pue_type(
    type_id: int,
    type_name: Optional[str] = Query(None),
    description: Optional[str] = Query(None),
    hub_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a PUE type"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can update PUE types")

    pue_type = db.query(PUEType).filter(PUEType.type_id == type_id).first()
    if not pue_type:
        raise HTTPException(status_code=404, detail="PUE type not found")

    if type_name is not None:
        pue_type.type_name = type_name
    if description is not None:
        pue_type.description = description
    if hub_id is not None:
        pue_type.hub_id = hub_id

    db.commit()
    db.refresh(pue_type)

    return {"message": "PUE type updated", "type_id": pue_type.type_id}

@app.delete("/settings/pue-types/{type_id}", tags=["Settings"])
async def delete_pue_type(
    type_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a PUE type"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can delete PUE types")

    pue_type = db.query(PUEType).filter(PUEType.type_id == type_id).first()
    if not pue_type:
        raise HTTPException(status_code=404, detail="PUE type not found")

    db.delete(pue_type)
    db.commit()

    return {"message": "PUE type deleted"}

@app.get("/settings/pricing", tags=["Settings"])
async def get_pricing_configs(
    hub_id: Optional[int] = Query(None),
    item_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get pricing configurations"""
    query = db.query(PricingConfig)

    if hub_id:
        query = query.filter(
            or_(
                PricingConfig.hub_id == hub_id,
                PricingConfig.hub_id.is_(None)
            )
        )

    if item_type:
        query = query.filter(PricingConfig.item_type == item_type)

    if is_active is not None:
        query = query.filter(PricingConfig.is_active == is_active)

    configs = query.all()

    return [{
        "pricing_id": c.pricing_id,
        "item_type": c.item_type,
        "item_reference": c.item_reference,
        "unit_type": c.unit_type,
        "price": float(c.price) if c.price else 0,
        "hub_id": c.hub_id,
        "is_active": c.is_active,
        "created_at": c.created_at
    } for c in configs]

@app.post("/settings/pricing", tags=["Settings"])
async def create_pricing_config(
    item_type: str = Query(...),
    item_reference: str = Query(...),
    unit_type: str = Query(...),
    price: float = Query(...),
    hub_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new pricing configuration"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can create pricing")

    # Get currency from hub settings if hub_id is provided
    currency = 'USD'  # Default
    if hub_id:
        hub_settings = db.query(HubSettings).filter(HubSettings.hub_id == hub_id).first()
        if hub_settings and hub_settings.default_currency:
            currency = hub_settings.default_currency

    pricing = PricingConfig(
        item_type=item_type,
        item_reference=item_reference,
        unit_type=unit_type,
        price=price,
        hub_id=hub_id,
        currency=currency
    )
    db.add(pricing)
    db.commit()
    db.refresh(pricing)

    return {"message": "Pricing created", "pricing_id": pricing.pricing_id}

@app.delete("/settings/pricing/{pricing_id}", tags=["Settings"])
async def delete_pricing_config(
    pricing_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a pricing configuration"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can delete pricing")

    pricing = db.query(PricingConfig).filter(PricingConfig.pricing_id == pricing_id).first()
    if not pricing:
        raise HTTPException(status_code=404, detail="Pricing not found")

    db.delete(pricing)
    db.commit()

    return {"message": "Pricing deleted"}

@app.get("/settings/deposit-presets", tags=["Settings"])
async def get_deposit_presets(
    hub_id: Optional[int] = Query(None),
    item_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get deposit preset configurations"""
    query = db.query(DepositPreset)

    if hub_id:
        query = query.filter(
            or_(
                DepositPreset.hub_id == hub_id,
                DepositPreset.hub_id.is_(None)
            )
        )

    if item_type:
        query = query.filter(DepositPreset.item_type == item_type)

    if is_active is not None:
        query = query.filter(DepositPreset.is_active == is_active)

    presets = query.all()

    return {
        "deposit_presets": [{
            "preset_id": p.preset_id,
            "item_type": p.item_type,
            "item_reference": p.item_reference,
            "deposit_amount": float(p.deposit_amount) if p.deposit_amount else 0,
            "hub_id": p.hub_id,
            "currency": p.currency,
            "is_active": p.is_active,
            "created_at": p.created_at
        } for p in presets]
    }

@app.post("/settings/deposit-presets", tags=["Settings"])
async def create_deposit_preset(
    item_type: str = Query(...),
    item_reference: str = Query(...),
    deposit_amount: float = Query(...),
    hub_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new deposit preset configuration"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can create deposit presets")

    # Get currency from hub settings if hub_id is provided
    currency = 'USD'  # Default
    if hub_id:
        hub_settings = db.query(HubSettings).filter(HubSettings.hub_id == hub_id).first()
        if hub_settings and hub_settings.default_currency:
            currency = hub_settings.default_currency

    preset = DepositPreset(
        item_type=item_type,
        item_reference=item_reference,
        deposit_amount=deposit_amount,
        hub_id=hub_id,
        currency=currency
    )
    db.add(preset)
    db.commit()
    db.refresh(preset)

    return {"message": "Deposit preset created", "preset_id": preset.preset_id}

@app.delete("/settings/deposit-presets/{preset_id}", tags=["Settings"])
async def delete_deposit_preset(
    preset_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a deposit preset configuration"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can delete deposit presets")

    preset = db.query(DepositPreset).filter(DepositPreset.preset_id == preset_id).first()
    if not preset:
        raise HTTPException(status_code=404, detail="Deposit preset not found")

    db.delete(preset)
    db.commit()

    return {"message": "Deposit preset deleted"}

@app.get("/settings/payment-types", tags=["Settings"])
async def get_payment_types(
    hub_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get payment type options"""
    query = db.query(PaymentType)

    if hub_id:
        query = query.filter(
            or_(
                PaymentType.hub_id == hub_id,
                PaymentType.hub_id.is_(None)
            )
        )

    if is_active is not None:
        query = query.filter(PaymentType.is_active == is_active)

    payment_types = query.order_by(PaymentType.sort_order).all()

    return {
        "payment_types": [{
            "type_id": pt.type_id,
            "type_name": pt.type_name,
            "description": pt.description,
            "hub_id": pt.hub_id,
            "is_active": pt.is_active,
            "sort_order": pt.sort_order,
            "created_at": pt.created_at
        } for pt in payment_types]
    }

@app.post("/settings/payment-types", tags=["Settings"])
async def create_payment_type(
    type_name: str = Query(...),
    description: Optional[str] = Query(None),
    hub_id: Optional[int] = Query(None),
    sort_order: Optional[int] = Query(0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new payment type option"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can create payment types")

    payment_type = PaymentType(
        type_name=type_name,
        description=description,
        hub_id=hub_id,
        sort_order=sort_order
    )
    db.add(payment_type)
    db.commit()
    db.refresh(payment_type)

    return {"message": "Payment type created", "type_id": payment_type.type_id}

@app.delete("/settings/payment-types/{type_id}", tags=["Settings"])
async def delete_payment_type(
    type_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a payment type"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can delete payment types")

    payment_type = db.query(PaymentType).filter(PaymentType.type_id == type_id).first()
    if not payment_type:
        raise HTTPException(status_code=404, detail="Payment type not found")

    db.delete(payment_type)
    db.commit()

    return {"message": "Payment type deleted"}

# ============================================================================
# CUSTOMER FIELD OPTIONS ENDPOINTS (for GESI status, Business Category, Signup Reasons)
# ============================================================================

@app.get("/settings/customer-field-options", tags=["Settings"])
async def get_customer_field_options(
    hub_id: Optional[int] = Query(None),
    field_name: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get customer field options (GESI status, business category, signup reasons)"""
    query = db.query(CustomerFieldOption)

    if hub_id:
        query = query.filter(
            or_(
                CustomerFieldOption.hub_id == hub_id,
                CustomerFieldOption.hub_id.is_(None)
            )
        )
    elif not current_user.get('role') == UserRole.SUPERADMIN:
        query = query.filter(
            or_(
                CustomerFieldOption.hub_id == current_user.get('hub_id'),
                CustomerFieldOption.hub_id.is_(None)
            )
        )

    if field_name:
        query = query.filter(CustomerFieldOption.field_name == field_name)

    if is_active is not None:
        query = query.filter(CustomerFieldOption.is_active == is_active)

    options = query.order_by(CustomerFieldOption.field_name, CustomerFieldOption.sort_order).all()
    return options

@app.post("/settings/customer-field-options", tags=["Settings"])
async def create_customer_field_option(
    field_name: str = Query(..., description="Field name: gesi_status, business_category, main_reason_for_signup"),
    option_value: str = Query(...),
    description: Optional[str] = Query(None),
    sort_order: int = Query(0),
    hub_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new customer field option"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can create customer field options")

    # Validate field_name
    valid_field_names = ['gesi_status', 'business_category', 'main_reason_for_signup']
    if field_name not in valid_field_names:
        raise HTTPException(status_code=400, detail=f"Invalid field_name. Must be one of: {', '.join(valid_field_names)}")

    option = CustomerFieldOption(
        field_name=field_name,
        option_value=option_value,
        description=description,
        hub_id=hub_id,
        sort_order=sort_order
    )
    db.add(option)
    db.commit()
    db.refresh(option)

    return {"message": "Customer field option created", "option_id": option.option_id}

@app.put("/settings/customer-field-options/{option_id}", tags=["Settings"])
async def update_customer_field_option(
    option_id: int,
    option_value: Optional[str] = Query(None),
    description: Optional[str] = Query(None),
    sort_order: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a customer field option"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can update customer field options")

    option = db.query(CustomerFieldOption).filter(CustomerFieldOption.option_id == option_id).first()
    if not option:
        raise HTTPException(status_code=404, detail="Customer field option not found")

    if option_value is not None:
        option.option_value = option_value
    if description is not None:
        option.description = description
    if sort_order is not None:
        option.sort_order = sort_order
    if is_active is not None:
        option.is_active = is_active

    db.commit()
    db.refresh(option)

    return {"message": "Customer field option updated"}

@app.delete("/settings/customer-field-options/{option_id}", tags=["Settings"])
async def delete_customer_field_option(
    option_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a customer field option"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can delete customer field options")

    option = db.query(CustomerFieldOption).filter(CustomerFieldOption.option_id == option_id).first()
    if not option:
        raise HTTPException(status_code=404, detail="Customer field option not found")

    db.delete(option)
    db.commit()

    return {"message": "Customer field option deleted"}


# ============================================================================
# RETURN SURVEY SYSTEM ENDPOINTS
# ============================================================================

@app.get("/settings/return-survey-questions", tags=["Settings", "Survey"])
async def get_return_survey_questions(
    hub_id: Optional[int] = Query(None),
    applies_to_battery: Optional[bool] = Query(None),
    applies_to_pue: Optional[bool] = Query(None),
    is_active: Optional[bool] = Query(True),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all return survey questions with optional filters"""
    query = db.query(ReturnSurveyQuestion)

    if hub_id is not None:
        query = query.filter((ReturnSurveyQuestion.hub_id == hub_id) | (ReturnSurveyQuestion.hub_id == None))

    if applies_to_battery is not None:
        query = query.filter(ReturnSurveyQuestion.applies_to_battery == applies_to_battery)

    if applies_to_pue is not None:
        query = query.filter(ReturnSurveyQuestion.applies_to_pue == applies_to_pue)

    if is_active is not None:
        query = query.filter(ReturnSurveyQuestion.is_active == is_active)

    questions = query.order_by(ReturnSurveyQuestion.sort_order).all()

    # Include options for each question
    result = []
    for q in questions:
        question_dict = {
            "question_id": q.question_id,
            "hub_id": q.hub_id,
            "question_text": q.question_text,
            "question_type": q.question_type,
            "help_text": q.help_text,
            "applies_to_battery": q.applies_to_battery,
            "applies_to_pue": q.applies_to_pue,
            "parent_question_id": q.parent_question_id,
            "show_if_parent_answer": q.show_if_parent_answer,
            "is_required": q.is_required,
            "is_active": q.is_active,
            "sort_order": q.sort_order,
            "created_at": q.created_at,
            "updated_at": q.updated_at,
            "options": [
                {
                    "option_id": opt.option_id,
                    "option_text": opt.option_text,
                    "option_value": opt.option_value,
                    "is_open_text_trigger": opt.is_open_text_trigger,
                    "sort_order": opt.sort_order
                }
                for opt in q.options
            ]
        }
        result.append(question_dict)

    return {"questions": result}


@app.post("/settings/return-survey-questions", tags=["Settings", "Survey"])
async def create_return_survey_question(
    question_text: str = Query(...),
    question_type: str = Query(...),
    help_text: Optional[str] = Query(None),
    applies_to_battery: bool = Query(True),
    applies_to_pue: bool = Query(True),
    parent_question_id: Optional[int] = Query(None),
    show_if_parent_answer: Optional[str] = Query(None),
    rating_min: Optional[int] = Query(None),
    rating_max: Optional[int] = Query(None),
    rating_min_label: Optional[str] = Query(None),
    rating_max_label: Optional[str] = Query(None),
    is_required: bool = Query(True),
    is_active: bool = Query(True),
    sort_order: int = Query(0),
    hub_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new return survey question"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can create survey questions")

    new_question = ReturnSurveyQuestion(
        hub_id=hub_id,
        question_text=question_text,
        question_type=question_type,
        help_text=help_text,
        applies_to_battery=applies_to_battery,
        applies_to_pue=applies_to_pue,
        parent_question_id=parent_question_id,
        show_if_parent_answer=show_if_parent_answer,
        rating_min=rating_min,
        rating_max=rating_max,
        rating_min_label=rating_min_label,
        rating_max_label=rating_max_label,
        is_required=is_required,
        is_active=is_active,
        sort_order=sort_order
    )

    db.add(new_question)
    db.commit()
    db.refresh(new_question)

    return {
        "message": "Survey question created",
        "question_id": new_question.question_id,
        "question": {
            "question_id": new_question.question_id,
            "question_text": new_question.question_text,
            "question_type": new_question.question_type,
            "is_active": new_question.is_active,
            "sort_order": new_question.sort_order
        }
    }


@app.put("/settings/return-survey-questions/{question_id}", tags=["Settings", "Survey"])
async def update_return_survey_question(
    question_id: int,
    question_text: Optional[str] = Query(None),
    question_type: Optional[str] = Query(None),
    help_text: Optional[str] = Query(None),
    applies_to_battery: Optional[bool] = Query(None),
    applies_to_pue: Optional[bool] = Query(None),
    parent_question_id: Optional[int] = Query(None),
    show_if_parent_answer: Optional[str] = Query(None),
    rating_min: Optional[int] = Query(None),
    rating_max: Optional[int] = Query(None),
    rating_min_label: Optional[str] = Query(None),
    rating_max_label: Optional[str] = Query(None),
    is_required: Optional[bool] = Query(None),
    is_active: Optional[bool] = Query(None),
    sort_order: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a return survey question"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can update survey questions")

    question = db.query(ReturnSurveyQuestion).filter(ReturnSurveyQuestion.question_id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Survey question not found")

    if question_text is not None:
        question.question_text = question_text
    if question_type is not None:
        question.question_type = question_type
    if help_text is not None:
        question.help_text = help_text
    if applies_to_battery is not None:
        question.applies_to_battery = applies_to_battery
    if applies_to_pue is not None:
        question.applies_to_pue = applies_to_pue
    if parent_question_id is not None:
        question.parent_question_id = parent_question_id
    if show_if_parent_answer is not None:
        question.show_if_parent_answer = show_if_parent_answer
    if rating_min is not None:
        question.rating_min = rating_min
    if rating_max is not None:
        question.rating_max = rating_max
    if rating_min_label is not None:
        question.rating_min_label = rating_min_label
    if rating_max_label is not None:
        question.rating_max_label = rating_max_label
    if is_required is not None:
        question.is_required = is_required
    if is_active is not None:
        question.is_active = is_active
    if sort_order is not None:
        question.sort_order = sort_order

    db.commit()
    db.refresh(question)

    return {"message": "Survey question updated", "question_id": question.question_id}


@app.delete("/settings/return-survey-questions/{question_id}", tags=["Settings", "Survey"])
async def delete_return_survey_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a return survey question"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can delete survey questions")

    question = db.query(ReturnSurveyQuestion).filter(ReturnSurveyQuestion.question_id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Survey question not found")

    db.delete(question)
    db.commit()

    return {"message": "Survey question deleted"}


@app.post("/settings/return-survey-questions/{question_id}/options", tags=["Settings", "Survey"])
async def add_question_option(
    question_id: int,
    option_text: str = Query(...),
    option_value: str = Query(...),
    is_open_text_trigger: bool = Query(False),
    sort_order: int = Query(0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Add an option to a survey question"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can add question options")

    question = db.query(ReturnSurveyQuestion).filter(ReturnSurveyQuestion.question_id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Survey question not found")

    new_option = ReturnSurveyQuestionOption(
        question_id=question_id,
        option_text=option_text,
        option_value=option_value,
        is_open_text_trigger=is_open_text_trigger,
        sort_order=sort_order
    )

    db.add(new_option)
    db.commit()
    db.refresh(new_option)

    return {
        "message": "Question option added",
        "option_id": new_option.option_id,
        "option": {
            "option_id": new_option.option_id,
            "option_text": new_option.option_text,
            "option_value": new_option.option_value,
            "is_open_text_trigger": new_option.is_open_text_trigger,
            "sort_order": new_option.sort_order
        }
    }


@app.put("/settings/return-survey-question-options/{option_id}", tags=["Settings", "Survey"])
async def update_question_option(
    option_id: int,
    option_text: Optional[str] = Query(None),
    option_value: Optional[str] = Query(None),
    is_open_text_trigger: Optional[bool] = Query(None),
    sort_order: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a question option"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can update question options")

    option = db.query(ReturnSurveyQuestionOption).filter(ReturnSurveyQuestionOption.option_id == option_id).first()
    if not option:
        raise HTTPException(status_code=404, detail="Question option not found")

    if option_text is not None:
        option.option_text = option_text
    if option_value is not None:
        option.option_value = option_value
    if is_open_text_trigger is not None:
        option.is_open_text_trigger = is_open_text_trigger
    if sort_order is not None:
        option.sort_order = sort_order

    db.commit()
    db.refresh(option)

    return {"message": "Question option updated", "option_id": option.option_id}


@app.delete("/settings/return-survey-question-options/{option_id}", tags=["Settings", "Survey"])
async def delete_question_option(
    option_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a question option"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can delete question options")

    option = db.query(ReturnSurveyQuestionOption).filter(ReturnSurveyQuestionOption.option_id == option_id).first()
    if not option:
        raise HTTPException(status_code=404, detail="Question option not found")

    db.delete(option)
    db.commit()

    return {"message": "Question option deleted"}


# Survey Response Endpoints

@app.get("/return-survey/questions", tags=["Survey"])
async def get_active_survey_questions(
    rental_type: str = Query(..., regex="^(battery|pue)$"),
    hub_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Get active survey questions for a specific rental type"""
    query = db.query(ReturnSurveyQuestion).filter(
        ReturnSurveyQuestion.is_active == True
    )

    if rental_type == "battery":
        query = query.filter(ReturnSurveyQuestion.applies_to_battery == True)
    else:
        query = query.filter(ReturnSurveyQuestion.applies_to_pue == True)

    if hub_id is not None:
        query = query.filter((ReturnSurveyQuestion.hub_id == hub_id) | (ReturnSurveyQuestion.hub_id == None))

    questions = query.order_by(ReturnSurveyQuestion.sort_order).all()

    result = []
    for q in questions:
        question_dict = {
            "question_id": q.question_id,
            "question_text": q.question_text,
            "question_type": q.question_type,
            "help_text": q.help_text,
            "parent_question_id": q.parent_question_id,
            "show_if_parent_answer": q.show_if_parent_answer,
            "is_required": q.is_required,
            "sort_order": q.sort_order,
            "rating_min": q.rating_min,
            "rating_max": q.rating_max,
            "rating_min_label": q.rating_min_label,
            "rating_max_label": q.rating_max_label,
            "options": [
                {
                    "option_id": opt.option_id,
                    "option_text": opt.option_text,
                    "option_value": opt.option_value,
                    "is_open_text_trigger": opt.is_open_text_trigger,
                    "sort_order": opt.sort_order
                }
                for opt in sorted(q.options, key=lambda x: x.sort_order)
            ]
        }
        result.append(question_dict)

    return {"questions": result}


@app.post("/return-survey/responses", tags=["Survey"])
async def submit_survey_responses(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Submit survey responses for a rental return"""
    data = await request.json()

    battery_rental_id = data.get("battery_rental_id")
    pue_rental_id = data.get("pue_rental_id")
    responses = data.get("responses", [])

    if not battery_rental_id and not pue_rental_id:
        raise HTTPException(status_code=400, detail="Either battery_rental_id or pue_rental_id is required")

    if not responses:
        raise HTTPException(status_code=400, detail="No responses provided")

    # Verify rental exists
    if battery_rental_id:
        rental = db.query(BatteryRental).filter(BatteryRental.rental_id == battery_rental_id).first()
        if not rental:
            raise HTTPException(status_code=404, detail="Battery rental not found")
    else:
        rental = db.query(PUERental).filter(PUERental.pue_rental_id == pue_rental_id).first()
        if not rental:
            raise HTTPException(status_code=404, detail="PUE rental not found")

    # Save each response
    saved_responses = []
    for resp in responses:
        # Convert response_value to string if it's not None
        response_value = resp.get("response_value")
        if response_value is not None and not isinstance(response_value, str):
            response_value = str(response_value)

        new_response = ReturnSurveyResponse(
            battery_rental_id=battery_rental_id,
            pue_rental_id=pue_rental_id,
            question_id=resp["question_id"],
            response_value=response_value,
            response_values=json.dumps(resp.get("response_values")) if resp.get("response_values") else None,
            response_text=resp.get("response_text"),
            user_id=current_user.get("user_id")
        )
        db.add(new_response)
        saved_responses.append(new_response)

    db.commit()

    return {
        "message": f"Survey responses saved successfully",
        "response_count": len(saved_responses)
    }


@app.get("/return-survey/responses", tags=["Survey"])
async def get_survey_responses(
    hub_id: Optional[int] = Query(None),
    rental_type: Optional[str] = Query(None, regex="^(battery|pue)$"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get survey responses with optional filters"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.DATA_ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    query = db.query(ReturnSurveyResponse).join(
        ReturnSurveyQuestion,
        ReturnSurveyResponse.question_id == ReturnSurveyQuestion.question_id
    )

    if rental_type == "battery":
        query = query.filter(ReturnSurveyResponse.battery_rental_id != None)
    elif rental_type == "pue":
        query = query.filter(ReturnSurveyResponse.pue_rental_id != None)

    if start_date:
        query = query.filter(ReturnSurveyResponse.submitted_at >= start_date)

    if end_date:
        query = query.filter(ReturnSurveyResponse.submitted_at <= end_date)

    # Apply hub filter through rental relationship
    if hub_id:
        query = query.outerjoin(BatteryRental, ReturnSurveyResponse.battery_rental_id == BatteryRental.rental_id)
        query = query.outerjoin(PUERental, ReturnSurveyResponse.pue_rental_id == PUERental.pue_rental_id)
        query = query.filter((BatteryRental.hub_id == hub_id) | (PUERental.hub_id == hub_id))

    total = query.count()
    responses = query.order_by(ReturnSurveyResponse.submitted_at.desc()).offset(offset).limit(limit).all()

    result = []
    for resp in responses:
        result.append({
            "response_id": resp.response_id,
            "battery_rental_id": resp.battery_rental_id,
            "pue_rental_id": resp.pue_rental_id,
            "question_id": resp.question_id,
            "question_text": resp.question.question_text if resp.question else None,
            "response_value": resp.response_value,
            "response_values": json.loads(resp.response_values) if resp.response_values else None,
            "response_text": resp.response_text,
            "user_id": resp.user_id,
            "submitted_at": resp.submitted_at
        })

    return {
        "responses": result,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@app.get("/return-survey/responses/export", tags=["Survey"])
async def export_survey_responses(
    hub_id: Optional[int] = Query(None),
    rental_type: Optional[str] = Query(None, regex="^(battery|pue)$"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Export survey responses to CSV"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN, UserRole.DATA_ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    import csv
    import io

    # Build query with same filters as get_survey_responses
    # Need to join ProductiveUseEquipment to get hub_id for PUE rentals
    query = db.query(
        ReturnSurveyResponse,
        ReturnSurveyQuestion,
        BatteryRental,
        PUERental,
        User
    ).join(
        ReturnSurveyQuestion,
        ReturnSurveyResponse.question_id == ReturnSurveyQuestion.question_id
    ).outerjoin(
        BatteryRental,
        ReturnSurveyResponse.battery_rental_id == BatteryRental.rental_id
    ).outerjoin(
        PUERental,
        ReturnSurveyResponse.pue_rental_id == PUERental.pue_rental_id
    ).outerjoin(
        ProductiveUseEquipment,
        PUERental.pue_id == ProductiveUseEquipment.pue_id
    ).outerjoin(
        User,
        ReturnSurveyResponse.user_id == User.user_id
    )

    if rental_type == "battery":
        query = query.filter(ReturnSurveyResponse.battery_rental_id != None)
    elif rental_type == "pue":
        query = query.filter(ReturnSurveyResponse.pue_rental_id != None)

    if start_date:
        query = query.filter(ReturnSurveyResponse.submitted_at >= start_date)

    if end_date:
        query = query.filter(ReturnSurveyResponse.submitted_at <= end_date)

    if hub_id:
        # Filter by hub_id - BatteryRental has hub_id, PUE has it through ProductiveUseEquipment
        query = query.filter(
            or_(
                and_(BatteryRental.hub_id != None, BatteryRental.hub_id == hub_id),
                and_(ProductiveUseEquipment.hub_id != None, ProductiveUseEquipment.hub_id == hub_id)
            )
        )

    results = query.order_by(ReturnSurveyResponse.submitted_at.desc()).all()

    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        'Response ID',
        'Rental Type',
        'Rental ID',
        'User Name',
        'User ID',
        'Question',
        'Question Type',
        'Response Value',
        'Response Values',
        'Response Text',
        'Submitted At'
    ])

    # Write data rows
    for resp, question, battery_rental, pue_rental, user in results:
        rental_type_str = 'Battery' if resp.battery_rental_id else 'PUE'
        rental_id = resp.battery_rental_id or resp.pue_rental_id
        user_name = user.Name if user else 'N/A'
        user_id = user.short_id if user else 'N/A'

        writer.writerow([
            resp.response_id,
            rental_type_str,
            rental_id,
            user_name,
            user_id,
            question.question_text,
            question.question_type,
            resp.response_value or '',
            resp.response_values or '',
            resp.response_text or '',
            resp.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if resp.submitted_at else ''
        ])

    output.seek(0)
    csv_content = output.getvalue()

    # Use Response instead of StreamingResponse to ensure CORS headers are applied
    headers = {
        "Content-Disposition": f"attachment; filename=survey_responses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        "Content-Type": "text/csv",
        "Access-Control-Expose-Headers": "Content-Disposition"
    }

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers=headers
    )


# ============================================================================
# COST STRUCTURE ENDPOINTS
# ============================================================================

@app.get("/settings/cost-structures", tags=["Settings"])
async def get_cost_structures(
    hub_id: Optional[int] = Query(None),
    item_type: Optional[str] = Query(None),
    item_reference: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get cost structure configurations with their components"""
    query = db.query(CostStructure)

    if hub_id:
        query = query.filter(
            or_(
                CostStructure.hub_id == hub_id,
                CostStructure.hub_id.is_(None)
            )
        )

    if item_type:
        query = query.filter(CostStructure.item_type == item_type)

    if item_reference:
        query = query.filter(CostStructure.item_reference == item_reference)

    if is_active is not None:
        query = query.filter(CostStructure.is_active == is_active)

    structures = query.order_by(CostStructure.created_at.desc()).all()

    result = []
    for structure in structures:
        # Get components for this structure
        components = db.query(CostComponent).filter(
            CostComponent.structure_id == structure.structure_id
        ).order_by(CostComponent.sort_order).all()

        # Get duration options for this structure
        duration_opts = db.query(CostStructureDurationOption).filter(
            CostStructureDurationOption.structure_id == structure.structure_id
        ).order_by(CostStructureDurationOption.sort_order).all()

        result.append({
            "structure_id": structure.structure_id,
            "hub_id": structure.hub_id,
            "name": structure.name,
            "description": structure.description,
            "item_type": structure.item_type,
            "item_reference": structure.item_reference,
            "is_active": structure.is_active,
            "count_initial_checkout_as_recharge": structure.count_initial_checkout_as_recharge,
            "is_pay_to_own": structure.is_pay_to_own,
            "item_total_cost": float(structure.item_total_cost) if structure.item_total_cost is not None else None,
            "allow_multiple_items": structure.allow_multiple_items,
            "allow_custom_duration": structure.allow_custom_duration,
            "created_at": structure.created_at,
            "updated_at": structure.updated_at,
            "components": [{
                "component_id": comp.component_id,
                "component_name": comp.component_name,
                "unit_type": comp.unit_type,
                "rate": float(comp.rate),
                "is_calculated_on_return": comp.is_calculated_on_return,
                "sort_order": comp.sort_order,
                "late_fee_action": comp.late_fee_action,
                "late_fee_rate": float(comp.late_fee_rate) if comp.late_fee_rate is not None else None,
                "late_fee_grace_days": comp.late_fee_grace_days,
                "contributes_to_ownership": comp.contributes_to_ownership,
                "is_percentage_of_remaining": comp.is_percentage_of_remaining,
                "percentage_value": float(comp.percentage_value) if comp.percentage_value is not None else None,
                "is_recurring_payment": comp.is_recurring_payment,
                "recurring_interval": float(comp.recurring_interval) if comp.recurring_interval is not None else None
            } for comp in components],
            "duration_options": [{
                "option_id": opt.option_id,
                "input_type": opt.input_type,
                "label": opt.label,
                "custom_unit": opt.custom_unit,
                "default_value": opt.default_value,
                "min_value": opt.min_value,
                "max_value": opt.max_value,
                "dropdown_options": json.loads(opt.dropdown_options) if opt.dropdown_options else None,
                "sort_order": opt.sort_order
            } for opt in duration_opts]
        })

    return {"cost_structures": result}

@app.post("/settings/cost-structures", tags=["Settings"])
async def create_cost_structure(
    hub_id: Optional[int] = Query(None),
    name: str = Query(...),
    description: Optional[str] = Query(None),
    item_type: str = Query(...),
    item_reference: str = Query(...),
    components: str = Query(...),  # JSON string of components array
    duration_options: Optional[str] = Query(None),  # JSON string of duration options array
    count_initial_checkout_as_recharge: bool = Query(False),
    is_pay_to_own: bool = Query(False),
    item_total_cost: Optional[float] = Query(None),
    allow_multiple_items: bool = Query(True),
    allow_custom_duration: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new cost structure with components and duration options.

    Example duration_options JSON:
    [
        {
            "input_type": "custom",
            "label": "Number of Days",
            "custom_unit": "days",
            "default_value": 7,
            "min_value": 1,
            "max_value": 90
        },
        {
            "input_type": "dropdown",
            "label": "Select Rental Period",
            "dropdown_options": "[{\\"value\\": 1, \\"unit\\": \\"weeks\\", \\"label\\": \\"1 Week\\"}, {\\"value\\": 2, \\"unit\\": \\"weeks\\", \\"label\\": \\"2 Weeks\\"}]"
        }
    ]
    """
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can create cost structures")

    # Parse components JSON
    try:
        import json
        components_data = json.loads(components)
    except:
        raise HTTPException(status_code=400, detail="Invalid components JSON")

    # Validate components data
    if not isinstance(components_data, list) or len(components_data) == 0:
        raise HTTPException(status_code=400, detail="Components must be a non-empty array")

    # Parse duration options JSON (optional)
    duration_options_data = []
    if duration_options:
        try:
            duration_options_data = json.loads(duration_options)
            if not isinstance(duration_options_data, list):
                raise HTTPException(status_code=400, detail="Duration options must be an array")
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid duration_options JSON")

    # Create cost structure
    structure = CostStructure(
        hub_id=hub_id,
        name=name,
        description=description,
        item_type=item_type,
        item_reference=item_reference,
        count_initial_checkout_as_recharge=count_initial_checkout_as_recharge,
        is_pay_to_own=is_pay_to_own,
        item_total_cost=item_total_cost,
        allow_multiple_items=allow_multiple_items,
        is_active=True
    )
    db.add(structure)
    db.flush()  # Get structure_id without committing

    # Create components
    for idx, comp_data in enumerate(components_data):
        component = CostComponent(
            structure_id=structure.structure_id,
            component_name=comp_data.get('component_name'),
            unit_type=comp_data.get('unit_type'),
            rate=float(comp_data.get('rate', 0)),
            is_calculated_on_return=comp_data.get('is_calculated_on_return', False),
            sort_order=comp_data.get('sort_order', idx),
            late_fee_action=comp_data.get('late_fee_action', 'continue'),
            late_fee_rate=comp_data.get('late_fee_rate'),
            late_fee_grace_days=comp_data.get('late_fee_grace_days', 0),
            contributes_to_ownership=comp_data.get('contributes_to_ownership', True),
            is_percentage_of_remaining=comp_data.get('is_percentage_of_remaining', False),
            percentage_value=comp_data.get('percentage_value'),
            is_recurring_payment=comp_data.get('is_recurring_payment', False),
            recurring_interval=comp_data.get('recurring_interval')
        )
        db.add(component)

    # Create duration options
    for idx, option_data in enumerate(duration_options_data):
        duration_option = CostStructureDurationOption(
            structure_id=structure.structure_id,
            input_type=option_data.get('input_type'),
            label=option_data.get('label'),
            custom_unit=option_data.get('custom_unit'),
            default_value=option_data.get('default_value'),
            min_value=option_data.get('min_value'),
            max_value=option_data.get('max_value'),
            dropdown_options=option_data.get('dropdown_options'),
            sort_order=option_data.get('sort_order', idx)
        )
        db.add(duration_option)

    db.commit()
    db.refresh(structure)

    # Return with components and duration options
    components = db.query(CostComponent).filter(
        CostComponent.structure_id == structure.structure_id
    ).order_by(CostComponent.sort_order).all()

    duration_opts = db.query(CostStructureDurationOption).filter(
        CostStructureDurationOption.structure_id == structure.structure_id
    ).order_by(CostStructureDurationOption.sort_order).all()

    return {
        "structure_id": structure.structure_id,
        "hub_id": structure.hub_id,
        "name": structure.name,
        "description": structure.description,
        "item_type": structure.item_type,
        "item_reference": structure.item_reference,
        "is_active": structure.is_active,
        "count_initial_checkout_as_recharge": structure.count_initial_checkout_as_recharge,
        "created_at": structure.created_at,
        "updated_at": structure.updated_at,
        "components": [{
            "component_id": comp.component_id,
            "component_name": comp.component_name,
            "unit_type": comp.unit_type,
            "rate": float(comp.rate),
            "is_calculated_on_return": comp.is_calculated_on_return,
            "sort_order": comp.sort_order,
            "late_fee_action": comp.late_fee_action,
            "late_fee_rate": float(comp.late_fee_rate) if comp.late_fee_rate is not None else None,
            "late_fee_grace_days": comp.late_fee_grace_days
        } for comp in components],
        "duration_options": [{
            "option_id": opt.option_id,
            "input_type": opt.input_type,
            "label": opt.label,
            "custom_unit": opt.custom_unit,
            "default_value": opt.default_value,
            "min_value": opt.min_value,
            "max_value": opt.max_value,
            "dropdown_options": opt.dropdown_options,
            "sort_order": opt.sort_order
        } for opt in duration_opts]
    }

@app.put("/settings/cost-structures/{structure_id}", tags=["Settings"])
async def update_cost_structure(
    structure_id: int,
    name: Optional[str] = Query(None),
    description: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    components: Optional[str] = Query(None),  # JSON string of components array
    duration_options: Optional[str] = Query(None),  # JSON string of duration options array
    count_initial_checkout_as_recharge: Optional[bool] = Query(None),
    is_pay_to_own: Optional[bool] = Query(None),
    item_total_cost: Optional[float] = Query(None),
    allow_multiple_items: Optional[bool] = Query(None),
    allow_custom_duration: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a cost structure and optionally its components and duration options"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can update cost structures")

    structure = db.query(CostStructure).filter(CostStructure.structure_id == structure_id).first()

    if not structure:
        raise HTTPException(status_code=404, detail="Cost structure not found")

    # Update structure fields
    if name is not None:
        structure.name = name
    if description is not None:
        structure.description = description
    if is_active is not None:
        structure.is_active = is_active
    if count_initial_checkout_as_recharge is not None:
        structure.count_initial_checkout_as_recharge = count_initial_checkout_as_recharge
    if is_pay_to_own is not None:
        structure.is_pay_to_own = is_pay_to_own
    if item_total_cost is not None:
        structure.item_total_cost = item_total_cost
    if allow_multiple_items is not None:
        structure.allow_multiple_items = allow_multiple_items
    if allow_custom_duration is not None:
        structure.allow_custom_duration = allow_custom_duration

    # Update components if provided
    if components is not None:
        try:
            import json
            components_data = json.loads(components)
        except:
            raise HTTPException(status_code=400, detail="Invalid components JSON")

        # Delete existing components
        db.query(CostComponent).filter(CostComponent.structure_id == structure_id).delete()

        # Create new components
        for idx, comp_data in enumerate(components_data):
            component = CostComponent(
                structure_id=structure_id,
                component_name=comp_data.get('component_name'),
                unit_type=comp_data.get('unit_type'),
                rate=float(comp_data.get('rate', 0)),
                is_calculated_on_return=comp_data.get('is_calculated_on_return', False),
                sort_order=comp_data.get('sort_order', idx),
                late_fee_action=comp_data.get('late_fee_action', 'continue'),
                late_fee_rate=comp_data.get('late_fee_rate'),
                late_fee_grace_days=comp_data.get('late_fee_grace_days', 0),
                contributes_to_ownership=comp_data.get('contributes_to_ownership', True),
                is_percentage_of_remaining=comp_data.get('is_percentage_of_remaining', False),
                percentage_value=comp_data.get('percentage_value'),
                is_recurring_payment=comp_data.get('is_recurring_payment', False),
                recurring_interval=comp_data.get('recurring_interval')
            )
            db.add(component)

    # Update duration options if provided
    if duration_options is not None:
        try:
            import json
            duration_options_data = json.loads(duration_options)
        except:
            raise HTTPException(status_code=400, detail="Invalid duration_options JSON")

        # Delete existing duration options
        db.query(CostStructureDurationOption).filter(
            CostStructureDurationOption.structure_id == structure_id
        ).delete()

        # Create new duration options
        for idx, opt_data in enumerate(duration_options_data):
            duration_option = CostStructureDurationOption(
                structure_id=structure_id,
                input_type=opt_data.get('input_type'),
                label=opt_data.get('label'),
                custom_unit=opt_data.get('custom_unit'),
                default_value=opt_data.get('default_value'),
                min_value=opt_data.get('min_value'),
                max_value=opt_data.get('max_value'),
                dropdown_options=opt_data.get('dropdown_options'),
                sort_order=opt_data.get('sort_order', idx)
            )
            db.add(duration_option)

    db.commit()
    db.refresh(structure)

    # Return with components and duration options
    components_list = db.query(CostComponent).filter(
        CostComponent.structure_id == structure.structure_id
    ).order_by(CostComponent.sort_order).all()

    duration_opts = db.query(CostStructureDurationOption).filter(
        CostStructureDurationOption.structure_id == structure.structure_id
    ).order_by(CostStructureDurationOption.sort_order).all()

    return {
        "structure_id": structure.structure_id,
        "hub_id": structure.hub_id,
        "name": structure.name,
        "description": structure.description,
        "item_type": structure.item_type,
        "item_reference": structure.item_reference,
        "is_active": structure.is_active,
        "count_initial_checkout_as_recharge": structure.count_initial_checkout_as_recharge,
        "created_at": structure.created_at,
        "updated_at": structure.updated_at,
        "components": [{
            "component_id": comp.component_id,
            "component_name": comp.component_name,
            "unit_type": comp.unit_type,
            "rate": float(comp.rate),
            "is_calculated_on_return": comp.is_calculated_on_return,
            "sort_order": comp.sort_order,
            "late_fee_action": comp.late_fee_action,
            "late_fee_rate": float(comp.late_fee_rate) if comp.late_fee_rate is not None else None,
            "late_fee_grace_days": comp.late_fee_grace_days
        } for comp in components_list],
        "duration_options": [{
            "option_id": opt.option_id,
            "input_type": opt.input_type,
            "label": opt.label,
            "custom_unit": opt.custom_unit,
            "default_value": opt.default_value,
            "min_value": opt.min_value,
            "max_value": opt.max_value,
            "dropdown_options": opt.dropdown_options,
            "sort_order": opt.sort_order
        } for opt in duration_opts]
    }

@app.delete("/settings/cost-structures/{structure_id}", tags=["Settings"])
async def delete_cost_structure(
    structure_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a cost structure and its components"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can delete cost structures")

    structure = db.query(CostStructure).filter(CostStructure.structure_id == structure_id).first()

    if not structure:
        raise HTTPException(status_code=404, detail="Cost structure not found")

    # Components will be deleted automatically due to CASCADE
    db.delete(structure)
    db.commit()

    return {"message": "Cost structure deleted"}

@app.post("/settings/cost-structures/{structure_id}/estimate", tags=["Settings"])
async def estimate_rental_cost(
    structure_id: int,
    duration_value: float = Query(...),
    duration_unit: str = Query(...),
    kwh_estimate: Optional[float] = Query(None),
    estimated_kwh: Optional[float] = Query(None),
    kg_estimate: Optional[float] = Query(None),
    vat_percentage: float = Query(0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Calculate estimated cost for a rental based on cost structure"""
    # Accept either kwh_estimate or estimated_kwh
    if estimated_kwh is not None:
        kwh_estimate = estimated_kwh
    structure = db.query(CostStructure).filter(CostStructure.structure_id == structure_id).first()

    if not structure:
        raise HTTPException(status_code=404, detail="Cost structure not found")

    # Get components
    components = db.query(CostComponent).filter(
        CostComponent.structure_id == structure_id
    ).order_by(CostComponent.sort_order).all()

    # Calculate cost breakdown
    breakdown = []
    subtotal = 0.0

    for comp in components:
        amount = 0.0
        quantity = 0.0

        if comp.unit_type == 'per_day':
            if duration_unit == 'days':
                quantity = duration_value
            elif duration_unit == 'weeks':
                quantity = duration_value * 7
            elif duration_unit == 'months':
                quantity = duration_value * 30  # Approximate
            elif duration_unit == 'hours':
                quantity = duration_value / 24
            amount = quantity * comp.rate

        elif comp.unit_type == 'per_hour':
            if duration_unit == 'hours':
                quantity = duration_value
            elif duration_unit == 'days':
                quantity = duration_value * 24
            elif duration_unit == 'weeks':
                quantity = duration_value * 7 * 24
            elif duration_unit == 'months':
                quantity = duration_value * 30 * 24
            amount = quantity * comp.rate

        elif comp.unit_type == 'per_kwh':
            if kwh_estimate is not None:
                quantity = kwh_estimate
                amount = quantity * comp.rate
            else:
                # Can't calculate without estimate, will be calculated on return
                quantity = 0
                amount = 0

        elif comp.unit_type == 'per_kg':
            if kg_estimate is not None:
                quantity = kg_estimate
                amount = quantity * comp.rate
            else:
                quantity = 0
                amount = 0

        elif comp.unit_type == 'per_week':
            if duration_unit == 'weeks':
                quantity = duration_value
            elif duration_unit == 'days':
                quantity = duration_value / 7
            elif duration_unit == 'months':
                quantity = duration_value * 4.33  # Approximate weeks per month
            elif duration_unit == 'hours':
                quantity = duration_value / (24 * 7)
            amount = quantity * comp.rate

        elif comp.unit_type == 'per_month':
            if duration_unit == 'months':
                quantity = duration_value
            elif duration_unit == 'weeks':
                quantity = duration_value / 4.33
            elif duration_unit == 'days':
                quantity = duration_value / 30
            elif duration_unit == 'hours':
                quantity = duration_value / (24 * 30)
            amount = quantity * comp.rate

        elif comp.unit_type == 'per_recharge':
            # If cost structure counts initial checkout as recharge, start with 1
            if structure.count_initial_checkout_as_recharge:
                quantity = 1
                amount = quantity * comp.rate
            else:
                quantity = 0
                amount = 0

        elif comp.unit_type == 'one_time':
            # One-time fee charged once regardless of duration
            quantity = 1
            amount = comp.rate

        elif comp.unit_type == 'fixed':
            quantity = 1
            amount = comp.rate

        breakdown.append({
            "component_name": comp.component_name,
            "unit_type": comp.unit_type,
            "rate": float(comp.rate),
            "quantity": float(quantity),
            "amount": float(amount),
            "is_calculated_on_return": comp.is_calculated_on_return
        })

        subtotal += amount

    # Calculate VAT
    vat_amount = subtotal * (vat_percentage / 100)
    total = subtotal + vat_amount

    # Check for estimated components
    has_estimated_component = any(comp.is_calculated_on_return for comp in components)

    return {
        "structure_id": structure.structure_id,
        "structure_name": structure.name,
        "breakdown": breakdown,
        "subtotal": float(subtotal),
        "vat_percentage": float(vat_percentage),
        "vat_amount": float(vat_amount),
        "total": float(total),
        "deposit_amount": float(structure.deposit_amount or 0),
        "has_estimated_component": has_estimated_component
    }

@app.get("/settings/hub/{hub_id}", tags=["Settings"])
async def get_hub_settings(
    hub_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get hub settings"""
    settings = db.query(HubSettings).filter(HubSettings.hub_id == hub_id).first()

    if not settings:
        # Return default settings
        return {
            "hub_id": hub_id,
            "debt_notification_threshold": -100,
            "default_currency": "USD",
            "currency_symbol": None,
            "vat_percentage": 0.0,
            "timezone": "UTC",
            "overdue_notification_hours": 24,
            "default_table_rows_per_page": 50,
            "battery_status_green_hours": 3,
            "battery_status_orange_hours": 8
        }

    return {
        "hub_id": settings.hub_id,
        "debt_notification_threshold": float(settings.debt_notification_threshold) if settings.debt_notification_threshold else -100,
        "default_currency": settings.default_currency or "USD",
        "currency_symbol": settings.currency_symbol,
        "vat_percentage": float(settings.vat_percentage) if settings.vat_percentage else 0.0,
        "timezone": settings.timezone or "UTC",
        "overdue_notification_hours": settings.overdue_notification_hours if settings.overdue_notification_hours else 24,
        "default_table_rows_per_page": settings.default_table_rows_per_page if settings.default_table_rows_per_page else 50,
        "battery_status_green_hours": settings.battery_status_green_hours if settings.battery_status_green_hours else 3,
        "battery_status_orange_hours": settings.battery_status_orange_hours if settings.battery_status_orange_hours else 8
    }

@app.put("/settings/hub/{hub_id}", tags=["Settings"])
async def update_hub_settings(
    hub_id: int,
    debt_notification_threshold: Optional[float] = Query(None),
    default_currency: Optional[str] = Query(None),
    vat_percentage: Optional[float] = Query(None),
    timezone: Optional[str] = Query(None),
    overdue_notification_hours: Optional[int] = Query(None),
    default_table_rows_per_page: Optional[int] = Query(None),
    battery_status_green_hours: Optional[int] = Query(None),
    battery_status_orange_hours: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update hub settings"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can update hub settings")

    settings = db.query(HubSettings).filter(HubSettings.hub_id == hub_id).first()

    if not settings:
        settings = HubSettings(hub_id=hub_id)
        db.add(settings)

    if debt_notification_threshold is not None:
        settings.debt_notification_threshold = debt_notification_threshold

    if default_currency is not None:
        settings.default_currency = default_currency

    if vat_percentage is not None:
        settings.vat_percentage = vat_percentage

    if timezone is not None:
        settings.timezone = timezone

    if overdue_notification_hours is not None:
        settings.overdue_notification_hours = overdue_notification_hours

    if default_table_rows_per_page is not None:
        settings.default_table_rows_per_page = default_table_rows_per_page

    if battery_status_green_hours is not None:
        settings.battery_status_green_hours = battery_status_green_hours

    if battery_status_orange_hours is not None:
        settings.battery_status_orange_hours = battery_status_orange_hours

    db.commit()
    db.refresh(settings)

    return {"message": "Hub settings updated"}

# ============================================================================
# SUBSCRIPTION ENDPOINTS
# ============================================================================

@app.get("/settings/subscription-packages", tags=["Settings", "Subscriptions"])
async def get_subscription_packages(
    hub_id: Optional[int] = Query(None),
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all subscription packages for a hub"""
    if not hub_id:
        hub_id = current_user.get('hub_id')

    if not hub_id:
        raise HTTPException(status_code=400, detail="Hub ID required")

    query = db.query(SubscriptionPackage).filter(SubscriptionPackage.hub_id == hub_id)

    if not include_inactive:
        query = query.filter(SubscriptionPackage.is_active == True)

    packages = query.all()

    result = []
    for pkg in packages:
        # Get package items
        items = db.query(SubscriptionPackageItem).filter(
            SubscriptionPackageItem.package_id == pkg.package_id
        ).order_by(SubscriptionPackageItem.sort_order).all()

        result.append({
            "package_id": pkg.package_id,
            "hub_id": pkg.hub_id,
            "package_name": pkg.package_name,
            "description": pkg.description,
            "billing_period": pkg.billing_period,
            "price": float(pkg.price),
            "currency": pkg.currency,
            "max_concurrent_batteries": pkg.max_concurrent_batteries,
            "max_concurrent_pue": pkg.max_concurrent_pue,
            "included_kwh": float(pkg.included_kwh) if pkg.included_kwh else None,
            "overage_rate_kwh": float(pkg.overage_rate_kwh) if pkg.overage_rate_kwh else None,
            "auto_renew": pkg.auto_renew,
            "is_active": pkg.is_active,
            "created_at": pkg.created_at.isoformat() if pkg.created_at else None,
            "items": [{
                "item_id": item.item_id,
                "item_type": item.item_type,
                "item_reference": item.item_reference,
                "quantity_limit": item.quantity_limit,
                "sort_order": item.sort_order
            } for item in items]
        })

    return {"packages": result}


@app.post("/settings/subscription-packages", tags=["Settings", "Subscriptions"])
async def create_subscription_package(
    hub_id: int = Query(...),
    package_name: str = Query(...),
    billing_period: str = Query(...),  # 'daily', 'weekly', 'monthly', 'yearly'
    price: float = Query(...),
    description: Optional[str] = Query(None),
    currency: str = Query("USD"),
    max_concurrent_batteries: Optional[int] = Query(None),
    max_concurrent_pue: Optional[int] = Query(None),
    included_kwh: Optional[float] = Query(None),
    overage_rate_kwh: Optional[float] = Query(None),
    auto_renew: bool = Query(True),
    items: str = Query("[]"),  # JSON string of items
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new subscription package"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can create subscription packages")

    # Validate billing period
    if billing_period not in ['daily', 'weekly', 'monthly', 'yearly']:
        raise HTTPException(status_code=400, detail="Invalid billing period")

    # Create package
    package = SubscriptionPackage(
        hub_id=hub_id,
        package_name=package_name,
        description=description,
        billing_period=billing_period,
        price=price,
        currency=currency,
        max_concurrent_batteries=max_concurrent_batteries,
        max_concurrent_pue=max_concurrent_pue,
        included_kwh=included_kwh,
        overage_rate_kwh=overage_rate_kwh,
        auto_renew=auto_renew,
        is_active=True
    )

    db.add(package)
    db.flush()

    # Parse and add items
    try:
        items_data = json.loads(items)
        for idx, item_data in enumerate(items_data):
            package_item = SubscriptionPackageItem(
                package_id=package.package_id,
                item_type=item_data.get('item_type'),
                item_reference=item_data.get('item_reference'),
                quantity_limit=item_data.get('quantity_limit'),
                sort_order=item_data.get('sort_order', idx)
            )
            db.add(package_item)
    except json.JSONDecodeError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Invalid items JSON")

    db.commit()
    db.refresh(package)

    return {
        "package_id": package.package_id,
        "package_name": package.package_name,
        "message": "Subscription package created successfully"
    }


@app.put("/settings/subscription-packages/{package_id}", tags=["Settings", "Subscriptions"])
async def update_subscription_package(
    package_id: int,
    package_name: Optional[str] = Query(None),
    billing_period: Optional[str] = Query(None),
    price: Optional[float] = Query(None),
    description: Optional[str] = Query(None),
    currency: Optional[str] = Query(None),
    max_concurrent_batteries: Optional[int] = Query(None),
    max_concurrent_pue: Optional[int] = Query(None),
    included_kwh: Optional[float] = Query(None),
    overage_rate_kwh: Optional[float] = Query(None),
    auto_renew: Optional[bool] = Query(None),
    is_active: Optional[bool] = Query(None),
    items: Optional[str] = Query(None),  # JSON string of items
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update an existing subscription package"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can update subscription packages")

    package = db.query(SubscriptionPackage).filter(
        SubscriptionPackage.package_id == package_id
    ).first()

    if not package:
        raise HTTPException(status_code=404, detail="Subscription package not found")

    # Update fields
    if package_name is not None:
        package.package_name = package_name
    if billing_period is not None:
        if billing_period not in ['daily', 'weekly', 'monthly', 'yearly']:
            raise HTTPException(status_code=400, detail="Invalid billing period")
        package.billing_period = billing_period
    if price is not None:
        package.price = price
    if description is not None:
        package.description = description
    if currency is not None:
        package.currency = currency
    if max_concurrent_batteries is not None:
        package.max_concurrent_batteries = max_concurrent_batteries
    if max_concurrent_pue is not None:
        package.max_concurrent_pue = max_concurrent_pue
    if included_kwh is not None:
        package.included_kwh = included_kwh
    if overage_rate_kwh is not None:
        package.overage_rate_kwh = overage_rate_kwh
    if auto_renew is not None:
        package.auto_renew = auto_renew
    if is_active is not None:
        package.is_active = is_active

    # Update items if provided
    if items is not None:
        try:
            items_data = json.loads(items)
            # Delete existing items
            db.query(SubscriptionPackageItem).filter(
                SubscriptionPackageItem.package_id == package_id
            ).delete()

            # Add new items
            for idx, item_data in enumerate(items_data):
                package_item = SubscriptionPackageItem(
                    package_id=package.package_id,
                    item_type=item_data.get('item_type'),
                    item_reference=item_data.get('item_reference'),
                    quantity_limit=item_data.get('quantity_limit'),
                    sort_order=item_data.get('sort_order', idx)
                )
                db.add(package_item)
        except json.JSONDecodeError:
            db.rollback()
            raise HTTPException(status_code=400, detail="Invalid items JSON")

    package.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": "Subscription package updated successfully"}


@app.delete("/settings/subscription-packages/{package_id}", tags=["Settings", "Subscriptions"])
async def delete_subscription_package(
    package_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a subscription package"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can delete subscription packages")

    package = db.query(SubscriptionPackage).filter(
        SubscriptionPackage.package_id == package_id
    ).first()

    if not package:
        raise HTTPException(status_code=404, detail="Subscription package not found")

    # Check if any active subscriptions use this package
    active_subs = db.query(UserSubscription).filter(
        UserSubscription.package_id == package_id,
        UserSubscription.status == 'active'
    ).count()

    if active_subs > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete package: {active_subs} active subscriptions are using it"
        )

    # Delete package items
    db.query(SubscriptionPackageItem).filter(
        SubscriptionPackageItem.package_id == package_id
    ).delete()

    # Delete package
    db.delete(package)
    db.commit()

    return {"message": "Subscription package deleted successfully"}


@app.get("/users/{user_id}/subscriptions", tags=["Users", "Subscriptions"])
async def get_user_subscriptions(
    user_id: int,
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all subscriptions for a user"""
    query = db.query(UserSubscription).filter(UserSubscription.user_id == user_id)

    if not include_inactive:
        query = query.filter(UserSubscription.status == 'active')

    subscriptions = query.all()

    result = []
    for sub in subscriptions:
        # Get package details
        package = db.query(SubscriptionPackage).filter(
            SubscriptionPackage.package_id == sub.package_id
        ).first()

        if package:
            # Get package items
            items = db.query(SubscriptionPackageItem).filter(
                SubscriptionPackageItem.package_id == package.package_id
            ).order_by(SubscriptionPackageItem.sort_order).all()

            result.append({
                "subscription_id": sub.subscription_id,
                "user_id": sub.user_id,
                "package_id": sub.package_id,
                "package_name": package.package_name,
                "billing_period": package.billing_period,
                "price": float(package.price),
                "currency": package.currency,
                "start_date": sub.start_date.isoformat() if sub.start_date else None,
                "end_date": sub.end_date.isoformat() if sub.end_date else None,
                "next_billing_date": sub.next_billing_date.isoformat() if sub.next_billing_date else None,
                "status": sub.status,
                "auto_renew": sub.auto_renew,
                "kwh_used_current_period": float(sub.kwh_used_current_period),
                "included_kwh": float(package.included_kwh) if package.included_kwh else None,
                "period_start_date": sub.period_start_date.isoformat() if sub.period_start_date else None,
                "notes": sub.notes,
                "created_at": sub.created_at.isoformat() if sub.created_at else None,
                "items": [{
                    "item_type": item.item_type,
                    "item_reference": item.item_reference,
                    "quantity_limit": item.quantity_limit
                } for item in items]
            })

    return {"subscriptions": result}


@app.post("/users/{user_id}/subscriptions", tags=["Users", "Subscriptions"])
async def create_user_subscription(
    user_id: int,
    package_id: int = Query(...),
    start_date: Optional[str] = Query(None),  # ISO format
    auto_renew: bool = Query(True),
    notes: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new subscription for a user"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can create subscriptions")

    # Verify user exists
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify package exists
    package = db.query(SubscriptionPackage).filter(
        SubscriptionPackage.package_id == package_id
    ).first()
    if not package:
        raise HTTPException(status_code=404, detail="Subscription package not found")

    # Parse start date or use current time
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format")
    else:
        start_dt = datetime.now(timezone.utc)

    # Calculate next billing date based on billing period
    if package.billing_period == 'daily':
        next_billing = start_dt + timedelta(days=1)
    elif package.billing_period == 'weekly':
        next_billing = start_dt + timedelta(weeks=1)
    elif package.billing_period == 'monthly':
        next_billing = start_dt + timedelta(days=30)
    elif package.billing_period == 'yearly':
        next_billing = start_dt + timedelta(days=365)
    else:
        next_billing = start_dt + timedelta(days=30)

    # Create subscription
    subscription = UserSubscription(
        user_id=user_id,
        package_id=package_id,
        start_date=start_dt,
        end_date=None,  # Active indefinitely
        next_billing_date=next_billing,
        status='active',
        auto_renew=auto_renew,
        kwh_used_current_period=0,
        period_start_date=start_dt,
        notes=notes
    )

    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    return {
        "subscription_id": subscription.subscription_id,
        "message": "Subscription created successfully"
    }


@app.put("/users/{user_id}/subscriptions/{subscription_id}", tags=["Users", "Subscriptions"])
async def update_user_subscription(
    user_id: int,
    subscription_id: int,
    status: Optional[str] = Query(None),  # 'active', 'paused', 'cancelled', 'expired'
    auto_renew: Optional[bool] = Query(None),
    end_date: Optional[str] = Query(None),  # ISO format
    notes: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a user's subscription"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can update subscriptions")

    subscription = db.query(UserSubscription).filter(
        UserSubscription.subscription_id == subscription_id,
        UserSubscription.user_id == user_id
    ).first()

    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    # Update fields
    if status is not None:
        if status not in ['active', 'paused', 'cancelled', 'expired']:
            raise HTTPException(status_code=400, detail="Invalid status")
        subscription.status = status

    if auto_renew is not None:
        subscription.auto_renew = auto_renew

    if end_date is not None:
        try:
            subscription.end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format")

    if notes is not None:
        subscription.notes = notes

    subscription.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": "Subscription updated successfully"}


@app.delete("/users/{user_id}/subscriptions/{subscription_id}", tags=["Users", "Subscriptions"])
async def delete_user_subscription(
    user_id: int,
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a user's subscription"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can delete subscriptions")

    subscription = db.query(UserSubscription).filter(
        UserSubscription.subscription_id == subscription_id,
        UserSubscription.user_id == user_id
    ).first()

    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    db.delete(subscription)
    db.commit()

    return {"message": "Subscription deleted successfully"}


@app.get("/rentals/check-subscription-coverage", tags=["Rentals", "Subscriptions"])
async def check_subscription_coverage(
    user_id: int = Query(...),
    item_type: str = Query(...),  # 'battery' or 'pue'
    item_reference: str = Query(...),  # battery capacity, 'all', pue_type, pue_item_id
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Check if a rental item is covered by user's active subscription"""
    # Get user's active subscriptions
    subscriptions = db.query(UserSubscription).filter(
        UserSubscription.user_id == user_id,
        UserSubscription.status == 'active'
    ).all()

    if not subscriptions:
        return {
            "covered": False,
            "message": "No active subscription"
        }

    # Check each subscription
    for sub in subscriptions:
        # Get package items
        package_items = db.query(SubscriptionPackageItem).filter(
            SubscriptionPackageItem.package_id == sub.package_id
        ).all()

        for item in package_items:
            # Check if item matches
            if item.item_type == item_type:
                # Check for exact match or "all" coverage
                if item.item_reference == 'all' or item.item_reference == item_reference:
                    # Get package details
                    package = db.query(SubscriptionPackage).filter(
                        SubscriptionPackage.package_id == sub.package_id
                    ).first()

                    # Check concurrent limits
                    if item_type == 'battery' and package.max_concurrent_batteries:
                        # Count active battery rentals for this user
                        active_battery_rentals = db.query(Rental).filter(
                            Rental.user_id == user_id,
                            Rental.is_active == True,
                            Rental.battery_returned_date.is_(None),
                            Rental.subscription_id == sub.subscription_id
                        ).count()

                        if active_battery_rentals >= package.max_concurrent_batteries:
                            return {
                                "covered": False,
                                "message": f"Subscription limit reached: {active_battery_rentals}/{package.max_concurrent_batteries} batteries"
                            }

                    return {
                        "covered": True,
                        "subscription_id": sub.subscription_id,
                        "subscription_name": package.package_name,
                        "message": f"Covered by '{package.package_name}' subscription"
                    }

    return {
        "covered": False,
        "message": "Item not covered by subscription"
    }

# ============================================================================
# ACCOUNTS ENDPOINTS
# ============================================================================

@app.get("/accounts/user/{user_id}", tags=["Accounts"])
async def get_user_account(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get user account details"""
    account = db.query(UserAccount).filter(UserAccount.user_id == user_id).first()

    if not account:
        # Auto-create account
        account = UserAccount(
            user_id=user_id,
            balance=0,
            total_spent=0,
            total_owed=0
        )
        db.add(account)
        db.commit()
        db.refresh(account)

    return {
        "account_id": account.account_id,
        "user_id": account.user_id,
        "balance": float(account.balance),
        "total_spent": float(account.total_spent),
        "total_owed": float(account.total_owed),
        "created_at": account.created_at
    }

@app.post("/accounts/user/{user_id}/transaction", tags=["Accounts"])
async def create_transaction(
    user_id: int,
    transaction_type: str = Query(...),
    amount: float = Query(...),
    description: Optional[str] = Query(None),
    related_rental_id: Optional[int] = Query(None),
    payment_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Record a transaction (payment, charge, refund, adjustment)"""
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can record transactions")

    # Get or create user account
    account = db.query(UserAccount).filter(UserAccount.user_id == user_id).first()
    if not account:
        account = UserAccount(user_id=user_id, balance=0, total_spent=0, total_owed=0)
        db.add(account)
        db.flush()

    # Calculate new balance before creating transaction
    old_balance = account.balance

    # Update account balance based on transaction type
    if transaction_type == 'payment':
        account.balance += amount
        account.total_owed = max(0, account.total_owed - amount)
    elif transaction_type == 'credit':
        account.balance += amount
    elif transaction_type == 'charge':
        account.balance -= amount
        account.total_spent += amount
        account.total_owed += amount
    elif transaction_type == 'refund':
        account.balance += amount
    elif transaction_type == 'adjustment':
        account.balance += amount

    # Create transaction with account_id and balance_after
    transaction = AccountTransaction(
        account_id=account.account_id,
        rental_id=related_rental_id,
        transaction_type=transaction_type,
        amount=amount,
        balance_after=account.balance,
        description=description,
        payment_type=payment_type
    )
    db.add(transaction)
    db.flush()  # Get transaction ID before creating ledger entries

    # Create double-entry ledger entries
    try:
        from api.app.utils.accounting import create_ledger_entries
        ledger_entries = create_ledger_entries(
            db=db,
            transaction_id=transaction.transaction_id,
            transaction_type=transaction_type,
            amount=amount,
            description=description
        )
    except Exception as e:
        # Log error but don't fail transaction (graceful degradation)
        print(f"Warning: Failed to create ledger entries: {e}")

    db.commit()

    return {
        "message": "Transaction recorded",
        "transaction_id": transaction.transaction_id,
        "ledger_entries_created": len(ledger_entries) if 'ledger_entries' in locals() else 0
    }

@app.get("/accounts/user/{user_id}/transactions", tags=["Accounts"])
async def get_user_transactions(
    user_id: int,
    limit: Optional[int] = Query(100),
    offset: Optional[int] = Query(0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get transaction history for a user"""
    # First get the user's account
    user_account = db.query(UserAccount).filter(UserAccount.user_id == user_id).first()

    if not user_account:
        # If no account exists yet, return empty transactions
        return {
            "user_id": user_id,
            "transactions": [],
            "count": 0
        }

    # Get transactions for this account
    transactions = db.query(AccountTransaction).filter(
        AccountTransaction.account_id == user_account.account_id
    ).order_by(
        AccountTransaction.created_at.desc()
    ).limit(limit).offset(offset).all()

    return {
        "user_id": user_id,
        "transactions": [
            {
                "transaction_id": t.transaction_id,
                "transaction_type": t.transaction_type,
                "amount": float(t.amount),
                "description": t.description,
                "related_rental_id": t.rental_id,
                "timestamp": t.created_at.isoformat() if t.created_at else None,
                "payment_type": t.payment_type
            }
            for t in transactions
        ],
        "count": len(transactions)
    }

@app.get("/accounts/hub/{hub_id}/summary", tags=["Accounts"])
async def get_hub_summary(
    hub_id: int,
    time_period: Optional[str] = Query("all"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get financial summary for a hub"""
    # Calculate time range
    now = datetime.now(timezone.utc)
    start_time = None

    if time_period == "day":
        start_time = now - timedelta(days=1)
    elif time_period == "week":
        start_time = now - timedelta(weeks=1)
    elif time_period == "month":
        start_time = now - timedelta(days=30)

    # Get rentals for this hub
    battery_ids_query = db.query(BEPPPBattery.battery_id).filter(BEPPPBattery.hub_id == hub_id)
    battery_ids = [b[0] for b in battery_ids_query.all()]

    rentals_query = db.query(Rental).filter(Rental.battery_id.in_(battery_ids))

    if start_time:
        rentals_query = rentals_query.filter(Rental.timestamp_taken >= start_time)

    rentals = rentals_query.all()

    # Calculate totals
    total_revenue = sum(float(getattr(r, 'amount_paid', 0) or 0) for r in rentals)
    active_rentals = len([r for r in rentals if r.is_active])

    # Get users with debt in this hub
    user_ids_query = db.query(User.user_id).filter(User.hub_id == hub_id)
    user_ids = [u[0] for u in user_ids_query.all()]

    # Get total debt from user accounts (consistent with users in debt query)
    accounts_with_debt_query = db.query(UserAccount).filter(
        UserAccount.user_id.in_(user_ids),
        UserAccount.total_owed > 0
    )

    accounts_with_debt = accounts_with_debt_query.count()
    total_owed = sum(float(account.total_owed or 0) for account in accounts_with_debt_query.all())

    return {
        "total_revenue": total_revenue,
        "outstanding_debt": total_owed,
        "active_rentals": active_rentals,
        "total_users": len(user_ids),
        "users_with_debt": accounts_with_debt,
        "time_period": time_period
    }

@app.post("/accounts/{account_id}/reconcile", tags=["Accounts"])
async def reconcile_user_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Reconcile a user account to check for discrepancies.
    Compares calculated balance from transactions with actual balance.
    """
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can reconcile accounts")

    from api.app.utils.accounting import reconcile_account
    result = reconcile_account(db, account_id, current_user.get('user_id'))

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result

@app.get("/accounts/{account_id}/summary", tags=["Accounts"])
async def get_user_account_summary(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get comprehensive account summary with all financial metrics"""
    from api.app.utils.accounting import get_account_summary
    summary = get_account_summary(db, account_id)

    if "error" in summary:
        raise HTTPException(status_code=404, detail=summary["error"])

    return summary

@app.post("/accounts/user/{user_id}/payment", tags=["Accounts"])
async def record_payment(
    user_id: int,
    amount: float = Query(..., description="Payment amount"),
    payment_type: str = Query(..., description="Payment method: cash, mobile_money, bank_transfer, card"),
    description: Optional[str] = Query(None, description="Optional payment notes"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Record a payment from a user (reduces their debt).
    Tracks who received the payment for audit purposes.
    """
    if current_user.get('role') not in [UserRole.USER, UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Only authorized staff can record payments")

    if amount <= 0:
        raise HTTPException(status_code=400, detail="Payment amount must be positive")

    # Get or create user account
    account = db.query(UserAccount).filter(UserAccount.user_id == user_id).first()
    if not account:
        account = UserAccount(user_id=user_id, balance=0, total_spent=0, total_owed=0)
        db.add(account)
        db.flush()

    # Get user info for audit trail
    receiver_user = db.query(User).filter(User.user_id == current_user.get('user_id')).first()
    receiver_name = receiver_user.Name if receiver_user and receiver_user.Name else "Unknown"

    # Store old balance for response
    old_balance = float(account.balance)

    # Update account balance (payment increases balance, reduces debt)
    account.balance += amount
    account.total_owed = max(0, account.total_owed - amount)

    # Build description with receiver info
    payment_desc = f"{payment_type.replace('_', ' ').title()} payment received by {receiver_name}"
    if description:
        payment_desc += f" - {description}"

    # Create transaction record
    transaction = AccountTransaction(
        account_id=account.account_id,
        rental_id=None,
        transaction_type='debit',  # Payment reduces debt
        amount=amount,
        balance_after=account.balance,
        description=payment_desc,
        payment_type=payment_type,
        created_by=current_user.get('user_id')
    )
    db.add(transaction)
    db.flush()  # Flush to get transaction_id before creating ledger entries

    # Create double-entry ledger entries
    try:
        from api.app.utils.accounting import create_ledger_entries
        ledger_entries = create_ledger_entries(
            db=db,
            transaction_id=transaction.transaction_id,
            transaction_type='payment',
            amount=amount,
            description=payment_desc
        )
    except Exception as e:
        # Log error but don't fail transaction
        print(f"Warning: Failed to create ledger entries: {e}")

    db.commit()
    db.refresh(account)

    return {
        "success": True,
        "message": f"Payment of {amount} recorded successfully",
        "transaction_id": transaction.transaction_id,
        "old_balance": old_balance,
        "new_balance": float(account.balance),
        "amount_paid": amount,
        "payment_type": payment_type,
        "received_by": receiver_name,
        "timestamp": transaction.created_at.isoformat() if transaction.created_at else None
    }

@app.post("/accounts/user/{user_id}/manual-adjustment", tags=["Accounts"])
async def create_manual_adjustment(
    user_id: int,
    amount: float = Query(..., description="Adjustment amount (positive increases balance, negative decreases)"),
    reason: str = Query(..., description="Reason for manual adjustment"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a manual journal entry to adjust a user's balance.
    Logs the adjustment with the administrator who made it.
    """
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can make manual adjustments")

    if amount == 0:
        raise HTTPException(status_code=400, detail="Adjustment amount cannot be zero")

    # Get or create user account
    account = db.query(UserAccount).filter(UserAccount.user_id == user_id).first()
    if not account:
        account = UserAccount(user_id=user_id, balance=0, total_spent=0, total_owed=0)
        db.add(account)
        db.flush()

    # Get admin user info for audit trail
    admin_user = db.query(User).filter(User.user_id == current_user.get('user_id')).first()
    admin_name = admin_user.Name if admin_user and admin_user.Name else "Unknown Admin"

    # Store old balance
    old_balance = float(account.balance)

    # Apply adjustment
    account.balance += amount

    # Build description
    adjustment_type = "Credit" if amount > 0 else "Debit"
    description = f"Manual {adjustment_type} Adjustment by {admin_name}: {reason}"

    # Create transaction record
    transaction = AccountTransaction(
        account_id=account.account_id,
        rental_id=None,
        transaction_type='manual_adjustment',
        amount=abs(amount),
        balance_after=account.balance,
        description=description,
        payment_type='manual_journal_entry',
        created_by=current_user.get('user_id')
    )
    db.add(transaction)
    db.flush()

    # Create double-entry ledger entries
    try:
        from api.app.utils.accounting import create_ledger_entries
        ledger_entries = create_ledger_entries(
            db=db,
            transaction_id=transaction.transaction_id,
            transaction_type='manual_adjustment',
            amount=abs(amount),
            description=description
        )
    except Exception as e:
        # Log error but don't fail transaction
        print(f"Warning: Failed to create ledger entries: {e}")

    db.commit()
    db.refresh(account)

    return {
        "success": True,
        "message": f"Manual adjustment of {amount} applied successfully",
        "transaction_id": transaction.transaction_id,
        "old_balance": old_balance,
        "new_balance": float(account.balance),
        "adjustment_amount": amount,
        "adjustment_type": adjustment_type,
        "reason": reason,
        "created_by": admin_name,
        "timestamp": transaction.created_at.isoformat() if transaction.created_at else None
    }

@app.get("/accounts/financial-report", tags=["Accounts"])
async def get_financial_report(
    hub_id: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Generate financial report using double-entry accounting.
    Shows assets, liabilities, revenue, expenses, and net income.
    """
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can view financial reports")

    from api.app.utils.accounting import get_financial_report
    from datetime import datetime

    # Parse dates if provided
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None

    report = get_financial_report(db, hub_id, start, end)
    return report

@app.get("/accounts/users/in-debt", tags=["Accounts"])
async def get_users_in_debt(
    hub_id: Optional[int] = Query(None),
    min_debt: Optional[float] = Query(0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get list of users with outstanding debt"""
    query = db.query(
        UserAccount,
        User
    ).join(
        User, UserAccount.user_id == User.user_id
    ).filter(
        UserAccount.total_owed > min_debt
    )

    if hub_id:
        query = query.filter(User.hub_id == hub_id)

    results = query.all()

    users_in_debt = []
    for account, user in results:
        users_in_debt.append({
            "user_id": user.user_id,
            "user": user.username or user.Name or f"User {user.user_id}",
            "balance": float(account.balance),
            "total_owed": float(account.total_owed),
            "total_spent": float(account.total_spent)
        })

    return {"users": users_in_debt}

# ============================================================================
# NOTIFICATIONS
# ============================================================================

def check_and_create_notifications(hub_id: int, db: Session):
    """
    Check for conditions that warrant notifications and create them.
    Called on user login.
    """
    # Get hub settings
    hub_settings = db.query(HubSettings).filter(HubSettings.hub_id == hub_id).first()
    if not hub_settings:
        return

    current_time = datetime.now(timezone.utc)

    # 1. Check for overdue rentals
    overdue_threshold_hours = hub_settings.overdue_notification_hours or 24
    overdue_time = current_time - timedelta(hours=overdue_threshold_hours)

    # Query rentals via battery to get hub_id
    overdue_rentals = db.query(Rental).join(
        BEPPPBattery, Rental.battery_id == BEPPPBattery.battery_id
    ).filter(
        BEPPPBattery.hub_id == hub_id,
        Rental.status == 'active',
        Rental.due_back < overdue_time
    ).all()

    for rental in overdue_rentals:
        # Check if notification already exists for this rental
        existing = db.query(Notification).filter(
            Notification.hub_id == hub_id,
            Notification.notification_type == 'overdue_rental',
            Notification.link_id == str(rental.rentral_id)
        ).first()

        if not existing:
            # Get user info
            user = db.query(User).filter(User.user_id == rental.user_id).first()
            user_name = user.username or user.Name or f"User {user.user_id}"

            # Make due_back timezone-aware if it's naive
            due_back_aware = rental.due_back.replace(tzinfo=timezone.utc) if rental.due_back.tzinfo is None else rental.due_back
            hours_overdue = int((current_time - due_back_aware).total_seconds() / 3600)

            notification = Notification(
                hub_id=hub_id,
                user_id=None,  # Hub-wide notification for admins
                notification_type='overdue_rental',
                title='Overdue Rental',
                message=f'{user_name} has rental #{rental.rentral_id} overdue by {hours_overdue} hours.',
                severity='warning',
                link_type='rental',
                link_id=str(rental.rentral_id)
            )
            db.add(notification)

    # 2. Check for users exceeding debt threshold
    debt_threshold = hub_settings.debt_notification_threshold or -100.0

    # Get all users at this hub
    users_at_hub = db.query(User).filter(User.hub_id == hub_id).all()
    user_ids = [u.user_id for u in users_at_hub]

    # Find accounts below threshold
    accounts_below_threshold = db.query(UserAccount).filter(
        UserAccount.user_id.in_(user_ids),
        UserAccount.balance < debt_threshold
    ).all()

    for account in accounts_below_threshold:
        # Check if notification already exists for this user's debt
        existing = db.query(Notification).filter(
            Notification.hub_id == hub_id,
            Notification.notification_type == 'debt_threshold',
            Notification.link_id == str(account.user_id),
            Notification.is_read == False  # Only check unread notifications
        ).first()

        if not existing:
            user = db.query(User).filter(User.user_id == account.user_id).first()
            user_name = user.username or user.Name or f"User {user.user_id}"

            # Get currency symbol
            currency = hub_settings.default_currency or 'USD'
            symbols = {'USD': '$', 'GBP': '£', 'EUR': '€', 'MWK': 'MK'}
            symbol = symbols.get(currency, currency)

            notification = Notification(
                hub_id=hub_id,
                user_id=None,  # Hub-wide notification for admins
                notification_type='debt_threshold',
                title='Debt Threshold Exceeded',
                message=f'{user_name} has exceeded the debt threshold. Current balance: {symbol}{abs(account.balance):.2f}',
                severity='error',
                link_type='user',
                link_id=str(account.user_id)
            )
            db.add(notification)

    db.commit()


@app.get("/notifications", tags=["Notifications"])
async def get_notifications(
    hub_id: Optional[int] = Query(None),
    unread_only: bool = Query(False),
    limit: int = Query(50),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get notifications for the user's hub"""
    if not hub_id:
        hub_id = current_user.get('hub_id')

    if not hub_id:
        raise HTTPException(status_code=400, detail="Hub ID required")

    query = db.query(Notification).filter(Notification.hub_id == hub_id)

    if unread_only:
        query = query.filter(Notification.is_read == False)

    notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()

    return {
        "notifications": [
            {
                "id": n.notification_id,
                "type": n.notification_type,
                "title": n.title,
                "message": n.message,
                "severity": n.severity,
                "read": n.is_read,
                "link_type": n.link_type,
                "link_id": n.link_id,
                "timestamp": n.created_at.isoformat()
            }
            for n in notifications
        ]
    }


@app.post("/notifications", tags=["Notifications"])
async def create_notification(
    notification: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new notification.

    Required fields:
    - message: str
    - notification_type: str (e.g., 'maintenance', 'alert', 'info')

    Optional fields:
    - title: str (default: auto-generated from type)
    - severity: str ('info', 'warning', 'error', 'success', default: 'info')
    - link_type: str ('battery', 'rental', 'user', 'account')
    - link_id: str (ID of related entity)
    - hub_id: int (default: current user's hub)
    - user_id: int (default: null for hub-wide notifications)
    """
    # Get hub_id
    hub_id = notification.get('hub_id') or current_user.get('hub_id')
    if not hub_id:
        raise HTTPException(status_code=400, detail="Hub ID required")

    # Check permissions
    if current_user.get('role') not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Validate required fields
    if not notification.get('message'):
        raise HTTPException(status_code=400, detail="Message is required")

    notification_type = notification.get('notification_type', 'info')

    # Auto-generate title if not provided
    title = notification.get('title')
    if not title:
        type_titles = {
            'maintenance': 'Maintenance Required',
            'alert': 'Alert',
            'overdue_rental': 'Overdue Rental',
            'low_battery': 'Low Battery',
            'payment_overdue': 'Payment Overdue',
            'info': 'Information'
        }
        title = type_titles.get(notification_type, 'Notification')

    # Create notification
    new_notification = Notification(
        hub_id=hub_id,
        user_id=notification.get('user_id'),
        notification_type=notification_type,
        title=title,
        message=notification['message'],
        severity=notification.get('severity', 'info'),
        link_type=notification.get('link_type'),
        link_id=str(notification.get('link_id')) if notification.get('link_id') else None
    )

    try:
        db.add(new_notification)
        db.commit()
        db.refresh(new_notification)

        return {
            "notification_id": new_notification.notification_id,
            "message": "Notification created successfully"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create notification: {str(e)}")


@app.post("/notifications/check", tags=["Notifications"])
async def trigger_notification_check(
    hub_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Manually trigger notification check (called on login)"""
    if not hub_id:
        hub_id = current_user.get('hub_id')

    if not hub_id:
        raise HTTPException(status_code=400, detail="Hub ID required")

    check_and_create_notifications(hub_id, db)

    return {"message": "Notification check completed"}


@app.put("/notifications/{notification_id}/read", tags=["Notifications"])
async def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Mark a notification as read"""
    notification = db.query(Notification).filter(
        Notification.notification_id == notification_id
    ).first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    # Verify user has access to this hub's notifications
    if current_user.get('hub_id') != notification.hub_id:
        raise HTTPException(status_code=403, detail="Access denied")

    notification.is_read = True
    db.commit()

    return {"message": "Notification marked as read"}


@app.put("/notifications/mark-all-read", tags=["Notifications"])
async def mark_all_notifications_as_read(
    hub_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Mark all notifications as read for a hub"""
    if not hub_id:
        hub_id = current_user.get('hub_id')

    if not hub_id:
        raise HTTPException(status_code=400, detail="Hub ID required")

    # Verify user has access to this hub
    if current_user.get('hub_id') != hub_id:
        raise HTTPException(status_code=403, detail="Access denied")

    db.query(Notification).filter(
        Notification.hub_id == hub_id,
        Notification.is_read == False
    ).update({"is_read": True})

    db.commit()

    return {"message": "All notifications marked as read"}


# ============================================================================
# JOB CARDS / MAINTENANCE BOARD
# ============================================================================

@app.post("/job-cards/", tags=["Job Cards"])
async def create_job_card(
    card: JobCardCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new job card"""
    from models import JobCard, JobCardActivity

    # Get hub_id from current user
    hub_id = current_user.get('hub_id')
    if not hub_id:
        raise HTTPException(status_code=400, detail="User must belong to a hub")

    # Parse due_date if provided
    due_date_parsed = None
    if card.due_date:
        try:
            # Try parsing as date only (YYYY-MM-DD)
            if len(card.due_date) == 10:
                due_date_parsed = datetime.strptime(card.due_date, '%Y-%m-%d')
            else:
                # Try parsing as full datetime
                due_date_parsed = datetime.fromisoformat(card.due_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD or ISO datetime")

    # Create the job card
    new_card = JobCard(
        hub_id=hub_id,
        title=card.title,
        description=card.description,
        status=card.status,
        priority=card.priority,
        assigned_to=card.assigned_to,
        linked_entity_type=card.linked_entity_type,
        linked_battery_id=card.linked_battery_id,
        linked_pue_id=card.linked_pue_id,
        linked_user_id=card.linked_user_id,
        linked_rental_id=card.linked_rental_id,
        due_date=due_date_parsed,
        created_by=current_user.get('user_id')
    )

    db.add(new_card)
    db.flush()  # Get the card_id

    # Create initial activity entry
    activity = JobCardActivity(
        card_id=new_card.card_id,
        activity_type='created',
        description=f"Card created by {current_user.get('username', 'user')}",
        created_by=current_user.get('user_id')
    )
    db.add(activity)

    db.commit()
    db.refresh(new_card)

    return {
        "card_id": new_card.card_id,
        "message": "Job card created successfully"
    }


@app.get("/job-cards/", tags=["Job Cards"])
async def list_job_cards(
    hub_id: Optional[int] = Query(None, description="Filter by hub ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    assigned_to: Optional[int] = Query(None, description="Filter by assigned user"),
    linked_entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    linked_entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List job cards with optional filters"""
    from models import JobCard

    # Build query
    query = db.query(JobCard)

    # Access control: superadmin sees all, others see their hub only
    if current_user.get('role') != 'SUPERADMIN':
        query = query.filter(JobCard.hub_id == current_user.get('hub_id'))
    elif hub_id:
        query = query.filter(JobCard.hub_id == hub_id)

    # Apply filters
    if status:
        query = query.filter(JobCard.status == status)
    if assigned_to:
        query = query.filter(JobCard.assigned_to == assigned_to)
    if linked_entity_type:
        query = query.filter(JobCard.linked_entity_type == linked_entity_type)
        if linked_entity_id:
            if linked_entity_type == 'battery':
                query = query.filter(JobCard.linked_battery_id == linked_entity_id)
            elif linked_entity_type == 'pue':
                query = query.filter(JobCard.linked_pue_id == linked_entity_id)
            elif linked_entity_type == 'user':
                query = query.filter(JobCard.linked_user_id == int(linked_entity_id))
            elif linked_entity_type == 'rental':
                query = query.filter(JobCard.linked_rental_id == int(linked_entity_id))

    # Order by sort_order, then created_at
    query = query.order_by(JobCard.sort_order, JobCard.created_at.desc())

    cards = query.all()

    # Format response
    result = []
    for card in cards:
        card_dict = {
            "card_id": card.card_id,
            "hub_id": card.hub_id,
            "title": card.title,
            "description": card.description,
            "status": card.status,
            "priority": card.priority,
            "sort_order": card.sort_order,
            "assigned_to": card.assigned_to,
            "assigned_user_name": card.assigned_user.Name if card.assigned_user else None,
            "linked_entity_type": card.linked_entity_type,
            "linked_battery_id": card.linked_battery_id,
            "linked_pue_id": card.linked_pue_id,
            "linked_user_id": card.linked_user_id,
            "linked_rental_id": card.linked_rental_id,
            "due_date": card.due_date,
            "created_at": card.created_at,
            "updated_at": card.updated_at,
            "started_at": card.started_at,
            "completed_at": card.completed_at,
            "created_by": card.created_by,
            "creator_name": card.creator.Name if card.creator else None,
            "activity_count": len(card.activities)
        }

        # Add linked entity details
        if card.linked_battery_id and card.linked_battery:
            card_dict["linked_entity_name"] = card.linked_battery.battery_id
        elif card.linked_pue_id and card.linked_pue:
            card_dict["linked_entity_name"] = card.linked_pue.name
        elif card.linked_user_id and card.linked_user:
            card_dict["linked_entity_name"] = card.linked_user.Name
        elif card.linked_rental_id and card.linked_rental:
            card_dict["linked_entity_name"] = f"Rental #{card.linked_rental_id}"
        else:
            card_dict["linked_entity_name"] = None

        result.append(card_dict)

    return {"cards": result, "total": len(result)}


@app.get("/job-cards/admin-users", tags=["Job Cards"])
async def get_admin_users_for_assignment(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get list of admin/superadmin users for job card assignment"""
    from models import User

    # Get users with ADMIN or SUPERADMIN roles only
    users = db.query(User).filter(
        User.user_access_level.in_(['admin', 'superadmin'])
    ).all()

    result = []
    for user in users:
        result.append({
            "user_id": user.user_id,
            "Name": user.Name or user.username,
            "username": user.username,
            "role": user.user_access_level
        })

    return {"users": result}


@app.get("/job-cards/{card_id}", tags=["Job Cards"])
async def get_job_card(
    card_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a single job card with full activity history"""
    from models import JobCard

    card = db.query(JobCard).filter(JobCard.card_id == card_id).first()

    if not card:
        raise HTTPException(status_code=404, detail="Job card not found")

    # Access control
    if current_user.get('role') != 'SUPERADMIN' and card.hub_id != current_user.get('hub_id'):
        raise HTTPException(status_code=403, detail="Access denied")

    # Format activities
    activities = []
    for activity in card.activities:
        activities.append({
            "activity_id": activity.activity_id,
            "activity_type": activity.activity_type,
            "description": activity.description,
            "metadata": activity.activity_metadata,
            "created_at": activity.created_at,
            "created_by": activity.created_by,
            "creator_name": activity.creator.Name if activity.creator else None
        })

    # Build response
    card_dict = {
        "card_id": card.card_id,
        "hub_id": card.hub_id,
        "title": card.title,
        "description": card.description,
        "status": card.status,
        "priority": card.priority,
        "sort_order": card.sort_order,
        "assigned_to": card.assigned_to,
        "assigned_user_name": card.assigned_user.Name if card.assigned_user else None,
        "linked_entity_type": card.linked_entity_type,
        "linked_battery_id": card.linked_battery_id,
        "linked_pue_id": card.linked_pue_id,
        "linked_user_id": card.linked_user_id,
        "linked_rental_id": card.linked_rental_id,
        "due_date": card.due_date,
        "created_at": card.created_at,
        "updated_at": card.updated_at,
        "started_at": card.started_at,
        "completed_at": card.completed_at,
        "created_by": card.created_by,
        "creator_name": card.creator.Name if card.creator else None,
        "activities": activities
    }

    # Add linked entity details
    if card.linked_battery_id and card.linked_battery:
        card_dict["linked_entity_name"] = card.linked_battery.battery_id
        card_dict["linked_entity_details"] = {
            "battery_id": card.linked_battery.battery_id,
            "status": card.linked_battery.status
        }
    elif card.linked_pue_id and card.linked_pue:
        card_dict["linked_entity_name"] = card.linked_pue.name
        card_dict["linked_entity_details"] = {
            "pue_id": card.linked_pue.pue_id,
            "name": card.linked_pue.name,
            "status": card.linked_pue.status
        }
    elif card.linked_user_id and card.linked_user:
        card_dict["linked_entity_name"] = card.linked_user.Name
        card_dict["linked_entity_details"] = {
            "user_id": card.linked_user.user_id,
            "name": card.linked_user.Name,
            "mobile_number": card.linked_user.mobile_number
        }
    elif card.linked_rental_id and card.linked_rental:
        card_dict["linked_entity_name"] = f"Rental #{card.linked_rental_id}"
        card_dict["linked_entity_details"] = {
            "rental_id": card.linked_rental_id,
            "status": card.linked_rental.status,
            "user_name": card.linked_rental.user.Name if card.linked_rental.user else None
        }

    return card_dict


@app.put("/job-cards/{card_id}", tags=["Job Cards"])
async def update_job_card(
    card_id: int,
    card_update: JobCardUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a job card and create activity entries for changes"""
    from models import JobCard, JobCardActivity
    import json

    card = db.query(JobCard).filter(JobCard.card_id == card_id).first()

    if not card:
        raise HTTPException(status_code=404, detail="Job card not found")

    # Access control
    if current_user.get('role') != 'SUPERADMIN' and card.hub_id != current_user.get('hub_id'):
        raise HTTPException(status_code=403, detail="Access denied")

    # Track changes for activity log
    changes = []

    # Update status
    if card_update.status is not None and card_update.status != card.status:
        old_status = card.status
        card.status = card_update.status
        changes.append({
            "type": "status_changed",
            "description": f"Status changed from {old_status} to {card_update.status}",
            "metadata": json.dumps({"old_status": old_status, "new_status": card_update.status})
        })

        # Update started_at or completed_at
        if card_update.status == 'in_progress' and not card.started_at:
            card.started_at = datetime.now()
        elif card_update.status == 'done' and not card.completed_at:
            card.completed_at = datetime.now()

    # Update priority
    if card_update.priority is not None and card_update.priority != card.priority:
        old_priority = card.priority
        card.priority = card_update.priority
        changes.append({
            "type": "updated",
            "description": f"Priority changed from {old_priority} to {card_update.priority}",
            "metadata": json.dumps({"old_priority": old_priority, "new_priority": card_update.priority})
        })

    # Update assignment
    if card_update.assigned_to is not None and card_update.assigned_to != card.assigned_to:
        old_user = db.query(User).filter(User.user_id == card.assigned_to).first() if card.assigned_to else None
        new_user = db.query(User).filter(User.user_id == card_update.assigned_to).first()
        card.assigned_to = card_update.assigned_to
        changes.append({
            "type": "assigned",
            "description": f"Assigned to {new_user.Name if new_user else 'Unassigned'}" + (f" (was: {old_user.Name})" if old_user else ""),
            "metadata": json.dumps({"old_user_id": card.assigned_to, "new_user_id": card_update.assigned_to})
        })

    # Update due date
    if card_update.due_date is not None:
        # Parse the date string
        try:
            if len(card_update.due_date) == 10:
                new_due_date = datetime.strptime(card_update.due_date, '%Y-%m-%d')
            else:
                new_due_date = datetime.fromisoformat(card_update.due_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD or ISO datetime")

        if new_due_date != card.due_date:
            old_due = card.due_date
            card.due_date = new_due_date
            changes.append({
                "type": "due_date_changed",
                "description": f"Due date changed to {new_due_date.strftime('%Y-%m-%d')}",
                "metadata": json.dumps({"old_due_date": str(old_due) if old_due else None, "new_due_date": str(new_due_date)})
            })

    # Update title and description
    if card_update.title is not None:
        card.title = card_update.title
    if card_update.description is not None:
        card.description = card_update.description

    # Update sort order
    if card_update.sort_order is not None:
        card.sort_order = card_update.sort_order

    # Create activity entries for changes
    for change in changes:
        activity = JobCardActivity(
            card_id=card.card_id,
            activity_type=change["type"],
            description=change["description"],
            metadata=change.get("metadata"),
            created_by=current_user.get('user_id')
        )
        db.add(activity)

    db.commit()
    db.refresh(card)

    return {"message": "Job card updated successfully", "changes_logged": len(changes)}


@app.delete("/job-cards/{card_id}", tags=["Job Cards"])
async def delete_job_card(
    card_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a job card"""
    from models import JobCard

    card = db.query(JobCard).filter(JobCard.card_id == card_id).first()

    if not card:
        raise HTTPException(status_code=404, detail="Job card not found")

    # Access control
    if current_user.get('role') != 'SUPERADMIN' and card.hub_id != current_user.get('hub_id'):
        raise HTTPException(status_code=403, detail="Access denied")

    db.delete(card)
    db.commit()

    return {"message": "Job card deleted successfully"}


@app.post("/job-cards/{card_id}/activities", tags=["Job Cards"])
async def add_job_card_activity(
    card_id: int,
    activity: JobCardActivityCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Add a comment or activity to a job card"""
    from models import JobCard, JobCardActivity

    card = db.query(JobCard).filter(JobCard.card_id == card_id).first()

    if not card:
        raise HTTPException(status_code=404, detail="Job card not found")

    # Access control
    if current_user.get('role') != 'SUPERADMIN' and card.hub_id != current_user.get('hub_id'):
        raise HTTPException(status_code=403, detail="Access denied")

    new_activity = JobCardActivity(
        card_id=card_id,
        activity_type=activity.activity_type,
        description=activity.description,
        activity_metadata=activity.metadata,
        created_by=current_user.get('user_id')
    )

    db.add(new_activity)
    db.commit()
    db.refresh(new_activity)

    return {
        "activity_id": new_activity.activity_id,
        "message": "Activity added successfully"
    }


@app.put("/job-cards/reorder", tags=["Job Cards"])
async def reorder_job_cards(
    updates: List[JobCardReorder],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Batch update sort order and status for drag-and-drop"""
    from models import JobCard, JobCardActivity
    import json

    updated_count = 0

    for update in updates:
        card = db.query(JobCard).filter(JobCard.card_id == update.card_id).first()

        if not card:
            continue

        # Access control
        if current_user.get('role') != 'SUPERADMIN' and card.hub_id != current_user.get('hub_id'):
            continue

        # Track status changes
        if update.status != card.status:
            old_status = card.status
            card.status = update.status

            # Update started_at or completed_at
            if update.status == 'in_progress' and not card.started_at:
                card.started_at = datetime.now()
            elif update.status == 'done' and not card.completed_at:
                card.completed_at = datetime.now()

            # Create activity
            activity = JobCardActivity(
                card_id=card.card_id,
                activity_type='status_changed',
                description=f"Status changed from {old_status} to {update.status} (drag & drop)",
                metadata=json.dumps({"old_status": old_status, "new_status": update.status}),
                created_by=current_user.get('user_id')
            )
            db.add(activity)

        card.sort_order = update.sort_order
        updated_count += 1

    db.commit()

    return {"message": f"Updated {updated_count} job cards"}

# ============================================================================
# RUN THE APP
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)