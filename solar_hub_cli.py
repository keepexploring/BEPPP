#!/usr/bin/env python3
"""
Solar Hub Management CLI
A command-line interface for managing the Solar Hub system
"""
import click
import sys
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
import subprocess
import json
from tabulate import tabulate
from functools import wraps
import jwt
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from models import *
from database import DATABASE_URL, engine, SessionLocal
from passlib.context import CryptContext
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration - Make sure these match your API settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"

# Password hashing - Use same context as API
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Authentication functions (same as in API)
def create_access_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

@click.group()
@click.pass_context
def cli(ctx):
    """Solar Hub Management CLI - Manage users, hubs, batteries, and more."""
    ctx.ensure_object(dict)

# ============= User Management =============
@cli.group()
def user():
    """Manage users"""
    pass

@user.command()
@click.option('--username', prompt=True, help='Username for the admin user')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Password for the admin user')
@click.option('--name', prompt=True, default='Admin User', help='Full name')
@click.option('--hub-id', type=int, help='Hub ID (creates default hub if not specified)')
def create_admin(username, password, name, hub_id):
    """Create an admin user"""
    db = SessionLocal()
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            click.echo(f"❌ User '{username}' already exists!")
            return
        
        # Handle hub
        if not hub_id:
            hub = db.query(SolarHub).first()
            if not hub:
                click.echo("📍 No hub found. Creating default hub...")
                hub = SolarHub(
                    hub_id=1,
                    what_three_word_location="main.solar.hub",
                    solar_capacity_kw=100,
                    country="Kenya"
                )
                db.add(hub)
                db.commit()
                click.echo(f"✅ Created hub with ID: {hub.hub_id}")
            hub_id = hub.hub_id
        
        # Get next user ID
        max_user_id = db.query(func.max(User.user_id)).scalar()
        next_user_id = (max_user_id + 1) if max_user_id else 1
        
        # Create admin user
        admin_user = User(
            user_id=next_user_id,
            Name=name,
            hub_id=hub_id,
            user_access_level="admin",
            username=username,
            password_hash=hash_password(password)
        )
        db.add(admin_user)
        db.commit()
        
        click.echo(f"✅ Created admin user:")
        click.echo(f"   Username: {admin_user.username}")
        click.echo(f"   User ID: {admin_user.user_id}")
        click.echo(f"   Hub ID: {admin_user.hub_id}")
        
    except Exception as e:
        db.rollback()
        click.echo(f"❌ Error: {e}")
    finally:
        db.close()

@user.command()
@click.option('--username', prompt=True, help='Username')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Password')
@click.option('--name', prompt=True, help='Full name')
@click.option('--hub-id', type=int, prompt=True, help='Hub ID')
@click.option('--access-level', type=click.Choice(['user', 'admin', 'technician']), default='user', help='Access level')
@click.option('--mobile', help='Mobile number')
@click.option('--address', help='Address')
def create(username, password, name, hub_id, access_level, mobile, address):
    """Create a new user"""
    db = SessionLocal()
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            click.echo(f"❌ User '{username}' already exists!")
            return
        
        # Check if hub exists
        hub = db.query(SolarHub).filter(SolarHub.hub_id == hub_id).first()
        if not hub:
            click.echo(f"❌ Hub {hub_id} not found!")
            return
        
        # Get next user ID
        max_user_id = db.query(func.max(User.user_id)).scalar()
        next_user_id = (max_user_id + 1) if max_user_id else 1
        
        # Create user
        user = User(
            user_id=next_user_id,
            Name=name,
            hub_id=hub_id,
            user_access_level=access_level,
            username=username,
            password_hash=hash_password(password),
            mobile_number=mobile,
            address=address
        )
        db.add(user)
        db.commit()
        
        click.echo(f"✅ Created user:")
        click.echo(f"   Username: {user.username}")
        click.echo(f"   User ID: {user.user_id}")
        click.echo(f"   Access Level: {user.user_access_level}")
        
    except Exception as e:
        db.rollback()
        click.echo(f"❌ Error: {e}")
    finally:
        db.close()

