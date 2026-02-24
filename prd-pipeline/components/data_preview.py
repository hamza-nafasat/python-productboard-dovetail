"""Data preview: tables, counts (insights, feedback)."""
import streamlit as st
from typing import Any, List


def count_cards(insight_count: int, feedback_count: int) -> None:
    """Show two metric-style cards for insight and feedback counts."""
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Insights (Dovetail)", insight_count)
    with c2:
        st.metric("Feedback items (Productboard)", feedback_count)


def table_from_dicts(items: List[dict[str, Any]], columns: List[str], max_rows: int = 50) -> None:
    """Show a dataframe-style table from list of dicts. columns = ['id','name',...]."""
    if not items:
        st.caption("No items.")
        return
    limited = items[:max_rows]
    data = {col: [str(it.get(col, ""))[:80] for it in limited] for col in columns}
    st.dataframe(data, use_container_width=True)
