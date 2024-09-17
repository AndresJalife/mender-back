#!/bin/sh
# Run Alembic Upgrade
echo "Running Alembic upgrade..."
poetry run alembic upgrade head

# Start Uvicorn server
echo "Starting Uvicorn server..."
poetry run uvicorn --host=0.0.0.0 --port=8443 src.main:app