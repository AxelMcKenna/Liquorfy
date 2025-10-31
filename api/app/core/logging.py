from __future__ import annotations

import logging
import sys
from typing import Any, Dict

from .config import get_settings


def configure_logging() -> None:
    settings = get_settings()
    log_level = logging.DEBUG if settings.environment != "production" else logging.INFO

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


__all__ = ["configure_logging"]
