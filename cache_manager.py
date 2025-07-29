import os
import json
import time
import hashlib
from config import CACHE_DIR, DEFAULT_CACHE_TTL


class CacheManager:
    """Manages API context caching and storage"""

    _instance = None

    def __new__(cls):
        """Implement singleton pattern"""
        if cls._instance is None:
            cls._instance = super(CacheManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the cache manager"""
        if not self._initialized:
            self.cache_registry = {}
            self.cache_ttl = DEFAULT_CACHE_TTL
            self._load_cache_registry()
            self._initialized = True

    def get_cache_key(self, personal_context):
        """Generate a unique key for caching based on personal context and system template"""
        # Create a unique hash from the combination of personal context and system template
        content = personal_context
        return hashlib.md5(content.encode()).hexdigest()

    def save_cache_info(self, cache_key, cache_name, expiry_time):
        """Save cache information to registry"""
        self.cache_registry[cache_key] = {
            "cache_name": cache_name,
            "expiry": expiry_time
        }
        # Save to disk too for persistence between app restarts
        self._persist_cache_registry()

    def _persist_cache_registry(self):
        """Save registry to disk"""
        cache_file = os.path.join(CACHE_DIR, "cache_registry.json")
        try:
            with open(cache_file, 'w') as f:
                json.dump(self.cache_registry, f)
        except Exception as e:
            # Silently fail for cache registry persistence issues
            print(f"Error persisting cache registry: {str(e)}")

    def _load_cache_registry(self):
        """Load cache registry from disk"""
        cache_file = os.path.join(CACHE_DIR, "cache_registry.json")
        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    self.cache_registry = json.load(f)
                    # Filter out expired caches
                    self._clean_expired_caches()
        except Exception as e:
            # If there's any issue, start with an empty registry
            print(f"Error loading cache registry: {str(e)}")
            self.cache_registry = {}

    def _clean_expired_caches(self):
        """Remove expired caches from registry"""
        current_time = time.time()
        self.cache_registry = {
            k: v for k, v in self.cache_registry.items()
            if v.get("expiry", 0) > current_time
        }

    def get_cache_config(self, cache_key):
        """Check if we have a valid cache for this key and return config if found"""
        current_time = time.time()

        if cache_key in self.cache_registry:
            cache_info = self.cache_registry[cache_key]
            if cache_info["expiry"] > current_time:
                # Cache is valid, return its name
                return cache_info["cache_name"]

        return None

    def set_cache_ttl(self, ttl):
        """Set the cache Time-To-Live in seconds"""
        self.cache_ttl = ttl

    def delete_all_caches(self, api_client=None):
        """Delete all caches through API and clear local registry"""
        if api_client:
            # Try to delete caches via API
            for cache_key, info in list(self.cache_registry.items()):
                if "cache_name" in info:
                    try:
                        api_client.caches.delete(name=info["cache_name"])
                    except Exception:
                        pass  # Ignore errors for individual cache deletions

        # Clear local registry regardless of API success
        self.cache_registry = {}

        # Clear stored registry
        cache_file = os.path.join(CACHE_DIR, "cache_registry.json")
        if os.path.exists(cache_file):
            try:
                os.remove(cache_file)
            except Exception:
                pass

        return True

    @property
    def ttl_seconds(self):
        return self.cache_ttl

    @property
    def ttl_string(self):
        """Get the TTL in string format with 's' suffix for API"""
        return f"{self.cache_ttl}s"

    def get_active_caches_info(self):
        """Get information about active caches"""
        current_time = time.time()
        active_caches = []

        for cache_key, info in self.cache_registry.items():
            if "expiry" in info and info["expiry"] > current_time:
                time_left = info["expiry"] - current_time
                active_caches.append({
                    "name": info["cache_name"],
                    "minutes_remaining": int(time_left / 60)
                })

        return active_caches
