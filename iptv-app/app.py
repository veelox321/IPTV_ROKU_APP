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


def call_api(method: str, path: str, payload: dict | None = None) -> tuple[dict | list | None, str | None]:
    """Make a request to the backend and handle errors gracefully."""
    url = f"{get_base_url()}{path}"
    try:
        response = requests.request(method, url, json=payload, timeout=10)
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
    if status_error:
        st.error(status_error)
    elif isinstance(status_data, dict):
        st.success("Status retrieved.")
        st.json(
            {
                "logged_in": status_data.get("logged_in"),
                "cache_available": status_data.get("cache_available"),
                "channel_count": status_data.get("channel_count"),
                "last_refresh": status_data.get("last_refresh"),
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
    refresh_data, refresh_error = call_api("POST", "/refresh")
    if refresh_error:
        st.error(refresh_error)
    else:
        st.success("Refresh completed.")
        st.json(refresh_data)

st.divider()


# ---- Channel Browser ----

st.subheader("Channel Browser")
st.write("Search available channels.")

search_term = st.text_input("Search", value="", placeholder="UFC, Paramount, News...")

if st.button("Search", key="search_button"):
    channels_data, channels_error = call_api("GET", "/channels")
    if channels_error:
        st.error(channels_error)
    else:
        if isinstance(channels_data, dict) and "channels" in channels_data:
            channels = channels_data.get("channels", [])
        else:
            channels = channels_data if isinstance(channels_data, list) else []

        filtered = [
            channel
            for channel in channels
            if search_term.lower() in str(channel.get("name", "")).lower()
        ]

        st.write(f"Channel count: {len(filtered)}")
        if filtered:
            st.table(
                [
                    {
                        "name": channel.get("name"),
                        "group": channel.get("group") or channel.get("category"),
                    }
                    for channel in filtered
                ]
            )
        else:
            st.info("No channels match your search.")
