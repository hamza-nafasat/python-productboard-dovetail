"""Markdown editor with side-by-side preview."""
import streamlit as st
from typing import Callable, Optional


def render_editor_and_preview(
    value: str,
    key: str = "prd_editor",
    height: int = 400,
    on_change: Optional[Callable[[], None]] = None,
) -> str:
    """
    Two columns: left = text_area for Markdown, right = st.markdown preview.
    Returns the current text (from session state if key is used).
    """
    col1, col2 = st.columns(2)
    with col1:
        text = st.text_area(
            "Edit PRD (Markdown)",
            value=value,
            height=height,
            key=key,
            on_change=on_change,
        )
    with col2:
        st.caption("Preview")
        if text:
            st.markdown(text)
        else:
            st.caption("No content yet.")
    return text


def extract_section_by_heading(
    md: str, heading: str
) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Find a section that starts with the given heading (e.g. '## 2. Business Goals').
    Returns (section_content, before, after) or (None, None, None) if not found.
    """
    lines = md.split("\n")
    start = -1
    end = -1
    target = heading.strip().lower()
    for i, line in enumerate(lines):
        if line.strip().lower().startswith("#") and target in line.strip().lower():
            start = i
            break
    if start < 0:
        return None, None, None
    # Find next heading of same or higher level
    level = 0
    for c in lines[start]:
        if c == "#":
            level += 1
        else:
            break
    for i in range(start + 1, len(lines)):
        if lines[i].strip().startswith("#"):
            l = 0
            for c in lines[i]:
                if c == "#":
                    l += 1
                else:
                    break
            if l <= level:
                end = i
                break
    if end < 0:
        end = len(lines)
    section = "\n".join(lines[start:end])
    before = "\n".join(lines[:start]) if start > 0 else ""
    after = "\n".join(lines[end:]) if end < len(lines) else ""
    return section, before or None, after or None
