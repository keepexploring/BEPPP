import asyncio
import os
from prisma import Prisma
from passlib.context import CryptContext
import random
import datetime

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def setup_database():
    # Connect to database
    db = Prisma()
    await db.connect()

    print("Connected to database. Setting up initial data...")

    # ----- Create Hubs -----

    # Check if admin hub exists
    admin_hub = await db.solarhub.find_unique(where={"hub_id": 1})

    if not admin_hub:
        # Create admin hub
        admin_hub = await db.solarhub.create(
            data={
                "hub_id": 1,
                "what_three_word_location": "admin.central.hub",
                "solar_capacity_kw": 0,
                "country": "Admin Hub",
            }
        )
        print(f"Created Admin Hub with ID: {admin_hub.hub_id}")
    else:
        print(f"Using existing Admin Hub with ID: {admin_hub.hub_id}")

    # Create Hub 1 (Kenya)
    kenya_hub = await db.solarhub.find_unique(where={"hub_id": 2})

    if not kenya_hub:
        kenya_hub = await db.solarhub.create(
            data={
                "hub_id": 2,
                "what_three_word_location": "market.nairobi.power",
                "solar_capacity_kw": 5,
                "country": "Kenya",
                "latitude": -1.2921,
                "longitude": 36.8219,
            }
        )
        print(f"Created Kenya Hub with ID: {kenya_hub.hub_id}")
    else:
        print(f"Using existing Kenya Hub with ID: {kenya_hub.hub_id}")

    # Create Hub 2 (Tanzania)
    tanzania_hub = await db.solarhub.find_unique(where={"hub_id": 3})

    if not tanzania_hub:
        tanzania_hub = await db.solarhub.create(
            data={
                "hub_id": 3,
                "what_three_word_location": "station.dar.energy",
                "solar_capacity_kw": 7,
                "country": "Tanzania",
                "latitude": -6.7924,
                "longitude": 39.2083,
            }
        )
        print(f"Created Tanzania Hub with ID: {tanzania_hub.hub_id}")
    else:
        print(f"Using existing Tanzania Hub with ID: {tanzania_hub.hub_id}")

    # ----- Create Users -----

    # Admin user
    admin_user = await db.user.find_unique(where={"username": "admin"})

    if not admin_user:
        admin_user = await db.user.create(
            data={
                "user_id": 1,
                "Name": "Admin User",
                "users_identification_document_number": "ADMIN001",
                "mobile_number": "0000000000",
                "address": "Admin Address",
                "hub_id": 1,  # Admin hub
                "user_access_level": "admin",
                "username": "admin",
                "password_hash": pwd_context.hash("admin_password"),
            }
        )
        print(f"Created Admin User: {admin_user.username}")
    else:
        print(f"Using existing Admin User: {admin_user.username}")

    # Kiosk Owners (one for each hub)
    kiosk_users = [
        {
            "user_id": 2,
            "Name": "Kenya Kiosk Manager",
            "users_identification_document_number": "KIOSK001",
            "mobile_number": "254712345678",
            "address": "Nairobi Market",
            "hub_id": 2,  # Kenya hub
            "user_access_level": "kiosk_owner",
            "username": "kenya_kiosk",
            "password": "kiosk_password",
        },
        {
            "user_id": 3,
            "Name": "Tanzania Kiosk Manager",
            "users_identification_document_number": "KIOSK002",
            "mobile_number": "255712345678",
            "address": "Dar es Salaam Station",
            "hub_id": 3,  # Tanzania hub
            "user_access_level": "kiosk_owner",
            "username": "tanzania_kiosk",
            "password": "kiosk_password",
        },
    ]

    for kiosk_data in kiosk_users:
        username = kiosk_data["username"]
        existing_user = await db.user.find_unique(where={"username": username})

        if not existing_user:
            password = kiosk_data.pop("password")
            kiosk_data["password_hash"] = pwd_context.hash(password)

            kiosk_user = await db.user.create(data=kiosk_data)
            print(f"Created Kiosk Owner: {kiosk_user.username}")
        else:
            print(f"Using existing Kiosk Owner: {username}")

    # Regular Users (3 for each hub)
    regular_users = [
        # Kenya hub users
        {
            "user_id": 4,
            "Name": "John Kamau",
            "users_identification_document_number": "ID123456",
            "mobile_number": "254723456789",
            "address": "45 Kenyatta Ave, Nairobi",
            "hub_id": 2,
            "user_access_level": "user",
            "username": "john_k",
            "password": "user_password",
        },
        {
            "user_id": 5,
            "Name": "Sarah Wangari",
            "users_identification_document_number": "ID234567",
            "mobile_number": "254734567890",
            "address": "12 Moi Ave, Nairobi",
            "hub_id": 2,
            "user_access_level": "user",
            "username": "sarah_w",
            "password": "user_password",
        },
        {
            "user_id": 6,
            "Name": "Daniel Omondi",
            "users_identification_document_number": "ID345678",
            "mobile_number": "254745678901",
            "address": "78 Uhuru Highway, Nairobi",
            "hub_id": 2,
            "user_access_level": "user",
            "username": "daniel_o",
            "password": "user_password",
        },
        # Tanzania hub users
        {
            "user_id": 7,
            "Name": "Amina Mohamed",
            "users_identification_document_number": "ID456789",
            "mobile_number": "255756789012",
            "address": "23 Independence Ave, Dar es Salaam",
            "hub_id": 3,
            "user_access_level": "user",
            "username": "amina_m",
            "password": "user_password",
        },
        {
            "user_id": 8,
            "Name": "Joseph Mkapa",
            "users_identification_document_number": "ID567890",
            "mobile_number": "255767890123",
            "address": "56 Nyerere Rd, Dar es Salaam",
            "hub_id": 3,
            "user_access_level": "user",
            "username": "joseph_m",
            "password": "user_password",
        },
        {
            "user_id": 9,
            "Name": "Grace Kwame",
            "users_identification_document_number": "ID678901",
            "mobile_number": "255778901234",
            "address": "34 Kariakoo Market, Dar es Salaam",
            "hub_id": 3,
            "user_access_level": "user",
            "username": "grace_k",
            "password": "user_password",
        },
    ]

    for user_data in regular_users:
        username = user_data["username"]
        existing_user = await db.user.find_unique(where={"username": username})

        if not existing_user:
            password = user_data.pop("password")
            user_data["password_hash"] = pwd_context.hash(password)

            reg_user = await db.user.create(data=user_data)
            print(f"Created Regular User: {reg_user.username}")
        else:
            print(f"Using existing Regular User: {username}")

    # ----- Create Batteries -----

    # 15 batteries for Kenya hub
    for i in range(1, 16):
        battery_id = i
        existing_battery = await db.bepppbattery.find_unique(
            where={"battery_id": battery_id}
        )

        if not existing_battery:
            status = random.choice(
                ["available", "available", "available", "maintenance"]
            )

            # Using simpler approach without nested relation
            battery = await db.bepppbattery.create(
                data={
                    "battery_id": battery_id,
                    "hub_id": 2,  # Kenya hub
                    "battery_capacity_wh": 1000,
                    "status": status,
                }
            )
            print(f"Created Battery {battery_id} for Kenya Hub")

            # Create a note for each battery using direct query
            note_id_query = 'SELECT MAX("id") as max_id FROM "Note";'
            result = await db.query_raw(note_id_query)
            next_note_id = 1
            if result and result[0]["max_id"] is not None:
                next_note_id = result[0]["max_id"] + 1

            # Create note first
            note = await db.note.create(
                data={
                    "id": next_note_id,
                    "content": f"Initial setup for battery {battery_id}. Status: {status}",
                }
            )

            # Then create the relationship
            await db.query_raw(
                f'INSERT INTO "BEPPPBattery_Notes" ("battery_id", "note_id") VALUES ({battery_id}, {next_note_id});'
            )
        else:
            print(f"Using existing Battery {battery_id} for Kenya Hub")

    # 15 batteries for Tanzania hub
    for i in range(16, 31):
        battery_id = i
        existing_battery = await db.bepppbattery.find_unique(
            where={"battery_id": battery_id}
        )

        if not existing_battery:
            status = random.choice(
                ["available", "available", "available", "maintenance"]
            )

            battery = await db.bepppbattery.create(
                data={
                    "battery_id": battery_id,
                    "hub_id": 3,  # Tanzania hub
                    "battery_capacity_wh": 1000,
                    "status": status,
                }
            )
            print(f"Created Battery {battery_id} for Tanzania Hub")

            # Create a note for each battery using direct query
            note_id_query = 'SELECT MAX("id") as max_id FROM "Note";'
            result = await db.query_raw(note_id_query)
            next_note_id = 1
            if result and result[0]["max_id"] is not None:
                next_note_id = result[0]["max_id"] + 1

            # Create note first
            note = await db.note.create(
                data={
                    "id": next_note_id,
                    "content": f"Initial setup for battery {battery_id}. Status: {status}",
                }
            )

            # Then create the relationship
            await db.query_raw(
                f'INSERT INTO "BEPPPBattery_Notes" ("battery_id", "note_id") VALUES ({battery_id}, {next_note_id});'
            )
        else:
            print(f"Using existing Battery {battery_id} for Tanzania Hub")

    # Create a few rental records
    rental_data = [
        {
            "id": 1,
            "battery_id": 1,
            "user_id": 4,
            "days_ago": 5,
            "duration": 2,
            "returned": True,
        },
        {
            "id": 2,
            "battery_id": 2,
            "user_id": 5,
            "days_ago": 3,
            "duration": 3,
            "returned": True,
        },
        {
            "id": 3,
            "battery_id": 3,
            "user_id": 6,
            "days_ago": 2,
            "duration": 4,
            "returned": False,
        },
        {
            "id": 4,
            "battery_id": 16,
            "user_id": 7,
            "days_ago": 7,
            "duration": 2,
            "returned": True,
        },
        {
            "id": 5,
            "battery_id": 17,
            "user_id": 8,
            "days_ago": 4,
            "duration": 3,
            "returned": True,
        },
        {
            "id": 6,
            "battery_id": 18,
            "user_id": 9,
            "days_ago": 1,
            "duration": 5,
            "returned": False,
        },
    ]

    now = datetime.datetime.now()

    for rental in rental_data:
        rental_id = rental["id"]
        existing_rental = await db.rental.find_unique(where={"rentral_id": rental_id})

        if not existing_rental:
            taken_date = now - datetime.timedelta(days=rental["days_ago"])
            due_back = taken_date + datetime.timedelta(days=rental["duration"])
            returned_date = (
                due_back - datetime.timedelta(hours=random.randint(1, 12))
                if rental["returned"]
                else None
            )

            # Try direct SQL for rentals
            try:
                await db.query_raw(
                    f"""
                    INSERT INTO "Rental" ("rentral_id", "battery_id", "user_id", "timestamp_taken", "due_back", "date_returned")
                    VALUES ({rental_id}, {rental["battery_id"]}, {rental["user_id"]}, 
                    '{taken_date.isoformat()}', '{due_back.isoformat()}', 
                    {f"'{returned_date.isoformat()}'" if returned_date else "NULL"});
                    """
                )
                print(f"Created Rental {rental_id} for Battery {rental['battery_id']}")

                # Update battery status if currently rented
                if not rental["returned"]:
                    await db.bepppbattery.update(
                        where={"battery_id": rental["battery_id"]},
                        data={"status": "rented"},
                    )

                # Create a note for the rental
                note_id_query = 'SELECT MAX("id") as max_id FROM "Note";'
                result = await db.query_raw(note_id_query)
                next_note_id = 1
                if result and result[0]["max_id"] is not None:
                    next_note_id = result[0]["max_id"] + 1

                rental_purpose = random.choice(
                    ["lighting", "phone charging", "small appliance", "business use"]
                )

                # Create note first
                await db.note.create(
                    data={
                        "id": next_note_id,
                        "content": f"Rental purpose: {rental_purpose}",
                        "created_at": taken_date,
                    }
                )

                # Then create the relationship
                await db.query_raw(
                    f'INSERT INTO "Rental_Notes" ("rental_id", "note_id") VALUES ({rental_id}, {next_note_id});'
                )
            except Exception as e:
                print(f"Error creating rental {rental_id}: {str(e)}")
        else:
            print(f"Using existing Rental {rental_id}")

    await db.disconnect()
    print("Database setup complete!")


if __name__ == "__main__":
    asyncio.run(setup_database())
