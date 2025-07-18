#!/bin/bash
# Display API documentation information

echo "📚 Rental Management System API Documentation"
echo "=============================================="

# Check if services are running
if ! docker-compose ps | grep -q "Up"; then
    echo "❌ Services are not running. Start them with:"
    echo "   ./start_with_docs.sh"
    echo "   OR"
    echo "   docker-compose --profile dev up -d"
    exit 1
fi

# Check if app is responding
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ API is running and healthy"
    echo ""
    echo "📖 Documentation URLs:"
    echo "   Swagger UI:  http://localhost:8000/docs"
    echo "   ReDoc:       http://localhost:8000/redoc"
    echo "   OpenAPI:     http://localhost:8000/openapi.json"
    echo ""
    echo "🔍 Key API Endpoints:"
    echo "   Health:      GET  http://localhost:8000/health"
    echo "   Auth Login:  POST http://localhost:8000/api/auth/login"
    echo "   Purchase:    POST http://localhost:8000/api/transactions/new-purchase"
    echo ""
    echo "💡 Purchase Transaction Features:"
    echo "   ✓ Complete validation (UUIDs, dates, amounts, conditions)"
    echo "   ✓ Automatic stock level updates"
    echo "   ✓ Financial calculations (tax, discounts, totals)"
    echo "   ✓ Transaction number generation (PUR-YYYYMMDD-XXXX)"
    echo "   ✓ Comprehensive error handling"
    echo "   ✓ JWT authentication required"
    echo ""
    echo "📋 Example Request (see example_purchase_request.json):"
    echo "   curl -X POST http://localhost:8000/api/transactions/new-purchase \\"
    echo "     -H 'Content-Type: application/json' \\"
    echo "     -H 'Authorization: Bearer YOUR_TOKEN' \\"
    echo "     -d @example_purchase_request.json"
    echo ""
    echo "🔑 Authentication:"
    echo "   1. Register: POST /api/auth/register"
    echo "   2. Login:    POST /api/auth/login"
    echo "   3. Use returned token in Authorization header"
    echo ""
    echo "=============================================="
else
    echo "❌ API is not responding. Check if services are running:"
    echo "   docker-compose ps"
    echo "   docker-compose logs app"
fi