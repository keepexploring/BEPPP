#!/bin/bash
# start.sh

# Activate virtual environment
source .venv/bin/activate

# Start the API in background
echo "Starting API..."
cd api
uvicorn app.main:app --reload --port 8000 &
API_PID=$!
cd ..

# Start Jupyter
echo "Starting Jupyter..."
cd notebooks
jupyter lab &
JUPYTER_PID=$!
cd ..

echo "Services started:"
echo "- API: http://127.0.0.1:8000"
echo "- API Documentation: http://127.0.0.1:8000/docs"
echo "- Jupyter: http://127.0.0.1:8888"

# Wait for user to stop services
echo "Press Ctrl+C to stop services"
wait $API_PID $JUPYTER_PID