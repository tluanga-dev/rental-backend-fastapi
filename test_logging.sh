#!/bin/bash

# Test script for the comprehensive logging system
echo "🚀 Testing Comprehensive Logging System"
echo "========================================"

# Set working directory
cd /Users/tluanga/current_work/rental-manager/rental-backend-fastapi

# Check if we're in the right directory
if [ ! -f "app/main.py" ]; then
    echo "❌ Error: Not in the correct directory"
    exit 1
fi

echo "📂 Working directory: $(pwd)"

# Check if required directories exist, create if they don't
echo "📁 Setting up log directories..."
mkdir -p logs
mkdir -p logs/transactions

# Run the simple logging test
echo "🧪 Running logging system tests..."
python3 test_logging_simple.py

# Check the exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Logging system test completed successfully!"
    echo ""
    echo "📊 Summary of generated files:"
    echo "  Main logs directory:"
    ls -la logs/*.md 2>/dev/null | tail -5 || echo "    No .md files in logs/"
    echo ""
    echo "  Transaction logs directory:"
    ls -la logs/transactions/*.md 2>/dev/null | tail -5 || echo "    No .md files in logs/transactions/"
    echo ""
    echo "🎯 The comprehensive logging mechanism is working correctly!"
    echo "   ✓ File-based markdown logging"
    echo "   ✓ Centralized logging configuration"  
    echo "   ✓ Transaction event tracking"
    echo "   ✓ Proper file naming convention"
    echo "   ✓ Multi-layered logging architecture"
else
    echo ""
    echo "❌ Logging system test failed!"
    echo "Check the output above for error details."
    exit 1
fi