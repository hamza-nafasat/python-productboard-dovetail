"""Connection status indicators and test buttons."""
import streamlit as st
from typing import Optional


def status_indicator(ok: bool, label: str, error: Optional[str] = None) -> None:
    """Show a single service status: green check or red cross + optional error."""
    if ok:
        st.success(f"✓ {label}")
    else:
        st.error(f"✗ {label}" + (f" — {error}" if error else ""))


def render_status_grid(status: dict[str, bool], errors: Optional[dict[str, str]] = None) -> None:
    """Render a grid of connection statuses. status: { 'dovetail': True, ... }."""
    errors = errors or {}
    cols = st.columns(2)
    for idx, (name, ok) in enumerate(status.items()):
        with cols[idx % 2]:
            status_indicator(ok, name.replace("_", " ").title(), errors.get(name))
