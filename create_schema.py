"""Create database schema from SQLAlchemy models."""
import sys
sys.path.insert(0, '/app')

from api.app.database import engine, Base
from models import *  # Import all models

# Create all tables
Base.metadata.create_all(bind=engine)
print("✅ Database schema created successfully")
