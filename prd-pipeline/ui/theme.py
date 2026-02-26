"""Dark/light theme and custom CSS."""
import streamlit as st


def apply_theme() -> None:
    """Apply theme from st.session_state.dark_mode and inject CSS for a modern look."""
    dark = st.session_state.get("dark_mode", False)
    # Streamlit theme is set via query params or config; we use custom CSS for accents
    st.markdown(
        """
    <style>
    /* Card-style containers */
    .stBlockContainer { padding-top: 0.5rem; }
    div[data-testid="stVerticalBlock"] > div { border-radius: 8px; }
    /* Progress in sidebar */
    .step-item { padding: 0.4rem 0; font-size: 0.95rem; }
    .step-done { color: var(--text-secondary); }
    .step-active { font-weight: 600; }
    </style>
    """,
        unsafe_allow_html=True,
    )


def render_theme_toggle() -> None:
    """Render a toggle for dark/light mode in the sidebar."""
    label = "Dark Mode" if not st.session_state.get("dark_mode", False) else "Light Mode"
    if st.button(label, key="theme_toggle"):
        st.session_state.dark_mode = not st.session_state.get("dark_mode", False)
        st.rerun()
