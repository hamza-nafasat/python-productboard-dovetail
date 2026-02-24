"""Sidebar: step navigation and progress."""
import streamlit as st

from app.config import STEP_NAMES, TOTAL_STEPS
from app.state import set_step
from ui.theme import render_theme_toggle


def render_sidebar() -> None:
    with st.sidebar:
        st.title("PRD Pipeline")
        st.caption("Multi-step workflow")
        st.divider()

        current = st.session_state.get("step", 1)
        visited = st.session_state.get("step_visited", set())

        for i in range(1, TOTAL_STEPS + 1):
            label = f"Step {i}: {STEP_NAMES[i - 1]}"
            is_done = i < current or (i == current and current in visited)
            is_active = i == current
            if is_active:
                st.markdown(f"**{label}**")
            else:
                if st.button(label, key=f"sidebar_step_{i}"):
                    set_step(i)
                    st.rerun()
        st.divider()
        progress = current / TOTAL_STEPS
        st.progress(progress)
        st.caption(f"Step {current} of {TOTAL_STEPS}")
        st.divider()
        render_theme_toggle()
