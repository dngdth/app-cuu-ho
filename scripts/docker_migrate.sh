#!/bin/bash
# Script to run database migrations inside Docker container

echo "Running database migrations..."
docker-compose exec app alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✓ Migrations completed successfully!"
else
    echo "✗ Migration failed!"
    exit 1
fi
