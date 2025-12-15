import os
from dotenv import load_dotenv

# Load .env file if it exists (for local development)
load_dotenv()

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
DATABASE_URL = os.getenv("DATABASE_URL")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
USER_TOKEN_EXPIRE_HOURS = int(os.getenv("USER_TOKEN_EXPIRE_HOURS", "24"))
BATTERY_TOKEN_EXPIRE_HOURS = int(os.getenv("BATTERY_TOKEN_EXPIRE_HOURS", "24"))
BATTERY_SECRET_KEY = os.getenv("BATTERY_SECRET_KEY", "your-secret-key-change-this-in-production")

# Webhook logging configuration
WEBHOOK_LOG_LIMIT = int(os.getenv("WEBHOOK_LOG_LIMIT", "100"))  # Keep last N webhook logs (default: 100, set to 200 or any number)