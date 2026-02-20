import hashlib
import pickle
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
from enum import Enum
from src.config import CacheStrategy

logger = logging.getLogger(__name__)

@dataclass
class CachedResponse:
    """Represents a cached HTTP response."""
    content: bytes
    status_code: int
    headers: Dict[str, str]
    cached_at: datetime
    etag: Optional[str] = None
    last_modified: Optional[str] = None
    
    @property
    def age(self) -> timedelta:
        """Get age of cached response."""
        return datetime.now() - self.cached_at
    
    def is_fresh(self, ttl: timedelta) -> bool:
        """Check if cached response is still fresh."""
        return self.age <= ttl
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'content': self.content.hex(),
            'status_code': self.status_code,
            'headers': self.headers,
            'cached_at': self.cached_at.isoformat(),
            'etag': self.etag,
            'last_modified': self.last_modified
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CachedResponse':
        """Create from dictionary."""
        return cls(
            content=bytes.fromhex(data['content']),
            status_code=data['status_code'],
            headers=data['headers'],
            cached_at=datetime.fromisoformat(data['cached_at']),
            etag=data.get('etag'),
            last_modified=data.get('last_modified')
        )

@dataclass
class CacheConfig:
    """Configuration for cache behavior."""
    enabled: bool = True
    strategy: CacheStrategy = CacheStrategy.HYBRID
    ttl: timedelta = timedelta(minutes=15)
    max_memory_items: int = 100
    persistent: bool = True
    cache_dir: Optional[Path] = None
    respect_headers: bool = True
    stale_while_revalidate: bool = True
    
    def __post_init__(self):
        """Set default cache directory if not provided."""
        if self.persistent and not self.cache_dir:
            self.cache_dir = Path.home() / '.cache' / 'rss-fetcher'

class CacheStats:
    """Track cache statistics."""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.stale_hits = 0
        self.stores = 0
        self.evictions = 0
        self.errors = 0
    
    @property
    def total_requests(self) -> int:
        return self.hits + self.misses
    
    @property
    def hit_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.hits / self.total_requests) * 100
    
    def reset(self):
        """Reset all stats."""
        self.hits = self.misses = self.stale_hits = 0
        self.stores = self.evictions = self.errors = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary."""
        return {
            'hits': self.hits,
            'misses': self.misses,
            'stale_hits': self.stale_hits,
            'stores': self.stores,
            'evictions': self.evictions,
            'errors': self.errors,
            'total_requests': self.total_requests,
            'hit_rate': self.hit_rate
        }

class Cache:
    """Main cache implementation."""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.stats = CacheStats()
        self._memory_cache: Dict[str, CachedResponse] = {}
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """Ensure cache directory exists."""
        if self.config.persistent and self.config.cache_dir:
            self.config.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, url: str) -> str:
        """Generate cache key from URL."""
        return hashlib.sha256(url.encode()).hexdigest()
    
    def _get_persistent_path(self, key: str) -> Path:
        """Get filesystem path for persistent cache."""
        if not self.config.cache_dir:
            raise ValueError("Cache directory not configured")
        return self.config.cache_dir / f"{key}.cache"
    
    def _save_persistent(self, key: str, response: CachedResponse):
        """Save response to persistent storage."""
        if not self.config.persistent:
            return
        
        try:
            path = self._get_persistent_path(key)
            with open(path, 'wb') as f:
                pickle.dump(response.to_dict(), f)
        except Exception as e:
            self.stats.errors += 1
            logger.warning(f"Failed to save persistent cache for {key}: {e}")
    
    def _load_persistent(self, key: str) -> Optional[CachedResponse]:
        """Load response from persistent storage."""
        if not self.config.persistent:
            return None
        
        try:
            path = self._get_persistent_path(key)
            if not path.exists():
                return None
            
            with open(path, 'rb') as f:
                data = pickle.load(f)
                return CachedResponse.from_dict(data)
        except Exception as e:
            self.stats.errors += 1
            logger.warning(f"Failed to load persistent cache for {key}: {e}")
            return None
    
    def _evict_if_needed(self):
        """Evict oldest entries if memory cache is full."""
        if len(self._memory_cache) < self.config.max_memory_items:
            return
        
        # Sort by cached_at and remove oldest
        sorted_items = sorted(
            self._memory_cache.items(),
            key=lambda item: item[1].cached_at
        )
        
        # Remove oldest 20% of items
        remove_count = max(1, len(sorted_items) // 5)
        for key, _ in sorted_items[:remove_count]:
            del self._memory_cache[key]
            self.stats.evictions += 1
    
    def get(self, url: str, allow_stale: bool = False) -> Optional[CachedResponse]:
        """Get cached response for URL."""
        key = self._get_cache_key(url)
        response = None
        
        # Try memory cache first
        if key in self._memory_cache:
            response = self._memory_cache[key]
            logger.debug(f"Memory cache hit for {url}")
        elif self.config.persistent:
            # Try persistent cache
            response = self._load_persistent(key)
            if response:
                logger.debug(f"Persistent cache hit for {url}")
                # Promote to memory cache
                self._memory_cache[key] = response
        
        if not response:
            self.stats.misses += 1
            return None
        
        # Check freshness
        if response.is_fresh(self.config.ttl):
            self.stats.hits += 1
            return response
        elif allow_stale and self.config.stale_while_revalidate:
            self.stats.stale_hits += 1
            return response
        else:
            # Stale, remove from cache
            self.delete(url)
            self.stats.misses += 1
            return None
    
    def set(self, url: str, response: CachedResponse):
        """Cache response for URL."""
        key = self._get_cache_key(url)
        
        # Update memory cache
        self._evict_if_needed()
        self._memory_cache[key] = response
        
        # Update persistent cache if configured
        if self.config.persistent:
            self._save_persistent(key, response)
        
        self.stats.stores += 1
    
    def delete(self, url: str):
        """Remove URL from cache."""
        key = self._get_cache_key(url)
        
        # Remove from memory
        if key in self._memory_cache:
            del self._memory_cache[key]
        
        # Remove from persistent
        if self.config.persistent:
            try:
                path = self._get_persistent_path(key)
                if path.exists():
                    path.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete persistent cache for {key}: {e}")
    
    def clear(self):
        """Clear all cache."""
        self._memory_cache.clear()
        
        if self.config.persistent and self.config.cache_dir:
            for path in self.config.cache_dir.glob("*.cache"):
                try:
                    path.unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete {path}: {e}")
        
        self.stats.reset()
    
    def get_all_keys(self) -> List[str]:
        """Get all cache keys (for monitoring)."""
        keys = set(self._memory_cache.keys())
        
        if self.config.persistent and self.config.cache_dir:
            for path in self.config.cache_dir.glob("*.cache"):
                keys.add(path.stem)
        
        return list(keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.stats.to_dict()