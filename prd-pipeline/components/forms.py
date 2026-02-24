"""Secure input fields and test connection buttons."""
import streamlit as st
from typing import Callable, Optional


def secret_input(label: str, key: str, default: str = "", help_text: Optional[str] = None) -> str:
    """Password-style input for API keys. Returns current value."""
    return st.text_input(
        label,
        value=default,
        type="password",
        key=key,
        help=help_text,
    )


def test_button(
    label: str,
    on_click: Callable[[], tuple[bool, str]],
    key: str,
    service_name: str,
) -> None:
    """
    Button that runs on_click (should return (success, error_message)),
    then updates st.session_state.connection_status and connection_errors.
    """
    if st.button(label, key=key):
        with st.spinner(f"Testing {service_name}..."):
            ok, err = on_click()
        status = st.session_state.get("connection_status", {})
        errors = st.session_state.get("connection_errors", {})
        status[service_name] = ok
        errors[service_name] = err or ""
        st.session_state.connection_status = status
        st.session_state.connection_errors = errors
        if ok:
            st.success(f"{service_name}: Connected.")
        else:
            st.error(f"{service_name}: {err}")
        st.rerun()
