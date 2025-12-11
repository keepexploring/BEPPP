#!/usr/bin/env python3
"""Update weekly rentals cost structure to include a deposit of 10"""

import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import CostStructure

# Database connection
DATABASE_URL = "postgresql://solar_user:solar_password@localhost:5433/solar_battery_db"

def main():
    # Create database connection
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # Find all cost structures with 'week' in the name (case-insensitive)
        weekly_structures = db.query(CostStructure).filter(
            CostStructure.name.ilike('%week%')
        ).all()

        if not weekly_structures:
            print("No weekly cost structures found.")
            return

        print(f"Found {len(weekly_structures)} weekly cost structure(s):")

        for structure in weekly_structures:
            old_deposit = structure.deposit_amount or 0
            structure.deposit_amount = 10.0
            print(f"  - Updated '{structure.name}' (ID: {structure.structure_id})")
            print(f"    Deposit: {old_deposit} → 10.0")

        db.commit()
        print("\nSuccessfully updated deposit amount for weekly rentals!")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
