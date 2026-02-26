"""Step 2: Data source selection - Dovetail projects, Productboard features/notes."""
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import streamlit as st

from api import dovetail, productboard
from app.state import get_api_config, next_step
from components.data_preview import count_cards, table_from_dicts
from components.loading import with_spinner

logger = logging.getLogger(__name__)


def _fetch_dovetail_projects() -> list:
    cfg = get_api_config()
    return dovetail.get_projects(cfg.get("dovetail_key", ""))


def _fetch_productboard() -> tuple[list, list]:
    cfg = get_api_config()
    features = productboard.get_features(cfg.get("productboard_key", ""))
    notes = productboard.get_notes(cfg.get("productboard_key", ""))
    return features, notes


def render_step_data_sources() -> None:
    st.header("Step 2: Data Source Selection")
    st.caption("Select Dovetail projects and Productboard items to include in the PRD.")

    cfg = get_api_config()
    if not cfg.get("dovetail_key") and not cfg.get("productboard_key"):
        st.warning("Configure API keys in Step 1 first.")
        return

    tab1, tab2, tab3 = st.tabs(["Dovetail", "Productboard", "Summary"])

    with tab1:
        if st.button("Fetch Dovetail projects", key="fetch_dovetail"):
            with with_spinner("Fetching projects..."):
                projects = _fetch_dovetail_projects()
            st.session_state.dovetail_projects = projects
            st.session_state.data_sources_loaded = True
            st.rerun()

        projects = st.session_state.get("dovetail_projects", [])
        if projects:
            options = {f"{p.get('name', p.get('title', str(p.get('id', ''))))} ({p.get('id', '')})": str(p.get("id", "")) for p in projects}
            selected_ids_prev = st.session_state.get("selected_dovetail_project_ids", [])
            default_labels = [l for l, i in options.items() if i in selected_ids_prev]
            selected_labels = st.multiselect(
                "Select projects",
                options=list(options.keys()),
                default=default_labels,
                key="dovetail_multiselect",
            )
            selected_ids = [options[l] for l in selected_labels]
            st.session_state.selected_dovetail_project_ids = selected_ids
            insight_count = 0
            key = get_api_config().get("dovetail_key")
            if key and selected_ids:
                for pid in selected_ids[:3]:
                    insight_count += len(dovetail.get_insights(key, project_id=pid))
            st.metric("Insights (selected projects)", insight_count)
            table_from_dicts(
                [p for p in projects if str(p.get("id", "")) in selected_ids],
                ["id", "name", "title"],
                20,
            )
        else:
            st.caption("Click 'Fetch Dovetail projects' to load.")

    with tab2:
        if st.button("Fetch Productboard", key="fetch_pb"):
            with with_spinner("Fetching features and notes..."):
                features, notes = _fetch_productboard()
            st.session_state.productboard_items = {"features": features, "notes": notes}
            st.session_state.data_sources_loaded = True
            st.rerun()

        # productboard_items is a dict {"features": [...], "notes": [...]}; state default is [] so guard against list
        raw = st.session_state.get("productboard_items", {})
        data = raw if isinstance(raw, dict) else {}
        features = data.get("features", [])
        notes = data.get("notes", [])
        if features or notes:
            all_items = [{"id": f.get("id"), "name": f.get("name", f.get("title", "")), "type": "feature"} for f in features]
            all_items += [{"id": n.get("id"), "name": n.get("name", n.get("title", "")), "type": "note"} for n in notes]
            options = {f"{x.get('name', '')} ({x.get('type', '')})": str(x.get("id", "")) for x in all_items}
            selected_ids_prev = st.session_state.get("selected_productboard_ids", [])
            default_labels_pb = [l for l, i in options.items() if i in selected_ids_prev]
            selected_labels = st.multiselect(
                "Select features/notes",
                options=list(options.keys()),
                default=default_labels_pb,
                key="pb_multiselect",
            )
            selected_ids = [options[l] for l in selected_labels]
            st.session_state.selected_productboard_ids = selected_ids
            count_cards(0, len(selected_ids))
            if all_items:
                table_from_dicts(all_items[:30], ["id", "name", "type"], 30)
        else:
            st.caption("Click 'Fetch Productboard' to load.")

    with tab3:
        d_ids = st.session_state.get("selected_dovetail_project_ids", [])
        p_ids = st.session_state.get("selected_productboard_ids", [])
        count_cards(len(d_ids), len(p_ids))
        st.caption("Selected Dovetail project IDs: " + (", ".join(d_ids) if d_ids else "None"))
        st.caption("Selected Productboard IDs: " + (", ".join(p_ids) if p_ids else "None"))

    st.divider()
    if st.button("Next: Prompt Config →", type="primary"):
        next_step()
        st.rerun()
