#!/bin/bash

# Script to clear all data except authentication

echo "This script will clear all data except authentication and RBAC data"
echo "Running the Python script..."

# Option 1: Direct Python execution
python scripts/clear_all_data_except_auth.py

# If the above doesn't work, try:
# Option 2: Docker execution
# docker-compose exec app python scripts/clear_all_data_except_auth.py

# Option 3: Direct docker command
# docker exec rental-backend-fastapi-app-1 python scripts/clear_all_data_except_auth.py