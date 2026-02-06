"""Helpers to format IPTV cache for Roku SceneGraph rows."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from backend.app.services import iptv

_ROW_LIMIT = 6
_ROW_ITEM_LIMIT = 12


CATEGORY_LABELS = {
    "tv": "Live",
    "movies": "Movies",
    "series": "Series",
    "other": "Other",
}


GENRE_FALLBACKS = {
    "tv": "Live",
    "movies": "Movies",
    "series": "Series",
    "other": "Other",
}


def build_rows(channels: Iterable[dict], category: str) -> list[dict]:
    """Build Roku-ready rows for a given category."""

    normalized_category = iptv.coerce_category(category, "")
    grouped: dict[str, list[dict]] = defaultdict(list)

    for channel in channels:
        channel_category = iptv.coerce_category(
            str(channel.get("category") or ""),
            str(channel.get("group") or ""),
        )
        if channel_category != normalized_category:
            continue

        group = str(channel.get("group") or "Unknown").strip() or "Unknown"
        grouped[group].append(channel)

    rows: list[dict] = []
    for group, items in sorted(grouped.items(), key=lambda item: item[0].lower()):
        row_items = []
        for idx, channel in enumerate(items[:_ROW_ITEM_LIMIT], start=1):
            channel_id = str(channel.get("tvg_chno") or channel.get("name") or idx)
            row_items.append(
                {
                    "id": channel_id,
                    "title": channel.get("name") or "Unknown",
                    "description": channel.get("name") or "",
                    "genre": group,
                    "category": normalized_category,
                    "stream_url": channel.get("url") or "",
                    "poster_url": channel.get("tvg_logo"),
                    "duration": "",
                    "rating": "",
                }
            )

        rows.append(
            {
                "title": group,
                "items": row_items,
            }
        )

    return rows[:_ROW_LIMIT]


def build_status_payload(cache_payload: dict | None) -> dict:
    """Return summary metrics used by Roku status panel."""

    if not cache_payload:
        return {
            "last_refresh": None,
            "channels": 0,
            "movies": 0,
            "series": 0,
            "episodes": 0,
            "total_playlists": 0,
            "account_status": "Disconnected",
        }

    stats = cache_payload.get("stats", {}) if isinstance(cache_payload, dict) else {}
    return {
        "last_refresh": cache_payload.get("timestamp"),
        "channels": int(stats.get("tv", 0)),
        "movies": int(stats.get("movies", 0)),
        "series": int(stats.get("series", 0)),
        "episodes": 0,
        "total_playlists": 1,
        "account_status": "Active",
    }
