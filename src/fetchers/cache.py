import hashlib
import pickle
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
from enum import Enum
from src.config import CacheStrategy

@dataclass
class CachedResponse:
    content: bytes
    status_code: int
    headers: Dict[str, str]
    cached_at: datetime
    etag: Optional[str] = None
    last_modified: Optional[str] = None
    
    @property
    def age(self) -> timedelta:
        return datetime.now() - self.cached_at
    
    def is_fresh(self, ttl: timedelta) -> bool:
        return self.age <= ttl
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'content': self.content.hex(),
            'status_code': self.status_code,
            'headers': self.headers,
            'cached_at': self.cached_at.isoformat(),
            'etag': self.etag,
            'last_modified': self.last_modified
        }
    
    # Without quotes in 'CachedResponse', Python would raise a NameError because CachedResponse isn't defined in the namespace yet
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CachedResponse':
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
    enabled: bool = True
    strategy: CacheStrategy = CacheStrategy.HYBRID
    ttl: timedelta = timedelta(minutes=15)
    max_memory_items: int = 100
    persistent: bool = True
    cache_dir: Optional[Path] = None
    respect_headers: bool = True
    stale_while_revalidate: bool = True
    
    def __post_init__(self):
        if self.persistent and not self.cache_dir:
            self.cache_dir = Path.home() / '.cache' / 'rss-fetcher'

class CacheStats:
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
        self.hits = self.misses = self.stale_hits = 0
        self.stores = self.evictions = self.errors = 0
    
    def to_dict(self) -> Dict[str, Any]:
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
    def __init__(self, config: CacheConfig):
        self.config = config
        self.stats = CacheStats()
        self._memory_cache: Dict[str, CachedResponse] = {}
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        if self.config.persistent and self.config.cache_dir:
            self.config.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, url: str) -> str:
        return hashlib.sha256(url.encode()).hexdigest()
    
    def _get_persistent_path(self, key: str) -> Path:
        if not self.config.cache_dir:
            raise ValueError("Cache directory not configured")
        return self.config.cache_dir / f"{key}.cache"
    
    def _save_persistent(self, key: str, response: CachedResponse):
        if not self.config.persistent:
            return
        
        try:
            path = self._get_persistent_path(key)
            with open(path, 'wb') as f:
                pickle.dump(response.to_dict(), f)
        except Exception:
            self.stats.errors += 1
    
    def _load_persistent(self, key: str) -> Optional[CachedResponse]:
        if not self.config.persistent:
            return None
        
        try:
            path = self._get_persistent_path(key)
            if not path.exists():
                return None
            
            with open(path, 'rb') as f:
                data = pickle.load(f)
                return CachedResponse.from_dict(data)
        except Exception:
            self.stats.errors += 1
            return None
    
    def _evict_if_needed(self):
        if len(self._memory_cache) < self.config.max_memory_items:
            return
        
        sorted_items = sorted(
            self._memory_cache.items(),
            key=lambda item: item[1].cached_at
        )
        
        remove_count = max(1, len(sorted_items) // 5)
        for key, _ in sorted_items[:remove_count]:
            del self._memory_cache[key]
            self.stats.evictions += 1
    
    def get(self, url: str, allow_stale: bool = False) -> Optional[CachedResponse]:
        key = self._get_cache_key(url)
    
        response = self._memory_cache.get(key)
    
        if response is None and self.config.persistent:
            response = self._load_persistent(key)
            if response:
                self._memory_cache[key] = response
    
        if response is None:
            self.stats.misses += 1
            return None
    
        if response.is_fresh(self.config.ttl):
            self.stats.hits += 1
            return response
    
        if allow_stale and self.config.stale_while_revalidate:
            self.stats.stale_hits += 1
            return response
    
        self.delete(url)
        self.stats.misses += 1
        return None
    
    def set(self, url: str, response: CachedResponse):
        key = self._get_cache_key(url)
        
        self._evict_if_needed()
        self._memory_cache[key] = response
        
        if self.config.persistent:
            self._save_persistent(key, response)
        
        self.stats.stores += 1
    
    def delete(self, url: str):
        key = self._get_cache_key(url)
        
        if key in self._memory_cache:
            del self._memory_cache[key]
        
        if self.config.persistent:
            try:
                path = self._get_persistent_path(key)
                if path.exists():
                    path.unlink()
            except Exception:
                pass
    
    def clear(self):
        self._memory_cache.clear()
        
        if self.config.persistent and self.config.cache_dir:
            for path in self.config.cache_dir.glob("*.cache"):
                try:
                    path.unlink()
                except Exception:
                    pass
        
        self.stats.reset()
    
    def get_all_keys(self) -> List[str]:
        keys = set(self._memory_cache.keys())
        
        if self.config.persistent and self.config.cache_dir:
            for path in self.config.cache_dir.glob("*.cache"):
                keys.add(path.stem)
        
        return list(keys)
    
    def get_stats(self) -> Dict[str, Any]:
        return self.stats.to_dict()