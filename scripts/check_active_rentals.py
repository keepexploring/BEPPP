#!/usr/bin/env python3
"""Quick script to check active rentals discrepancy"""
from database import SessionLocal
from models import Rental
from datetime import datetime, timezone

db = SessionLocal()

# Get all rentals matching "active" filter
active_rentals = db.query(Rental).filter(
    Rental.is_active == True,
    Rental.battery_returned_date.is_(None)
).all()

print(f"Found {len(active_rentals)} rentals matching active filter")
print("\nDetails:")
for rental in active_rentals:
    status = "returned" if rental.battery_returned_date else "active"
    if status == "active" and rental.due_back:
        due_back = rental.due_back
        if due_back.tzinfo is None:
            due_back = due_back.replace(tzinfo=timezone.utc)
        if due_back < datetime.now(timezone.utc):
            status = "overdue"

    print(f"  Rental {rental.rentral_id}: "
          f"is_active={rental.is_active}, "
          f"battery_returned_date={rental.battery_returned_date}, "
          f"status='{status}'")

# Count by computed status
active_count = sum(1 for r in active_rentals if (not r.battery_returned_date))
print(f"\nRentals with status='active': {active_count}")

db.close()
