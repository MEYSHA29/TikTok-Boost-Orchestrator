"""
TikTok Boost Orchestrator - Core Utilities
Shared helpers, logging setup, and common functions.
"""

import json
import os
import random
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger


def setup_logging(log_level: str = "INFO") -> None:
    """Configure loguru logger with colored output and file rotation."""
    logger.remove()
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )
    logger.add(
        "sessions/orchestrator.log",
        rotation="10 MB",
        retention="7 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    )


def random_delay(min_sec: float, max_sec: float) -> None:
    """Sleep for a random duration between min and max seconds."""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)


def parse_cooldown(text: str) -> Optional[int]:
    """Extract cooldown seconds from provider response text."""
    patterns = [
        r"Please wait\s*(\d+)\s*seconds",
        r"wait\s*(\d+)\s*sec",
        r"cooldown[:\s]*(\d+)",
        r"try again in\s*(\d+)",
        r"(\d+)\s*seconds remaining",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def save_session(provider_name: str, cookies: Dict[str, Any], session_dir: str = "./sessions") -> None:
    """Persist session cookies to disk."""
    path = Path(session_dir) / f"{provider_name}_session.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump({"cookies": cookies, "timestamp": datetime.now().isoformat()}, f)
    logger.debug(f"Session saved for {provider_name}")


def load_session(provider_name: str, session_dir: str = "./sessions") -> Optional[Dict[str, Any]]:
    """Load persisted session cookies if valid (< 6 hours old)."""
    path = Path(session_dir) / f"{provider_name}_session.json"
    if not path.exists():
        return None
    try:
        with open(path, "r") as f:
            data = json.load(f)
        saved_time = datetime.fromisoformat(data["timestamp"])
        if datetime.now() - saved_time < timedelta(hours=6):
            logger.debug(f"Loaded valid session for {provider_name}")
            return data["cookies"]
    except Exception as e:
        logger.warning(f"Failed to load session for {provider_name}: {e}")
    return None


def load_proxy_list(file_path: str) -> List[str]:
    """Load proxy list from file, one per line."""
    if not file_path or not os.path.exists(file_path):
        return []
    with open(file_path, "r") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


class StatsTracker:
    """Track boost statistics across all providers."""

    def __init__(self, stats_file: str = "./sessions/stats.json"):
        self.stats_file = stats_file
        self.stats = self._load()

    def _load(self) -> Dict[str, Any]:
        if os.path.exists(self.stats_file):
            with open(self.stats_file, "r") as f:
                return json.load(f)
        return {
            "total_boosts": 0,
            "providers": {},
            "services": {},
            "started_at": datetime.now().isoformat(),
        }

    def record(self, provider: str, service: str, success: bool, amount: int = 0) -> None:
        """Record a boost attempt result."""
        self.stats["total_boosts"] += 1

        if provider not in self.stats["providers"]:
            self.stats["providers"][provider] = {"success": 0, "failed": 0, "total": 0}
        self.stats["providers"][provider]["total"] += 1
        if success:
            self.stats["providers"][provider]["success"] += 1
        else:
            self.stats["providers"][provider]["failed"] += 1

        svc_key = f"{provider}:{service}"
        if svc_key not in self.stats["services"]:
            self.stats["services"][svc_key] = {"success": 0, "failed": 0, "amount": 0}
        self.stats["services"][svc_key]["success" if success else "failed"] += 1
        self.stats["services"][svc_key]["amount"] += amount

        self._save()

    def _save(self) -> None:
        with open(self.stats_file, "w") as f:
            json.dump(self.stats, f, indent=2)

    def get_summary(self) -> str:
        """Return formatted statistics summary."""
        lines = ["═" * 50, "📊 BOOST STATISTICS", "═" * 50]
        lines.append(f"Total Boosts: {self.stats['total_boosts']}")
        lines.append("")
        for provider, data in self.stats["providers"].items():
            rate = (data['success'] / data['total'] * 100) if data['total'] > 0 else 0
            lines.append(f"  {provider}: {data['success']}/{data['total']} ({rate:.1f}%)")
        return "\n".join(lines)


import sys
setup_logging("INFO")
