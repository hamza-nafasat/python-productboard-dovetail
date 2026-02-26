"""Step 3: Prompt configuration - template, context, goals, constraints, tone."""
import streamlit as st

from app.state import next_step


def render_step_prompt_config() -> None:
    st.header("Step 3: Prompt Configuration")
    st.caption("Customize how the PRD will be generated.")

    # Widgets with key= update st.session_state automatically; do not assign to those keys after creation
    st.selectbox(
        "PRD template",
        options=["default"],
        key="prd_template_id",
        index=0,
    )

    st.text_area(
        "Product context",
        value=st.session_state.get("product_context", ""),
        placeholder="Brief description of the product and problem space...",
        height=120,
        key="product_context",
    )

    st.text_area(
        "Business goals",
        value=st.session_state.get("business_goals", ""),
        placeholder="What are the business objectives?",
        height=100,
        key="business_goals",
    )

    st.text_area(
        "Constraints",
        value=st.session_state.get("constraints", ""),
        placeholder="Technical, timeline, or resource constraints...",
        height=100,
        key="constraints",
    )

    st.selectbox(
        "Audience type",
        options=["internal_stakeholders", "executives", "engineering", "customers"],
        format_func=lambda x: x.replace("_", " ").title(),
        key="audience_type",
    )

    st.selectbox(
        "Output tone",
        options=["professional", "concise", "detailed", "conversational"],
        key="output_tone",
    )

    st.checkbox(
        "Include roadmap section",
        value=st.session_state.get("include_roadmap", True),
        key="include_roadmap",
    )

    st.divider()
    if st.button("Next: Generate PRD prompt →", type="primary"):
        next_step()
        st.rerun()
