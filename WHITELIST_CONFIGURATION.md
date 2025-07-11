# Whitelist Configuration Guide

## Overview

The FastAPI Rental Management System includes a comprehensive whitelist system for managing CORS origins and API endpoint access. This system provides fine-grained control over which origins can access your API and implements rate limiting for security.

## Configuration Files

### 1. Main Configuration: `config/whitelist.json`

This is the primary configuration file that controls all whitelist behavior:

```json
{
  "cors_origins": {
    "localhost_range": {
      "enabled": true,
      "start_port": 3000,
      "end_port": 3050,
      "protocols": ["http", "https"]
    },
    "localhost_aliases": {
      "enabled": true,
      "aliases": ["localhost", "127.0.0.1", "0.0.0.0"]
    },
    "additional_origins": [
      "http://localhost:8000",
      "https://localhost:8000"
    ],
    "development": {
      "enabled": true,
      "origins": []
    },
    "production": {
      "enabled": false,
      "origins": []
    }
  }
}
```

### 2. Environment Variables: `.env`

Key environment variables for whitelist configuration:

```bash
# Enable whitelist system
USE_WHITELIST_CONFIG=true

# Custom config path (optional)
WHITELIST_CONFIG_PATH=/path/to/custom/whitelist.json

# Fallback CORS origins (when whitelist disabled)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

## Features

### 1. **Automatic Localhost Range (3000-3050)**

The system automatically generates CORS origins for localhost ports 3000-3050:

- `http://localhost:3000` through `http://localhost:3050`
- `http://127.0.0.1:3000` through `http://127.0.0.1:3050`
- Optional HTTPS support

**Configuration:**
```json
{
  "cors_origins": {
    "localhost_range": {
      "enabled": true,
      "start_port": 3000,
      "end_port": 3050,
      "protocols": ["http", "https"]
    }
  }
}
```

### 2. **Development vs Production Origins**

Separate origin management for different environments:

```json
{
  "cors_origins": {
    "development": {
      "enabled": true,
      "origins": [
        "http://localhost:5173",
        "http://localhost:8080"
      ]
    },
    "production": {
      "enabled": false,
      "origins": [
        "https://yourapp.com",
        "https://www.yourapp.com"
      ]
    }
  }
}
```

### 3. **API Endpoint Access Control**

Control access levels for different API endpoints:

```json
{
  "api_endpoints": {
    "whitelist_enabled": true,
    "default_access": "restricted",
    "public_endpoints": [
      "/health",
      "/docs",
      "/api/auth/login",
      "/api/auth/register"
    ],
    "protected_endpoints": [
      "/api/users/**",
      "/api/inventory/**"
    ],
    "admin_only_endpoints": [
      "/api/system/**",
      "/api/users/{user_id}/status"
    ]
  }
}
```

### 4. **Rate Limiting**

Built-in rate limiting with per-endpoint configuration:

```json
{
  "rate_limiting": {
    "enabled": true,
    "global_rate_limit": {
      "requests": 1000,
      "window": "1h"
    },
    "endpoint_specific": {
      "/api/auth/login": {
        "requests": 5,
        "window": "15m"
      }
    }
  }
}
```

### 5. **Security Headers**

Automatic security header management:

```json
{
  "security": {
    "require_https": false,
    "allowed_methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    "allowed_headers": [
      "Origin", "Content-Type", "Authorization"
    ],
    "expose_headers": [
      "X-Total-Count", "X-Page-Count"
    ],
    "max_age": 3600
  }
}
```

## Management API Endpoints

The system provides API endpoints for runtime configuration management:

### Get Whitelist Status
```http
GET /api/system/system/whitelist/status
```

**Response:**
```json
{
  "enabled": true,
  "total_cors_origins": 153,
  "localhost_range_enabled": true,
  "localhost_start_port": 3000,
  "localhost_end_port": 3050,
  "public_endpoints_count": 7,
  "protected_endpoints_count": 8,
  "admin_endpoints_count": 5
}
```

### Get CORS Origins
```http
GET /api/system/system/whitelist/cors-origins
```

### Add CORS Origin
```http
POST /api/system/system/whitelist/cors-origins
Content-Type: application/json

{
  "origin": "https://myapp.com",
  "category": "production"
}
```

### Update Localhost Range
```http
PUT /api/system/system/whitelist/localhost-range
Content-Type: application/json

{
  "start_port": 3000,
  "end_port": 3100
}
```

### Test Origin
```http
GET /api/system/system/whitelist/test-origin?origin=http://localhost:3000
```

