#!/bin/sh
set -e

echo "Stopping and removing containers..."
docker compose down

echo "To also remove volumes, run: docker compose down -v"


