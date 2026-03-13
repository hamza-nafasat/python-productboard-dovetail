"""Step 2: Context Selection — load Dovetail projects + Productboard notes first; load insights per selected projects."""
from __future__ import annotations

import logging

import streamlit as st

from app.state import get_api_config, next_step
from components.loading import with_spinner
from services.context_data import (
    fetch_dovetail_projects_only,
    fetch_insights_for_project_ids,
    fetch_productboard_notes_only,
)

logger = logging.getLogger(__name__)


def render_step_data_sources() -> None:
    st.header("Step 2: Context Selection")
    st.caption(
        "Use **Tab 1 (Dovetail)** to fetch projects and insights, then **Tab 2 (Productboard)** to fetch and select notes. "
        "Then go to Step 3."
    )
    cfg = get_api_config()
    if not (cfg.get("dovetail_key") or "").strip() and not (cfg.get("productboard_key") or "").strip():
        st.warning("Configure API keys in Step 1 first.")
        return

    # Ensure context_data exists so both tabs can merge their fetch results
    if st.session_state.get("context_data") is None:
        st.session_state.context_data = {
            "dovetail": {"projects": []},
            "productboard": {"notes": []},
        }

    context = st.session_state.context_data

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

    # Scrollable tab content
    st.markdown("""
    <style>
    /* Scrollable tab content */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
        max-height: 65vh;
        overflow-y: auto;
        overflow-x: hidden;
    }
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]::-webkit-scrollbar { width: 8px; }
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.2); border-radius: 4px; }
    .streamlit-expanderHeader { font-weight: 500; }
    </style>
    """, unsafe_allow_html=True)

    # ---------- Tabs: Dovetail (first) and Productboard (second) ----------
    tab_dovetail, tab_productboard = st.tabs(["Dovetail Research", "Productboard Notes"])

    with tab_dovetail:
        st.caption("Fetch Dovetail projects, then select projects and load insights, then pick which insights to include.")
        if st.button("Fetch Dovetail", type="primary", key="fetch_dovetail_btn"):
            with with_spinner("Fetching Dovetail projects..."):
                dovetail_slice = fetch_dovetail_projects_only(cfg.get("dovetail_key", "") or "")
            st.session_state.context_data.setdefault("dovetail", {})["projects"] = dovetail_slice.get("projects", [])
            st.rerun()
        dovetail_search = (st.text_input("Search projects", key="dovetail_search", placeholder="Type to filter by name...") or "").strip().lower()
        if dovetail_search:
            projects_filtered = [p for p in projects if dovetail_search in (p.get("name") or "").lower()]
        else:
            projects_filtered = projects
        st.markdown("**Projects**")
        selected_for_loading: list[str] = list(st.session_state.get("selected_dovetail_project_ids_for_loading", []))
        for proj in projects_filtered:
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

        st.divider()
        st.markdown("**Insights**")
        selected_insight_ids: set[str] = set(st.session_state.get("selected_dovetail_insight_ids", []))
        for proj in projects_filtered:
            proj_id = proj.get("id", "")
            proj_name = proj.get("name", "Unnamed project")
            insights = proj.get("insights") or []
            if not insights:
                continue
            with st.expander(f"▸ {proj_name} ({len(insights)} insight(s))", expanded=False, key=f"exp_proj_{proj_id}"):
                for ins in insights:
                    iid = str(ins.get("id", ""))
                    title = ins.get("title", "(No title)")
                    key = f"insight_{proj_id}_{iid}"
                    checked = st.checkbox(title, value=(iid in selected_insight_ids), key=key)
                    if checked:
                        selected_insight_ids.add(iid)
                    elif iid in selected_insight_ids:
                        selected_insight_ids.discard(iid)
                    if checked:
                        raw_data = ins.get("raw")
                        with st.expander("View full data (JSON)", expanded=False, key=f"exp_raw_{proj_id}_{iid}"):
                            if raw_data is not None:
                                st.json(raw_data)
                            else:
                                st.caption("Full data not available.")

        st.session_state.selected_dovetail_insight_ids = list(selected_insight_ids)
        selected_project_ids = set()
        for proj in projects:
            for ins in proj.get("insights") or []:
                if str(ins.get("id", "")) in selected_insight_ids:
                    selected_project_ids.add(proj.get("id", ""))
        st.session_state.selected_dovetail_project_ids = list(selected_project_ids)

    with tab_productboard:
        st.caption("Fetch Productboard notes, then select which notes to include in the PRD context.")
        if st.button("Fetch Productboard", type="primary", key="fetch_productboard_btn"):
            with with_spinner("Fetching Productboard notes..."):
                pb_slice = fetch_productboard_notes_only(cfg.get("productboard_key", "") or "")
            st.session_state.context_data.setdefault("productboard", {})["notes"] = pb_slice.get("notes", [])
            st.rerun()
        pb_search = (st.text_input("Search notes", key="productboard_search", placeholder="Type to filter by name or title...") or "").strip().lower()
        if pb_search:
            notes_filtered = [
                n for n in notes
                if pb_search in (n.get("name") or "").lower()
                or (isinstance(n.get("raw"), dict) and pb_search in str((n.get("raw") or {}).get("title", "")).lower())
            ]
        else:
            notes_filtered = notes
        st.markdown("**Notes**")
        selected_note_ids: list[str] = list(st.session_state.get("selected_productboard_product_ids", []))
        for note in notes_filtered:
            nid = str(note.get("id", ""))
            name = note.get("name", "Unnamed note")
            key = f"note_{nid}"
            checked = st.checkbox(name, value=(nid in selected_note_ids), key=key)
            if checked:
                if nid not in selected_note_ids:
                    selected_note_ids.append(nid)
            else:
                if nid in selected_note_ids:
                    selected_note_ids = [x for x in selected_note_ids if x != nid]
            if checked:
                raw_data = note.get("raw")
                with st.expander("View full data (JSON)", expanded=False, key=f"exp_raw_note_{nid}"):
                    if raw_data is not None:
                        st.json(raw_data)
                    else:
                        st.caption("Full data not available.")
        st.session_state.selected_productboard_product_ids = selected_note_ids

    st.divider()
    st.caption(
        f"**Selected:** {len(selected_insight_ids)} insight(s), {len(selected_note_ids)} note(s)."
    )
    if st.button("Next: Generate PRD prompt →", type="primary"):
        next_step()
        st.rerun()
