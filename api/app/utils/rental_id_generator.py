"""
Rental ID Generator Utility

Generates unique rental IDs in the format: RNT-YYYY-MMDDHHMMSS-XXX
Where:
- RNT: Prefix for rental
- YYYY: Year
- MMDDHHMMSS: Month, Day, Hour, Minute, Second
- XXX: Random 3-digit number for collision handling
"""

from datetime import datetime
import random
from sqlalchemy.orm import Session
from typing import Optional


def generate_rental_id(db: Session, max_attempts: int = 10) -> str:
    """
    Generate a unique rental ID for display/transaction purposes.

    Note: This generates a string ID like "RNT-2025-1209123456-123" that is used
    for transaction descriptions and display purposes only. It is NOT stored in
    the database as the primary key (rentral_id is a BIGINT auto-generated field).

    Args:
        db: Database session (kept for API compatibility but not used)
        max_attempts: Maximum number of attempts (kept for compatibility)

    Returns:
        Unique rental ID string in format: RNT-YYYY-MMDDHHMMSS-XXX
    """
    # Get current timestamp
    now = datetime.now()

    # Format: RNT-YYYY-MMDDHHMMSS-XXX
    year = now.strftime("%Y")
    timestamp = now.strftime("%m%d%H%M%S")
    random_suffix = f"{random.randint(0, 999):03d}"

    rental_id = f"RNT-{year}-{timestamp}-{random_suffix}"

    # Note: We don't check for duplicates because:
    # 1. This ID is not stored in the database (no rental_unique_id column exists)
    # 2. Collision chance is extremely low (timestamp precision + random suffix)
    # 3. The actual primary key is the auto-generated BIGINT rentral_id field

    return rental_id


def validate_rental_id_format(rental_id: str) -> bool:
    """
    Validate that a rental ID follows the expected format.

    Args:
        rental_id: The rental ID to validate

    Returns:
        True if valid, False otherwise
    """
    if not rental_id:
        return False

    parts = rental_id.split('-')

    # Should have 4 parts: RNT, YYYY, MMDDHHMMSS, XXX
    if len(parts) != 4:
        return False

    prefix, year, timestamp, suffix = parts

    # Check prefix
    if prefix != "RNT":
        return False

    # Check year (4 digits)
    if not (year.isdigit() and len(year) == 4):
        return False

    # Check timestamp (10 digits: MMDDHHMMSS)
    if not (timestamp.isdigit() and len(timestamp) == 10):
        return False

    # Check suffix (3 digits)
    if not (suffix.isdigit() and len(suffix) == 3):
        return False

    return True
