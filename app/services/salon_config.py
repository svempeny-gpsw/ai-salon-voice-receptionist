from __future__ import annotations
import json
from functools import lru_cache
from pathlib import Path

from app.core.config import settings


@lru_cache(maxsize=1)
def load_salon_config(path: str | None = None):
    target = Path(path or settings.salon_config_path)
    return json.loads(target.read_text())


def get_service(config: dict, service_id: str):
    for svc in config.get("salon", {}).get("services", []):
        if svc.get("id") == service_id:
            return svc
    return None
