#!/usr/bin/env python3
"""
Create initial admin user during deployment
Reads ADMIN_USERNAME, ADMIN_PASSWORD, and ADMIN_EMAIL from environment variables
"""
import sys
import os
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# Add parent directory to path to import models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import User, Base

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Get configuration from environment
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")

if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL environment variable not set")
    sys.exit(1)

if not ADMIN_PASSWORD:
    print("❌ ERROR: ADMIN_PASSWORD environment variable not set")
    sys.exit(1)

# Fix postgres:// to postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

try:
    # Create engine and session
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Check if admin user already exists
    existing_user = session.execute(
        select(User).where(User.username == ADMIN_USERNAME)
    ).scalar_one_or_none()

    if existing_user:
        print(f"✅ Admin user '{ADMIN_USERNAME}' already exists")
        # Update password in case it changed
        existing_user.password_hash = pwd_context.hash(ADMIN_PASSWORD)
        existing_user.email = ADMIN_EMAIL
        session.commit()
        print(f"✅ Admin user password updated")
        sys.exit(0)

    # Create new admin user
    hashed_password = pwd_context.hash(ADMIN_PASSWORD)

    admin_user = User(
        username=ADMIN_USERNAME,
        email=ADMIN_EMAIL,
        password_hash=hashed_password,
        first_name="System",
        last_name="Administrator",
        role="superadmin",  # Use superadmin role for highest privileges
        is_active=True
    )

    session.add(admin_user)
    session.commit()

    print(f"✅ Successfully created admin user:")
    print(f"   Username: {ADMIN_USERNAME}")
    print(f"   Email: {ADMIN_EMAIL}")
    print(f"   Role: superadmin")

except Exception as e:
    print(f"❌ Error creating admin user: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    session.close()
