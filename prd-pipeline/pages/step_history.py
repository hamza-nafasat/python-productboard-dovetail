"""Step 7: History & Audit - list past PRDs, metadata, load or export."""
import streamlit as st

from services.history import get_entry, list_entries


def render_step_history() -> None:
    st.header("Step 5: History & Audit")
    st.caption("Generated PRDs and metadata (stored locally).")

    entries = list_entries(limit=50)
    if not entries:
        st.info("No PRDs in history yet. Generate one in Step 4.")
        return

    for e in entries:
        with st.expander(f"{e.get('title', 'Untitled')} — {e.get('timestamp', '')[:19]}", expanded=False):
            st.caption(f"ID: {e.get('id')} | Run: {e.get('pipeline_run_id', '')} | Version: {e.get('version', 1)}")
            st.json({
                "timestamp": e.get("timestamp"),
                "selected_dovetail_ids": e.get("selected_dovetail_ids", []),
                "selected_productboard_ids": e.get("selected_productboard_ids", []),
            })
            st.download_button(
                "Download Markdown",
                data=e.get("content", ""),
                file_name=f"prd_{e.get('id', '')}.md",
                mime="text/markdown",
                key=f"dl_{e.get('id')}",
            )
            st.text_area("Content Preview", value=(e.get("content", ""))[:2000] + "...", height=120, disabled=True, key=f"prev_{e.get('id')}")
