"""Streamlit admin/debug UI for the IPTV FastAPI backend."""

from __future__ import annotations

from typing import Any

import streamlit as st

from components import DEFAULT_API_URL, request_json


st.set_page_config(page_title="IPTV Admin Console", layout="wide")


@st.cache_data(ttl=10)
def fetch_status(base_url: str) -> tuple[dict[str, Any] | None, str | None]:
    return request_json("GET", f"{base_url}/status")


@st.cache_data(ttl=10)
def fetch_stats(base_url: str) -> tuple[dict[str, Any] | None, str | None]:
    return request_json("GET", f"{base_url}/stats")


@st.cache_data(ttl=30)
def fetch_groups(base_url: str) -> tuple[dict[str, Any] | None, str | None]:
    return request_json("GET", f"{base_url}/groups")


with st.sidebar:
    st.header("Admin Controls")
    api_url = st.text_input("Backend API URL", value=DEFAULT_API_URL).rstrip("/")

    st.divider()
    st.subheader("Login (optional)")
    host = st.text_input("IPTV Host", placeholder="https://provider.example")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Send credentials"):
        if not host or not username or not password:
            st.warning("Provide host, username, and password to login.")
        else:
            payload, error = request_json(
                "POST",
                f"{api_url}/login",
                payload={"host": host, "username": username, "password": password},
            )
            if error:
                st.error(error)
            else:
                st.success("Credentials accepted.")

    st.divider()

    if st.button("Refresh channel cache"):
        payload, error = request_json("POST", f"{api_url}/refresh", payload={})
        if error:
            st.error(error)
        elif payload and payload.get("status") == "already_running":
            st.info("Refresh already in progress.")
        else:
            st.success("Refresh started.")
        fetch_status.clear()
        fetch_stats.clear()
        fetch_groups.clear()


st.title("IPTV Admin Console")

status_payload, status_error = fetch_status(api_url)
stats_payload, stats_error = fetch_stats(api_url)
groups_payload, groups_error = fetch_groups(api_url)

col1, col2, col3, col4, col5 = st.columns(5)

if status_payload:
    col1.metric("Logged In", "Yes" if status_payload.get("logged_in") else "No")
    col2.metric("Refreshing", "Yes" if status_payload.get("refreshing") else "No")
    col3.metric("Cache", "Ready" if status_payload.get("cache_available") else "Empty")
    col4.metric("Channels", status_payload.get("channel_count", 0))
    col5.metric("Last Refresh", status_payload.get("last_refresh", "n/a"))
else:
    st.warning(status_error or "Unable to fetch status.")

st.divider()

st.subheader("Cache Stats")
if stats_payload:
    st.bar_chart(
        {
            "tv": stats_payload.get("tv", 0),
            "movies": stats_payload.get("movies", 0),
            "series": stats_payload.get("series", 0),
            "other": stats_payload.get("other", 0),
        }
    )
else:
    st.warning(stats_error or "Unable to fetch stats.")

st.subheader("Top Groups")
if groups_payload:
    groups = groups_payload.get("groups", [])
    st.dataframe(groups[:15], use_container_width=True)
elif groups_error:
    st.warning(groups_error)

st.subheader("Debug")
with st.expander("Raw payloads"):
    st.write("/status", status_payload)
    st.write("/stats", stats_payload)
    st.write("/groups", groups_payload)
