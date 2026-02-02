"""Streamlit frontend for the IPTV FastAPI backend."""

from __future__ import annotations

import json
from typing import Any

import requests
import streamlit as st

DEFAULT_API_URL = "http://localhost:8000"


def post_json(url: str, payload: dict[str, Any]) -> requests.Response:
    """Send a JSON POST request and return the response."""

    return requests.post(url, json=payload, timeout=30)


def get_json(url: str, params: dict[str, Any] | None = None) -> requests.Response:
    """Send a JSON GET request and return the response."""

    return requests.get(url, params=params, timeout=30)


st.set_page_config(page_title="IPTV Dashboard", layout="wide")
st.title("IPTV Dashboard")

with st.sidebar:
    st.header("Backend connection")
    api_url = st.text_input("API base URL", value=DEFAULT_API_URL)

    st.subheader("IPTV credentials")
    host = st.text_input("Host", placeholder="https://provider.example")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if not host or not username or not password:
            st.warning("Please provide host, username, and password.")
        else:
            response = post_json(
                f"{api_url}/login",
                {"host": host, "username": username, "password": password},
            )
            if response.ok:
                st.success("Credentials stored.")
            else:
                st.error(
                    f"Login failed ({response.status_code}): {response.text}",
                )

    if st.button("Refresh channels"):
        response = post_json(f"{api_url}/refresh", {})
        if response.ok:
            st.success("Channel cache refreshed.")
        else:
            st.error(f"Refresh failed ({response.status_code}): {response.text}")

st.subheader("Channels")

search_term = st.text_input("Search channels")
if st.button("Load channels"):
    params = {"search": search_term} if search_term else None
    response = get_json(f"{api_url}/channels", params=params)
    if response.ok:
        payload = response.json()
        channels = payload.get("channels", [])
        st.caption(
            f"Status: {payload.get('status')} | Total: {payload.get('total', 0)}",
        )
        if channels:
            st.dataframe(channels, use_container_width=True)
        else:
            st.info(payload.get("detail", "No channels returned."))
    else:
        st.error(f"Request failed ({response.status_code}): {response.text}")

with st.expander("Raw response"):
    if "response" in locals():
        try:
            raw_payload = response.json()
        except json.JSONDecodeError:
            raw_payload = {"raw": response.text}
        st.code(json.dumps(raw_payload, indent=2), language="json")
    else:
        st.caption("Load channels to see the raw response here.")
