"""Streamlit frontend for the IPTV FastAPI backend."""

from __future__ import annotations

import json
from typing import Any

import requests
import streamlit as st

DEFAULT_API_URL = "http://localhost:8000"
MAX_PAGE_SIZE = 100


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


st.set_page_config(page_title="IPTV Dashboard", layout="wide")
st.title("IPTV Dashboard")

with st.sidebar:
    st.header("Backend connection")
    st.text_input("API base URL", value=DEFAULT_API_URL, key="api_url")

    st.subheader("IPTV credentials")
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

    if st.button("Refresh channels"):
        with st.spinner("Refreshing channels..."):
            payload, error = request_json("POST", f"{api_url()}/refresh", payload={})
        if error:
            st.error(error)
        elif payload and payload.get("status") == "already_running":
            st.info("Refresh already in progress.")
        else:
            st.success("Refresh started.")

error_banner = st.empty()

st.subheader("Dashboard")
if st.button("Refresh dashboard"):
    status_payload, status_error = request_json("GET", f"{api_url()}/status")
    stats_payload, stats_error = request_json("GET", f"{api_url()}/stats")
    if status_error or stats_error:
        error_banner.error(status_error or stats_error)
    else:
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Channels", stats_payload.get("total", 0))
        col2.metric("TV", stats_payload.get("tv", 0))
        col3.metric("Movies", stats_payload.get("movies", 0))
        col4.metric("Series", stats_payload.get("series", 0))
        col5.metric("Other", stats_payload.get("other", 0))
        st.caption(
            f"Last refresh: {status_payload.get('last_refresh')} | "
            f"Refreshing: {status_payload.get('refreshing')}"
        )

st.subheader("Channels")
search_term = st.text_input("Search channels")
page_size = st.number_input("Page size", min_value=1, max_value=MAX_PAGE_SIZE, value=50)
page = st.number_input("Page", min_value=1, value=1)

categories_payload, categories_error = request_json("GET", f"{api_url()}/groups")
categories = ["all"]
if categories_payload and "categories" in categories_payload:
    categories.extend(categories_payload["categories"])
category = st.selectbox("Category", categories)

if st.button("Load channels"):
    params = {
        "page": int(page),
        "page_size": int(page_size),
    }
    if search_term:
        params["search"] = search_term
    if category and category != "all":
        params["category"] = category

    payload, error = request_json("GET", f"{api_url()}/channels", params=params)
    if error:
        error_banner.error(error)
    elif payload:
        channels = payload.get("channels", [])
        st.caption(
            f"Total: {payload.get('total', 0)} | "
            f"Page: {payload.get('page', page)}"
        )
        if channels:
            st.dataframe(channels, use_container_width=True)
        else:
            st.info("No channels returned.")

with st.expander("Raw response"):
    if "payload" in locals() and payload is not None:
        st.code(json.dumps(payload, indent=2), language="json")
    else:
        st.caption("Load channels or refresh the dashboard to see raw responses.")
