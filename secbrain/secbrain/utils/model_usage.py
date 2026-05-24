"""Model usage tracking and tier enforcement."""

import fcntl
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

CACHE_DIR = Path.home() / ".secbrain_cache"
PRO_USAGE_FILE = CACHE_DIR / "pro_daily.json"


def _load_usage_from_locked_file(handle: Any, today: str) -> dict[str, Any]:
    handle.seek(0)
    try:
        data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {"date": today, "count": 0}

    if isinstance(data, dict) and data.get("date") == today:
        return data
    return {"date": today, "count": 0}

def get_premium_model_with_cap(tier_name: str = "premium", fallback_tier: str = "reason") -> str:
    """
    Get the premium model, with a daily cap check.
    If cap is reached, falls back to the reasoning tier.
    """
    from secbrain.config.constants import MODEL_TIERS
    
    model = MODEL_TIERS.get(tier_name, "gemini-2.5-pro")
    
    # Only enforce cap for gemini-2.5-pro
    if "gemini-2.5-pro" not in model.lower():
        return model
        
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        with open(PRO_USAGE_FILE, "a+", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            try:
                usage = _load_usage_from_locked_file(f, today)
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
                
        count = int(usage.get("count", 0))
        if count >= 45:
            logger.warning(
                "WARNING: %s daily cap reached (%d/45), falling back to %s tier",
                model, usage["count"], fallback_tier
            )
            return MODEL_TIERS.get(fallback_tier, "gemini-2.5-flash")
            
        return model
    except Exception as e:
        logger.error("Error checking premium model cap: %s", e)
        return model

def increment_premium_usage() -> None:
    """Increment the daily usage count for premium models."""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        
        with open(PRO_USAGE_FILE, "a+", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                usage = _load_usage_from_locked_file(f, today)
                usage["count"] = int(usage.get("count", 0)) + 1
                f.seek(0)
                f.truncate()
                json.dump(usage, f)
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
    except Exception as e:
        logger.error("Error incrementing premium usage: %s", e)
