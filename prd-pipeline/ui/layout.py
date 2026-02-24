"""Common layout: cards, tabs, containers."""
import streamlit as st
from typing import Any, Callable, Optional


def card(title: str, content: Callable[[], Any], key: Optional[str] = None) -> None:
    """Render a section inside an expander (card-like)."""
    with st.expander(title, expanded=True, key=key):
        content()


def tabs(tab_names: list[str], key: str = "tabs") -> Any:
    """Return streamlit tabs. Usage: t1, t2 = tabs(['A','B']); with t1: ..."""
    return st.tabs(tab_names)
