#!/bin/bash

# Admin User Initialization Script for Docker
# This script runs during container startup to ensure an admin user exists

set -e  # Exit on any error

echo "Starting FastAPI application initialization..."

# Wait for database to be ready
echo "Waiting for database to be ready..."
until python -c "
import asyncio
import sys
sys.path.insert(0, '/app')
from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def check_db():
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text('SELECT 1'))
        return True
    except Exception as e:
        print(f'Database not ready: {e}')
        return False

result = asyncio.run(check_db())
exit(0 if result else 1)
"; do
    echo "Database is not ready yet. Waiting 2 seconds..."
    sleep 2
done

echo "Database is ready!"

# Initialize database tables
echo "Initializing database tables..."
python -c "
import asyncio
import sys
sys.path.insert(0, '/app')
from app.core.database import init_db
# Import all models to ensure they are registered with SQLAlchemy
from app.modules.users.models import User, UserProfile
from app.modules.auth.models import RefreshToken, LoginAttempt, PasswordResetToken

asyncio.run(init_db())
print('Database tables initialized successfully')
"

# Create admin user
echo "Creating admin user..."
python /app/scripts/create_admin.py

# Start the FastAPI application
echo "Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000