import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import your models
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from models import Base
except ImportError:
    # Fallback if models import fails
    print("Warning: Could not import models, using empty metadata")
    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use the SAME logic as your database.py file
def get_database_url():
    """Get database URL with the same conversion logic as database.py"""
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    # Heroku DATABASE_URL starts with postgres:// but SQLAlchemy needs postgresql://
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        print("Converted postgres:// to postgresql:// for Alembic")
    
    if DATABASE_URL:
        print(f"Using database URL: {DATABASE_URL[:50]}...")
    else:
        print("WARNING: No DATABASE_URL environment variable found")
    
    return DATABASE_URL

# Set the SQLAlchemy URL from environment variable
database_url = get_database_url()
if database_url:
    config.set_main_option('sqlalchemy.url', database_url)

# add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    
    # Use the same configuration as your database.py - with NullPool for Heroku
    configuration = config.get_section(config.config_ini_section, {})
    
    try:
        connectable = engine_from_config(
            configuration,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,  # Same as your database.py
        )
        
        print("Database engine created successfully")
        
        with connectable.connect() as connection:
            print("Database connection established")
            
            context.configure(
                connection=connection, 
                target_metadata=target_metadata
            )

            with context.begin_transaction():
                print("Running migrations...")
                context.run_migrations()
                print("Migrations completed successfully")
                
    except Exception as e:
        print(f"ERROR during migration: {str(e)}")
        print(f"Database URL: {config.get_main_option('sqlalchemy.url', 'NOT SET')}")
        raise

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()