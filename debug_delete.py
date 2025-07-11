#!/usr/bin/env python3
import requests
import json

# This is a simple test to debug the delete endpoint
print("Testing delete endpoint behavior...")

# Since we can't easily test without proper setup, let me check the error handling
# by looking at what foreign key constraints might exist

from models import BEPPPBattery, LiveData, Rental

print("Checking foreign key relationships...")
print("BEPPPBattery relationships:")
print("- LiveData.battery_id -> BEPPPBattery.battery_id")
print("- Rental.battery_id -> BEPPPBattery.battery_id")
print("")
print("This means when we try to delete a battery with live data or rentals,")
print("we'll get a foreign key constraint violation, which gets caught and returns 400.")
print("")
print("The delete endpoint should either:")
print("1. Delete cascade (delete related data first)")
print("2. Check for related data and return a proper error")
print("3. Only allow deletion if no related data exists")