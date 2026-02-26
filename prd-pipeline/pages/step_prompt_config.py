"""Step 3: Prompt configuration - template, context, goals, constraints, tone."""
import streamlit as st

from app.state import next_step


def render_step_prompt_config() -> None:
    st.header("Step 3: Prompt Configuration")
    st.caption("Customize how the PRD will be generated.")

    # Ensure defaults exist in session state only once; widgets below
    # will then read/write these keys automatically.
    if "prd_template_id" not in st.session_state:
        st.session_state.prd_template_id = "default"
    if "product_context" not in st.session_state:
        st.session_state.product_context = ""
    if "business_goals" not in st.session_state:
        st.session_state.business_goals = ""
    if "constraints" not in st.session_state:
        st.session_state.constraints = ""
    if "audience_type" not in st.session_state:
        st.session_state.audience_type = "internal_stakeholders"
    if "output_tone" not in st.session_state:
        st.session_state.output_tone = "professional"
    if "include_roadmap" not in st.session_state:
        st.session_state.include_roadmap = True

    # Widgets with key= update st.session_state automatically; we avoid
    # passing value= on every rerun so user input is not overwritten.
    st.selectbox(
        "PRD Template",
        options=["default"],
        format_func=lambda x: x.title(),
        key="prd_template_id",
        index=0,
    )

    st.text_area(
        "Product Context",
        placeholder="Brief description of the product and problem space...",
        height=120,
        key="product_context",
    )

    st.text_area(
        "Business Goals",
        placeholder="What are the business objectives?",
        height=100,
        key="business_goals",
    )

    st.text_area(
        "Constraints",
        placeholder="Technical, timeline, or resource constraints...",
        height=100,
        key="constraints",
    )

    st.selectbox(
        "Audience Type",
        options=["internal_stakeholders", "executives", "engineering", "customers"],
        format_func=lambda x: x.replace("_", " ").title(),
        key="audience_type",
    )

    st.selectbox(
        "Output Tone",
        options=["professional", "concise", "detailed", "conversational"],
        format_func=lambda x: x.title(),
        key="output_tone",
    )

    st.checkbox(
        "Include Roadmap Section",
        key="include_roadmap",
    )

    st.divider()
    if st.button("Next: Generate PRD prompt →", type="primary"):
        # Save prompt config to snapshot before leaving step 3; on step 4 the widget keys
        # are not rendered so Streamlit removes them—we need this copy to build the payload and display.
        st.session_state.generation_prompt_config_snapshot = {
            "prd_template_id": st.session_state.get("prd_template_id", "default"),
            "product_context": st.session_state.get("product_context", ""),
            "business_goals": st.session_state.get("business_goals", ""),
            "constraints": st.session_state.get("constraints", ""),
            "audience_type": st.session_state.get("audience_type", "internal_stakeholders"),
            "output_tone": st.session_state.get("output_tone", "professional"),
            "include_roadmap": st.session_state.get("include_roadmap", True),
        }
        next_step()
        st.rerun()
