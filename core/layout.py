"""Cadre de section commun : bordure avec le titre pose sur le trait (style CSS dans core/ui.py)."""
import streamlit as st


def section(key, icon, title):
    box = st.container(border=True, key=f"sec_{key}")
    box.markdown(f"{icon} **{title}**")
    return box
