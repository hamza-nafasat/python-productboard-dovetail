"""Step 2: Context Selection — load Dovetail + Productboard in parallel, select insights and products."""
from __future__ import annotations

import logging

import streamlit as st

from app.state import get_api_config, next_step
from components.loading import with_spinner
from services.context_data import fetch_context_data

logger = logging.getLogger(__name__)


def render_step_data_sources() -> None:
    st.header("Step 2: Context Selection")
    st.caption(
        "Load Dovetail projects & insights and Productboard products in one go. "
        "Select insights and products, then go to Prompt Config and Generate PRD."
    )

    cfg = get_api_config()
    if not (cfg.get("dovetail_key") or "").strip() and not (cfg.get("productboard_key") or "").strip():
        st.warning("Configure API keys in Step 1 first.")
        return

    # ---------- Load context (parallel fetch) ----------
    if st.button("Load context", type="primary", key="load_context_btn"):
        with with_spinner("Fetching Dovetail projects, insights, and Productboard products in parallel..."):
            data = fetch_context_data(
                cfg.get("dovetail_key", "") or "",
                cfg.get("productboard_key", "") or "",
            )
        st.session_state.context_data = data
        st.session_state.data_sources_loaded = True
        # Sync legacy keys for pipeline: dovetail_projects from context
        st.session_state.dovetail_projects = data.get("dovetail", {}).get("projects", [])
        st.rerun()

    context = st.session_state.get("context_data")
    if not context:
        st.info("Click **Load context** to fetch Dovetail and Productboard data.")
        st.divider()
        if st.button("Next: Prompt Config →", type="primary"):
            next_step()
            st.rerun()
        return

    dovetail_data = context.get("dovetail") or {}
    pb_data = context.get("productboard") or {}
    projects = dovetail_data.get("projects") or []
    products = pb_data.get("products") or []

    # ---------- Section 1: Dovetail Research (projects with insights grouped) ----------
    st.subheader("Section 1 — Dovetail Research")
    selected_insight_ids: set[str] = set(st.session_state.get("selected_dovetail_insight_ids", []))

    for proj in projects:
        proj_id = proj.get("id", "")
        proj_name = proj.get("name", "Unnamed project")
        insights = proj.get("insights") or []
        if not insights:
            st.markdown(f"**{proj_name}**")
            st.caption("No insights")
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
        st.caption("")

    st.session_state.selected_dovetail_insight_ids = list(selected_insight_ids)
    # Derive selected project IDs for pipeline (any project that has a selected insight)
    selected_project_ids = set()
    for proj in projects:
        for ins in proj.get("insights") or []:
            if str(ins.get("id", "")) in selected_insight_ids:
                selected_project_ids.add(proj.get("id", ""))
    st.session_state.selected_dovetail_project_ids = list(selected_project_ids)

    st.divider()

    # ---------- Section 2: Productboard Products ----------
    st.subheader("Section 2 — Productboard Products")
    selected_product_ids: list[str] = list(st.session_state.get("selected_productboard_product_ids", []))

    for prod in products:
        pid = str(prod.get("id", ""))
        name = prod.get("name", "Unnamed product")
        key = f"product_{pid}"
        if st.checkbox(name, value=(pid in selected_product_ids), key=key):
            if pid not in selected_product_ids:
                selected_product_ids.append(pid)
        else:
            if pid in selected_product_ids:
                selected_product_ids = [x for x in selected_product_ids if x != pid]

    st.session_state.selected_productboard_product_ids = selected_product_ids

    st.divider()
    st.caption(
        f"Selected: {len(selected_insight_ids)} insight(s), {len(selected_product_ids)} product(s)."
    )

    st.divider()
    if st.button("Next: Prompt Config →", type="primary"):
        next_step()
        st.rerun()