@user.command('list')
@click.option('--hub-id', type=int, help='Filter by hub ID')
@click.option('--access-level', type=click.Choice(['user', 'admin', 'technician']), help='Filter by access level')
def list_users(hub_id, access_level):
    """List all users"""
    db = SessionLocal()
    
    try:
        # Build query
        query = db.query(User)
        if hub_id:
            query = query.filter(User.hub_id == hub_id)
        if access_level:
            query = query.filter(User.user_access_level == access_level)
        
        # Get users
        users = query.all()
        
        if not users:
            click.echo("No users found.")
            return
        
        # Prepare table data
        table_data = []
        for user in users:
            table_data.append([
                user.user_id,
                user.username,
                user.Name,
                user.user_access_level,
                user.hub_id,
                user.hub.what_three_word_location if user.hub else "N/A",
                user.mobile_number or "N/A"
            ])
        
        # Display table
        headers = ["ID", "Username", "Name", "Access Level", "Hub ID", "Hub Location", "Mobile"]
        click.echo(tabulate(table_data, headers=headers, tablefmt="grid"))
        click.echo(f"\nTotal users: {len(users)}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")
    finally:
        db.close()

@user.command()
@click.argument('username')
def delete(username):
    """Delete a user"""
    db = SessionLocal()
    
    try:
        # Find user
        user = db.query(User).filter(User.username == username).first()
        if not user:
            click.echo(f"❌ User '{username}' not found!")
            return
        
        # Confirm deletion
        if not click.confirm(f"Are you sure you want to delete user '{username}'?"):
            click.echo("Cancelled.")
            return
        
        # Delete user
        db.delete(user)
        db.commit()
        click.echo(f"✅ Deleted user '{username}'")
        
    except Exception as e:
        db.rollback()
        click.echo(f"❌ Error: {e}")
    finally:
        db.close()

@user.command()
@click.option('--username', prompt=True, help='Username')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Password')
def reset_password(username, password):
    """Reset a user's password"""
    db = SessionLocal()
    
    try:
        # Find user
        user = db.query(User).filter(User.username == username).first()
        if not user:
            click.echo(f"❌ User '{username}' not found!")
            return
        
        # Update password
        user.password_hash = hash_password(password)
        db.commit()
        
        click.echo(f"✅ Reset password for user '{username}'")
        
    except Exception as e:
        db.rollback()
        click.echo(f"❌ Error: {e}")
    finally:
        db.close()

@user.command()
@click.option('--username', prompt=True, help='Username')
@click.option('--password', prompt=True, hide_input=True, help='Password')
def generate_token(username, password):
    """Generate a JWT access token for a user"""
    db = SessionLocal()
    
    try:
        # Fetch user by username
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            click.echo("❌ Invalid username or password.")
            return
        
        # Check password
        if not verify_password(password, user.password_hash):
            click.echo("❌ Invalid username or password.")
            return
        
        # Generate token
        token_data = {
            "sub": user.username,
            "user_id": user.user_id,
            "role": user.user_access_level
        }
        token = create_access_token(token_data)
        
        click.echo("✅ Access Token Generated:")
        click.echo(f"Bearer {token}")
        click.echo("\nYou can use this token in API requests like:")
        click.echo(f"curl -H 'Authorization: Bearer {token}' http://localhost:8000/hubs/")
        
    except Exception as e:
        click.echo(f"❌ Error generating token: {str(e)}")
    finally:
        db.close()

# ============= Hub Management =============
@cli.group()
def hub():
    """Manage solar hubs"""
    pass

