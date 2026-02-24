"""Step 1: API Configuration - keys, Confluence URL/space, test connection."""
import logging

import streamlit as st

from api import confluence, dovetail, productboard
from api.anthropic_client import test_connection as anthropic_test
from app.run_async import run_async
from app.state import get_api_config, next_step
from components.connection_status import render_status_grid
from components.forms import secret_input, test_button
from core.models import APIConfig

logger = logging.getLogger(__name__)


def _test_dovetail() -> tuple[bool, str]:
    cfg = get_api_config()
    return dovetail.test_connection(cfg.get("dovetail_key", ""))


def _test_productboard() -> tuple[bool, str]:
    cfg = get_api_config()
    return productboard.test_connection(cfg.get("productboard_key", ""))


def _test_anthropic() -> tuple[bool, str]:
    cfg = get_api_config()
    return run_async(anthropic_test(cfg.get("anthropic_key", "")))


def _test_confluence() -> tuple[bool, str]:
    cfg = get_api_config()
    return confluence.test_connection(
        cfg.get("confluence_base_url", ""),
        cfg.get("confluence_key", ""),
        cfg.get("confluence_space"),
    )


def render_step_setup() -> None:
    st.header("Step 1: Setup / API Configuration")
    st.caption("Enter API keys and Confluence settings. Keys are stored only in this session.")

    cfg = st.session_state.get("api_config", {})

    with st.form("api_config_form", clear_on_submit=False):
        st.subheader("API Keys")
        dovetail_key = secret_input("Dovetail API key", "dovetail_key", cfg.get("dovetail_key", ""))
        productboard_key = secret_input(
            "Productboard API key", "productboard_key", cfg.get("productboard_key", "")
        )
        anthropic_key = secret_input("Anthropic API key", "anthropic_key", cfg.get("anthropic_key", ""))
        confluence_key = secret_input(
            "Confluence API key (or email:api_token for Cloud)",
            "confluence_key",
            cfg.get("confluence_key", ""),
        )
        st.subheader("Confluence")
        confluence_base_url = st.text_input(
            "Confluence base URL",
            value=cfg.get("confluence_base_url", ""),
            placeholder="https://your-domain.atlassian.net/wiki",
            key="confluence_base_url",
        )
        confluence_space = st.text_input(
            "Confluence space key",
            value=cfg.get("confluence_space", ""),
            placeholder="PRD",
            key="confluence_space",
        )

        submitted = st.form_submit_button("Save configuration")
        if submitted:
            st.session_state.api_config = {
                "dovetail_key": dovetail_key,
                "productboard_key": productboard_key,
                "anthropic_key": anthropic_key,
                "confluence_key": confluence_key,
                "confluence_base_url": confluence_base_url.strip(),
                "confluence_space": confluence_space.strip(),
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
        if st.button("Test Anthropic", key="test_anthropic_btn"):
            with st.spinner("Testing Anthropic..."):
                ok, err = _test_anthropic()
            status["anthropic"] = ok
            errors["anthropic"] = err
            st.session_state.connection_status = status
            st.session_state.connection_errors = errors
            st.success("Connected.") if ok else st.error(err)
            st.rerun()
        if st.button("Test Confluence", key="test_confluence_btn"):
            with st.spinner("Testing Confluence..."):
                ok, err = _test_confluence()
            status["confluence"] = ok
            errors["confluence"] = err
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
