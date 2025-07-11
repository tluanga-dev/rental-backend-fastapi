"""
Routes for managing whitelist configuration.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.whitelist import whitelist_manager, reload_whitelist_config


router = APIRouter(tags=["Whitelist Management"])


class CORSOriginRequest(BaseModel):
    """Request model for adding CORS origins."""
    origin: str
    category: str = "additional_origins"  # additional_origins, development, production


class LocalhostRangeRequest(BaseModel):
    """Request model for updating localhost port range."""
    start_port: int = 3000
    end_port: int = 3050


class WhitelistStatusResponse(BaseModel):
    """Response model for whitelist status."""
    enabled: bool
    total_cors_origins: int
    localhost_range_enabled: bool
    localhost_start_port: int
    localhost_end_port: int
    public_endpoints_count: int
    protected_endpoints_count: int
    admin_endpoints_count: int


@router.get("/whitelist/status", response_model=WhitelistStatusResponse)
async def get_whitelist_status():
    """Get current whitelist configuration status."""
    cors_origins = whitelist_manager.get_cors_origins()
    config = whitelist_manager._config
    
    cors_config = config.get("cors_origins", {})
    localhost_range = cors_config.get("localhost_range", {})
    
    return WhitelistStatusResponse(
        enabled=True,
        total_cors_origins=len(cors_origins),
        localhost_range_enabled=localhost_range.get("enabled", True),
        localhost_start_port=localhost_range.get("start_port", 3000),
        localhost_end_port=localhost_range.get("end_port", 3050),
        public_endpoints_count=len(whitelist_manager.get_public_endpoints()),
        protected_endpoints_count=len(whitelist_manager.get_protected_endpoints()),
        admin_endpoints_count=len(whitelist_manager.get_admin_only_endpoints())
    )


@router.get("/whitelist/cors-origins")
async def get_cors_origins() -> Dict[str, Any]:
    """Get all CORS origins grouped by category."""
    cors_origins = whitelist_manager.get_cors_origins()
    config = whitelist_manager._config.get("cors_origins", {})
    
    # Generate localhost range origins for display
    localhost_range = config.get("localhost_range", {})
    localhost_origins = []
    
    if localhost_range.get("enabled", True):
        start_port = localhost_range.get("start_port", 3000)
        end_port = localhost_range.get("end_port", 3050)
        protocols = localhost_range.get("protocols", ["http"])
        aliases = config.get("localhost_aliases", {}).get("aliases", ["localhost", "127.0.0.1"])
        
        for protocol in protocols:
            for alias in aliases:
                for port in range(start_port, min(start_port + 10, end_port + 1)):  # Show only first 10 for display
                    localhost_origins.append(f"{protocol}://{alias}:{port}")
        
        if end_port - start_port > 10:
            localhost_origins.append(f"... and {(end_port - start_port + 1) * len(protocols) * len(aliases) - 10} more")
    
    return {
        "localhost_range": {
            "enabled": localhost_range.get("enabled", True),
            "start_port": localhost_range.get("start_port", 3000),
            "end_port": localhost_range.get("end_port", 3050),
            "sample_origins": localhost_origins
        },
        "additional_origins": config.get("additional_origins", []),
        "development": config.get("development", {}),
        "production": config.get("production", {}),
        "total_origins": len(cors_origins)
    }


@router.post("/whitelist/cors-origins")
async def add_cors_origin(request: CORSOriginRequest):
    """Add a new CORS origin."""
    try:
        whitelist_manager.add_cors_origin(request.origin, request.category)
        return {"message": f"Successfully added origin {request.origin} to {request.category}"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to add CORS origin: {str(e)}"
        )


@router.delete("/whitelist/cors-origins")
async def remove_cors_origin(origin: str):
    """Remove a CORS origin."""
    success = whitelist_manager.remove_cors_origin(origin)
    
    if success:
        return {"message": f"Successfully removed origin {origin}"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Origin {origin} not found in configuration"
        )


@router.put("/whitelist/localhost-range")
async def update_localhost_range(request: LocalhostRangeRequest):
    """Update localhost port range."""
    try:
        whitelist_manager.update_localhost_range(request.start_port, request.end_port)
        return {
            "message": f"Successfully updated localhost range to {request.start_port}-{request.end_port}",
            "start_port": request.start_port,
            "end_port": request.end_port
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update localhost range: {str(e)}"
        )


@router.get("/whitelist/endpoints")
async def get_endpoint_configuration():
    """Get endpoint access configuration."""
    return {
        "public_endpoints": whitelist_manager.get_public_endpoints(),
        "protected_endpoints": whitelist_manager.get_protected_endpoints(),
        "admin_only_endpoints": whitelist_manager.get_admin_only_endpoints()
    }


@router.post("/whitelist/reload")
async def reload_whitelist():
    """Reload whitelist configuration from file."""
    try:
        reload_whitelist_config()
        return {"message": "Whitelist configuration reloaded successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reload whitelist configuration: {str(e)}"
        )


@router.get("/whitelist/config")
async def get_full_configuration():
    """Get complete whitelist configuration (admin only)."""
    return whitelist_manager._config


@router.get("/whitelist/test-origin")
async def test_origin(origin: str):
    """Test if an origin is allowed."""
    is_allowed = whitelist_manager.is_origin_allowed(origin)
    return {
        "origin": origin,
        "allowed": is_allowed,
        "message": "Origin is allowed" if is_allowed else "Origin is not allowed"
    }


@router.get("/whitelist/test-endpoint")
async def test_endpoint(endpoint: str):
    """Test endpoint access configuration."""
    is_public = whitelist_manager.is_endpoint_public(endpoint)
    is_admin_only = whitelist_manager.is_endpoint_admin_only(endpoint)
    
    access_type = "public" if is_public else ("admin_only" if is_admin_only else "protected")
    
    return {
        "endpoint": endpoint,
        "access_type": access_type,
        "is_public": is_public,
        "is_admin_only": is_admin_only,
        "requires_auth": not is_public
    }