import base64
import hashlib
import json
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
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
        now = datetime.now(timezone.utc)
        cached_at = self.cached_at if self.cached_at.tzinfo else self.cached_at.replace(tzinfo=timezone.utc)
        return now - cached_at
    
    def is_fresh(self, ttl: timedelta) -> bool:
        return self.age <= ttl
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'content': 'b64:' + base64.b64encode(self.content).decode('ascii'),
            'status_code': self.status_code,
            'headers': self.headers,
            'cached_at': self.cached_at.isoformat(),
            'etag': self.etag,
            'last_modified': self.last_modified
        }
    
    # Quotes required: 'CachedResponse' isn't bound as a name until the class statement finishes executing
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CachedResponse':
        raw = data['content']
        if raw.startswith('b64:'):
            content = base64.b64decode(raw[4:])
        else:
            content = bytes.fromhex(raw)
        return cls(
            content=content,
            status_code=data['status_code'],
            headers=data['headers'],
            cached_at=datetime.fromisoformat(data['cached_at']),
            etag=data.get('etag'),
            last_modified=data.get('last_modified')
        )

@dataclass
class CacheConfig:
    enabled: bool = True
    ttl: timedelta = timedelta(minutes=15)
    max_memory_items: int = 100
    persistent: bool = True
    cache_dir: Path = Path.home() / ".cache" / "muxfeed"
    respect_headers: bool = True
    stale_while_revalidate: bool = True

class Cache:
    def __init__(self, config: CacheConfig):
        self.config = config
        self._memory_cache: Dict[str, CachedResponse] = {}
        self._lock = threading.Lock()
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
            tmp = path.with_suffix('.tmp')
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(response.to_dict(), f)
            tmp.rename(path)
        except Exception:
            pass
    
    def _load_persistent(self, key: str) -> Optional[CachedResponse]:
        try:
            path = self._get_persistent_path(key)
            if not path.exists():
                return None

            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return CachedResponse.from_dict(data)

        except Exception:
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

    def _delete_entry(self, url: str, key: str):
        if key in self._memory_cache:
            del self._memory_cache[key]

        if self.config.persistent:
            try:
                path = self._get_persistent_path(key)
                if path.exists():
                    path.unlink()
            except Exception:
                pass
    
    def get(self, url: str, allow_stale: bool = False) -> Optional[CachedResponse]:
        key = self._get_cache_key(url)
        with self._lock:
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

            self._memory_cache.pop(key, None)
            return None
    
    def set(self, url: str, response: CachedResponse):
        key = self._get_cache_key(url)
        with self._lock:
            self._evict_if_needed()
            self._memory_cache[key] = response

        if self.config.persistent:
            self._save_persistent(key, response)

    def delete(self, url: str):
        key = self._get_cache_key(url)
        with self._lock:
            self._delete_entry(url, key)

    def clear(self):
        with self._lock:
            self._memory_cache.clear()

        if self.config.persistent:
            for path in self.config.cache_dir.glob("*.cache"):
                try:
                    path.unlink()
                except Exception:
                    pass