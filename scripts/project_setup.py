#!/usr/bin/env python3
"""
Setup script for Solar Hub API project
This ensures Prisma is properly configured for the project structure
"""
import os
import sys
from pathlib import Path
import subprocess

def setup_project():
    """Setup the project with proper Prisma configuration"""
    
    # Get project root
    project_root = Path(__file__).parent
    prisma_dir = project_root / "prisma"
    api_dir = project_root / "api"
    
    print("🔧 Solar Hub API Project Setup")
    print("==============================")
    print(f"📁 Project root: {project_root}")
    print(f"📂 Prisma directory: {prisma_dir}")
    print(f"📂 API directory: {api_dir}")
    
    # Check if directories exist
    if not prisma_dir.exists():
        print("❌ Prisma directory not found!")
        return False
    
    if not api_dir.exists():
        print("❌ API directory not found!")
        return False
    
    # Set environment variable for Prisma schema location
    os.environ['PRISMA_SCHEMA_PATH'] = str(prisma_dir / 'schema.prisma')
    
    # Check if .env file exists
    env_file = project_root / '.env'
    if not env_file.exists():
        print("⚠️  .env file not found. Creating template...")
        with open(env_file, 'w') as f:
            f.write("""# Database configuration
DATABASE_URL=postgresql://postgres@localhost:5433/BEPPP_dev

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production
WEBHOOK_SECRET=mySuperSecret123

# Prisma configuration
PRISMA_SCHEMA_PATH=./prisma/schema.prisma
""")
        print("✅ Created .env template. Please update with your settings.")
    else:
        print("✅ .env file found")
    
    # Install dependencies
    print("\n📦 Installing dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Generate Prisma client
    print("\n🔨 Generating Prisma client...")
    os.chdir(project_root)  # Change to project root for Prisma
    
    # Set the schema path for prisma generate
    result = subprocess.run([
        sys.executable, "-m", "prisma", "generate",
        "--schema", str(prisma_dir / "schema.prisma")
    ])
    
    if result.returncode != 0:
        print("❌ Failed to generate Prisma client")
        return False
    
    print("✅ Prisma client generated successfully")
    
    # Push schema to database
    print("\n📊 Pushing schema to database...")
    result = subprocess.run([
        sys.executable, "-m", "prisma", "db", "push",
        "--schema", str(prisma_dir / "schema.prisma"),
        "--skip-generate"  # We already generated the client
    ])
    
    if result.returncode != 0:
        print("❌ Failed to push schema to database")
        print("Make sure PostgreSQL is running on localhost:5433")
        return False
    
    print("✅ Database schema updated successfully")
    
    # Create initial admin user
    print("\n👤 Creating initial admin user...")
    create_admin_script = project_root / "create_admin_user.py"
    if create_admin_script.exists():
        subprocess.run([sys.executable, str(create_admin_script)])
    else:
        print("⚠️  create_admin_user.py not found. Skipping admin user creation.")
    
    print("\n✅ Setup complete!")
    print("\nTo start the API, run:")
    print("  python run_api.py")
    
    return True

if __name__ == "__main__":
    success = setup_project()
    sys.exit(0 if success else 1)