@hub.command()
@click.option('--hub-id', type=int, prompt=True, help='Hub ID')
@click.option('--location', prompt=True, help='What3Words location')
@click.option('--capacity', type=int, prompt=True, help='Solar capacity in kW')
@click.option('--country', prompt=True, help='Country')
@click.option('--latitude', type=float, help='Latitude')
@click.option('--longitude', type=float, help='Longitude')
def create(hub_id, location, capacity, country, latitude, longitude):
    """Create a new solar hub"""
    db = SessionLocal()
    
    try:
        # Check if hub already exists
        existing_hub = db.query(SolarHub).filter(SolarHub.hub_id == hub_id).first()
        if existing_hub:
            click.echo(f"❌ Hub {hub_id} already exists!")
            return
        
        # Create hub
        hub = SolarHub(
            hub_id=hub_id,
            what_three_word_location=location,
            solar_capacity_kw=capacity,
            country=country,
            latitude=latitude,
            longitude=longitude
        )
        db.add(hub)
        db.commit()
        
        click.echo(f"✅ Created hub:")
        click.echo(f"   Hub ID: {hub.hub_id}")
        click.echo(f"   Location: {hub.what_three_word_location}")
        click.echo(f"   Capacity: {hub.solar_capacity_kw} kW")
        click.echo(f"   Country: {hub.country}")
        
    except Exception as e:
        db.rollback()
        click.echo(f"❌ Error: {e}")
    finally:
        db.close()

@hub.command('list')
def list_hubs():
    """List all hubs"""
    db = SessionLocal()
    
    try:
        # Get hubs
        hubs = db.query(SolarHub).all()
        
        if not hubs:
            click.echo("No hubs found.")
            return
        
        # Prepare table data
        table_data = []
        for hub in hubs:
            user_count = db.query(User).filter(User.hub_id == hub.hub_id).count()
            battery_count = db.query(BEPPPBattery).filter(BEPPPBattery.hub_id == hub.hub_id).count()
            pue_count = db.query(ProductiveUseEquipment).filter(ProductiveUseEquipment.hub_id == hub.hub_id).count()
            
            table_data.append([
                hub.hub_id,
                hub.what_three_word_location or "N/A",
                f"{hub.solar_capacity_kw} kW" if hub.solar_capacity_kw else "N/A",
                hub.country or "N/A",
                user_count,
                battery_count,
                pue_count
            ])
        
        # Display table
        headers = ["ID", "Location", "Capacity", "Country", "Users", "Batteries", "PUE Items"]
        click.echo(tabulate(table_data, headers=headers, tablefmt="grid"))
        click.echo(f"\nTotal hubs: {len(hubs)}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")
    finally:
        db.close()

# ============= Battery Management =============
@cli.group()
def battery():
    """Manage batteries"""
    pass

@battery.command()
@click.option('--battery-id', type=int, prompt=True, help='Battery ID')
@click.option('--hub-id', type=int, prompt=True, help='Hub ID')
@click.option('--capacity', type=int, prompt=True, help='Battery capacity in Wh')
def create(battery_id, hub_id, capacity):
    """Create a new battery"""
    db = SessionLocal()
    
    try:
        # Check if battery already exists
        existing_battery = db.query(BEPPPBattery).filter(BEPPPBattery.battery_id == battery_id).first()
        if existing_battery:
            click.echo(f"❌ Battery {battery_id} already exists!")
            return
        
        # Check if hub exists
        hub = db.query(SolarHub).filter(SolarHub.hub_id == hub_id).first()
        if not hub:
            click.echo(f"❌ Hub {hub_id} not found!")
            return
        
        # Create battery
        battery = BEPPPBattery(
            battery_id=battery_id,
            hub_id=hub_id,
            battery_capacity_wh=capacity,
            status="available"
        )
        db.add(battery)
        db.commit()
        
        click.echo(f"✅ Created battery:")
        click.echo(f"   Battery ID: {battery.battery_id}")
        click.echo(f"   Hub ID: {battery.hub_id}")
        click.echo(f"   Capacity: {battery.battery_capacity_wh} Wh")
        click.echo(f"   Status: {battery.status}")
        
    except Exception as e:
        db.rollback()
        click.echo(f"❌ Error: {e}")
    finally:
        db.close()

