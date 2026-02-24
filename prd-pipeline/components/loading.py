"""Loading skeletons and spinners."""
import streamlit as st
from typing import Optional


def skeleton_lines(count: int = 5, key: Optional[str] = None) -> None:
    """Placeholder lines while content loads."""
    for i in range(count):
        st.markdown("---")
    if key:
        st.empty()


def with_spinner(label: str = "Loading..."):
    """Context manager for spinner. Usage: with with_spinner('Fetching...'): ..."""
    return st.spinner(label)
