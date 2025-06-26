import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env file if present (for local dev)
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

def get_env_var(key: str, default: str = None, required: bool = False):
    value = os.getenv(key, default)
    if required and value is None:
        raise ValueError(f"Missing required environment variable: {key}")
    return value

# --- Core Configuration ---
SECRET_KEY = get_env_var("SECRET_KEY", required=True)
ALGORITHM = get_env_var("ALGORITHM", default="HS256")

# --- Optional ---
DEBUG = get_env_var("DEBUG", default="false").lower() == "true"
PORT = int(get_env_var("PORT", default="8000"))

# --- Webhooks / External Services ---
WEBHOOK_SECRET = get_env_var("WEBHOOK_SECRET", required=True)

# --- Database ---
DATABASE_URL = get_env_var("DATABASE_URL", required=True)