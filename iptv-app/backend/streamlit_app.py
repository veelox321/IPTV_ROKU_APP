"""TV-style Streamlit frontend for the IPTV FastAPI backend.

Manual validation steps:
1) Delete old cache file: iptv-app/backend/data/channels.json
2) Start backend: uvicorn backend.app.main:app --reload
3) POST /refresh
4) GET /stats returns non-zero tv/movies/series
5) Run UI: streamlit run backend/streamlit_app.py
6) UI shows categories, grid, and stats chart
"""

from __future__ import annotations

import html
import json
import time
from typing import Any

import matplotlib.pyplot as plt
import requests
import streamlit as st
import streamlit.components.v1 as components

DEFAULT_API_URL = "http://localhost:8000"
PAGE_SIZE = 50
GRID_COLUMNS = 6


# ---------------------------------------------------------------------------
# API HELPERS
# ---------------------------------------------------------------------------


def request_json(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    """Send a JSON request and return parsed payload or an error message."""

    try:
        response = requests.request(
            method,
            url,
            json=payload,
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        return response.json(), None
    except requests.RequestException as exc:
        return None, f"Network error: {exc}"
    except json.JSONDecodeError:
        return None, "Server returned invalid JSON."


def api_url() -> str:
    """Return the API base URL from session state."""

    return st.session_state.get("api_url", DEFAULT_API_URL).rstrip("/")


@st.cache_data(ttl=10)
def fetch_status(base_url: str) -> tuple[dict[str, Any] | None, str | None]:
    return request_json("GET", f"{base_url}/status")


@st.cache_data(ttl=10)
def fetch_stats(base_url: str) -> tuple[dict[str, Any] | None, str | None]:
    return request_json("GET", f"{base_url}/stats")


@st.cache_data(ttl=30)
def fetch_groups(base_url: str) -> tuple[dict[str, Any] | None, str | None]:
    return request_json("GET", f"{base_url}/groups")


# ---------------------------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------------------------


def init_state() -> None:
    defaults = {
        "channels": [],
        "page": 0,
        "total": 0,
        "selected_index": 0,
        "favorites": {},
        "last_filters": {},
        "search_query": "",
        "search_changed_at": 0.0,
        "search_pending": False,
        "refresh_polling": False,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


init_state()


# ---------------------------------------------------------------------------
# STYLES
# ---------------------------------------------------------------------------


st.set_page_config(page_title="IPTV TV", layout="wide")

st.markdown(
    """
    <style>
    body {
        background-color: #0f1115;
        color: #f5f5f5;
    }
    .top-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.5rem 1rem;
        background: #151a21;
        border-radius: 14px;
        box-shadow: 0 8px 18px rgba(0, 0, 0, 0.35);
        margin-bottom: 1rem;
    }
    .status-dot {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    .grid-wrapper {
        background: #12151b;
        border-radius: 16px;
        padding: 1rem;
        box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.05);
    }
    .channel-grid {
        display: grid;
        grid-template-columns: repeat(var(--columns, 6), minmax(0, 1fr));
        gap: 14px;
    }
    .channel-card {
        background: #1a1f27;
        border-radius: 14px;
        padding: 12px;
        height: 140px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        color: #f5f5f5;
        border: 2px solid transparent;
        outline: none;
        cursor: pointer;
        box-shadow: 0 6px 14px rgba(0,0,0,0.4);
        position: relative;
    }
    .channel-card img {
        max-width: 70px;
        max-height: 48px;
        object-fit: contain;
        margin-bottom: 8px;
        filter: drop-shadow(0 4px 8px rgba(0,0,0,0.4));
    }
    .channel-card:focus {
        border-color: #4cc2ff;
        box-shadow: 0 0 0 3px rgba(76,194,255,0.6);
    }
    .channel-card.selected {
        border-color: #ffb347;
        box-shadow: 0 0 0 3px rgba(255,179,71,0.6);
    }
    .favorite-badge {
        position: absolute;
        top: 8px;
        right: 8px;
        font-size: 18px;
        color: #ffd166;
    }
    .details-panel {
        background: #161b22;
        border-radius: 16px;
        padding: 1rem;
        min-height: 420px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.4);
    }
    .pill {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        background: rgba(255,255,255,0.08);
        font-size: 12px;
        margin-right: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# SIDEBAR CONTROLS
# ---------------------------------------------------------------------------


with st.sidebar:
    st.header("IPTV Control Room")
    st.text_input("API base URL", value=DEFAULT_API_URL, key="api_url")

    st.subheader("Credentials")
    host = st.text_input("Host", placeholder="https://provider.example")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if not host or not username or not password:
            st.warning("Please provide host, username, and password.")
        else:
            payload, error = request_json(
                "POST",
                f"{api_url()}/login",
                payload={"host": host, "username": username, "password": password},
            )
            if error:
                st.error(error)
            else:
                st.success("Credentials stored.")

    if st.button("Refresh playlist"):
        payload, error = request_json("POST", f"{api_url()}/refresh", payload={})
        if error:
            st.error(error)
        elif payload and payload.get("status") == "already_running":
            st.info("Refresh already in progress.")
        else:
            st.session_state.refresh_polling = True
            st.success("Refresh started.")

    st.divider()

    st.subheader("Filters")
    search_query = st.text_input("Search", value=st.session_state.search_query)

    groups_payload, groups_error = fetch_groups(api_url())
    categories = ["all"]
    groups = ["All groups"]
    if groups_payload:
        categories.extend(groups_payload.get("categories", []))
        groups.extend([group["name"] for group in groups_payload.get("groups", [])])
    elif groups_error:
        st.caption(groups_error)

    category_choice = st.radio("Category", categories, horizontal=True)
    group_choice = st.selectbox("Group", groups)
    show_favorites = st.checkbox("Favorites only", value=False)


# ---------------------------------------------------------------------------
# HEADER + STATUS
# ---------------------------------------------------------------------------


status_payload, status_error = fetch_status(api_url())
stats_payload, stats_error = fetch_stats(api_url())

status_ok = bool(status_payload) and not status_error
status_color = "#2ecc71" if status_ok else "#e74c3c"
status_text = "Connected" if status_ok else "Disconnected"

st.markdown(
    f"""
    <div class="top-bar">
        <div>
            <strong style="font-size: 1.4rem;">IPTV TV</strong>
            <span style="margin-left: 12px; font-size: 0.9rem;">
                <span class="status-dot" style="background:{status_color};"></span>
                {status_text}
            </span>
        </div>
        <div style="font-size: 0.9rem; text-align:right;">
            <div>Last refresh: {html.escape(str(status_payload.get('last_refresh') if status_payload else 'n/a'))}</div>
            <div>Total channels: {stats_payload.get('total', 0) if stats_payload else 0}</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if status_error:
    st.error(status_error)

if stats_error:
    st.warning(stats_error)

if st.session_state.refresh_polling:
    if status_payload and status_payload.get("refreshing"):
        st.info("Refresh in progress…")
        time.sleep(1)
        st.experimental_rerun()
    else:
        st.session_state.refresh_polling = False
        fetch_status.clear()
        fetch_stats.clear()
        fetch_groups.clear()


# ---------------------------------------------------------------------------
# FILTER & PAGINATION
# ---------------------------------------------------------------------------


if search_query != st.session_state.search_query:
    st.session_state.search_query = search_query
    st.session_state.search_changed_at = time.time()
    st.session_state.search_pending = True

if st.session_state.search_pending:
    elapsed = time.time() - st.session_state.search_changed_at
    if elapsed < 0.4:
        time.sleep(0.4 - elapsed)
        st.experimental_rerun()
    st.session_state.search_pending = False
    st.session_state.last_filters = {}

filters = {
    "search": st.session_state.search_query.strip(),
    "category": category_choice,
    "group": group_choice,
    "favorites_only": show_favorites,
}

reset_needed = filters != st.session_state.last_filters

if reset_needed:
    st.session_state.channels = []
    st.session_state.page = 0
    st.session_state.total = 0
    st.session_state.last_filters = filters


def load_channels() -> tuple[list[dict[str, Any]], int, str | None]:
    if show_favorites:
        favorites = list(st.session_state.favorites.values())
        return favorites, len(favorites), None

    params: dict[str, Any] = {
        "page": st.session_state.page + 1,
        "page_size": PAGE_SIZE,
    }
    if filters["search"]:
        params["search"] = filters["search"]
    if filters["category"] and filters["category"] != "all":
        params["category"] = filters["category"]
    if filters["group"] and filters["group"] != "All groups":
        params["group"] = filters["group"]

    payload, error = request_json("GET", f"{api_url()}/channels", params=params)
    if error:
        return [], 0, error
    if not payload:
        return [], 0, "No response from /channels."

    return payload.get("channels", []), payload.get("total", 0), None


def append_channels() -> None:
    channels, total, error = load_channels()
    if error:
        st.error(error)
        return

    if show_favorites:
        st.session_state.channels = channels
        st.session_state.total = total
        return

    st.session_state.channels.extend(channels)
    st.session_state.page += 1
    st.session_state.total = total


if reset_needed and not show_favorites:
    append_channels()


# ---------------------------------------------------------------------------
# STATS CHART
# ---------------------------------------------------------------------------


if stats_payload:
    fig, ax = plt.subplots(figsize=(5, 2.5))
    categories = ["TV", "Movies", "Series", "Other"]
    values = [
        stats_payload.get("tv", 0),
        stats_payload.get("movies", 0),
        stats_payload.get("series", 0),
        stats_payload.get("other", 0),
    ]
    ax.bar(categories, values, color=["#4cc2ff", "#ffb347", "#b388ff", "#95a5a6"])
    ax.set_facecolor("#0f1115")
    fig.patch.set_facecolor("#0f1115")
    ax.tick_params(colors="#f5f5f5")
    ax.spines["bottom"].set_color("#f5f5f5")
    ax.spines["left"].set_color("#f5f5f5")
    ax.set_title("Channel Mix", color="#f5f5f5")
    st.pyplot(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# GRID + DETAILS PANEL
# ---------------------------------------------------------------------------


def render_channel_grid(channels: list[dict[str, Any]]) -> dict[str, Any] | None:
    cards: list[str] = []
    favorites = st.session_state.favorites

    def favorite_key(channel: dict[str, Any]) -> str:
        return channel.get("url") or channel.get("name", "Unknown")

    for idx, ch in enumerate(channels):
        name = html.escape(ch.get("name", "Unknown"))
        logo = html.escape(ch.get("tvg_logo", ""))
        favorite = favorite_key(ch) in favorites
        selected_class = "selected" if idx == st.session_state.selected_index else ""
        favorite_badge = "★" if favorite else ""

        logo_html = (
            f"<img src='{logo}' alt='logo'>" if logo else "<div style='height:48px;'></div>"
        )

        cards.append(
            f"""
            <div class="channel-card {selected_class}" tabindex="0" data-index="{idx}">
                {logo_html}
                <div>{name}</div>
                <div class="favorite-badge">{favorite_badge}</div>
            </div>
            """
        )

    html_payload = f"""
    <div class="grid-wrapper">
        <div class="channel-grid" style="--columns: {GRID_COLUMNS};">
            {''.join(cards)}
        </div>
    </div>
    <script>
        const cards = Array.from(document.querySelectorAll('.channel-card'));
        const columns = {GRID_COLUMNS};

        function selectCard(index) {{
            if (!cards[index]) return;
            cards.forEach((card) => card.classList.remove('selected'));
            cards[index].classList.add('selected');
            if (window.Streamlit) {{
                Streamlit.setComponentValue({{ action: 'select', index }});
            }}
        }}

        function toggleFavorite(index) {{
            if (window.Streamlit) {{
                Streamlit.setComponentValue({{ action: 'favorite', index }});
            }}
        }}

        cards.forEach((card) => {{
            card.addEventListener('click', () => selectCard(parseInt(card.dataset.index, 10)));
            card.addEventListener('keydown', (event) => {{
                const current = parseInt(card.dataset.index, 10);
                let target = current;
                if (event.key === 'ArrowRight') target = current + 1;
                if (event.key === 'ArrowLeft') target = current - 1;
                if (event.key === 'ArrowDown') target = current + columns;
                if (event.key === 'ArrowUp') target = current - columns;
                if (target !== current && cards[target]) {{
                    event.preventDefault();
                    cards[target].focus();
                }}
                if (event.key === 'Enter') {{
                    event.preventDefault();
                    selectCard(current);
                }}
                if (event.key === ' ') {{
                    event.preventDefault();
                    toggleFavorite(current);
                }}
            }});
        }});

        if (cards.length) {{
            const initial = cards[{st.session_state.selected_index}] || cards[0];
            initial.focus();
        }}
    </script>
    """

    return components.html(html_payload, height=520, scrolling=True)


left, right = st.columns([3.5, 1.5], gap="large")

with left:
    if not st.session_state.channels:
        append_channels()

    channels_to_display = st.session_state.channels
    if show_favorites:
        channels_to_display = list(st.session_state.favorites.values())

    if channels_to_display:
        event = render_channel_grid(channels_to_display)
        if isinstance(event, dict):
            if event.get("action") == "select":
                st.session_state.selected_index = int(event.get("index", 0))
            elif event.get("action") == "favorite":
                idx = int(event.get("index", 0))
                if 0 <= idx < len(channels_to_display):
                    channel = channels_to_display[idx]
                    key = channel.get("url") or channel.get("name")
                    if key in st.session_state.favorites:
                        st.session_state.favorites.pop(key, None)
                    else:
                        st.session_state.favorites[key] = channel
    else:
        st.info("No channels loaded yet.")

    if not show_favorites and len(st.session_state.channels) < st.session_state.total:
        if st.button("Load more"):
            append_channels()

with right:
    st.markdown("<div class='details-panel'>", unsafe_allow_html=True)

    selected_channel = None
    if channels_to_display:
        if st.session_state.selected_index >= len(channels_to_display):
            st.session_state.selected_index = 0
        selected_channel = channels_to_display[st.session_state.selected_index]

    if selected_channel:
        st.subheader(selected_channel.get("name", "Unknown"))
        st.caption(selected_channel.get("group", "Unknown"))

        st.markdown(
            f"<span class='pill'>{selected_channel.get('category', 'other')}</span>",
            unsafe_allow_html=True,
        )

        logo_url = selected_channel.get("tvg_logo")
        if logo_url:
            st.image(logo_url, width=120)

        url = selected_channel.get("url", "about:blank")
        st.markdown(f"[Play Stream]({url})")

        components.html(
            f"""
            <button style="padding:6px 12px;border-radius:10px;background:#4cc2ff;border:none;color:#0f1115;cursor:pointer;"
                onclick="navigator.clipboard.writeText('{html.escape(url)}')">
                Copy URL
            </button>
            """,
            height=50,
        )

        st.code(url, language="text")
        st.write("TVG ID:", selected_channel.get("tvg_id", "n/a"))
        st.write("TVG Name:", selected_channel.get("tvg_name", "n/a"))
        st.write("Channel No:", selected_channel.get("tvg_chno", "n/a"))
    else:
        st.caption("Select a channel to see details.")

    st.markdown("</div>", unsafe_allow_html=True)
