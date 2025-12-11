
#!/bin/bash

# Start Panel server for Battery Analytics Dashboard
# This script should be run from the panel_dashboard directory

# Configuration
PORT=5100
HOST="0.0.0.0"
ALLOWED_ORIGIN="*"  # Change this in production to your actual domain

# Activate virtual environment if it exists
if [ -d "../venv" ]; then
    source ../venv/bin/activate
fi

# Start Panel server with authentication
echo "Starting Panel server on http://${HOST}:${PORT}"
echo "Allowed WebSocket origin: ${ALLOWED_ORIGIN}"
echo "Authentication: JWT-based (via application code)"

panel serve battery_analytics_v3.py \
    --port ${PORT} \
    --address ${HOST} \
    --allow-websocket-origin="${ALLOWED_ORIGIN}" \
    --use-xheaders \
    --cookie-secret="${SECRET_KEY:-panel-cookie-secret-change-in-production}" \
    --show
