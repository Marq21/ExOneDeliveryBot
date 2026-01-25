# src/utils/config_loader.py
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Dict

class ConfigLoader:
    _cache: Dict[str, Any] = {}
    _last_load: datetime = datetime.min
    _ttl_seconds = 30  # обновлять не чаще чем раз в 30 сек

    @classmethod
    def _load_from_file(cls) -> Dict[str, Any]:
        config_path = Path(__file__).parent.parent / "config" / "constants.json"
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        now = datetime.now()
        if now - cls._last_load > timedelta(seconds=cls._ttl_seconds):
            cls._cache = cls._load_from_file()
            cls._last_load = now
        return cls._cache

    @classmethod
    def get(cls, key: str, default=None):
        return cls.get_config().get(key, default)