@battery.command('list')
@click.option('--hub-id', type=int, help='Filter by hub ID')
@click.option('--status', type=click.Choice(['available', 'in_use', 'maintenance']), help='Filter by status')
def list_batteries(hub_id, status):
    """List all batteries"""
    db = SessionLocal()
    
    try:
        # Build query
        query = db.query(BEPPPBattery)
        if hub_id:
            query = query.filter(BEPPPBattery.hub_id == hub_id)
        if status:
            query = query.filter(BEPPPBattery.status == status)
        
        # Get batteries
        batteries = query.all()
        
        if not batteries:
            click.echo("No batteries found.")
            return
        
        # Prepare table data
        table_data = []
        for battery in batteries:
            rental_count = db.query(Rental).filter(Rental.battery_id == battery.battery_id).count()
            data_count = db.query(LiveData).filter(LiveData.battery_id == battery.battery_id).count()
            
            table_data.append([
                battery.battery_id,
                battery.hub_id,
                battery.hub.what_three_word_location if battery.hub else "N/A",
                f"{battery.battery_capacity_wh} Wh" if battery.battery_capacity_wh else "N/A",
                battery.status,
                rental_count,
                data_count
            ])
        
        # Display table
        headers = ["ID", "Hub ID", "Hub Location", "Capacity", "Status", "Rentals", "Data Points"]
        click.echo(tabulate(table_data, headers=headers, tablefmt="grid"))
        click.echo(f"\nTotal batteries: {len(batteries)}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")
    finally:
        db.close()

# ============= Database Management =============
@cli.group()
def db():
    """Database management commands"""
    pass

@db.command()
def init():
    """Initialize database tables"""
    click.echo("📊 Initializing database...")
    try:
        from database import init_db
        init_db()
        click.echo("✅ Database initialized successfully!")
    except Exception as e:
        click.echo(f"❌ Error: {e}")

@db.command()
def stats():
    """Show database statistics"""
    db = SessionLocal()
    
    try:
        # Get counts
        stats = {
            "Hubs": db.query(SolarHub).count(),
            "Users": db.query(User).count(),
            "Batteries": db.query(BEPPPBattery).count(),
            "Rentals": db.query(Rental).count(),
            "PUE Items": db.query(ProductiveUseEquipment).count(),
            "PUE Rentals": db.query(PUERental).count(),
            "Live Data Points": db.query(LiveData).count(),
            "Notes": db.query(Note).count()
        }
        
        # Display stats
        click.echo("\n📊 Database Statistics")
        click.echo("=" * 40)
        for entity, count in stats.items():
            click.echo(f"{entity:<20} {count:>10}")
        click.echo("=" * 40)
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")
    finally:
        db.close()

@db.command()
@click.option('--yes', is_flag=True, help='Skip confirmation')
def reset(yes):
    """Reset database (WARNING: Deletes all data!)"""
    if not yes:
        if not click.confirm("⚠️  This will DELETE ALL DATA. Are you sure?"):
            click.echo("Cancelled.")
            return
    
    try:
        click.echo("🗑️  Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        click.echo("🔨 Creating new tables...")
        Base.metadata.create_all(bind=engine)
        click.echo("✅ Database reset successfully!")
    except Exception as e:
        click.echo(f"❌ Error: {e}")

# ============= API Management =============
@cli.group()
def api():
    """API management commands"""
    pass

@api.command()
def start():
    """Start the API server"""
    click.echo("🚀 Starting Solar Hub API...")
    subprocess.run([sys.executable, "-m", "uvicorn", "api.app.main:app", "--reload", "--reload-exclude", ".venv/*", "--host", "0.0.0.0", "--port", "8000"])

@api.command()
def test():
    """Run API tests"""
    click.echo("🧪 Running API tests...")
    try:
        subprocess.run([sys.executable, "-m", "pytest", "test_api.py", "-v"])
    except Exception as e:
        click.echo(f"❌ Error: {e}")

@api.command()
def docs():
    """Open API documentation in browser"""
    import webbrowser
    url = "http://localhost:8000/docs"
    click.echo(f"📚 Opening API docs at {url}")
    webbrowser.open(url)

if __name__ == '__main__':
    cli()