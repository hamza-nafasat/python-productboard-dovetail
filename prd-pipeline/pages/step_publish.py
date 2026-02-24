"""Step 6: Publish to Confluence - page title, parent, space, preview, publish."""
import logging

import streamlit as st

from api import confluence
from app.state import get_api_config, next_step

logger = logging.getLogger(__name__)


def render_step_publish() -> None:
    st.header("Step 6: Publish to Confluence")
    st.caption("Set page title, parent page, and space; then publish.")

    current = st.session_state.get("current_prd_text", "")
    cfg = get_api_config()
    base_url = cfg.get("confluence_base_url", "").strip()
    space_key = cfg.get("confluence_space", "").strip()
    api_key = cfg.get("confluence_key", "").strip()

    if not current:
        st.warning("No PRD to publish. Generate and review in Steps 4–5.")
        return
    if not base_url or not api_key:
        st.warning("Configure Confluence base URL and API key in Step 1.")
        return

    # Default title from first line of PRD
    default_title = (current.split("\n")[0] or "PRD").replace("#", "").strip()
    page_title = st.text_input(
        "Page title",
        value=st.session_state.get("confluence_page_title", "") or default_title,
        key="publish_page_title",
    )
    st.session_state.confluence_page_title = page_title

    if space_key:
        st.caption(f"Space: {space_key}")
    else:
        space_key = st.text_input("Confluence space key", value="", key="publish_space")
    pages_in_space = []
    if base_url and api_key and space_key:
        pages_in_space = confluence.get_pages(base_url, api_key, space_key)
    parent_options = ["(None - top level)"] + [f"{p.get('title', '')} ({p.get('id', '')})" for p in pages_in_space]
    parent_choice = st.selectbox("Parent page", options=parent_options, key="parent_choice")
    parent_id = None
    if parent_choice and parent_choice != "(None - top level)":
        try:
            parent_id = parent_choice.split("(")[-1].rstrip(")")
        except Exception:
            pass

    st.subheader("Preview")
    st.markdown(current[:3000] + ("..." if len(current) > 3000 else ""))

    if st.button("Publish to Confluence", type="primary", key="publish_btn"):
        if not page_title or not space_key:
            st.error("Page title and space key are required.")
        else:
            with st.spinner("Publishing..."):
                try:
                    html = confluence.markdown_to_confluence_storage(current)
                    result = confluence.create_page(
                        base_url=base_url,
                        api_key=api_key,
                        space_key=space_key,
                        title=page_title,
                        body_storage_html=html,
                        parent_id=parent_id,
                    )
                    page_id = result.get("id")
                    links = result.get("_links", {})
                    webui = links.get("webui", "")
                    url = f"{base_url.rstrip('/')}{webui}" if webui else ""
                    st.success(f"Published. Page ID: {page_id}")
                    if url:
                        st.link_button("Open in Confluence", url)
                    st.session_state.confluence_parent_page_id = str(page_id) if page_id else ""
                except Exception as e:
                    logger.exception("Publish failed: %s", e)
                    st.error(str(e))

    st.divider()
    if st.button("Next: History & Audit →", type="primary"):
        next_step()
        st.rerun()
