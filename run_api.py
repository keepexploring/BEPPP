
#!/usr/bin/env python3
"""
Launch script for Solar Hub API
Run this from the project root directory
"""
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run uvicorn
import uvicorn

if __name__ == "__main__":
    print("🚀 Starting Solar Hub Management API...")
    print(f"📁 Project root: {project_root}")
    print(f"📍 Current directory: {os.getcwd()}")
    
    # Change to the API directory for uvicorn
    api_path = project_root / "api" / "app"
    print(f"📂 API path: {api_path}")
    
    print("🌐 API will be available at: http://localhost:8000")
    print("📚 API docs at: http://localhost:8000/docs")
    
    # Run uvicorn with the correct module path
    uvicorn.run(
    "api.app.main:app",
    host="0.0.0.0",
    port=8000,
    reload=True,
    reload_dirs=[
        str(project_root / "api"),
        str(project_root / "app"),
        str(project_root / "models"),  # add more if needed
        str(project_root / "config"),
        str(project_root / "database"),
    ],
    reload_excludes=[
        str(project_root / ".venv"),
    ]
)