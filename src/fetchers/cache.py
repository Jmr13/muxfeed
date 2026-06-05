import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List

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
    ttl: timedelta = timedelta(minutes=15)
    max_memory_items: int = 100
    max_disk_items: int = 1000
    persistent: bool = True
    cache_dir: Path = Path.home() / ".cache" / "muxfeed"
    respect_headers: bool = True
    stale_while_revalidate: bool = True

class Cache:
    def __init__(self, config: CacheConfig):
        self.config = config
        self._memory_cache: Dict[str, CachedResponse] = {}
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        if self.config.persistent:
            self.config.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, url: str) -> str:
        return hashlib.sha256(url.encode()).hexdigest()
    
    def _get_persistent_path(self, key: str) -> Path:
        if not self.config.cache_dir:
            raise ValueError("Cache directory not configured")
        return self.config.cache_dir / f"{key}.cache"
    
    def _save_persistent(self, key: str, response: CachedResponse):
        try:
            path = self._get_persistent_path(key)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(response.to_dict(), f)
        except Exception:
            pass
    
    def _load_persistent(self, key: str) -> Optional[CachedResponse]:
        try:
            path = self._get_persistent_path(key)
            if not path.exists():
                return None
    
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                response = CachedResponse.from_dict(data)
    
            if not response.is_fresh(self.config.ttl):
                path.unlink(missing_ok=True)
                return None
    
            return response
    
        except Exception:
            return None
    
    def _evict_memory_if_needed(self):
        if len(self._memory_cache) < self.config.max_memory_items:
            return
    
        sorted_items = sorted(
            self._memory_cache.items(),
            key=lambda item: item[1].cached_at
        )
    
        remove_count = max(1, len(sorted_items) // 5)
    
        for key, _ in sorted_items[:remove_count]:
            del self._memory_cache[key]
            
    def _evict_disk_if_needed(self):
        cache_files = list(self.config.cache_dir.glob("*.cache"))
    
        if len(cache_files) < self.config.max_disk_items:
            return
    
        cache_files.sort(key=lambda p: p.stat().st_mtime)
    
        remove_count = max(1, len(cache_files) // 5)
    
        for path in cache_files[:remove_count]:
            path.unlink(missing_ok=True)
    
    def get(self, url: str, allow_stale) -> Optional[CachedResponse]:
        key = self._get_cache_key(url)
        response = self._memory_cache.get(key)
    
        if response is None and self.config.persistent:
            response = self._load_persistent(key)
            if response:
                self._memory_cache[key] = response
    
        if response is None:
            return None
    
        if response.is_fresh(self.config.ttl):
            return response
    
        if allow_stale and self.config.stale_while_revalidate:
            return response
    
        self.delete(url)
        return None
    
    def set(self, url: str, response: CachedResponse):
        key = self._get_cache_key(url)
        
        self._evict_memory_if_needed()
        # self._evict_disk_if_needed()
        self._memory_cache[key] = response
        
        if self.config.persistent:
            self._save_persistent(key, response)
    
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
        
        if self.config.persistent:
            for path in self.config.cache_dir.glob("*.cache"):
                try:
                    path.unlink()
                except Exception:
                    pass