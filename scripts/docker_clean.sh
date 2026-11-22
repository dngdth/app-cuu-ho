#!/bin/bash
# Script to clean (reset) database inside Docker container

echo "⚠️  WARNING: This will DROP all tables and recreate them!"
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

echo "Cleaning database..."
docker-compose exec app python scripts/clean_db.py

if [ $? -eq 0 ]; then
    echo "✓ Database cleaned successfully!"
    echo "Run './scripts/docker_migrate.sh' to recreate tables."
else
    echo "✗ Clean failed!"
    exit 1
fi
