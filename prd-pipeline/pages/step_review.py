"""Step 5: PRD review - markdown editor, side-by-side preview, section regeneration."""
import difflib
import logging
from concurrent.futures import ThreadPoolExecutor

import streamlit as st

from api.anthropic_client import regenerate_section
from app.run_async import run_async
from app.state import get_api_config, next_step
from components.markdown_editor import extract_section_by_heading, render_editor_and_preview

logger = logging.getLogger(__name__)
_executor = ThreadPoolExecutor(max_workers=1)

_versions: list[dict] = []  # [{version, text}, ...]


def _regenerate_section(section: str, context: str, api_key: str) -> str:
    return run_async(regenerate_section(section, context, api_key))


def render_step_review() -> None:
    st.header("Step 5: PRD Review")
    st.caption("Edit the PRD, preview live, or regenerate a section with Claude.")

    current = st.session_state.get("current_prd_text", "")
    if not current:
        st.warning("No PRD content yet. Generate one in Step 4.")
        return

    # Editor and preview
    new_text = render_editor_and_preview(
        current,
        key="review_editor",
        height=450,
    )
    if new_text != current:
        st.session_state.current_prd_text = new_text

    # Use latest text for section extraction
    text_for_sections = st.session_state.get("current_prd_text", "")

    st.divider()
    st.subheader("Section regeneration")
    headings = [
        line.strip() for line in text_for_sections.split("\n")
        if line.strip().startswith("#") and len(line.strip()) > 1
    ]
    if headings:
        chosen = st.selectbox(
            "Select section to regenerate",
            options=headings,
            key="section_heading",
        )
        if st.button("Regenerate this section", key="regen_sec"):
            section, before, after = extract_section_by_heading(text_for_sections, chosen)
            if section:
                cfg = get_api_config()
                api_key = cfg.get("anthropic_key", "")
                if api_key:
                    with st.spinner("Regenerating..."):
                        context = (before or "") + "\n[...]\n" + (after or "")
                        try:
                            new_section = _regenerate_section(section, context, api_key)
                            # Replace section in full text
                            full = (before or "") + "\n" + new_section + "\n" + (after or "")
                            if not full.strip():
                                full = new_section
                            st.session_state.current_prd_text = full
                            st.session_state.current_prd_version = st.session_state.get("current_prd_version", 1) + 1
                            st.success("Section updated.")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))
                else:
                    st.error("Set Anthropic API key in Step 1.")
            else:
                st.warning("Section not found.")
    else:
        st.caption("No headings found for section regeneration.")

    # Version comparison
    if "prd_versions" not in st.session_state:
        st.session_state.prd_versions = []
    versions = st.session_state.prd_versions
    if new_text and (not versions or versions[-1].get("text") != new_text):
        # Optionally snapshot current as new version for comparison
        pass  # we don't auto-snapshot on every edit; user can "Save version"
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
            st.text_area("Diff", value="\n".join(diff), height=200, key="diff_view")

    st.divider()
    if st.button("Next: Publish to Confluence →", type="primary"):
        next_step()
        st.rerun()
