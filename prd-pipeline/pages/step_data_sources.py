"""Step 2: Context Selection — load Dovetail projects + Productboard notes first; load insights per selected projects."""
from __future__ import annotations

import logging

import streamlit as st

from app.state import get_api_config, next_step
from components.loading import with_spinner
from services.context_data import (
    fetch_insights_for_project_ids,
    fetch_projects_and_products_only,
)

logger = logging.getLogger(__name__)


def render_step_data_sources() -> None:
    st.header("Step 2: Context Selection")
    st.caption(
        "Load Dovetail projects and Productboard notes, then select projects and load their insights. "
        "Select insights and notes, then go to Prompt Config and Generate PRD."
    )

    cfg = get_api_config()
    if not (cfg.get("dovetail_key") or "").strip() and not (cfg.get("productboard_key") or "").strip():
        st.warning("Configure API keys in Step 1 first.")
        return

    # ---------- Load context (projects + notes only, no Dovetail insights) ----------
    if st.button("Load context", type="primary", key="load_context_btn"):
        with with_spinner("Fetching Dovetail projects and Productboard notes..."):
            data = fetch_projects_and_products_only(
                cfg.get("dovetail_key", "") or "",
                cfg.get("productboard_key", "") or "",
            )
        st.session_state.context_data = data
        st.session_state.data_sources_loaded = True
        st.session_state.dovetail_projects = data.get("dovetail", {}).get("projects", [])
        st.rerun()

    context = st.session_state.get("context_data")
    if not context:
        st.info("Click **Load context** to fetch Dovetail projects and Productboard notes.")
        st.divider()
        if st.button("Next: Prompt Config →", type="primary"):
            next_step()
            st.rerun()
        return

    # Run insights fetch only once per click (in a dedicated run) to avoid loop/multiple API calls
    pending = st.session_state.pop("pending_insights_load", None)
    if pending is not None:
        with with_spinner(f"Loading insights for {len(pending)} project(s)..."):
            by_project = fetch_insights_for_project_ids(
                cfg.get("dovetail_key", "") or "",
                pending,
            )
        for proj in st.session_state.context_data.setdefault("dovetail", {}).setdefault("projects", []):
            pid = str(proj.get("id", ""))
            if pid in by_project:
                proj["insights"] = by_project[pid]
        st.rerun()

    dovetail_data = context.get("dovetail") or {}
    pb_data = context.get("productboard") or {}
    projects = dovetail_data.get("projects") or []
    notes = pb_data.get("notes") or []

    # ---------- Two sections side by side (50% / 50%) with separator ----------
    col_dovetail, col_sep, col_pb = st.columns([1, 0.03, 1])

    with col_dovetail:
        st.subheader("Dovetail Research")
        # Project checkboxes (which projects to load insights for)
        selected_for_loading: list[str] = list(st.session_state.get("selected_dovetail_project_ids_for_loading", []))
        for proj in projects:
            proj_id = str(proj.get("id", ""))
            proj_name = proj.get("name", "Unnamed project")
            key = f"proj_{proj_id}"
            checked = st.checkbox(proj_name, value=(proj_id in selected_for_loading), key=key)
            if checked and proj_id not in selected_for_loading:
                selected_for_loading.append(proj_id)
            elif not checked and proj_id in selected_for_loading:
                selected_for_loading = [x for x in selected_for_loading if x != proj_id]
        st.session_state.selected_dovetail_project_ids_for_loading = selected_for_loading

        if selected_for_loading:
            if st.button("Load insights for selected project(s)", type="secondary", key="load_insights_btn"):
                st.session_state.pending_insights_load = list(selected_for_loading)
                st.rerun()
        else:
            st.caption("Select one or more projects above, then click **Load insights for selected project(s)**.")

        selected_insight_ids: set[str] = set(st.session_state.get("selected_dovetail_insight_ids", []))
        for proj in projects:
            proj_id = proj.get("id", "")
            proj_name = proj.get("name", "Unnamed project")
            insights = proj.get("insights") or []
            if not insights:
                continue
            st.markdown(f"**{proj_name}**")
            for ins in insights:
                iid = str(ins.get("id", ""))
                title = ins.get("title", "(No title)")
                key = f"insight_{iid}"
                checked = st.checkbox(title, value=(iid in selected_insight_ids), key=key)
                if checked:
                    selected_insight_ids.add(iid)
                elif iid in selected_insight_ids:
                    selected_insight_ids.discard(iid)
                if checked:
                    raw_data = ins.get("raw")
                    with st.expander("View full insight data (JSON)", expanded=True):
                        if raw_data is not None:
                            st.json(raw_data)
                        else:
                            st.caption("Full data not available.")
            st.caption("")

        st.session_state.selected_dovetail_insight_ids = list(selected_insight_ids)
        selected_project_ids = set()
        for proj in projects:
            for ins in proj.get("insights") or []:
                if str(ins.get("id", "")) in selected_insight_ids:
                    selected_project_ids.add(proj.get("id", ""))
        st.session_state.selected_dovetail_project_ids = list(selected_project_ids)

    with col_sep:
        st.markdown(
            "<div style='border-left: 2px solid #ccc; min-height: 400px; margin: 0 4px;'></div>",
            unsafe_allow_html=True,
        )

    with col_pb:
        st.subheader("Productboard Notes")
        selected_note_ids: list[str] = list(st.session_state.get("selected_productboard_product_ids", []))
        for note in notes:
            nid = str(note.get("id", ""))
            name = note.get("name", "Unnamed note")
            key = f"note_{nid}"
            if st.checkbox(name, value=(nid in selected_note_ids), key=key):
                if nid not in selected_note_ids:
                    selected_note_ids.append(nid)
            else:
                if nid in selected_note_ids:
                    selected_note_ids = [x for x in selected_note_ids if x != nid]
        st.session_state.selected_productboard_product_ids = selected_note_ids

    st.divider()
    st.caption(
        f"Selected: {len(selected_insight_ids)} insight(s), {len(selected_note_ids)} note(s)."
    )

    st.divider()
    if st.button("Next: Prompt Config →", type="primary"):
        next_step()
        st.rerun()
