"""Streamlit GUI for the IPTV FastAPI backend."""

from __future__ import annotations

import requests
import streamlit as st


# ---- Configuration helpers ----

def get_base_url() -> str:
    """Return the backend base URL from session state or default."""
    return st.session_state.get("base_url", "http://127.0.0.1:8000").rstrip("/")


def set_base_url(value: str) -> None:
    """Store the backend base URL in session state."""
    st.session_state["base_url"] = value.strip().rstrip("/")


def call_api(
    method: str,
    path: str,
    payload: dict | None = None,
    params: dict | None = None,
) -> tuple[dict | list | None, str | None]:
    """Make a request to the backend and handle errors gracefully."""
    url = f"{get_base_url()}{path}"
    try:
        response = requests.request(
            method,
            url,
            json=payload,
            params=params,
            timeout=10,
        )
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.RequestException as exc:
        return None, f"Network error: {exc}"
    except ValueError:
        return None, "Server returned invalid JSON."


# ---- Page setup ----

st.set_page_config(page_title="IPTV Backend GUI", layout="wide")
st.title("IPTV Backend GUI (Prototype)")
st.caption("Developer-focused GUI for the FastAPI backend. No credentials are stored.")


# ---- Status Panel ----

st.subheader("Status Panel")
st.write("Check backend status and cached data.")

if st.button("Check status", key="status_button"):
    status_data, status_error = call_api("GET", "/status")
    stats_data, stats_error = call_api("GET", "/stats")
    if status_error or stats_error:
        st.error(status_error or stats_error)
    elif isinstance(status_data, dict) and isinstance(stats_data, dict):
        st.success("Status retrieved.")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total", stats_data.get("total", 0))
        col2.metric("TV", stats_data.get("tv", 0))
        col3.metric("Movies", stats_data.get("movies", 0))
        col4.metric("Series", stats_data.get("series", 0))
        col5.metric("Other", stats_data.get("other", 0))
        st.json(
            {
                "logged_in": status_data.get("logged_in"),
                "cache_available": status_data.get("cache_available"),
                "channel_count": status_data.get("channel_count"),
                "last_refresh": status_data.get("last_refresh"),
                "refreshing": status_data.get("refreshing"),
            }
        )
    else:
        st.error("Unexpected status response.")

st.divider()


# ---- Login Panel ----

st.subheader("Login Panel")
st.write("Login is optional if .env credentials exist on the backend.")

col1, col2 = st.columns(2)
with col1:
    host_input = st.text_input("Host", value=get_base_url(), placeholder="http://127.0.0.1:8000")
    username = st.text_input("Username", value="", placeholder="user@example.com")
with col2:
    password = st.text_input(
        "Password",
        value="",
        type="password",
        placeholder="••••••••",
        key="login_password",
    )

if st.button("Login", key="login_button"):
    set_base_url(host_input)
    login_payload = {"host": host_input, "username": username, "password": password}
    login_data, login_error = call_api("POST", "/login", payload=login_payload)
    st.session_state["login_password"] = ""

    if login_error:
        st.error(login_error)
    else:
        st.success("Login request sent.")
        st.json(login_data)

st.divider()


# ---- Refresh Panel ----

st.subheader("Refresh Panel")
st.write("Refresh channels and update cache.")

if st.button("Refresh channels", key="refresh_button"):
    with st.spinner("Refreshing channels..."):
        refresh_data, refresh_error = call_api("POST", "/refresh")
    if refresh_error:
        st.error(refresh_error)
    elif isinstance(refresh_data, dict) and refresh_data.get("status") == "already_running":
        st.info("Refresh already in progress.")
    else:
        st.success("Refresh started.")
        st.json(refresh_data)

st.divider()


# ---- Channel Browser ----

st.subheader("Channel Browser")
st.write("Search available channels.")

search_term = st.text_input("Search", value="", placeholder="UFC, Paramount, News...")
page = st.number_input("Page", min_value=1, value=1)
page_size = st.number_input("Page size", min_value=1, max_value=100, value=50)
categories_data, categories_error = call_api("GET", "/groups")
categories = ["all"]
if isinstance(categories_data, dict):
    categories.extend(categories_data.get("categories", []))
category = st.selectbox("Category", categories)

if st.button("Search", key="search_button"):
    params = {"page": int(page), "page_size": int(page_size)}
    if search_term:
        params["search"] = search_term
    if category and category != "all":
        params["category"] = category
    channels_data, channels_error = call_api("GET", "/channels", params=params)
    if channels_error:
        st.error(channels_error)
    else:
        channels = (
            channels_data.get("channels", [])
            if isinstance(channels_data, dict)
            else []
        )

        st.write(f"Channel count: {channels_data.get('total', 0)}")
        if channels:
            st.table(
                [
                    {
                        "name": channel.get("name"),
                        "group": channel.get("group"),
                        "category": channel.get("category"),
                    }
                    for channel in channels
                ]
            )
        else:
            st.info("No channels match your search.")
