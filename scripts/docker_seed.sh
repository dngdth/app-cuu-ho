#!/bin/bash
# Script to seed database inside Docker container

echo "Seeding database..."
docker-compose exec app python scripts/seed_db.py

if [ $? -eq 0 ]; then
    echo "✓ Database seeded successfully!"
else
    echo "✗ Seed failed!"
    exit 1
fi
