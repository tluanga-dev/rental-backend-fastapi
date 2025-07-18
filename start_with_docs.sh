#!/bin/bash
# Start the rental management system with documentation

echo "🚀 Starting Rental Management System with API Documentation"
echo "============================================================="

# Function to check if a service is healthy
check_service() {
    local service=$1
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Waiting for $service to be healthy..."
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose ps $service | grep -q "healthy"; then
            echo "✅ $service is healthy"
            return 0
        fi
        
        echo "   Attempt $attempt/$max_attempts - $service not ready yet..."
        sleep 2
        ((attempt++))
    done
    
    echo "❌ $service failed to become healthy after $max_attempts attempts"
    return 1
}

# Start services
echo "🔧 Starting services..."
docker-compose --profile dev up -d

# Wait for services to be healthy
if check_service "db" && check_service "redis"; then
    echo "📦 Database and Redis are ready"
    
    # Wait a bit more for the app to fully start
    echo "⏳ Waiting for FastAPI application to start..."
    sleep 5
    
    # Check if the app is responding
    attempt=1
    max_attempts=15
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:8000/health > /dev/null; then
            echo "✅ FastAPI application is ready"
            break
        fi
        
        echo "   Attempt $attempt/$max_attempts - App not ready yet..."
        sleep 2
        ((attempt++))
    done
    
    if [ $attempt -le $max_attempts ]; then
        echo "============================================================="
        echo "🎉 System is ready! API Documentation is available at:"
        echo ""
        echo "📚 Swagger UI (Interactive):  http://localhost:8000/docs"
        echo "📖 ReDoc (Clean):            http://localhost:8000/redoc"
        echo "📄 OpenAPI JSON:             http://localhost:8000/openapi.json"
        echo "🏥 Health Check:             http://localhost:8000/health"
        echo ""
        echo "🔗 Purchase Transaction Endpoint:"
        echo "   POST http://localhost:8000/api/transactions/new-purchase"
        echo ""
        echo "💡 Key Features:"
        echo "   ✓ Purchase transaction creation with validation"
        echo "   ✓ Automatic stock level updates"
        echo "   ✓ Comprehensive error handling"
        echo "   ✓ JWT authentication required"
        echo "   ✓ Complete financial calculations"
        echo ""
        echo "📋 Example curl command:"
        echo "curl -X POST http://localhost:8000/api/transactions/new-purchase \\"
        echo "  -H 'Content-Type: application/json' \\"
        echo "  -H 'Authorization: Bearer YOUR_TOKEN' \\"
        echo "  -d @example_purchase_request.json"
        echo ""
        echo "🔑 To get an auth token, first register/login via:"
        echo "   POST http://localhost:8000/api/auth/login"
        echo ""
        echo "============================================================="
        echo "📊 Service Status:"
        docker-compose ps
        echo ""
        echo "📝 To view logs: docker-compose logs -f app"
        echo "🛑 To stop: docker-compose down"
        echo "🔄 To restart: docker-compose restart app"
        
        # Try to open browser automatically (works on macOS/Linux with GUI)
        if command -v open >/dev/null 2>&1; then
            echo "🌐 Opening Swagger UI in browser..."
            open http://localhost:8000/docs
        elif command -v xdg-open >/dev/null 2>&1; then
            echo "🌐 Opening Swagger UI in browser..."
            xdg-open http://localhost:8000/docs
        fi
        
    else
        echo "❌ FastAPI application failed to start"
        echo "📝 Check logs with: docker-compose logs app"
        exit 1
    fi
else
    echo "❌ Dependencies failed to start"
    echo "📝 Check logs with: docker-compose logs"
    exit 1
fi