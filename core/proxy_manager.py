"""
TikTok Boost Orchestrator - Proxy Management
Rotating proxy support with health checking and failover.
"""

import random
from typing import List, Optional
from loguru import logger


class ProxyManager:
    """Manages a pool of proxies with rotation and health tracking."""

    def __init__(self, proxies: List[str] = None):
        self.proxies = proxies or []
        self.current_index = 0
        self.failed_proxies = set()
        self.proxy_health = {}  # proxy -> success_count
        logger.info(f"ProxyManager initialized with {len(self.proxies)} proxies")

    def add_proxy(self, proxy: str) -> None:
        """Add a proxy to the pool."""
        if proxy not in self.proxies:
            self.proxies.append(proxy)
            logger.debug(f"Added proxy: {proxy}")

    def get_next(self) -> Optional[str]:
        """Get next available proxy using round-robin with health awareness."""
        available = [p for p in self.proxies if p not in self.failed_proxies]
        if not available:
            logger.warning("All proxies failed, resetting failed list")
            self.failed_proxies.clear()
            available = self.proxies

        if not available:
            return None

        # Prefer healthy proxies
        healthy = [p for p in available if self.proxy_health.get(p, 0) >= 0]
        if healthy:
            proxy = random.choice(healthy)
        else:
            proxy = random.choice(available)

        self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy

    def mark_failed(self, proxy: str) -> None:
        """Mark a proxy as failed."""
        if proxy:
            self.failed_proxies.add(proxy)
            self.proxy_health[proxy] = self.proxy_health.get(proxy, 0) - 1
            logger.warning(f"Marked proxy as failed: {proxy}")

    def mark_success(self, proxy: str) -> None:
        """Mark a proxy as successful."""
        if proxy:
            self.proxy_health[proxy] = self.proxy_health.get(proxy, 0) + 1
            if proxy in self.failed_proxies:
                self.failed_proxies.remove(proxy)

    def get_proxy_dict(self, proxy: Optional[str]) -> dict:
        """Convert proxy string to requests/httpx proxy dict."""
        if not proxy:
            return {}
        return {
            "http": proxy,
            "https": proxy,
        }

    def get_playwright_proxy(self, proxy: Optional[str]) -> Optional[dict]:
        """Convert proxy string to Playwright proxy config."""
        if not proxy:
            return None
        # Parse proxy string: http://user:pass@host:port or host:port
        if "://" in proxy:
            protocol, rest = proxy.split("://", 1)
            if "@" in rest:
                auth, server = rest.split("@", 1)
                username, password = auth.split(":", 1)
                return {
                    "server": f"{protocol}://{server}",
                    "username": username,
                    "password": password,
                }
            return {"server": f"{protocol}://{rest}"}
        return {"server": f"http://{proxy}"}
