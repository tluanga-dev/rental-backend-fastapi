"""
Whitelist configuration manager for CORS origins and API endpoints.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Set, Optional, Any
from functools import lru_cache

logger = logging.getLogger(__name__)


class WhitelistManager:
    """Manages whitelist configuration for CORS origins and API endpoints."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize whitelist manager with configuration file."""
        if config_path is None:
            # Default config path relative to project root
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "whitelist.json"
        
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._cors_origins_cache: Optional[List[str]] = None
        
        self.load_config()
    
    def load_config(self) -> None:
        """Load whitelist configuration from JSON file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                logger.info(f"Loaded whitelist configuration from {self.config_path}")
            else:
                logger.warning(f"Whitelist config file not found at {self.config_path}, using defaults")
                self._config = self._get_default_config()
                self.save_config()
        except Exception as e:
            logger.error(f"Failed to load whitelist config: {e}")
            self._config = self._get_default_config()
        
        # Clear cache when config is reloaded
        self._cors_origins_cache = None
    
    def save_config(self) -> None:
        """Save current configuration to JSON file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved whitelist configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save whitelist config: {e}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default whitelist configuration."""
        return {
            "cors_origins": {
                "localhost_range": {
                    "enabled": True,
                    "start_port": 3000,
                    "end_port": 3050,
                    "protocols": ["http", "https"]
                },
                "localhost_aliases": {
                    "enabled": True,
                    "aliases": ["localhost", "127.0.0.1", "0.0.0.0"]
                },
                "additional_origins": [
                    "http://localhost:8000",
                    "http://127.0.0.1:8000"
                ],
                "development": {
                    "enabled": True,
                    "origins": []
                },
                "production": {
                    "enabled": False,
                    "origins": []
                }
            },
            "api_endpoints": {
                "whitelist_enabled": True,
                "default_access": "restricted",
                "public_endpoints": [
                    "/health",
                    "/docs",
                    "/redoc",
                    "/openapi.json"
                ],
                "protected_endpoints": [],
                "admin_only_endpoints": []
            }
        }
    
    @lru_cache(maxsize=1)
    def get_cors_origins(self) -> List[str]:
        """Get all allowed CORS origins."""
        if self._cors_origins_cache is not None:
            return self._cors_origins_cache
        
        origins = set()
        cors_config = self._config.get("cors_origins", {})
        
        # Add localhost range (3000-3050)
        localhost_range = cors_config.get("localhost_range", {})
        if localhost_range.get("enabled", True):
            start_port = localhost_range.get("start_port", 3000)
            end_port = localhost_range.get("end_port", 3050)
            protocols = localhost_range.get("protocols", ["http"])
            aliases = cors_config.get("localhost_aliases", {}).get("aliases", ["localhost", "127.0.0.1"])
            
            for protocol in protocols:
                for alias in aliases:
                    for port in range(start_port, end_port + 1):
                        origins.add(f"{protocol}://{alias}:{port}")
        
        # Add additional origins
        additional = cors_config.get("additional_origins", [])
        origins.update(additional)
        
        # Add development origins
        dev_config = cors_config.get("development", {})
        if dev_config.get("enabled", True):
            origins.update(dev_config.get("origins", []))
        
        # Add production origins
        prod_config = cors_config.get("production", {})
        if prod_config.get("enabled", False):
            origins.update(prod_config.get("origins", []))
        
        self._cors_origins_cache = sorted(list(origins))
        logger.info(f"Generated {len(self._cors_origins_cache)} CORS origins")
        
        return self._cors_origins_cache
    
    def is_origin_allowed(self, origin: str) -> bool:
        """Check if an origin is allowed."""
        return origin in self.get_cors_origins()
    
    def get_public_endpoints(self) -> List[str]:
        """Get list of public endpoints that don't require authentication."""
        api_config = self._config.get("api_endpoints", {})
        return api_config.get("public_endpoints", [])
    
    def get_protected_endpoints(self) -> List[str]:
        """Get list of protected endpoints that require authentication."""
        api_config = self._config.get("api_endpoints", {})
        return api_config.get("protected_endpoints", [])
    
    def get_admin_only_endpoints(self) -> List[str]:
        """Get list of admin-only endpoints."""
        api_config = self._config.get("api_endpoints", {})
        return api_config.get("admin_only_endpoints", [])
    
    def is_endpoint_public(self, endpoint: str) -> bool:
        """Check if an endpoint is public (no authentication required)."""
        public_endpoints = self.get_public_endpoints()
        
        # Exact match
        if endpoint in public_endpoints:
            return True
        
        # Pattern match (basic glob-style)
        for pattern in public_endpoints:
            if pattern.endswith("/**"):
                prefix = pattern[:-3]
                if endpoint.startswith(prefix):
                    return True
            elif pattern.endswith("/*"):
                prefix = pattern[:-2]
                if endpoint.startswith(prefix) and "/" not in endpoint[len(prefix):]:
                    return True
        
        return False
    
    def is_endpoint_admin_only(self, endpoint: str) -> bool:
        """Check if an endpoint requires admin privileges."""
        admin_endpoints = self.get_admin_only_endpoints()
        
        # Exact match
        if endpoint in admin_endpoints:
            return True
        
        # Pattern match (basic glob-style)
        for pattern in admin_endpoints:
            if pattern.endswith("/**"):
                prefix = pattern[:-3]
                if endpoint.startswith(prefix):
                    return True
            elif pattern.endswith("/*"):
                prefix = pattern[:-2]
                if endpoint.startswith(prefix) and "/" not in endpoint[len(prefix):]:
                    return True
        
        return False
    
    def add_cors_origin(self, origin: str, category: str = "additional_origins") -> None:
        """Add a new CORS origin to the configuration."""
        cors_config = self._config.setdefault("cors_origins", {})
        
        if category == "additional_origins":
            additional = cors_config.setdefault("additional_origins", [])
            if origin not in additional:
                additional.append(origin)
        elif category in ["development", "production"]:
            cat_config = cors_config.setdefault(category, {"enabled": True, "origins": []})
            origins = cat_config.setdefault("origins", [])
            if origin not in origins:
                origins.append(origin)
        
        # Clear cache and save config
        self._cors_origins_cache = None
        self.get_cors_origins.cache_clear()
        self.save_config()
        logger.info(f"Added CORS origin {origin} to {category}")
    
    def remove_cors_origin(self, origin: str) -> bool:
        """Remove a CORS origin from the configuration."""
        removed = False
        cors_config = self._config.get("cors_origins", {})
        
        # Remove from additional_origins
        additional = cors_config.get("additional_origins", [])
        if origin in additional:
            additional.remove(origin)
            removed = True
        
        # Remove from development/production
        for category in ["development", "production"]:
            cat_config = cors_config.get(category, {})
            origins = cat_config.get("origins", [])
            if origin in origins:
                origins.remove(origin)
                removed = True
        
        if removed:
            # Clear cache and save config
            self._cors_origins_cache = None
            self.get_cors_origins.cache_clear()
            self.save_config()
            logger.info(f"Removed CORS origin {origin}")
        
        return removed
    
    def update_localhost_range(self, start_port: int, end_port: int) -> None:
        """Update the localhost port range."""
        cors_config = self._config.setdefault("cors_origins", {})
        localhost_range = cors_config.setdefault("localhost_range", {})
        
        localhost_range["start_port"] = start_port
        localhost_range["end_port"] = end_port
        localhost_range["enabled"] = True
        
        # Clear cache and save config
        self._cors_origins_cache = None
        self.get_cors_origins.cache_clear()
        self.save_config()
        logger.info(f"Updated localhost port range to {start_port}-{end_port}")
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration."""
        return self._config.get("security", {})
    
    def get_rate_limiting_config(self) -> Dict[str, Any]:
        """Get rate limiting configuration."""
        return self._config.get("rate_limiting", {})
    
    def reload_config(self) -> None:
        """Reload configuration from file."""
        self.load_config()
        logger.info("Whitelist configuration reloaded")


# Global whitelist manager instance
whitelist_manager = WhitelistManager()


# Convenience functions
def get_cors_origins() -> List[str]:
    """Get allowed CORS origins."""
    return whitelist_manager.get_cors_origins()


def is_origin_allowed(origin: str) -> bool:
    """Check if an origin is allowed."""
    return whitelist_manager.is_origin_allowed(origin)


def is_endpoint_public(endpoint: str) -> bool:
    """Check if an endpoint is public."""
    return whitelist_manager.is_endpoint_public(endpoint)


def is_endpoint_admin_only(endpoint: str) -> bool:
    """Check if an endpoint requires admin privileges."""
    return whitelist_manager.is_endpoint_admin_only(endpoint)


def reload_whitelist_config() -> None:
    """Reload whitelist configuration."""
    whitelist_manager.reload_config()