### Reload Configuration
```http
POST /api/system/system/whitelist/reload
```

## Usage Examples

### 1. **Frontend Development Setup**

For React/Vue/Angular development typically using ports 3000-5173:

```json
{
  "cors_origins": {
    "localhost_range": {
      "enabled": true,
      "start_port": 3000,
      "end_port": 3050
    },
    "development": {
      "enabled": true,
      "origins": [
        "http://localhost:5173",
        "http://localhost:8080",
        "http://localhost:4200"
      ]
    }
  }
}
```

### 2. **Production Deployment**

```json
{
  "cors_origins": {
    "localhost_range": {
      "enabled": false
    },
    "development": {
      "enabled": false
    },
    "production": {
      "enabled": true,
      "origins": [
        "https://yourdomain.com",
        "https://www.yourdomain.com",
        "https://app.yourdomain.com"
      ]
    }
  },
  "security": {
    "require_https": true
  }
}
```

### 3. **Microservices Setup**

```json
{
  "cors_origins": {
    "additional_origins": [
      "http://auth-service:8001",
      "http://payment-service:8002",
      "http://notification-service:8003"
    ]
  }
}
```

## Programming Interface

### Python Usage

```python
from app.core.whitelist import whitelist_manager

# Check if origin is allowed
is_allowed = whitelist_manager.is_origin_allowed("http://localhost:3000")

# Add new origin
whitelist_manager.add_cors_origin("https://newapp.com", "production")

# Update localhost range
whitelist_manager.update_localhost_range(3000, 3100)

# Check endpoint access
is_public = whitelist_manager.is_endpoint_public("/api/auth/login")
is_admin = whitelist_manager.is_endpoint_admin_only("/api/system/settings")

# Reload configuration
whitelist_manager.reload_config()
```

### JavaScript/Frontend Usage

```javascript
// Test if your origin is allowed
async function testOrigin() {
  const response = await fetch('/api/system/system/whitelist/test-origin?origin=' + window.location.origin);
  const result = await response.json();
  console.log('Origin allowed:', result.allowed);
}

// Get current whitelist status
async function getWhitelistStatus() {
  const response = await fetch('/api/system/system/whitelist/status');
  const status = await response.json();
  console.log('Whitelist status:', status);
}
```

## Security Considerations

### 1. **Production Security**

- Disable localhost ranges in production
- Use HTTPS-only origins
- Enable rate limiting
- Restrict admin endpoints

### 2. **Rate Limiting**

- Configure appropriate limits for your use case
- Monitor for rate limit violations
- Use different limits for different endpoint types

### 3. **Endpoint Access**

- Regularly review endpoint classifications
- Use principle of least privilege
- Monitor access attempts to restricted endpoints

## Troubleshooting

### Common Issues

1. **CORS Errors in Development**
   - Verify your frontend port is in the 3000-3050 range
   - Check if localhost_range is enabled
   - Test with `/api/system/system/whitelist/test-origin`

2. **Configuration Not Loading**
   - Check file path: `config/whitelist.json`
   - Verify JSON syntax
   - Check file permissions
   - Review application logs

3. **Rate Limit Exceeded**
   - Check rate limiting configuration
   - Verify client IP detection
   - Adjust limits for your use case

### Debug Commands

```bash
# Test configuration loading
curl http://localhost:8000/api/system/system/whitelist/status

# Test specific origin
curl "http://localhost:8000/api/system/system/whitelist/test-origin?origin=http://localhost:3000"

# Get all CORS origins
curl http://localhost:8000/api/system/system/whitelist/cors-origins

# Reload configuration
curl -X POST http://localhost:8000/api/system/system/whitelist/reload
```

## Best Practices

1. **Development**
   - Use localhost range for local development
   - Keep development origins in separate category
   - Test with multiple ports/protocols

2. **Production**
   - Disable localhost ranges
   - Use specific domain origins
   - Enable HTTPS requirements
   - Monitor and log access attempts

3. **Configuration Management**
   - Version control whitelist.json
   - Use environment-specific configurations
   - Regular security reviews
   - Automated testing of configurations

## Migration from Old CORS Configuration

If migrating from the old `ALLOWED_ORIGINS` environment variable:

1. **Keep existing setup** - Set `USE_WHITELIST_CONFIG=false`
2. **Gradual migration** - Move origins to `whitelist.json` gradually
3. **Full migration** - Set `USE_WHITELIST_CONFIG=true` and remove `ALLOWED_ORIGINS`

The system provides backward compatibility and will fall back to environment variables if needed.