import asyncio
import random
from prisma import Prisma
from datetime import datetime, timedelta


async def setup_database():
    # Initialize Prisma client
    db = Prisma()
    await db.connect()

    print("Connected to database. Creating sample data...")

    # Create or use existing solar hubs
    hubs = []
    hub_data = [
        {
            "hub_id": 1,
            "what_three_word_location": "table.chair.lamp",
            "solar_capacity_kw": 5,
            "country": "Kenya",
            "latitude": -1.2921,
            "longitude": 36.8219,
        },
        {
            "hub_id": 2,
            "what_three_word_location": "market.shop.corner",
            "solar_capacity_kw": 7,
            "country": "Tanzania",
            "latitude": -6.7924,
            "longitude": 39.2083,
        },
    ]

    for hub_info in hub_data:
        existing_hub = await db.solarhub.find_unique(
            where={"hub_id": hub_info["hub_id"]}
        )
        if existing_hub:
            print(
                f"Using existing Solar Hub: {existing_hub.hub_id} in {existing_hub.country}"
            )
            hubs.append(existing_hub)
        else:
            hub = await db.solarhub.create(data=hub_info)
            print(f"Created Solar Hub: {hub.hub_id} in {hub.country}")
            hubs.append(hub)

    # Create or use existing users
    users = []
    user_data = [
        {
            "user_id": 1,
            "Name": "John Doe",
            "users_identification_document_number": "ID12345678",
            "mobile_number": "+254712345678",
            "address": "123 Solar Street, Nairobi",
            "hub_id": 1,
            "user_access_level": "standard",
            "username": "johndoe",
            "password_hash": "hashed_password_would_go_here",
        },
        {
            "user_id": 2,
            "Name": "Jane Smith",
            "users_identification_document_number": "ID87654321",
            "mobile_number": "+255787654321",
            "address": "456 Power Avenue, Dar es Salaam",
            "hub_id": 2,
            "user_access_level": "standard",
            "username": "janesmith",
            "password_hash": "hashed_password_would_go_here",
        },
    ]

    for user_info in user_data:
        existing_user = await db.user.find_unique(
            where={"user_id": user_info["user_id"]}
        )
        if existing_user:
            print(f"Using existing User: {existing_user.Name}")
            users.append(existing_user)
        else:
            user = await db.user.create(data=user_info)
            print(f"Created User: {user.Name}")
            users.append(user)

    # Get next note ID
    next_note_id = 1
    try:
        note_query = 'SELECT MAX("id") as max_id FROM "Note";'
        note_result = await db.query_raw(note_query)
        if note_result and note_result[0]["max_id"] is not None:
            next_note_id = note_result[0]["max_id"] + 1
    except Exception as e:
        print(f"Error getting max note ID, starting with 1: {str(e)}")
        next_note_id = 1

    # Create or use existing batteries
    batteries = []
    # Create 20 batteries (10 for each hub)
    for i in range(1, 21):
        hub_id = 1 if i <= 10 else 2  # First 10 for hub 1, next 10 for hub 2

        # Check if the battery exists
        existing_battery = await db.bepppbattery.find_unique(where={"battery_id": i})
        if existing_battery:
            print(f"Battery ID {i} already exists, skipping...")
            batteries.append(existing_battery)
            continue

        try:
            battery = await db.bepppbattery.create(
                data={
                    "battery_id": i,
                    "hub_id": hub_id,
                    "battery_capacity_wh": 1000,
                    "status": random.choice(
                        ["available", "in use", "maintenance", "damaged"]
                    ),
                }
            )

            # Create a note for this battery
            note = await db.note.create(
                data={
                    "id": next_note_id,
                    "content": f"Initial setup for battery {i}. Status: {battery.status}, Last maintenance: 2023-10-15",
                    "batteries": {"create": {"battery_id": battery.battery_id}},
                }
            )

            next_note_id += 1
            batteries.append(battery)
            print(f"Created battery {i}/{20}", end="\r")
        except Exception as e:
            print(f"Error creating battery {i}: {str(e)}")
            continue

    print(f"\nCreated {len(batteries)} batteries")

    # Only proceed if we have batteries
    if not batteries:
        print("No batteries found. Exiting.")
        await db.disconnect()
        return

    # Create Productive Use Equipment (PUE)
    # Define PUE items with power consumption profiles
    pue_items = [
        {
            "name": "Hair Clipper",
            "description": "Professional hair cutting machine",
            "rental_cost": 5.0,
            "power_min": 15,
            "power_max": 30,
            "power_peak": 45,
        },
        {
            "name": "Water Pump",
            "description": "Small irrigation pump for farming",
            "rental_cost": 8.0,
            "power_min": 350,
            "power_max": 500,
            "power_peak": 700,
        },
        {
            "name": "Electric Drill",
            "description": "Cordless power drill for construction",
            "rental_cost": 6.0,
            "power_min": 200,
            "power_max": 400,
            "power_peak": 600,
        },
        {
            "name": "Sewing Machine",
            "description": "Portable sewing machine for tailoring",
            "rental_cost": 7.5,
            "power_min": 80,
            "power_max": 120,
            "power_peak": 180,
        },
        {
            "name": "Mobile Phone Charger",
            "description": "Multi-port phone charging station",
            "rental_cost": 2.0,
            "power_min": 10,
            "power_max": 25,
            "power_peak": 40,
        },
        {
            "name": "TV",
            "description": "12-inch energy-efficient television",
            "rental_cost": 10.0,
            "power_min": 50,
            "power_max": 80,
            "power_peak": 120,
        },
        {
            "name": "Radio",
            "description": "AM/FM radio with battery backup",
            "rental_cost": 3.0,
            "power_min": 5,
            "power_max": 10,
            "power_peak": 15,
        },
        {
            "name": "Grain Mill",
            "description": "Small electric grain grinding machine",
            "rental_cost": 9.0,
            "power_min": 400,
            "power_max": 600,
            "power_peak": 800,
        },
    ]

    # Get next PUE ID
    next_pue_id = 1
    try:
        pue_query = 'SELECT MAX("pue_id") as max_id FROM "ProductiveUseEquipment";'
        pue_result = await db.query_raw(pue_query)
        if pue_result and pue_result[0]["max_id"] is not None:
            next_pue_id = pue_result[0]["max_id"] + 1
    except Exception as e:
        print(f"Error getting max PUE ID, starting with 1: {str(e)}")
        next_pue_id = 1

    pue_objects = []
    # Create PUE items (distribute between hubs)
    for i, pue_item in enumerate(pue_items):
        # Alternate between hubs
        hub_id = 1 if i % 2 == 0 else 2

        try:
            # Check if PUE already exists
            existing_pue = await db.productiveuseequipment.find_first(
                where={"name": pue_item["name"], "hub_id": hub_id}
            )

            if existing_pue:
                print(
                    f"PUE {pue_item['name']} already exists in hub {hub_id}, skipping..."
                )
                # Store the power profile with the PUE object for later use
                existing_pue.power_min = pue_item["power_min"]
                existing_pue.power_max = pue_item["power_max"]
                existing_pue.power_peak = pue_item["power_peak"]
                pue_objects.append(existing_pue)
                continue

            pue = await db.productiveuseequipment.create(
                data={
                    "pue_id": next_pue_id,
                    "hub_id": hub_id,
                    "name": pue_item["name"],
                    "description": pue_item["description"],
                    "rental_cost": pue_item["rental_cost"],
                    "status": random.choice(["available", "in use", "maintenance"]),
                    "rental_count": 0,
                }
            )

            # Add power profile to the object for later use (not stored in DB)
            pue.power_min = pue_item["power_min"]
            pue.power_max = pue_item["power_max"]
            pue.power_peak = pue_item["power_peak"]

            # Create a note for this PUE
            note = await db.note.create(
                data={
                    "id": next_note_id,
                    "content": f"Initial setup for {pue.name}. Status: {pue.status}, Power consumption: {pue_item['power_min']}-{pue_item['power_max']}W",
                    "pue_items": {"create": {"pue_id": pue.pue_id}},
                }
            )

            next_note_id += 1
            next_pue_id += 1
            pue_objects.append(pue)
            print(f"Created PUE: {pue.name} at hub {hub_id}")

        except Exception as e:
            print(f"Error creating PUE {pue_item['name']}: {str(e)}")
            next_pue_id += 1
            continue

    print(f"Created {len(pue_objects)} PUE items")

    # Generate rental and usage data
    start_date = datetime.now() - timedelta(days=60)
    end_date = datetime.now()

    # Get next available IDs
    next_rental_id = 1
    try:
        rental_query = 'SELECT MAX("rentral_id") as max_id FROM "Rental";'
        rental_result = await db.query_raw(rental_query)
        if rental_result and rental_result[0]["max_id"] is not None:
            next_rental_id = rental_result[0]["max_id"] + 1
    except Exception as e:
        print(f"Error getting max rental ID, starting with 1: {str(e)}")
        next_rental_id = 1

    next_pue_rental_id = 1
    try:
        pue_rental_query = 'SELECT MAX("pue_rental_id") as max_id FROM "PUERental";'
        pue_rental_result = await db.query_raw(pue_rental_query)
        if pue_rental_result and pue_rental_result[0]["max_id"] is not None:
            next_pue_rental_id = pue_rental_result[0]["max_id"] + 1
    except Exception as e:
        print(f"Error getting max PUE rental ID, starting with 1: {str(e)}")
        next_pue_rental_id = 1

    next_live_data_id = 1
    try:
        live_data_query = 'SELECT MAX("id") as max_id FROM "LiveData";'
        live_data_result = await db.query_raw(live_data_query)
        if live_data_result and live_data_result[0]["max_id"] is not None:
            next_live_data_id = live_data_result[0]["max_id"] + 1
    except Exception as e:
        print(f"Error getting max live data ID, starting with 1: {str(e)}")
        next_live_data_id = 1

    rental_count = 0
    pue_rental_count = 0
    live_data_count = 0

    for battery in batteries:
        # Get user from the same hub as the battery
        hub_id = battery.hub_id
        hub_users = [user for user in users if user.hub_id == hub_id]
        user = random.choice(hub_users) if hub_users else users[0]

        # Get PUEs from the same hub
        hub_pues = [pue for pue in pue_objects if pue.hub_id == hub_id]

        # For each battery, create rentals over the time period
        current_date = start_date
        while current_date < end_date:
            # Create a rental every 3-4 days
            rental_duration = random.randint(1, 3)  # 1-3 days rental
            due_back = current_date + timedelta(days=rental_duration)
            date_returned = due_back - timedelta(
                hours=random.randint(0, 12)
            )  # Return up to 12 hours early

            # Determine if renting with PUE
            rental_with_pue = (
                hub_pues and random.random() < 0.7
            )  # 70% chance of also renting a PUE
            rented_pue = random.choice(hub_pues) if rental_with_pue else None

            try:
                # Create battery rental with associated note
                battery_rental = await db.rental.create(
                    data={
                        "rentral_id": next_rental_id,
                        "battery_id": battery.battery_id,
                        "user_id": user.user_id,
                        "timestamp_taken": current_date,
                        "due_back": due_back,
                        "date_returned": date_returned,
                    }
                )

                # Add a note about rental purpose
                rental_purpose = random.choice(
                    ["lighting", "phone charging", "small appliance"]
                )
                if rented_pue:
                    rental_purpose = f"{rented_pue.name} usage"

                note = await db.note.create(
                    data={
                        "id": next_note_id,
                        "content": f"Rental purpose: {rental_purpose}",
                        "created_at": current_date,
                        "rentals": {"create": {"rental_id": battery_rental.rentral_id}},
                    }
                )

                next_note_id += 1
                next_rental_id += 1
                rental_count += 1

                # Create PUE rental if applicable
                pue_rental = None
                if rented_pue:
                    # Create PUE rental with same dates as battery rental
                    pue_rental = await db.puerental.create(
                        data={
                            "pue_rental_id": next_pue_rental_id,
                            "pue_id": rented_pue.pue_id,
                            "user_id": user.user_id,
                            "timestamp_taken": current_date,
                            "due_back": due_back,
                            "date_returned": date_returned,
                        }
                    )

                    # Connect the PUE rental to the battery rental
                    await db.batterypuerental.create(
                        data={
                            "battery_rental_id": battery_rental.rentral_id,
                            "pue_rental_id": pue_rental.pue_rental_id,
                        }
                    )

                    # Add a note about PUE rental
                    note = await db.note.create(
                        data={
                            "id": next_note_id,
                            "content": f"PUE rental: {rented_pue.name} - Power consumption: {rented_pue.power_min}-{rented_pue.power_max}W",
                            "created_at": current_date,
                            "pue_rentals": {
                                "create": {"pue_rental_id": pue_rental.pue_rental_id}
                            },
                        }
                    )

                    # Increment rental count for this PUE
                    await db.productiveuseequipment.update(
                        where={"pue_id": rented_pue.pue_id},
                        data={"rental_count": {"increment": 1}},
                    )

                    next_note_id += 1
                    next_pue_rental_id += 1
                    pue_rental_count += 1

            except Exception as e:
                print(f"Error creating rental: {str(e)}")
                next_rental_id += 1
                continue

            # Generate live data during the rental period
            battery_date = current_date
            state_of_charge = 100  # Start fully charged

            # Define PUE usage patterns - when the PUE will be used during the rental period
            pue_usage_schedule = []
            if rented_pue:
                # Create 3-5 usage sessions per day
                for day in range(rental_duration):
                    day_start = current_date + timedelta(days=day)
                    # Morning, afternoon, and evening sessions
                    possible_times = [
                        day_start + timedelta(hours=random.randint(7, 10)),  # Morning
                        day_start
                        + timedelta(hours=random.randint(12, 15)),  # Afternoon
                        day_start + timedelta(hours=random.randint(18, 21)),  # Evening
                    ]
                    # Randomly select 2-3 of these times
                    selected_times = random.sample(possible_times, random.randint(2, 3))

                    for start_time in selected_times:
                        # Usage duration between 15 minutes and 2 hours
                        duration_minutes = random.randint(15, 120)
                        end_time = start_time + timedelta(minutes=duration_minutes)

                        # Only include if it's before the return time
                        if end_time <= date_returned:
                            pue_usage_schedule.append((start_time, end_time))

            # For testing, limit data points per rental
            data_points_limit = 100
            data_points_counter = 0

            while (
                battery_date < date_returned and data_points_counter < data_points_limit
            ):
                # Check if we're in a PUE usage period
                is_pue_active = False
                for start_time, end_time in pue_usage_schedule:
                    if start_time <= battery_date <= end_time:
                        is_pue_active = True
                        break

                # Determine if this is an active usage period
                is_active_usage = (
                    is_pue_active or random.random() < 0.4
                )  # 40% chance of active usage if no PUE

                # Set power consumption based on usage
                if is_pue_active and rented_pue:
                    # Using PUE - higher power consumption
                    increment = timedelta(
                        minutes=5
                    )  # Generate data every 5 minutes during PUE usage

                    # Use the power profile of the specific PUE
                    base_power = random.uniform(
                        rented_pue.power_min, rented_pue.power_max
                    )

                    # Occasionally have a peak load (10% chance)
                    if random.random() < 0.1:
                        power = random.uniform(
                            rented_pue.power_max, rented_pue.power_peak
                        )
                    else:
                        power = base_power

                    # Add some background power usage (lighting, etc.)
                    power += random.uniform(10, 30)

                elif is_active_usage:
                    # Active usage but not PUE - moderate power
                    increment = timedelta(minutes=5)
                    power = random.uniform(100, 200)  # 100-200W for standard usage

                    # Occasionally have a peak load
                    if random.random() < 0.05:  # 5% chance
                        power = random.uniform(250, 350)  # 250-350W (medium peak)
                else:
                    # Idle time - generate data hourly
                    increment = timedelta(hours=1)
                    # Minimal power usage during idle
                    power = random.uniform(0, 20)  # 0-20W standby power

                # Calculate energy consumption for this time period (Wh)
                hours = increment.total_seconds() / 3600
                energy_consumed = power * hours

                # Update state of charge
                state_of_charge -= (energy_consumed / 1000) * 100  # % of 1kWh

                # Don't let it go below 0
                if state_of_charge < 0:
                    state_of_charge = 0

                try:
                    # Create a live data record
                    await db.livedata.create(
                        data={
                            "id": next_live_data_id,
                            "battery_id": battery.battery_id,
                            "state_of_charge": int(state_of_charge),
                            "voltage": 12.0 - ((100 - state_of_charge) * 0.025),
                            "current_amps": power / 12.0,
                            "power_watts": power,
                            "time_remaining": (
                                int((state_of_charge / 100) * 1000 / power * 60)
                                if power > 0
                                else 0
                            ),
                            "temp_battery": random.uniform(20, 35 + (power / 500) * 10),
                            "amp_hours_consumed": (100 - state_of_charge) * 10 / 12,
                            "charging_current": 0,
                            "timestamp": battery_date,
                            "usb_voltage": 5.0 + random.uniform(-0.2, 0.2),
                            "usb_power": power * 0.2 if is_active_usage else 0,
                            "usb_current": (
                                (power * 0.2) / 5.0 if is_active_usage else 0
                            ),
                            "latitude": (
                                hubs[0].latitude if hub_id == 1 else hubs[1].latitude
                            )
                            + random.uniform(-0.01, 0.01),
                            "longitude": (
                                hubs[0].longitude if hub_id == 1 else hubs[1].longitude
                            )
                            + random.uniform(-0.01, 0.01),
                            "altitude": 1700 + random.uniform(-10, 10),
                            "SD_card_storage_remaining": 3200 - random.uniform(0, 800),
                            "battery_orientation": random.choice(
                                ["horizontal", "vertical"]
                            ),
                            "number_GPS_satellites_for_fix": random.randint(3, 12),
                            "mobile_signal_strength": random.randint(1, 5),
                            "event_type": (
                                "pue_operation" if is_pue_active else "normal_operation"
                            ),
                            "new_battery_cycle": 0,
                        }
                    )

                    live_data_count += 1
                    next_live_data_id += 1
                    data_points_counter += 1
                except Exception as e:
                    print(f"Error creating live data: {str(e)}")
                    next_live_data_id += 1
                    continue

                battery_date += increment

                # If battery is depleted, simulate a recharge
                if state_of_charge < 10:
                    # Recharge event
                    charging_time = timedelta(hours=3)  # Takes 3 hours to recharge
                    charge_end = battery_date + charging_time

                    # Add charging data points
                    charge_date = battery_date
                    charge_counter = 0
                    max_charge_points = 6  # One point every 30 min for 3 hours

                    while (
                        charge_date < charge_end and charge_counter < max_charge_points
                    ):
                        charge_increment = timedelta(minutes=30)
                        charge_progress = (
                            charge_date - battery_date
                        ).total_seconds() / charging_time.total_seconds()
                        new_soc = 10 + (charge_progress * 90)  # 10% to 100%

                        try:
                            await db.livedata.create(
                                data={
                                    "id": next_live_data_id,
                                    "battery_id": battery.battery_id,
                                    "state_of_charge": int(new_soc),
                                    "voltage": 12.0 + (charge_progress * 2.0),
                                    "current_amps": 0,
                                    "power_watts": 0,
                                    "time_remaining": 0,
                                    "temp_battery": random.uniform(25, 40),
                                    "amp_hours_consumed": (100 - new_soc) * 10 / 12,
                                    "charging_current": 10.0 - (charge_progress * 5),
                                    "timestamp": charge_date,
                                    "usb_voltage": 0,
                                    "usb_power": 0,
                                    "usb_current": 0,
                                    "latitude": (
                                        hubs[0].latitude
                                        if hub_id == 1
                                        else hubs[1].latitude
                                    )
                                    + random.uniform(-0.01, 0.01),
                                    "longitude": (
                                        hubs[0].longitude
                                        if hub_id == 1
                                        else hubs[1].longitude
                                    )
                                    + random.uniform(-0.01, 0.01),
                                    "altitude": 1700 + random.uniform(-10, 10),
                                    "SD_card_storage_remaining": 3200
                                    - random.uniform(0, 800),
                                    "battery_orientation": "horizontal",
                                    "number_GPS_satellites_for_fix": random.randint(
                                        3, 12
                                    ),
                                    "mobile_signal_strength": random.randint(1, 5),
                                    "event_type": "charging",
                                    "new_battery_cycle": 1,
                                }
                            )

                            live_data_count += 1
                            next_live_data_id += 1
                            data_points_counter += 1
                            charge_counter += 1
                        except Exception as e:
                            print(f"Error creating charging data: {str(e)}")
                            next_live_data_id += 1
                            continue

                        charge_date += charge_increment

                    # Update our tracking variables
                    battery_date = charge_end
                    state_of_charge = 100

            print(
                f"Battery {battery.battery_id}: Created {data_points_counter} data points for rental"
                + (
                    f" with {len(pue_usage_schedule)} PUE usage sessions"
                    if rented_pue
                    else ""
                )
            )
            current_date = date_returned + timedelta(days=random.randint(3, 4))

    # Create some standalone PUE rentals (without battery)
    if pue_objects:
        standalone_pue_count = 0
        for _ in range(10):  # Create 10 standalone PUE rentals
            pue = random.choice(pue_objects)
            hub_id = pue.hub_id
            hub_users = [user for user in users if user.hub_id == hub_id]
            user = random.choice(hub_users) if hub_users else users[0]

            rental_start = start_date + timedelta(days=random.randint(0, 55))
            rental_duration = random.randint(1, 3)
            due_back = rental_start + timedelta(days=rental_duration)
            date_returned = due_back - timedelta(hours=random.randint(0, 12))

            try:
                pue_rental = await db.puerental.create(
                    data={
                        "pue_rental_id": next_pue_rental_id,
                        "pue_id": pue.pue_id,
                        "user_id": user.user_id,
                        "timestamp_taken": rental_start,
                        "due_back": due_back,
                        "date_returned": date_returned,
                    }
                )

                # Add a note
                note = await db.note.create(
                    data={
                        "id": next_note_id,
                        "content": f"Standalone PUE rental: {pue.name} (no battery)",
                        "created_at": rental_start,
                        "pue_rentals": {
                            "create": {"pue_rental_id": pue_rental.pue_rental_id}
                        },
                    }
                )

                # Increment rental count for this PUE
                await db.productiveuseequipment.update(
                    where={"pue_id": pue.pue_id},
                    data={"rental_count": {"increment": 1}},
                )

                next_note_id += 1
                next_pue_rental_id += 1
                standalone_pue_count += 1

            except Exception as e:
                print(f"Error creating standalone PUE rental: {str(e)}")
                next_pue_rental_id += 1
                continue

        print(f"Created {standalone_pue_count} standalone PUE rentals")

    print(f"Created {rental_count} battery rental records")
    print(f"Created {pue_rental_count} PUE rental records with batteries")
    print(f"Created {live_data_count} live data records")

    await db.disconnect()
    print("Database setup complete!")


# Run the async function
if __name__ == "__main__":
    asyncio.run(setup_database())
