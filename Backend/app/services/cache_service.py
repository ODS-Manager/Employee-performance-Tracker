"""
No-Op Caching Service
Previously used external caching; now disabled to eliminate infrastructure cost.
All cache operations return their fallback values so callers continue to work.
"""
from typing import Any, Optional, Callable, TypeVar
from functools import wraps
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CacheService:
    """No-op caching service"""
    
    # Cache TTL constants (kept for reference if caching is re-enabled later)
    TTL_SHORT = 60 * 5          # 5 minutes
    TTL_MEDIUM = 60 * 15        # 15 minutes
    TTL_LONG = 60 * 60          # 1 hour
    TTL_REFERENCE = 60 * 60     # 1 hour for reference/lookup data
    TTL_DASHBOARD = 60 * 5      # 5 minutes for dashboard stats
    TTL_USER_LIST = 60 * 5      # 5 minutes for user/team lists
    
    # Cache key prefixes (kept for reference)
    PREFIX_REFERENCE = "ref"
    PREFIX_DASHBOARD = "dash"
    PREFIX_METRICS = "metrics"
    PREFIX_USERS = "users"
    PREFIX_TEAMS = "teams"
    PREFIX_ORGS = "orgs"
    PREFIX_ORDERS = "orders"
    PREFIX_PRODUCTIVITY = "productivity"
    PREFIX_BILLING = "billing"
    
    _instance: Optional['CacheService'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        pass
    
    @property
    def is_connected(self) -> bool:
        """Always returns False since caching is disabled"""
        return False
    
    def _build_key(self, prefix: str, *args) -> str:
        """Build a cache key from prefix and arguments"""
        parts = [prefix] + [str(arg) for arg in args if arg is not None]
        return ":".join(parts)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache — always returns None"""
        return None
    
    def set(self, key: str, value: Any, ttl: int = TTL_SHORT) -> bool:
        """Set value in cache with TTL — always returns False"""
        return False
    
    def delete(self, key: str) -> bool:
        """Delete a specific key from cache — always returns False"""
        return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern — always returns 0"""
        return 0
    
    def invalidate_reference_cache(self, ref_type: Optional[str] = None):
        """Invalidate reference data cache — no-op"""
        pass
    
    def invalidate_dashboard_cache(self, org_id: Optional[int] = None, user_id: Optional[int] = None):
        """Invalidate dashboard cache — no-op"""
        pass
    
    def invalidate_user_cache(self, org_id: Optional[int] = None):
        """Invalidate users list cache — no-op"""
        pass
    
    def invalidate_team_cache(self, org_id: Optional[int] = None):
        """Invalidate teams list cache — no-op"""
        pass

    def invalidate_order_cache(self):
        """Invalidate cached order lists and exports — no-op"""
        pass

    def invalidate_productivity_cache(self):
        """Invalidate cached productivity calculations — no-op"""
        pass

    def invalidate_billing_cache(self):
        """Invalidate cached billing lists and previews — no-op"""
        pass
    
    def invalidate_all(self):
        """Clear all application cache — no-op"""
        pass
    
    # Convenience methods for specific cache types
    def get_reference(self, ref_type: str, is_active: Optional[bool] = None) -> Optional[Any]:
        """Get cached reference data — always returns None"""
        return None
    
    def set_reference(self, ref_type: str, data: Any, is_active: Optional[bool] = None) -> bool:
        """Cache reference data — always returns False"""
        return False
    
    def get_dashboard(self, dashboard_type: str, org_id: Optional[int] = None, 
                      user_id: Optional[int] = None, team_ids: Optional[str] = None) -> Optional[Any]:
        """Get cached dashboard data — always returns None"""
        return None
    
    def set_dashboard(self, dashboard_type: str, data: Any, org_id: Optional[int] = None,
                      user_id: Optional[int] = None, team_ids: Optional[str] = None) -> bool:
        """Cache dashboard data — always returns False"""
        return False
    
    def get_metrics(self, metric_type: str, org_id: Optional[int] = None, 
                    extra_key: Optional[str] = None) -> Optional[Any]:
        """Get cached metrics data — always returns None"""
        return None
    
    def set_metrics(self, metric_type: str, data: Any, org_id: Optional[int] = None,
                    extra_key: Optional[str] = None, ttl: Optional[int] = None) -> bool:
        """Cache metrics data — always returns False"""
        return False


# Global cache instance
cache = CacheService()


def cached(prefix: str, ttl: int = CacheService.TTL_SHORT, 
           key_builder: Optional[Callable[..., str]] = None):
    """
    Decorator for caching function results — now a transparent pass-through.
    
    The original caching logic is preserved in comments for easy re-enabling.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Caching disabled — call function directly
            result = await func(*args, **kwargs)
            return result
        return wrapper
    return decorator
