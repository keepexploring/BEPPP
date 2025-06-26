56
#!/usr/bin/env python3
"""
Solar Hub Management CLI
A command-line interface for managing the Solar Hub system
"""
import asyncio
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

from prisma import Prisma

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from prisma import Prisma
from passlib.context import CryptContext
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration - Make sure these match your API settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"

# Password hashing - Use same context as API
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Utility decorator for async commands
def async_cmd(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper

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
@async_cmd
async def create_admin(username, password, name, hub_id):
    """Create an admin user"""
    prisma = Prisma()
    await prisma.connect()
    
    try:
        # Check if user already exists
        existing_user = await prisma.user.find_first(where={"username": username})
        if existing_user:
            click.echo(f"❌ User '{username}' already exists!")
            return
        
        # Handle hub
        if not hub_id:
            hub = await prisma.solarhub.find_first()
            if not hub:
                click.echo("📍 No hub found. Creating default hub...")
                hub = await prisma.solarhub.create(
                    data={
                        "hub_id": 1,
                        "what_three_word_location": "main.solar.hub",
                        "solar_capacity_kw": 100,
                        "country": "Kenya"
                    }
                )
                click.echo(f"✅ Created hub with ID: {hub.hub_id}")
            hub_id = hub.hub_id
        
        # Get next user ID
        last_user = await prisma.user.find_first(order={"user_id": "desc"})
        next_user_id = (last_user.user_id + 1) if last_user else 1
        
        # Create admin user
        admin_user = await prisma.user.create(
            data={
                "user_id": next_user_id,
                "Name": name,
                "hub_id": hub_id,
                "user_access_level": "admin",
                "username": username,
                "password_hash": hash_password(password)
            }
        )
        
        click.echo(f"✅ Created admin user:")
        click.echo(f"   Username: {admin_user.username}")
        click.echo(f"   User ID: {admin_user.user_id}")
        click.echo(f"   Hub ID: {admin_user.hub_id}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")
    finally:
        await prisma.disconnect()

@user.command()
@click.option('--username', prompt=True, help='Username')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Password')
@click.option('--name', prompt=True, help='Full name')
@click.option('--hub-id', type=int, prompt=True, help='Hub ID')
@click.option('--access-level', type=click.Choice(['user', 'admin', 'technician']), default='user', help='Access level')
@click.option('--mobile', help='Mobile number')
@click.option('--address', help='Address')
@async_cmd
async def create(username, password, name, hub_id, access_level, mobile, address):
    """Create a new user"""
    prisma = Prisma()
    await prisma.connect()
    
    try:
        # Check if user already exists
        existing_user = await prisma.user.find_first(where={"username": username})
        if existing_user:
            click.echo(f"❌ User '{username}' already exists!")
            return
        
        # Check if hub exists
        hub = await prisma.solarhub.find_unique(where={"hub_id": hub_id})
        if not hub:
            click.echo(f"❌ Hub {hub_id} not found!")
            return
        
        # Get next user ID
        last_user = await prisma.user.find_first(order={"user_id": "desc"})
        next_user_id = (last_user.user_id + 1) if last_user else 1
        
        # Create user
        user = await prisma.user.create(
            data={
                "user_id": next_user_id,
                "Name": name,
                "hub_id": hub_id,
                "user_access_level": access_level,
                "username": username,
                "password_hash": hash_password(password),
                "mobile_number": mobile,
                "address": address
            }
        )
        
        click.echo(f"✅ Created user:")
        click.echo(f"   Username: {user.username}")
        click.echo(f"   User ID: {user.user_id}")
        click.echo(f"   Access Level: {user.user_access_level}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")
    finally:
        await prisma.disconnect()

@user.command('list')
@click.option('--hub-id', type=int, help='Filter by hub ID')
@click.option('--access-level', type=click.Choice(['user', 'admin', 'technician']), help='Filter by access level')
@async_cmd
async def list_users(hub_id, access_level):
    """List all users"""
    prisma = Prisma()
    await prisma.connect()
    
    try:
        # Build where clause
        where = {}
        if hub_id:
            where["hub_id"] = hub_id
        if access_level:
            where["user_access_level"] = access_level
        
        # Get users
        users = await prisma.user.find_many(
            where=where,
            include={"hub": True}
        )
        
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
        await prisma.disconnect()

@user.command()
@click.argument('username')
@async_cmd
async def delete(username):
    """Delete a user"""
    prisma = Prisma()
    await prisma.connect()
    
    try:
        # Find user
        user = await prisma.user.find_first(where={"username": username})
        if not user:
            click.echo(f"❌ User '{username}' not found!")
            return
        
        # Confirm deletion
        if not click.confirm(f"Are you sure you want to delete user '{username}'?"):
            click.echo("Cancelled.")
            return
        
        # Delete user
        await prisma.user.delete(where={"user_id": user.user_id})
        click.echo(f"✅ Deleted user '{username}'")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")
    finally:
        await prisma.disconnect()

@user.command()
@click.option('--username', prompt=True, help='Username')
@async_cmd
async def inspect_hash(username):
    """Inspect the password hash for a user (for debugging)"""
    prisma = Prisma()
    await prisma.connect()
    
    try:
        user = await prisma.user.find_unique(where={"username": username})
        if not user:
            click.echo(f"❌ User '{username}' not found!")
            return
        
        click.echo(f"User: {username}")
        click.echo(f"Hash length: {len(user.password_hash) if user.password_hash else 0}")
        click.echo(f"Hash starts with: {user.password_hash[:50] if user.password_hash else 'None'}...")
        click.echo(f"Hash ends with: ...{user.password_hash[-20:] if user.password_hash else 'None'}")
        
        # Check if it looks like a bcrypt hash
        if user.password_hash:
            bcrypt_prefixes = ['$2b$', '$2a$', '$2x$', '$2y$']
            is_bcrypt = any(user.password_hash.startswith(prefix) for prefix in bcrypt_prefixes)
            if is_bcrypt:
                click.echo("✅ Hash appears to be bcrypt format")
            else:
                click.echo("❌ Hash does NOT appear to be bcrypt format")
                click.echo("This explains the error. The hash needs to be regenerated.")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")
    finally:
        await prisma.disconnect()

@user.command()
@click.option('--username', prompt=True, help='Username')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Password')
@async_cmd
async def force_reset_password(username, password):
    """Force reset a user's password (clears any corruption)"""
    prisma = Prisma()
    await prisma.connect()
    
    try:
        # Find user
        user = await prisma.user.find_first(where={"username": username})
        if not user:
            click.echo(f"❌ User '{username}' not found!")
            return
        
        # Generate a fresh hash
        new_hash = hash_password(password)
        click.echo(f"Debug: New hash length: {len(new_hash)}")
        click.echo(f"Debug: New hash starts with: {new_hash[:20]}...")
        
        # Update password with explicit data
        await prisma.user.update(
            where={"user_id": user.user_id},
            data={"password_hash": new_hash}
        )
        
        click.echo(f"✅ Force reset password for user '{username}'")
        click.echo("You can now try generating an access token.")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")
    finally:
        await prisma.disconnect()

@user.command()
@click.option('--username', prompt=True, help='Username')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Password')
@async_cmd
async def generate_access_token(username, password):
    """Generate a JWT access token for a user"""
    prisma = Prisma()
    await prisma.connect()

    try:
        # Fetch user by username
        user = await prisma.user.find_unique(where={"username": username})

        if not user:
            click.echo("❌ Invalid username or password.")
            return

        # Check if password hash exists and is valid
        if not user.password_hash:
            click.echo("❌ User has no password set. Please reset password first.")
            return

        # Debug info
        click.echo(f"Debug: Hash length: {len(user.password_hash) if user.password_hash else 0}")
        
        # Check if hash looks like bcrypt
        bcrypt_prefixes = ['$2b$', '$2a$', '$2x$', '$2y$']
        is_bcrypt = any(user.password_hash.startswith(prefix) for prefix in bcrypt_prefixes)
        
        if not is_bcrypt:
            click.echo("❌ Password hash is corrupted (not in bcrypt format)")
            click.echo("Run: python solar_hub_cli.py user force-reset-password")
            return
        
        # Check password
        try:
            if not verify_password(password, user.password_hash):
                click.echo("❌ Invalid username or password.")
                return
        except Exception as e:
            click.echo(f"❌ Password verification failed: {str(e)}")
            click.echo("Run: python solar_hub_cli.py user force-reset-password")
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
        await prisma.disconnect()

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
@async_cmd
async def create(hub_id, location, capacity, country, latitude, longitude):
    """Create a new solar hub"""
    prisma = Prisma()
    await prisma.connect()
    
    try:
        # Check if hub already exists
        existing_hub = await prisma.solarhub.find_unique(where={"hub_id": hub_id})
        if existing_hub:
            click.echo(f"❌ Hub {hub_id} already exists!")
            return
        
        # Create hub
        hub = await prisma.solarhub.create(
            data={
                "hub_id": hub_id,
                "what_three_word_location": location,
                "solar_capacity_kw": capacity,
                "country": country,
                "latitude": latitude,
                "longitude": longitude
            }
        )
        
        click.echo(f"✅ Created hub:")
        click.echo(f"   Hub ID: {hub.hub_id}")
        click.echo(f"   Location: {hub.what_three_word_location}")
        click.echo(f"   Capacity: {hub.solar_capacity_kw} kW")
        click.echo(f"   Country: {hub.country}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")
    finally:
        await prisma.disconnect()

@hub.command('list')
@async_cmd
async def list_hubs():
    """List all hubs"""
    prisma = Prisma()
    await prisma.connect()
    
    try:
        # Get hubs with counts
        hubs = await prisma.solarhub.find_many(
            include={
                "_count": {
                    "select": {
                        "users": True,
                        "batteries": True,
                        "pue_items": True
                    }
                }
            }
        )
        
        if not hubs:
            click.echo("No hubs found.")
            return
        
        # Prepare table data
        table_data = []
        for hub in hubs:
            table_data.append([
                hub.hub_id,
                hub.what_three_word_location or "N/A",
                f"{hub.solar_capacity_kw} kW" if hub.solar_capacity_kw else "N/A",
                hub.country or "N/A",
                hub._count.users,
                hub._count.batteries,
                hub._count.pue_items
            ])
        
        # Display table
        headers = ["ID", "Location", "Capacity", "Country", "Users", "Batteries", "PUE Items"]
        click.echo(tabulate(table_data, headers=headers, tablefmt="grid"))
        click.echo(f"\nTotal hubs: {len(hubs)}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")
    finally:
        await prisma.disconnect()

# ============= Battery Management =============
@cli.group()
def battery():
    """Manage batteries"""
    pass

@battery.command()
@click.option('--battery-id', type=int, prompt=True, help='Battery ID')
@click.option('--hub-id', type=int, prompt=True, help='Hub ID')
@click.option('--capacity', type=int, prompt=True, help='Battery capacity in Wh')
@async_cmd
async def create(battery_id, hub_id, capacity):
    """Create a new battery"""
    prisma = Prisma()
    await prisma.connect()
    
    try:
        # Check if battery already exists
        existing_battery = await prisma.bepppbattery.find_unique(where={"battery_id": battery_id})
        if existing_battery:
            click.echo(f"❌ Battery {battery_id} already exists!")
            return
        
        # Check if hub exists
        hub = await prisma.solarhub.find_unique(where={"hub_id": hub_id})
        if not hub:
            click.echo(f"❌ Hub {hub_id} not found!")
            return
        
        # Create battery
        battery = await prisma.bepppbattery.create(
            data={
                "battery_id": battery_id,
                "hub_id": hub_id,
                "battery_capacity_wh": capacity,
                "status": "available"
            }
        )
        
        click.echo(f"✅ Created battery:")
        click.echo(f"   Battery ID: {battery.battery_id}")
        click.echo(f"   Hub ID: {battery.hub_id}")
        click.echo(f"   Capacity: {battery.battery_capacity_wh} Wh")
        click.echo(f"   Status: {battery.status}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")
    finally:
        await prisma.disconnect()

@battery.command('list')
@click.option('--hub-id', type=int, help='Filter by hub ID')
@click.option('--status', type=click.Choice(['available', 'in_use', 'maintenance']), help='Filter by status')
@async_cmd
async def list_batteries(hub_id, status):
    """List all batteries"""
    prisma = Prisma()
    await prisma.connect()
    
    try:
        # Build where clause
        where = {}
        if hub_id:
            where["hub_id"] = hub_id
        if status:
            where["status"] = status
        
        # Get batteries
        batteries = await prisma.bepppbattery.find_many(
            where=where,
            include={
                "hub": True,
                "_count": {
                    "select": {
                        "rentals": True,
                        "live_data": True
                    }
                }
            }
        )
        
        if not batteries:
            click.echo("No batteries found.")
            return
        
        # Prepare table data
        table_data = []
        for battery in batteries:
            table_data.append([
                battery.battery_id,
                battery.hub_id,
                battery.hub.what_three_word_location if battery.hub else "N/A",
                f"{battery.battery_capacity_wh} Wh" if battery.battery_capacity_wh else "N/A",
                battery.status,
                battery._count.rentals,
                battery._count.live_data
            ])
        
        # Display table
        headers = ["ID", "Hub ID", "Hub Location", "Capacity", "Status", "Rentals", "Data Points"]
        click.echo(tabulate(table_data, headers=headers, tablefmt="grid"))
        click.echo(f"\nTotal batteries: {len(batteries)}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")
    finally:
        await prisma.disconnect()

# ============= Database Management =============
@cli.group()
def db():
    """Database management commands"""
    pass

@db.command()
def push():
    """Push schema changes to database"""
    click.echo("📊 Pushing schema to database...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "prisma", "db", "push",
            "--schema", str(project_root / "prisma" / "schema.prisma")
        ])
        if result.returncode == 0:
            click.echo("✅ Schema pushed successfully!")
        else:
            click.echo("❌ Failed to push schema")
    except Exception as e:
        click.echo(f"❌ Error: {e}")

