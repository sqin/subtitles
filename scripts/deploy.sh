#!/bin/sh
set -e

# Build and start services
echo "Building images..."
docker compose build

echo "Starting containers..."
docker compose up -d

echo "Done. Frontend: http://<server-ip>/  Backend: http://<server-ip>:8000"


