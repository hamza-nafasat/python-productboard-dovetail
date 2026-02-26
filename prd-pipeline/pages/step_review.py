"""Step 5: PRD review - markdown editor, side-by-side preview, paste from AI tool."""
import difflib
import logging

import streamlit as st

from app.state import next_step
from components.markdown_editor import render_editor_and_preview

logger = logging.getLogger(__name__)


def render_step_review() -> None:
    st.header("Step 5: PRD Review")
    st.caption("Paste your PRD from your AI tool, then edit and preview before publishing.")

    current = st.session_state.get("current_prd_text", "")

    # If no content yet, offer paste-from-AI-tool
    if not current:
        st.info("Paste the PRD you generated with your AI tool below, then click **Load PRD** to edit and publish.")
        pasted = st.text_area(
            "Paste PRD From Your AI Tool",
            value=st.session_state.get("paste_prd_input", ""),
            height=200,
            placeholder="Paste your full PRD markdown here...",
            key="paste_prd_input",
        )
        if st.button("Load PRD", type="primary", key="load_pasted_prd"):
            # Use session state so we have the value after the button click
            content = st.session_state.get("paste_prd_input", "") or pasted
            if content and str(content).strip():
                st.session_state.current_prd_text = str(content).strip()
                st.rerun()
            else:
                st.warning("Please paste some content first.")
        return

    # Editor and preview
    new_text = render_editor_and_preview(
        current,
        key="review_editor",
        height=450,
    )
    if new_text != current:
        st.session_state.current_prd_text = new_text

    # Version comparison
    if "prd_versions" not in st.session_state:
        st.session_state.prd_versions = []
    versions = st.session_state.prd_versions
    if st.button("Save current as version snapshot", key="save_ver"):
        v = st.session_state.get("current_prd_version", 1)
        versions.append({"version": v, "text": st.session_state.current_prd_text})
        st.session_state.prd_versions = versions
        st.session_state.current_prd_version = v + 1
        st.rerun()

    if len(versions) >= 2:
        st.subheader("Version comparison")
        v1 = st.selectbox("Version A", range(len(versions)), format_func=lambda i: f"v{versions[i]['version']}", key="v1")
        v2 = st.selectbox("Version B", range(len(versions)), format_func=lambda i: f"v{versions[i]['version']}", key="v2")
        if v1 != v2:
            a = versions[v1]["text"].splitlines()
            b = versions[v2]["text"].splitlines()
            diff = list(difflib.unified_diff(a, b, lineterm=""))
            st.text_area("Diff View", value="\n".join(diff), height=200, key="diff_view")

    st.divider()
    if st.button("Next: Publish to Confluence →", type="primary"):
        next_step()
        st.rerun()
