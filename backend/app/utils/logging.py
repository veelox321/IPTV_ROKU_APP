"""Logging helpers for the IPTV backend."""

from __future__ import annotations

import logging


def configure_logging(debug: bool) -> None:
    """Configure application logging level and format."""

    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
