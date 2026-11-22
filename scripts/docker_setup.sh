#!/bin/bash
# Complete database setup: clean, migrate, and seed
# Step 1: Clean
echo "Step 1/3: Cleaning database..."
docker-compose exec app python scripts/clean_db.py --force

# Step 2: Migrate
echo ""
echo "Step 2/3: Running migrations..."
docker-compose exec app alembic upgrade head

# Step 3: Seed
echo ""
echo "Step 3/3: Seeding data..."
docker-compose exec app python scripts/seed_db.py

echo ""
echo "✓ Database setup complete!"
