#!/usr/bin/env python3
"""
Script to run migrations on test database
"""
import os
import subprocess
import sys

# Set test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://fastapi_user:fastapi_password@db:5432/fastapi_test_db"

# Set environment variable
os.environ['DATABASE_URL'] = TEST_DATABASE_URL

# Run migrations
result = subprocess.run([sys.executable, '-m', 'alembic', 'upgrade', 'head'], 
                       capture_output=True, text=True)

if result.returncode == 0:
    print("✓ Migrations applied successfully to test database")
    print(result.stdout)
else:
    print("✗ Failed to apply migrations")
    print(result.stderr)
    sys.exit(1)