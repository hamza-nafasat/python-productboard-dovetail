"""Step 1: API Configuration - keys, test connection."""
import logging

import streamlit as st

from api import dovetail, productboard
from app.state import get_api_config, next_step
from components.connection_status import render_status_grid
from components.forms import secret_input
from core.models import APIConfig

logger = logging.getLogger(__name__)


def _test_dovetail() -> tuple[bool, str]:
    cfg = get_api_config()
    return dovetail.test_connection(cfg.get("dovetail_key", ""))


def _test_productboard() -> tuple[bool, str]:
    cfg = get_api_config()
    return productboard.test_connection(cfg.get("productboard_key", ""))


def render_step_setup() -> None:
    st.header("Step 1: Setup / API Configuration")
    st.caption("Enter API keys. Keys are stored only in this session.")

    cfg = st.session_state.get("api_config", {})

    with st.form("api_config_form", clear_on_submit=False):
        st.subheader("API Keys")
        dovetail_key = secret_input("Dovetail API Key", "dovetail_key", cfg.get("dovetail_key", ""))
        productboard_key = secret_input(
            "Productboard API Key", "productboard_key", cfg.get("productboard_key", "")
        )

        submitted = st.form_submit_button("Save configuration")
        if submitted:
            st.session_state.api_config = {
                "dovetail_key": dovetail_key,
                "productboard_key": productboard_key,
            }
            st.success("Configuration saved to session.")
            st.rerun()

    st.divider()
    st.subheader("Test connections")
    status = st.session_state.get("connection_status", {})
    errors = st.session_state.get("connection_errors", {})

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Test Dovetail", key="test_dovetail_btn"):
            with st.spinner("Testing Dovetail..."):
                ok, err = _test_dovetail()
            status["dovetail"] = ok
            errors["dovetail"] = err
            st.session_state.connection_status = status
            st.session_state.connection_errors = errors
            st.success("Connected.") if ok else st.error(err)
            st.rerun()
        if st.button("Test Productboard", key="test_pb_btn"):
            with st.spinner("Testing Productboard..."):
                ok, err = _test_productboard()
            status["productboard"] = ok
            errors["productboard"] = err
            st.session_state.connection_status = status
            st.session_state.connection_errors = errors
            st.success("Connected.") if ok else st.error(err)
            st.rerun()
    with c2:
        render_status_grid(status, errors)

    st.divider()
    if st.button("Next: Data Sources →", type="primary"):
        next_step()
        st.rerun()
