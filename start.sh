#!/bin/bash
echo "Starting application..."
echo "Fetching Prisma binaries..."
prisma py fetch
echo "Starting Uvicorn..."
exec uvicorn api.app.main:app --host 0.0.0.0 --port $PORT