@db.command()
def generate():
    """Generate Prisma client"""
    click.echo("🔨 Generating Prisma client...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "prisma", "generate",
            "--schema", str(project_root / "prisma" / "schema.prisma")
        ])
        if result.returncode == 0:
            click.echo("✅ Prisma client generated successfully!")
        else:
            click.echo("❌ Failed to generate Prisma client")
    except Exception as e:
        click.echo(f"❌ Error: {e}")

@db.command()
@async_cmd
async def stats():
    """Show database statistics"""
    prisma = Prisma()
    await prisma.connect()
    
    try:
        # Get counts
        stats = {
            "Hubs": await prisma.solarhub.count(),
            "Users": await prisma.user.count(),
            "Batteries": await prisma.bepppbattery.count(),
            "Rentals": await prisma.rental.count(),
            "PUE Items": await prisma.productiveuseequipment.count(),
            "PUE Rentals": await prisma.puerental.count(),
            "Live Data Points": await prisma.livedata.count(),
            "Notes": await prisma.note.count()
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
        await prisma.disconnect()


@user.command()
@click.option('--dry-run', is_flag=True, help='Show what would be fixed without making changes')
@async_cmd
async def fix_all_passwords(dry_run):
    """Fix all users with corrupted password hashes (padded with spaces)"""
    prisma = Prisma()
    await prisma.connect()
    
    try:
        # Find all users
        users = await prisma.user.find_many()
        
        click.echo(f"🔍 Checking {len(users)} users for password issues...")
        
        fixed_count = 0
        issues = []
        
        for user in users:
            if user.password_hash:
                # Check if hash is padded (has trailing spaces)
                original_length = len(user.password_hash)
                trimmed_hash = user.password_hash.strip()
                trimmed_length = len(trimmed_hash)
                
                if original_length != trimmed_length:
                    issues.append({
                        'username': user.username,
                        'user_id': user.user_id,
                        'original_length': original_length,
                        'trimmed_length': trimmed_length,
                        'trimmed_hash': trimmed_hash
                    })
        
        if not issues:
            click.echo("✅ No password issues found!")
            return
        
        click.echo(f"\n⚠️  Found {len(issues)} users with padded password hashes:")
        
        for issue in issues:
            click.echo(f"\n👤 User: {issue['username']} (ID: {issue['user_id']})")
            click.echo(f"   Original length: {issue['original_length']} chars")
            click.echo(f"   Trimmed length: {issue['trimmed_length']} chars")
            
            if issue['trimmed_length'] == 60 and issue['trimmed_hash'].startswith('$2'):
                click.echo(f"   ✅ Valid bcrypt hash detected after trimming")
                
                if not dry_run:
                    # Fix the password hash
                    try:
                        await prisma.user.update(
                            where={"user_id": issue['user_id']},
                            data={"password_hash": issue['trimmed_hash']}
                        )
                        click.echo(f"   ✅ Fixed password hash")
                        fixed_count += 1
                    except Exception as e:
                        click.echo(f"   ❌ Failed to fix: {e}")
                else:
                    click.echo(f"   🔧 Would fix this hash (dry run mode)")
            else:
                click.echo(f"   ❌ Not a valid bcrypt hash even after trimming")
                click.echo(f"      User needs to reset password manually")
        
        if not dry_run:
            click.echo(f"\n✅ Fixed {fixed_count} out of {len(issues)} password issues")
        else:
            click.echo(f"\n🔍 Dry run complete. Would fix {len([i for i in issues if i['trimmed_length'] == 60])} passwords")
            click.echo("Run without --dry-run to apply fixes")
            
    except Exception as e:
        click.echo(f"❌ Error: {e}")
    finally:
        await prisma.disconnect()

# ============= API Management =============
@cli.group()
def api():
    """API management commands"""
    pass

@api.command()
def start():
    """Start the API server"""
    click.echo("🚀 Starting Solar Hub API...")
    run_api_path = project_root / "run_api.py"
    if run_api_path.exists():
        subprocess.run([sys.executable, str(run_api_path)])
    else:
        click.echo("❌ run_api.py not found!")

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