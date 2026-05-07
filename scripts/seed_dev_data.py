#!/usr/bin/env python3
"""
Seed local dev database with batteries, live data, users, PUE types, and rentals.
Safe to run multiple times — skips items that already exist (by ID/username/short_id).

Usage:
    DATABASE_URL=postgresql://beppp:changeme@localhost:5432/beppp \
        python scripts/seed_dev_data.py
"""
import os
import sys
import random
import math
from datetime import datetime, timedelta

# Allow running from repo root or scripts/ dir
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://beppp:test_password_123@localhost:5432/beppp_test'
)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

from models import (
    Base, SolarHub, User, BEPPPBattery, LiveData,
    ProductiveUseEquipment, PUEType,
    BatteryRental, BatteryRentalItem,
    PUERental,
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

NOW = datetime.utcnow()
HUB_ID = 1

print(f"Connected to {DATABASE_URL.split('@')[-1]}")

# ─── Hub (must exist) ────────────────────────────────────────────────────────

hub = db.query(SolarHub).filter_by(hub_id=HUB_ID).first()
if not hub:
    print("ERROR: hub_id=1 not found. Run the normal DB init first.")
    sys.exit(1)
print(f"Hub: {hub.what_three_word_location}")

# ─── PUE Types ────────────────────────────────────────────────────────────────

PUE_TYPE_DEFS = [
    ("Rice Milling",      "Electric rice mill / dehusker"),
    ("Phone Charging",    "Mobile phone and small device charging"),
    ("Barbershop",        "Electric clippers and salon equipment"),
    ("TV & Entertainment","Television, radio, and lighting"),
    ("Grain Processing",  "Maize and grain grinding mills"),
]
pue_type_map = {}  # name -> PUEType
for name, desc in PUE_TYPE_DEFS:
    existing = db.query(PUEType).filter_by(type_name=name, hub_id=HUB_ID).first()
    if not existing:
        t = PUEType(type_name=name, description=desc, hub_id=HUB_ID)
        db.add(t)
        db.flush()
        pue_type_map[name] = t
        print(f"  + PUE type: {name}")
    else:
        pue_type_map[name] = existing
        print(f"  ~ PUE type exists: {name}")
db.commit()

# ─── Users ───────────────────────────────────────────────────────────────────

USER_DEFS = [
    ("amara_diallo",  "Amara",     "Diallo",    "user"),
    ("fatima_kone",   "Fatima",    "Koné",      "user"),
    ("ibrahima_sow",  "Ibrahima",  "Sow",       "user"),
    ("mariama_bah",   "Mariama",   "Bah",       "user"),
    ("ousmane_barry", "Ousmane",   "Barry",     "user"),
    ("aissatou_jallo","Aissatou",  "Jallo",     "user"),
    ("mamadou_diallo","Mamadou",   "Diallo",    "user"),
    ("hawa_camara",   "Hawa",      "Camara",    "user"),
]
user_map = {}  # username -> User
for username, first, last, role in USER_DEFS:
    u = db.query(User).filter_by(username=username).first()
    if not u:
        u = User(
            username=username,
            first_names=first,
            last_name=last,
            Name=f"{first} {last}",
            password_hash=pwd_context.hash("password123"),
            user_access_level=role,
            hub_id=HUB_ID,
            mobile_number=f"+224{random.randint(600000000, 699999999)}",
        )
        db.add(u)
        db.flush()
        print(f"  + User: {username}")
    else:
        print(f"  ~ User exists: {username}")
    user_map[username] = u
db.commit()

# ─── Batteries ────────────────────────────────────────────────────────────────

BATTERY_DEFS = [
    ("DEV-001", "BAT-DEV1", 1200, "available"),
    ("DEV-002", "BAT-DEV2", 1200, "available"),
    ("DEV-003", "BAT-DEV3",  800, "available"),
    ("DEV-004", "BAT-DEV4",  800, "available"),
    ("DEV-005", "BAT-DEV5", 1500, "available"),
    ("DEV-006", "BAT-DEV6",  500, "available"),
]
battery_ids_with_data = []
for bid, short_id, cap, status in BATTERY_DEFS:
    b = db.query(BEPPPBattery).filter_by(battery_id=bid).first()
    if not b:
        b = BEPPPBattery(
            battery_id=bid,
            short_id=short_id,
            battery_capacity_wh=cap,
            status=status,
            hub_id=HUB_ID,
        )
        db.add(b)
        db.flush()
        print(f"  + Battery: {bid} ({short_id}, {cap}Wh)")
    else:
        print(f"  ~ Battery exists: {bid}")
    battery_ids_with_data.append(bid)
db.commit()

# ─── Live Data (telemetry) ─────────────────────────────────────────────────────

# Only seed telemetry for 3 dev batteries and only if sparse
TELEMETRY_BATTERIES = ["DEV-001", "DEV-002", "DEV-003"]
DAYS = 35
INTERVAL_HOURS = 2  # one reading every 2 hours

print(f"\nGenerating telemetry for {TELEMETRY_BATTERIES} ({DAYS}d, every {INTERVAL_HOURS}h)...")
for bat_id in TELEMETRY_BATTERIES:
    existing_count = db.query(LiveData).filter_by(battery_id=bat_id).count()
    if existing_count > 100:
        print(f"  ~ Skipping {bat_id}: already has {existing_count} data points")
        continue

    points = []
    capacity_wh = next(cap for bid, _, cap, _ in BATTERY_DEFS if bid == bat_id)
    soc = random.uniform(40, 80)  # start mid-range
    total_intervals = DAYS * 24 // INTERVAL_HOURS

    for i in range(total_intervals):
        ts = NOW - timedelta(hours=(total_intervals - i) * INTERVAL_HOURS)
        hour = ts.hour

        # Simulate charging during day (8-18h), discharging at night
        if 8 <= hour <= 18:
            delta_soc = random.uniform(1, 4)   # charging
            current = random.uniform(3, 12)    # positive = charging
            power = random.uniform(20, 120)    # watts in
        else:
            delta_soc = -random.uniform(0.5, 3)  # discharging
            current = -random.uniform(1, 6)
            power = -random.uniform(10, 60)    # watts out

        soc = max(5, min(98, soc + delta_soc))
        voltage = 48.0 + (soc - 50) * 0.08  # voltage tracks SoC roughly

        points.append(LiveData(
            battery_id=bat_id,
            timestamp=ts,
            state_of_charge=int(soc),
            voltage=round(voltage, 2),
            current_amps=round(current, 2),
            power_watts=round(power, 1),
            temp_battery=round(random.uniform(22, 38), 1),
            time_remaining=int((soc / 100) * capacity_wh / max(abs(power), 1) * 60),
        ))

    db.bulk_save_objects(points)
    db.commit()
    print(f"  + {bat_id}: {len(points)} data points")

# ─── PUE Items ────────────────────────────────────────────────────────────────

PUE_ITEM_DEFS = [
    ("RICE-001", "Rice Mill #1",         pue_type_map["Rice Milling"],      45.0,  8.0),
    ("RICE-002", "Rice Mill #2",         pue_type_map["Rice Milling"],      45.0,  8.0),
    ("PHONE-001","Phone Charger Bank #1", pue_type_map["Phone Charging"],    5.0,   2.0),
    ("PHONE-002","Phone Charger Bank #2", pue_type_map["Phone Charging"],    5.0,   2.0),
    ("BARBER-001","Barber Kit #1",        pue_type_map["Barbershop"],        35.0,  6.0),
    ("TV-001",   "TV + Decoder #1",      pue_type_map["TV & Entertainment"], 20.0,  4.0),
    ("GRAIN-001","Grain Mill #1",         pue_type_map["Grain Processing"],  60.0, 10.0),
]
pue_item_map = {}  # pue_id -> item
for pue_id, name, pue_type_obj, power, cost in PUE_ITEM_DEFS:
    item = db.query(ProductiveUseEquipment).filter_by(pue_id=pue_id).first()
    if not item:
        item = ProductiveUseEquipment(
            pue_id=pue_id,
            name=name,
            hub_id=HUB_ID,
            pue_type_id=pue_type_obj.type_id,
            power_rating_watts=power,
            rental_cost=cost,
            status="available",
        )
        db.add(item)
        db.flush()
        print(f"  + PUE item: {pue_id} ({name})")
    else:
        print(f"  ~ PUE item exists: {pue_id}")
    pue_item_map[pue_id] = item
db.commit()

# ─── Battery Rentals + concurrent PUE Rentals for DEV batteries ───────────────
# Always create rentals for DEV batteries (which have telemetry) if missing

print("\nChecking DEV battery rentals (with telemetry)...")
users = list(user_map.values())
pue_items_list = list(pue_item_map.values())

RENTAL_SCENARIOS = [
    ("RICE-001", 0.9),
    ("PHONE-001", 0.8),
    ("BARBER-001", 0.8),
    ("TV-001", 0.7),
    ("GRAIN-001", 0.8),
    ("PHONE-002", 0.7),
    ("RICE-002", 0.9),
    None, None, None,
]

dev_batteries = ["DEV-001", "DEV-002", "DEV-003"]
rentals_added = 0

for bat_id in dev_batteries:
    # Check how many recent rentals this battery already has
    existing = (
        db.query(BatteryRentalItem)
        .join(BatteryRental, BatteryRentalItem.rental_id == BatteryRental.rental_id)
        .filter(
            BatteryRentalItem.battery_id == bat_id,
            BatteryRental.start_date > NOW - timedelta(days=40),
        )
        .count()
    )
    if existing >= 6:
        print(f"  ~ {bat_id}: already has {existing} recent rentals, skipping")
        continue

    needed = max(0, 6 - existing)
    print(f"  + {bat_id}: creating {needed} rentals")
    for i in range(needed):
        user = random.choice(users)
        days_ago = random.randint(1, 34)
        duration_days = random.randint(1, 4)
        start = NOW - timedelta(days=days_ago, hours=random.randint(0, 8))
        end_planned = start + timedelta(days=duration_days)

        is_active = days_ago < 2 and random.random() < 0.3
        actual_return = None if is_active else end_planned + timedelta(hours=random.randint(-8, 12))
        status = "active" if is_active else "returned"

        rental = BatteryRental(
            user_id=user.user_id,
            hub_id=HUB_ID,
            start_date=start,
            end_date=end_planned,
            actual_return_date=actual_return,
            status=status,
            amount_paid=round(random.uniform(2, 15), 2),
            amount_owed=0,
        )
        db.add(rental)
        db.flush()

        db.add(BatteryRentalItem(rental_id=rental.rental_id, battery_id=bat_id))

        scenario = random.choice(RENTAL_SCENARIOS)
        if scenario is not None:
            pue_item_id, prob = scenario
            if random.random() < prob and pue_item_id in pue_item_map:
                pue_item_obj = pue_item_map[pue_item_id]
                pue_end = actual_return or end_planned
                db.add(PUERental(
                    pue_id=pue_item_obj.pue_id,
                    user_id=user.user_id,
                    timestamp_taken=start + timedelta(hours=random.randint(0, 4)),
                    due_back=pue_end,
                    date_returned=None if is_active else pue_end + timedelta(hours=random.randint(-4, 4)),
                    is_active=is_active,
                    rental_cost=pue_item_obj.rental_cost * duration_days,
                ))
        rentals_added += 1

db.commit()
print(f"  Total new dev battery rentals: {rentals_added}")

# ─── GPS Data for DEV-001 ─────────────────────────────────────────────────────
# Simulate a battery being carried around a village near Kindia, Guinea

print("\nAdding GPS coordinates to DEV-001 telemetry...")
dev001_no_gps = (
    db.query(LiveData)
    .filter(LiveData.battery_id == "DEV-001", LiveData.latitude == None)
    .order_by(LiveData.timestamp)
    .all()
)
if dev001_no_gps:
    lat, lng = 10.0500, -12.8600  # near Kindia, Guinea
    gps_set = 0
    for point in dev001_no_gps:
        if random.random() < 0.25:  # ~25% have no GPS fix
            continue
        lat += random.uniform(-0.0008, 0.0008)
        lng += random.uniform(-0.0008, 0.0008)
        lat = max(10.040, min(10.060, lat))
        lng = max(-12.870, min(-12.850, lng))
        point.latitude = round(lat, 6)
        point.longitude = round(lng, 6)
        point.altitude = round(random.uniform(418, 445), 1)
        gps_set += 1
    db.commit()
    print(f"  + Set GPS on {gps_set} DEV-001 points ({len(dev001_no_gps)} had no coords)")
else:
    print("  ~ DEV-001 GPS data already set")

# ─── Done ─────────────────────────────────────────────────────────────────────

battery_count = db.query(BEPPPBattery).filter_by(hub_id=HUB_ID).count()
live_count = db.query(LiveData).count()
user_count = db.query(User).filter_by(hub_id=HUB_ID).count()
rental_count = db.query(BatteryRental).filter_by(hub_id=HUB_ID).count()
pue_rental_count = db.query(PUERental).count()
pue_type_count = db.query(PUEType).count()

print(f"""
✅ Seed complete:
   Batteries:        {battery_count}
   Live data points: {live_count}
   Users:            {user_count}
   Battery rentals:  {rental_count}
   PUE rentals:      {pue_rental_count}
   PUE types:        {pue_type_count}
""")
db.close()
